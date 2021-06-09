# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from datetime import datetime
from math import sqrt
import numpy as np
import random
import re
from typing import List

from azure.quantum import Workspace
from azure.quantum.optimization import Problem , ProblemType , Term , ParallelTempering , SimulatedAnnealing , Tabu

from util.tFunctions import *
from util.benchmark00 import *

# Workspace information
workspace = Workspace(
    subscription_id =   'xxx', # add your subscription_id
    resource_group =    'xxx', # add your resource_group
    name =              'xxx', # add your workspace name
)

print ( 'init...' )

workspace.login()
print ( 'login successful' )

# hc + tsp + knapsack / Lucas:  arXiv:1302.5843v3 [cond-mat.stat-mech] 24 Jan 2014

# loc [ 0 ] == depot ( ie, v = 0 ); loc [ v ] [ 0 ] == x coord of v; loc [ v ] [ 1 ] == y coord of v; loc [ v ] [ 2 ] == capacity of load at v
# j ranges from 0 ( starting point = depot ) to nLoc + 1 ( ending point = depot )
# the cycle that a vehicle follows starts and ends at v = 0; with the last n j values at v = 0

loc = getLoc ()
nLoc = len ( loc )
nVehicle = getNVehicle ()
nCapacity = getNCapacity ()
akIndexBase = ( nLoc - 1 ) * nVehicle * ( nLoc + 1 )  + nLoc * nVehicle + nVehicle
nkIndexBase = nLoc * nVehicle
nkIndexMax = ( nCapacity + 1 ) * nVehicle
fix = dict () # global dict for fixing solver variables

penalty = [ 1.0 for _ in range ( 10 ) ]

def vjk_index ( v , j , k ) :
    # vertex v ( loc [ v ] ) -- range ( nLoc )
    # step j in route        -- range ( nLoc + 1 )
    # vehicle k              -- range ( nVehicle )
    return v * nVehicle * ( nLoc + 1 )  + j * nVehicle + k 

def invert_vjk_index ( s ) :
    v = int ( s / ( ( nLoc + 1 ) * nVehicle ) )
    j = int ( ( s - ( nLoc + 1 ) * nVehicle * v ) / nVehicle )
    k = s - nVehicle * j - ( nLoc + 1 ) * nVehicle * v
    return ( v , j , k )

def ak_index ( a , k ) :
    # capacity index a ( loc [ a ] [ 2 ] ) -- range ( nLoc )
    # vehicle k                            -- range ( nVehicle )
    return akIndexBase + nVehicle * a + k

def invert_ak_index ( s ) :
    a = int ( ( s - akIndexBase ) / nVehicle )
    k = s - akIndexBase - nVehicle * a
    return ( a , k )

def nk_index ( n , k ) :
    # n is index in capacities -- range ( nCapacity + 1 )
    # vehicle k
    return akIndexBase + nkIndexBase + nVehicle * n + k

def invert_nk_index ( s ) :
    n = int ( ( s - akIndexBase - nkIndexBase ) / nVehicle )
    k = s - akIndexBase - nkIndexBase - nVehicle * n
    return ( n , k )

print ( 'nLoc-> {} nVehicle-> {} nCapacity-> {} akIndexBase-> {} nkIndexBase-> {} nkIndexMax-> {}'.format ( 
                                                                            nLoc , nVehicle , nCapacity , akIndexBase , nkIndexBase, nkIndexMax ) )

def cost ( u , v ) :
    return sqrt ( ( loc [ v ] [ 0 ] - loc [ u ] [ 0 ] ) ** 2 + ( loc [ v ] [ 1 ] - loc [ u ] [ 1 ] ) ** 2 )

def maxDistance () :
    c = 0.0
    for u in range ( nLoc ) :
        for v in range ( nLoc ) :
            if ( u != v ) :
                c = max ( c , cost ( u , v ) )
    return c

def tspSolutionCost () :
    sCost = 0
    for u , v in [ ( 0 , 4 ) , ( 4 , 3 ) , ( 3 , 8 ) , ( 8 , 1 ) , ( 1 , 0 ) ] :
        sCost += cost ( u , v )
    for u , v in [ ( 0 , 7 ) , ( 7 , 6 ) , ( 6 , 5 ) , ( 5 , 2 ) , ( 2 , 0 ) ] :
        sCost += cost ( u , v )
    return sCost

def setPenalties () :
    # tsp : p0 * h1 + p1 * h2 + p3 * h3 + p4 * h4
    #    0 < p4 * maxCost < p0 = p1 = p3
    # knapsack :  p5 * h5 + p6 * h6 + p7 * h7
    #    0 < p7 * maxCost < p5 = p6 
    # bridge : p8 * h8
    #    p8 = p5 = p6
    # multiple vehicles : p9 * h9
    #    p9 = 2 * p0

    #maxC = ( maxDistance () / 2 ) * nCapacity * nVehicle
    #maxC = maxDistance ()
    maxC = tspSolutionCost ()
    print ( 'max cost {}'.format ( maxC ) )
    #penalty [ 2 ] = 64
    penalty [ 4 ] = 2.0
    penalty [ 0 ] = penalty [ 1 ] = penalty [ 3 ] = penalty [ 4 ] * float ( round ( maxC ) )
    penalty [ 9 ] = penalty [ 0 ]
    penalty [ 7 ] = 2.0
    penalty [ 5 ] = penalty [ 6 ] =  penalty [ 8 ] = penalty [ 7 ] * float ( round ( maxC ) )
    print ( ' penalties : ' )
    for p in range ( len ( penalty ) ) :
        print ( '{} -> {}'.format ( p , penalty [ p ] ) )
    print ( ' ' )

def timeStamp ( msg : str ) :
    print ( msg + ': ' + datetime.now ().strftime ( '%H:%M:%S') )

def h1Terms () -> List [ Term ] :
    # every v should appear once in a cycle ( except v = 0 at j = 0 and j = nLoc + 1 )
    timeStamp ( 'h1' )
    terms = []
    for k in range ( nVehicle ) :
        for v in range ( 1 , nLoc ) :
            jTerms = []
            jTerms.append ( Term ( c = 1.0 , indices = [ ] ) )
            for j in range ( nLoc + 1 ) :
                jTerms.append ( Term ( c = -1.0 , indices = [ vjk_index ( v , j , k ) ] ) )
            terms += tSquare ( jTerms )
    return tMultiply ( terms , [ Term ( c = penalty [ 0 ] , indices = [] ) ] )

def h2Terms () -> List [ Term ] :
    # for each vehicle's cycle, every j should appear once in a cycle ( including 0 and n + 1 )
    timeStamp ( 'h2' )
    terms = []
    for k in range ( nVehicle ) :
        for j in range ( nLoc + 1 ) :
            vTerms = []
            vTerms.append ( Term ( c = 1.0 , indices = [ ] ) )
            for v in range ( nLoc ) :
                vTerms.append ( Term ( c = -1.0 , indices = [ vjk_index ( v , j , k ) ] ) )
            terms += tSquare ( vTerms )
    return tMultiply ( terms , [ Term ( c = penalty [ 1 ] , indices = [] ) ] )
'''
def p2Terms () -> List [ Term ] :
    # try to force starting and ending nodes = 0 ( penalize all other j for v0 )
    terms = []
    for k in range ( nVehicle ) :
        for j in range ( 1 , nLoc ) :
            terms.append ( Term ( c = penalty [ 2 ] , indices = [ vjk_index ( 0 , j , k ) ] ) )
    return tSimplify ( terms )
'''
def h3Terms () -> List [ Term ] :
    # for each vehicle's cycle, an edge does not trace to itself -- except v = 0
    timeStamp ( 'h3' )
    terms = []
    for k in range ( nVehicle ) :
        for v in range ( 1 , nLoc ) :
            for j in range ( nLoc ) :
                terms.append ( Term ( c = penalty [ 3 ] , indices = [ vjk_index ( v , j , k ) , vjk_index ( v , j + 1 , k ) ] ) )
    return tSimplify ( terms )

def h4Terms () -> List [ Term ] :
    # minimize each vehicle's cost of making cycle ( euclidian distance )
    timeStamp ( 'h4' )
    terms = []
    for k in range ( nVehicle ) :
        for u in range ( nLoc ) :
            for v in range ( nLoc ) :
                if ( u != v ) :
                    for j in range ( nLoc ) :
                        terms.append ( Term ( c = cost ( u , v ) , indices = [ vjk_index ( u , j , k ) , vjk_index ( v , j + 1 , k ) ] ) )
    return tMultiply ( terms , [ Term ( c = penalty [ 4 ] , indices = [] ) ] )

def h9Terms () -> List [ Term ] :
    # every v should appear in only one vehicle's cycle, except v = 0
    timeStamp ( 'h9' )
    terms = []
    for v in range ( 1 , nLoc ) :
        kjTerms = []
        kjTerms.append ( Term ( c = 1.0 , indices = [ ] ) )
        for k in range ( nVehicle ) :    
            for j in range ( 1 , nLoc + 1 ) :
                kjTerms.append ( Term ( c = -1.0 , indices = [ vjk_index ( v , j , k ) ] ) )
            terms += tSquare ( kjTerms )
    return tMultiply ( terms , [ Term ( c = penalty [ 9 ] , indices = [] ) ] )

def h5Terms () -> List [ Term ] :
    #each vehicle's capacity can only be 1 value
    timeStamp ( 'h5' )
    terms = []
    for k in range ( nVehicle ) :
        yTerms = []
        yTerms.append ( Term ( c = 1.0 , indices = [ ] ) )
        for n in range ( nCapacity + 1 ) :
            yTerms.append ( Term ( c = -1.0 , indices = [ nk_index ( n , k ) ] ) )
        terms += tSquare ( yTerms )
    return tMultiply ( terms , [ Term ( c = penalty [ 5 ] , indices = [] ) ] )

def h6Terms () -> List [ Term ] :
    #each vehicle's capacity must equal the sum of capacities of locations for ak_index
    timeStamp ( 'h6' )
    terms = []
    for k in range ( nVehicle ) :
        yTerms = []
        for n in range ( nCapacity + 1 ) :
            yTerms.append ( Term ( c = float ( n ) , indices = [ nk_index ( n , k ) ] ) )
        for a in range ( nLoc ) :
            yTerms.append ( Term ( c = -1.0 * loc [ a ] [ 2 ] , indices = [ ak_index ( a , k ) ] ) )
        terms += tSquare ( yTerms )
    return tMultiply ( terms , [ Term ( c = penalty [ 6 ] , indices = [] ) ] )  

def h8Terms () -> List [ Term ] :
    #each vehicle's capacity must equal the sum of capacities of locations for vjk_index
    timeStamp ( 'h8' )
    terms = []
    for k in range ( nVehicle ) :
        yTerms = []
        for n in range ( nCapacity + 1 ) :
            yTerms.append ( Term ( c = float ( n ) , indices = [ nk_index ( n , k ) ] ) )
        for a in range ( nLoc ) :
            for j in range ( 1 , nLoc ) :
                yTerms.append ( Term ( c = -1.0 * loc [ a ] [ 2 ] , indices = [ vjk_index ( a , j , k ) ] ) )
        terms += tSquare ( yTerms )
    return tMultiply ( terms , [ Term ( c = penalty [ 8 ] , indices = [] ) ] ) 

def fixIndex ( index , value ) :
    fix [ index ] = value

def fixDepotValues ( terms : List [ Term ] ) -> List [ Term ] :
    for k in range ( nVehicle ) :
        fixIndex ( vjk_index ( 0 , 0 , k ) , 1 )
        fixIndex ( vjk_index ( 0 , nLoc , k ) , 1 )

    print ( 'fixing variables -> {}'.format ( fix ) )
    return ( tFixPre ( terms , fix ) )

def printResults ( config : dict ) :
    results = np.ones ( ( nVehicle , nLoc + 1 ) ) * -1

    for key , val in config.items() :
        if val == 1 :
            if int ( key ) < akIndexBase : 
                ( v , j , k ) = invert_vjk_index ( int ( key ) )
                results [ k , j ] = v
            elif int ( key ) < akIndexBase + nkIndexBase :
                ( a , k ) = invert_ak_index ( int ( key ) )
                print ( 'vehicle {} capacity(a) {}'.format ( k , a ) )
            else :
                ( n , k ) = invert_nk_index ( int ( key ) )
                print ( 'vehicle {} capacity(n) {}'.format ( k , n ) )

    print ( 'results' )
    print ( results )

def dumpResults ( config : dict ) :
    print ( sorted ( [ ( int ( k ) , v ) for k , v in config.items() ] ) )

setPenalties ()

terms = h1Terms () + h2Terms () + h3Terms () + h4Terms () + h9Terms ()  + h5Terms () + h6Terms () + h8Terms () # + p2Terms ()

print ( 'terms-> ' , len ( terms ) )

terms = fixDepotValues ( terms )

timeStamp ( 'tSimplify' )
terms = tSimplify ( terms )

timeStamp ( 'terms' )
print ( 'terms-> ' , len ( terms ) )
#print ( terms )
#print ( ' ' )

problem = Problem ( name = 'vrp {} locs'.format ( nLoc ) , problem_type = ProblemType.pubo , terms = terms )

solver = SimulatedAnnealing ( workspace , timeout = 100 ) 
#solver = ParallelTempering ( workspace , timeout = 100 ) 

print ( 'calling solver: {}'.format ( solver.target ) )
result = solver.optimize ( problem )
print ( 'cost->{}'.format ( result [ 'cost' ] ) )

r = tFixPost ( result [ 'configuration' ] , fix )
r = result [ 'configuration' ]
dumpResults ( r )
printResults ( r )

print ( '...fini' )
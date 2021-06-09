# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from collections import Counter
from math import sqrt
import random
import re
from typing import List

from azure.quantum import Workspace
from azure.quantum.optimization import Problem , ProblemType , Term , ParallelTempering , SimulatedAnnealing , Tabu

from util.tFunctions import *

# Workspace information
workspace = Workspace(
    subscription_id =   'xxx', # add your subscription_id
    resource_group =    'xxx', # add your resource_group
    name =              'xxx', # add your workspace name
)

print ( 'init...' )

workspace.login()
print ( 'login successful' )

# travelling salesman / Lucas:  arXiv:1302.5843v3 [cond-mat.stat-mech] 24 Jan 2014
# [ 0 ] == depot
loc = [ [ 1 , 1 ] , [ 3 , 2 ] , [ 5 , 3 ] , [ 1 , 4 ] , [ 3 , 5 ] ]
nLoc = len ( loc )

penalty = [ 1.0 for _ in range ( 5 ) ]

def index ( v , j ) :
    return v * ( nLoc + 1 ) + j

def invertIndex ( s ) :
    v = int ( s / ( nLoc + 1 ) )
    j = s % ( nLoc + 1 )
    return ( v , j )

def cost ( u , v ) :
    return sqrt ( ( loc [ v ] [ 0 ] - loc [ u ] [ 0 ] ) ** 2 + ( loc [ v ] [ 1 ] - loc [ u ] [ 1 ] ) ** 2 )

def maxCost () :
    c = 0.0
    for u in range ( nLoc ) :
        for v in range ( nLoc ) :
            if ( u != v ) :
                c = max ( c , cost ( u , v ) )
    return c

def setPenalties () :
    maxC = maxCost ()
    print ( 'max cost {}'.format ( maxC ) )
    penalty [ 4 ] = penalty [ 2 ] = 2.0
    penalty [ 0 ] = penalty [ 1 ] = penalty [ 3 ] = penalty [ 4 ] * float ( round ( maxC ) ) * 2.0
    print ( ' penalties : ' )
    for p in range ( len ( penalty ) ) :
        print ( '{} -> {}'.format ( p , penalty [ p ] ) )
    print ( ' ' )

def h1Terms () -> List [ Term ] :
    #every v should appear once in a cycle ( except v0 )
    terms = []
    for v in range ( 1 , nLoc ) :
        vTerms = []
        vTerms.append ( Term ( c = 1.0 , indices = [ ] ) )
        for j in range ( nLoc + 1 ) :
            vTerms.append ( Term ( c = -1.0 , indices = [ index ( v , j ) ] ) )
        terms += tSquare ( vTerms )
    return tMultiply ( terms , [ Term ( c = penalty [ 0 ] , indices = [] ) ] )

def h2Terms () -> List [ Term ] :
    #every j should appear once in a cycle ( including 0 and n + 1 )
    terms = []
    for j in range ( nLoc + 1 ) :
        jTerms = []
        jTerms.append ( Term ( c = 1.0 , indices = [ ] ) )
        for v in range ( nLoc ) :
            jTerms.append ( Term ( c = -1.0 , indices = [ index ( v , j ) ] ) )
        terms += tSquare ( jTerms )
    return tMultiply ( terms , [ Term ( c = penalty [ 1 ] , indices = [] ) ] )

def p2Terms () -> List [ Term ] :
    #try to force starting and ending nodes = 0 (penalize all other spots for 0)
    terms = []
    for j in range ( 1 , nLoc ) :
        terms.append ( Term ( c = penalty [ 2 ] , indices = [ index ( 0 , j ) ] ) )
    return tSimplify ( terms )

def h3Terms () -> List [ Term ] :
    #an edge does not trace to itself
    terms = []
    for v in range ( nLoc ) :
        for j in range ( nLoc ) :
            terms.append ( Term ( c = penalty [ 3 ] , indices = [ index ( v , j ) , index ( v , j + 1 ) ] ) )
    return tSimplify ( terms )

def h4Terms () -> List [ Term ] :
    #minimize cost of making cycle ( euclidian distance )
    terms = []
    for u in range ( nLoc ) :
        for v in range ( nLoc ) :
            if ( u != v ) :
                for j in range ( nLoc ) :
                    terms.append ( Term ( c = cost ( u , v )  , indices = [ index ( u , j ) , index ( v , j + 1 ) ] ) )
    return tMultiply ( terms , [ Term ( c = penalty [ 4 ] , indices = [] ) ] )

def printResults ( config : dict ) :
    results = [ -1 for _ in range ( nLoc + 1 ) ]

    for key , val in config.items() :
        if val == 1 :
            ( v , j ) = invertIndex ( int ( key ) )
            results [ j ] = v

    print ( ' ' )
    print ( ' cycle : ' , end = '' )

    for r in range ( nLoc ) :
        print ( '{} -> '.format ( results [ r ] ) , end = '' )
        
    print ( '{} '.format ( results [ nLoc ] ) )
    print ( ' ' )

setPenalties ()

terms = tSimplify ( h1Terms () + h2Terms () + p2Terms () + h3Terms () + h4Terms () )

print ( 'terms-> ' , len ( terms ) )
print ( terms )
print ( ' ' )

problem = Problem ( name = 'tsp {} locs'.format ( nLoc ) , problem_type = ProblemType.pubo , terms = terms )

solver = SimulatedAnnealing ( workspace , timeout = 100 ) 

print ( 'calling solver' )
result = solver.optimize ( problem )

print ( result )
printResults ( result [ "configuration" ] )

print ( '...fini' )
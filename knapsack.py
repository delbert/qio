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

# knapsack / Lucas:  arXiv:1302.5843v3 [cond-mat.stat-mech] 24 Jan 2014
weights = [ 13 , 17 , 27 , 23 , 33 ]
values = [ 10 , 30 , 40 , 50 , 20 ]
nWeights = len ( weights )
nW = 42

penalty = [ 1.0 for _ in range ( 8 ) ]

def a_index ( a ) :
    return a

def a_invertIndex ( s ) :
    return s

def y_index ( y ) :
    return nWeights + y

def y_invertIndex ( s ) :
    return s - nWeights

def maxValue () :
    return max ( values )

def setPenalties () :
    print ( 'max value {}'.format ( maxValue () ) )
    penalty [ 7 ] = 2.0
    penalty [ 5 ] = penalty [ 6 ] =  penalty [ 7 ] * float ( round ( maxValue () ) ) * 2.0
    print ( ' penalties : ' )
    for p in range ( 5 , len ( penalty ) ) :
        print ( '{} -> {}'.format ( p , penalty [ p ] ) )
    print ( ' ' )

def h5Terms () -> List [ Term ] :
    #knapsack weight can only be 1 value
    yTerms = []
    yTerms.append ( Term ( c = 1.0 , indices = [ ] ) )
    for y in range ( nW ) :
        yTerms.append ( Term ( c = -1.0 , indices = [ y_index ( y ) ] ) )

    terms = tSquare ( yTerms )
    return tMultiply ( terms , [ Term ( c = penalty [ 5 ] , indices = [] ) ] )

def h6Terms () -> List [ Term ] :
    #knapsack weight = sum of weights of items
    yTerms = []
    for y in range ( nW ) :
        yTerms.append ( Term ( c = float ( y ) , indices = [ y_index ( y ) ] ) )
    for a in range ( nWeights ) :
        yTerms.append ( Term ( c = -1.0 * weights [ a ] , indices = [ a_index ( a ) ] ) )

    terms = tSquare ( yTerms )
    return tMultiply ( terms , [ Term ( c = penalty [ 6 ] , indices = [] ) ] )

def h7Terms () -> List [ Term ] :
    #maximize value of items
    terms = []
    for a in range ( nWeights ) :
        terms.append ( Term ( c = -1.0 * values [ a ] , indices = [ a_index ( a ) ] ) )

    return tMultiply ( terms , [ Term ( c = penalty [ 7 ] , indices = [] ) ] )

def printResults ( config : dict ) :
    results = [ ]
    print ( ' ' )

    for key , val in config.items() :
        if val == 1 :
            if int ( key ) < nWeights :
                results.append ( int ( key ) )
            else :
                print ( 'total weight -> {}'.format ( y_invertIndex ( int ( key ) ) ) )

    for r in results :
        print ( 'weight -> {} in backback value -> {}'.format ( weights [ r ] , values [ r ] ) )

    print ( ' ' )

setPenalties ()

terms = tSimplify ( h5Terms () + h6Terms () + h7Terms () )

print ( 'terms-> ' , len ( terms ) )
print ( terms )
print ( ' ' )

problem = Problem ( name = 'knapsack {} weights/values {} max weight'.format ( nWeights , nW ) , problem_type = ProblemType.pubo , terms = terms )

solver = SimulatedAnnealing ( workspace , timeout = 100 ) 

print ( 'calling solver' )
result = solver.optimize ( problem )

print ( result )
printResults ( result [ "configuration" ] )

print ( '...fini' )
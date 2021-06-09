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

# hamiltonian cycle, starting and ending with v0  / Lucas:  arXiv:1302.5843v3 [cond-mat.stat-mech] 24 Jan 2014
# [ 0 ] == depot
loc = [ [ 1 , 1 ] , [ 3 , 2 ] , [ 5 , 3 ] , [ 1 , 4 ] , [ 3 , 5 ] ]
nLoc = len ( loc )

#compute an average cost and then assign penalties?
# 5 - 10 X any valid solution; valid solution = ? (say)
penalty = [ 1 , 1 , 1 , 1 ] #remember that these become c's, along with euclidian distance

def index ( v , j ) :
    return v * ( nLoc + 1 ) + j

def invertIndex ( s ) :
    v = int ( s / ( nLoc + 1 ) )
    j = s % ( nLoc + 1 )
    return ( v , j )

def h1Terms () -> List [ Term ] :
    #every v should appear once in a cycle ( except v0 )
    terms = []
    for v in range ( 1, nLoc ) :
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

def printResults ( config : dict ) :
    results = [ -1 for _ in range ( nLoc + 1 ) ]

    for key , val in config.items() :
        if val == 1 :
            ( v , j ) = invertIndex ( int ( key ) )
            results [ j ] = v

    print ( ' cycle : ' , end = '' )
    for r in range ( nLoc ) :
        print ( '{} -> '.format ( results [ r ] ) , end = '' )

    print ( '{} '.format ( results [ nLoc ] ) )


terms = tSimplify ( h1Terms () + h2Terms () + p2Terms () + h3Terms () )

print ( 'terms-> ' , len ( terms ) )
print ( terms )
print ( ' ' )

problem = Problem ( name = 'hc {} locs'.format ( nLoc ) , problem_type = ProblemType.pubo , terms = terms )

solver = SimulatedAnnealing ( workspace , timeout = 100 ) 

print ( 'calling solver' )
result = solver.optimize ( problem )

print ( result )
printResults ( result [ "configuration" ] )

print ( '...fini' )
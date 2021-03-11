from collections import Counter
import random
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

'''
nShips = 3
nContainers = 6
penalty = 1.5
containerWeights = [ 1 , 2 , 3 , 13 , 14 , 15 ]
'''
nShips = 3
nContainers = 13
penalty = 1.0

def setWeights () -> List [ int ] :
    return [ random.randint ( 7 , 77 ) for _ in range( nContainers ) ]

def index ( nShip , nContainer ) :
    return ( nShips * nContainer + nShip )

def shipTerms1Ship ( nShip : int ) -> List [ Term ] :
    terms = []
    for j in range ( nContainers ) :
        terms.append ( Term ( c = float ( containerWeights [ j ] ) , indices = [ index ( nShip , j ) ] ) )
    return terms

def shipTerms () -> List [ Term ] :
    terms = []
    for nShip in range ( nShips ) :
        if nShip == nShips - 1 :
            nShipd = 0
        else:
            nShipd = nShip + 1
        terms += ( tSquare ( tSubtract ( shipTerms1Ship ( nShip ) , shipTerms1Ship ( nShipd ) ) ) )
    return ( tSimplify ( terms ) )

def penaltyTerms () -> List [ Term ] :
    terms = []
    for nContainer in range ( nContainers ) :
        penaltyTerms1Container = []
        for nShip in range ( nShips ) :
            penaltyTerms1Container.append ( Term ( c = 1.0 , indices = [ index ( nShip , nContainer ) ] ) ) 
        penaltyTerms1Container.append ( Term ( c = -1.0 , indices = [] ) ) 
        terms += tSquare ( penaltyTerms1Container )
    return tMultiply ( terms , [ Term ( c = penalty , indices = [] ) ] )

def print_results ( config : dict ) :

    shipWeights = []
    containers = []
    for _ in range ( nShips ) : 
        shipWeights.append ( 0 )

    for key , val in config.items() :
        if val == 1 :
            c = int ( int ( key ) / nShips )
            s = int ( key ) % nShips
            print ( 'container-> {} is on ship-> {}'.format ( c , s ) )
            shipWeights [ s ] += containerWeights [ c ]
            containers.append ( c )

    print ( ' ' )
    for key , val in Counter ( containers ).most_common () :
        if val > 1 :
            print ( 'container-> {} is on-> {} ships'.format ( key , val ) )

    print ( ' ' )
    for i in range ( len ( shipWeights ) ) :
        print ( 'ship-> {} weighs-> {}'.format ( i , shipWeights [ i ] ) )

#containerWeights = setWeights ()
containerWeights =  [ 76 , 32 , 43 , 40 , 61 , 55 , 22 , 13 , 61 , 74 , 65 , 58 , 71 ] # 224, 224, 223
print ( 'container weights-> ' , containerWeights )

terms = tSimplify ( shipTerms () + penaltyTerms () )

print ( 'terms-> ' , len ( terms ) )
print ( terms )
print ( ' ' )

problem = Problem ( name = 'shipping {} by {}'.format ( nShips, nContainers ) , problem_type = ProblemType.pubo , terms = terms )

solver = SimulatedAnnealing ( workspace , timeout = 100 ) 

print ( 'calling solver' )
result = solver.optimize ( problem )

print ( result )
print_results ( result [ "configuration" ] )

print ( '...fini' )
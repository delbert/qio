from collections import Counter
import numpy as np
import random
from typing import List

from azure.quantum import Workspace
from azure.quantum.optimization import Problem , ProblemType , Term , ParallelTempering , SimulatedAnnealing , Tabu

from util.tFunctions import *


print ( 'init...' )

'''
nShips = 3
containerWeights = [ 1 , 2 , 3 , 13 , 14 , 15 ] # 16 , 16 , 16
containerWeights =  [ 76 , 32 , 43 , 40 , 61 , 55 , 22 , 13 , 61 , 74 , 65 , 58 , 71 ] # 224 , 224 , 223
nShips = 7
containerWeights =  [ 30 , 70 , 65 , 23 , 34 , 53 , 33 , 14 , 23 , 41 , 16 , 29 , 37 , 9 , 49 , 76 , 21 , 23 , 65 , 8 , 16 , 10 , 13 ] # 108 , 108 , 108 , 108 , 109 , 109 , 108
'''
nShips = 7
#containerWeights = [ random.randint ( 7 , 77 ) for _ in range( 23 ) ]
containerWeights =  [ 30 , 70 , 65 , 23 , 34 , 53 , 33 , 14 , 23 , 41 , 16 , 29 , 37 , 9 , 49 , 76 , 21 , 23 , 65 , 8 , 16 , 10 , 13 ] # 108 , 108 , 108 , 108 , 109 , 109 , 108

nContainers = len ( containerWeights )
targetWeight = sum ( containerWeights ) / nShips
print ( 'container weights-> ' , containerWeights )
print ( 'target weight-> ' , targetWeight )


def index ( nShip , nContainer ) :
    return ( nShips * nContainer + nShip )

def shipTerms () -> List [ Term ] :
    terms = []
    for nShip in range ( nShips ) :
        shipTerms1Ship = []
        for nContainer in range ( nContainers ) :
            shipTerms1Ship.append ( Term ( c = 1.0 * containerWeights [ nContainer ] , indices = [ index ( nShip , nContainer ) ] ) ) 

        shipTerms1Ship.append ( Term ( c = -1.0 * targetWeight , indices = [] ) )
        terms += tSquare ( shipTerms1Ship )

    return tSimplify ( terms )

def penaltyTerms () -> List [ Term ] :
    terms = []
    for nContainer in range ( nContainers ) :
        penaltyTerms1Container = []
        for nShip in range ( nShips ) :
            penaltyTerms1Container.append ( Term ( c = 1.0  * containerWeights [ nContainer ] , indices = [ index ( nShip , nContainer ) ] ) ) 

        penaltyTerms1Container.append ( Term ( c = -1.0  * containerWeights [ nContainer ] , indices = [] ) ) 
        terms += tSquare ( penaltyTerms1Container )

    return tSimplify ( terms )

def submitTerms ( terms : List [ Term ] ) :
    # Workspace information
    workspace = Workspace(
        subscription_id =   '', # add your subscription_id
        resource_group =    '', # add your resource_group
        name =              '', # add your workspace name
    )

    workspace.login()
    print ( 'login successful' )

    problem = Problem ( name = 'shipping {} by {}'.format ( nShips, nContainers ) , problem_type = ProblemType.pubo , terms = terms )

    solver = SimulatedAnnealing ( workspace , timeout = 100 ) 

    print ( 'calling solver' )
    result = solver.optimize ( problem )

    print ( result )
    printResults ( result [ "configuration" ] )

def printResults ( config : dict ) :
    results = np.zeros ( ( nShips , nContainers ) )

    for key , val in config.items() :
        if val == 1 :
            c = int ( int ( key ) / nShips )
            s = int ( key ) % nShips
            results [ s , c ] = containerWeights [ c ]

    print ( 'results' )
    print ( np.append ( results , np.sum ( results , axis = 1 , keepdims = True ) , axis = 1 ) )

terms = tSimplify ( shipTerms () + penaltyTerms () )

print ( 'terms-> ' , len ( terms ) )
print ( terms )
print ( ' ' )

submitTerms ( terms )

print ( '...fini' )
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from collections import Counter
from typing import List

from azure.quantum.optimization import Term

def tOrder ( terms0 : Term ) -> int :
    if len ( terms0.ids ) == 0 :
        return ( 0 )
    return ( Counter ( terms0.ids ).most_common ( 1 )[ 0 ][ 1 ] )

def tGreaterThan ( term0 : Term , term1 : Term ) -> bool :
    if tOrder ( term0 ) > tOrder ( term1 ) :
        return ( True )
    return ( False )

def tSimplify ( terms0 : List [ Term ] ) -> List [ Term ] :
    terms = []
    
    for term in terms0 :
        combined = False
        inserted = False 
        term.ids.sort()

        for t in terms :
            if t.ids == term.ids :
                t.c += term.c
                combined = True
                break

        if not combined :
            for i in range ( len ( terms ) ) :
                if tGreaterThan ( term , terms [ i ] ) :
                    terms.insert ( i , term )
                    inserted = True
                    break

            if not inserted :
                terms.append ( term )

    ret = []
    for t in terms :
        if t.c != 0 :
            ret.append ( t )

    return ( ret )

def tAdd ( terms0 : List [ Term ] , terms1 : List [ Term ] ) -> List [ Term ] :
    return tSimplify ( terms0 + terms1 )
  
def tSubtract ( terms0 : List [ Term ] , terms1 : List [ Term ] ) -> List [ Term ] :
    terms = []
    for term0 in terms0 :
        terms.append( Term ( c = term0.c , indices = term0.ids ) )

    for term1 in terms1 :
        terms.append ( Term ( c = -1 * term1.c , indices = term1.ids ) )

    return tSimplify ( terms )

def tMultiply ( terms0 : List [ Term ] , terms1 : List [ Term ] ) -> List [ Term ] :
    terms = []
    for term0 in terms0 :
        for term1 in terms1 :
            terms.append ( Term ( c =  term0.c * term1.c , indices = term0.ids + term1.ids ) )
    return tSimplify ( terms )

def tSquare ( terms0 : List [ Term ] ) -> List [ Term ] :
    return ( tMultiply ( terms0 , terms0 ) )

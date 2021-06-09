# qio

Azure Quantum-Inspired Optimization Solver examples

based on the Lucas paper:  https://arxiv.org/abs/1302.5843v3

===

tFunctions.py goes in a directory: ../util/ directory in the working directory with the rest of the samples.

benchmark.py goes in ../util/ as well

../util/ should also contain an empty file:  \_\_init\_\_.py


===

to fix the values of selected variables, set up a dict with key:  variable index and value:  variable value and then call the pre- and post- functions as follows:

fix = { 3 : 0 , 5 : 1 }  # fixes index/variable 3 to 0 and index/variable 5 to 1 (sorry, not supporting Ising yet)

terms = tFixPre ( terms , fix )

problem = Problem ( name = 'vrp {} locs'.format ( nLoc ) , problem_type = ProblemType.pubo , terms = terms )

solver = SimulatedAnnealing ( workspace , timeout = 100 ) 

result = solver.optimize ( problem )

finalResult = tFixPost ( result [ 'configuration' ] , fix )


Copyright (c) Microsoft Corporation.
Licensed under the MIT License.

x
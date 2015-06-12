SKOPT is a tool that helps to optimise Slater-Koster files for 
use by Density-Functional-based Tight Binding (DFTB) programs 
like dftb+ (BCCMS Bremen), lodestar (The University of Hong Kong)
and other implementations of DFTB.

It implements particle swarm optimisation (PSO) algorithm, but 
the modular design means a drop-in replacement of an alternative
(possibly evolutionary) algorithm could be used too.

SKOPT requires skopt.py input file, which contains the definitions
of the atomic systems involved in the optimisation of the *.skf
sets, and relies on the SKGEN package from SKTOOLS.

The tool is still in development but is intended to be freely 
distributed, and can be obtained already via collaborations.

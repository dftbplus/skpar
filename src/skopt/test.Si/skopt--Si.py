#!/usr/local/bin/python3 -u
"""
Top level script to perform optimisation of DFTB parameters.
"""
# mandatory imports
import os, sys, logging, subprocess
import numpy as np
from datetime import datetime
from types import *
from subprocess import STDOUT
from collections import OrderedDict

# skopt
from skopt.runtasksDFTB import RunDFTB, RunDPbands, RunSKgen_sh
from skopt.queryDFTB import QueryDataDFTB
from skopt.plotBS import Plotter
from skopt.system import Analyser, System, queryData
from skopt.evaluate import Evaluator
from skopt.pso import PSO
from skopt.extras.bandstructure_Si import ref_Si, analyseEk_Si, analyseEkst_Si, analyseMeff_Si
from skopt.parameters import read_parameters, write_parameters
from deap.base import Toolbox
from skopt.optimise import SKopt

print (sys.version)

def main():
    """
    """

    # Project work directory
    # -------------------------------------------------------------------
    workdir = os.getcwd()


    # Input files for the optimiser and for skgen
    # skfdir is where skgen is run into: $workdir/$skfdir
    # skdefs_out naturally goes into the skfdir; the file is actually 
    # the input for skgen
    # skopt_in stays in $workdir, as it directs the optimiser
    # -------------------------------------------------------------------
    skfdir = "skf"
    skopt_in = "skdefs.template.py"
    skdefs_out = "skdefs.py"

    # Describe the systems involved in the optimisation
    # -------------------------------------------------------------------

    # System 1: Bulk Si band-structure
    s1 = System(workdir=os.path.join(workdir, 'Si'), name='Si',
                bsdata={'lattice': 'FCC', 'equivkpts': [('U', 'K'), ]},
                sccdata={},
                dirSCC=os.path.join(workdir, 'Si', 'scc', ),
                dirBS=os.path.join(workdir, 'Si', 'bs'))

    s1.tasks.append(RunDFTB(workdir=s1.dirSCC))
    s1.tasks.append(RunDPbands(workdir=s1.dirSCC))
    s1.tasks.append(RunDFTB(workdir=s1.dirBS,
                            chargesfile=os.path.join(s1.dirSCC, 'charges.bin')))
    s1.tasks.append(RunDPbands(workdir=s1.dirBS))
    s1.tasks.append(QueryDataDFTB(s1.bsdata, workdir=s1.dirBS, Eref='VBtop'))
#    s1.tasks.append(QueryDataDFTB(s1.sccdata, workdir=s1.dirSCC,
#                                  getBands=True, getHOMO=True, getkLines=False,
#                                  prepareforplot=False))
    s1.tasks.append(Plotter(data=s1.bsdata,
                            filename=os.path.join(s1.workdir, 'BS_Si.fcc.pdf'),
                            Erange=(-12, 6)))
    s1.tasks.append(Analyser(analyse=analyseEk_Si, data=s1.bsdata, results=s1.calculated))
    s1.tasks.append(Analyser(analyse=analyseEkst_Si, data=s1.bsdata, results=s1.calculated))
    s1.tasks.append(Analyser(analyse=analyseMeff_Si, data=s1.bsdata, results=s1.calculated))

    # Define the reference data for each system
    # ----------------------------------------------------------------------

    # Reference (target) data for system 1:
    refkeys = 'Dmin_c  Dmin_c_pos  ' + \
              'G15_c  G1_v  G2pr_c  ' + \
              'L1_c  L1_v  L2pr_v  L3_c  L3pr_v  ' + \
              'X4_v  X1_v  X1_c  ' + \
              'me_Xl  m_hh_001  m_hh_111'
    refdata = OrderedDict([(key, ref_Si[key]) for key in refkeys.split()])

    # weights of the reference data are composed as inverse of the
    # max tolerable relative error
    maxRelErr = [10] * len(refdata)
    maxRelErr[0:2] = [0.75, 1.5]  # band gap and position of CBmin
    maxRelErr[len(refdata) - 3:] = 10 * [5, ]
    maxErr = [abs(relerr * val / 100.) for relerr, val in zip(maxRelErr, list(refdata.values()))]
    weights = [1 / err for err in maxErr]
    weights = np.asarray(weights) / np.sum(weights)
    weights = OrderedDict(list(zip(refkeys.split(), weights)))
    assert len(refdata) == len(weights)

    # update the system's refdata and weights
    s1.refdata = refdata
    s1.weights = weights

    # Configure an instance of the optimiser
    # ----------------------------------------------------------------------

    # Decide whether to report any deviations, at each evaluation
    # NOTABENE: the evaluator has no concept of systems, so other than the 
    #           names of separate datum, we have to supply the provenance
    #           of each datum, i.e. the system name
    reportkeys = []   # this gets passed to the evaluator; represents all systems

    # report keys (system.name, datum.name) for system 1:
    s1keys = ['{s}.{k}'.format(s=s1.name, k=key) for key in list(s1.refdata.keys())]
    # s1keys = ['-'] * len(list(flatten(s1.refdata))) # if we want to report 
    # for all ref.data, but the default is of limited useability if we have 
    # a large set of k-pts.

    reportkeys.extend(s1keys)   # such line should exist for each system as needed

    # Parameters describing the optimisation strategy with PSO
    npart = 2           # Number of particles in the swarm; it depends on 
                        # the very specifics of the problem at hand
    objectives = (-1,)  # Keep single objective optimisation for now;
                        # don't know how to handle multiobjective optimisation
    # Stopping criteria:
    ngen = 2            # Number of generations through which the swarm evolves
    ErrTol = 0.05       # Use this as an alternative, if ngen is rather large,
                        # we stop as soon as the worst relative error accross
                        # the reference data falls below ErrTol.

    optimise = SKopt(workdir=workdir, skfdir=skfdir,
                     skopt_in=skopt_in, skdefs_out=skdefs_out,
                     systems=[s1, ], sysweights=[1,], 
                     # Evaluator arguments
                     reportkeys=reportkeys,
                     # PSO optimiser arguments as a list of kwargs
                     npart=npart, objectives=objectives,
                     ngen=ngen, ErrTol=ErrTol)

    # do the optimisation
    # ----------------------------------------------------------------------
    swarm, stats = optimise()
             


if __name__ == "__main__":
    main()

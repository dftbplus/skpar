"""Main environment of SKPAR"""
import os
import logging
import numpy as np
from skpar.core.utils    import get_logger
from skpar.core.input    import parse_input
from skpar.core.evaluate import Evaluator
from skpar.core.optimise import Optimiser


class SKPAR():
    """The main executable object."""

    def __init__(self, infile='skpar_in.yaml', verbose=True):

        # setup logger
        # -------------------------------------------------------------------
        loglevel = logging.DEBUG if verbose else logging.INFO
        self.logger = get_logger(name='skpar', filename='skpar.log',
                                 verbosity=loglevel)
        # specific for printing/reporting from numpy objects
        np.set_printoptions(threshold=60, linewidth=79, suppress=True)

        # Project work directory
        # -------------------------------------------------------------------
        self.workdir = os.getcwd()

        # Main part
        # -------------------------------------------------------------------
        # parse input file
        self.logger.info('Parsing input file {:s}'.format(infile))
        taskdict, tasklist, objectives, optimisation, config =\
            parse_input(infile, verbose=verbose)
        if optimisation is not None:
            algo, options, parameters = optimisation
            parnames = [p.name for p in parameters]
        else:
            parnames = None

        # instantiate the evaluator machinery
        self.logger.info('Instantiating Evaluator')
        self.evaluator = Evaluator(objectives, tasklist, taskdict, parnames,
                                   config, verbose=verbose)

        # instantiate the optimiser
        if optimisation is not None:
            self.do_optimisation = True
            self.logger.info('Instantiating Optimiser')
            self.optimiser = Optimiser(algo, parameters, self.evaluator,
                                       options, verbose=True)
        else:
            self.do_optimisation = False


    def __call__(self, evalonly=False):
        if self.do_optimisation and not evalonly:
            # run the optimiser
            self.logger.info('Starting optimisation')
            self.optimiser()
            # issue final report
            self.optimiser.report()
            self.logger.info('Done.')
        else:
            # no parameters: pass None to evaluator
            fitness = self.evaluator(None)
            self.logger.debug("Global fitness: {}".format(fitness))

    def __repr__(self):
        lines = []
        return "\n".join(lines)

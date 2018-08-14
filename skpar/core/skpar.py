"""Main environment of SKPAR"""
import os
import logging
import numpy as np
from skpar.core.utils    import get_logger
from skpar.core.input    import parse_input
from skpar.core.evaluate import Evaluator
from skpar.core.optimise import Optimiser


class SKPAR(object):
    """The main executable object."""

    def __init__(self, infile='skpar_in.yaml', verbose=False):

        # setup logger
        # -------------------------------------------------------------------
        loglevel = logging.DEBUG if verbose else logging.INFO
        self.logger = get_logger(name='skpar', filename='skpar.log',
                                   verbosity=loglevel)
        # specific for printing/reporting from numpy objects
        np.set_printoptions(threshold = 60, linewidth= 79, suppress=True)

        # Project work directory
        # -------------------------------------------------------------------
        self.workdir = os.getcwd()

        # Main part
        # -------------------------------------------------------------------
        # parse input file
        self.logger.info('Parsing input file {}'.format(infile))
        taskdict, tasklist, objectives, optimisation, config =\
            parse_input(infile, verbose=verbose)

        # instantiate the evaluator machinery
        self.logger.info('Instantiating Evaluator')
        self.evaluator = Evaluator(objectives, tasklist, taskdict, config,
                                    verbose=verbose)

        # instantiate the optimiser
        if optimisation is not None:
            self.do_optimisation = True
            algo, options, parameters = optimisation
            self.logger.info('Instantiating Optimiser')
            self.optimiser = Optimiser(algo, parameters, self.evaluator,
                                       verbose=True, **options)
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
            self.logger.debug("Individual objective fitness: {}".\
                              format(self.evaluator.objvfitness))
            self.logger.debug("Global fitness: {}".format(fitness))

    def __repr__(self):
        ss = []
        return "\n".join(ss)

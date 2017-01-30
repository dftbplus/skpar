#!/usr/bin/env python3
import os
import logging
from pprint import pformat
from skopt.core.utils    import get_logger
from skopt.core.input    import parse_input
from skopt.core.evaluate import Evaluator
from skopt.core.optimise import Optimiser
from skopt.core.query    import Query


class SKOPT(object):

    def __init__(self, infile='skopt_in.yaml', verbose=False):

        # setup logger
        # -------------------------------------------------------------------
        loglevel    = logging.DEBUG if verbose else logging.INFO
        self.logger = get_logger(name='skopt', filename='skopt.debug.log',  
                                   verbosity=loglevel)

        # Project work directory
        # -------------------------------------------------------------------
        self.workdir = os.getcwd()

        # Main part
        # -------------------------------------------------------------------
        # Do we really need to flush the modeldb?
        self.logger.info('Initialising ModelDataBase.')
        Query.flush_modelsdb()

        # parse input file
        self.logger.info('Parsing input file {}'.format(infile))
        tasks, objectives, optimisation = parse_input(infile)

        # instantiate the evaluator machinery
        self.logger.info('Instantiating Evaluator')
        self.evaluator   = Evaluator(objectives, tasks)

        # instantiate the optimiser
        if optimisation is not None:
            self.do_optimisation = True
            algo, options, parameters = optimisation
            self.logger.info('Instantiating optimiser')
            self.optimiser  = Optimiser(algo, parameters, self.evaluator, **options)
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
            self.logger.debug("Individual objective fitness: {}".format(self.evaluator.objvfitness))
            self.logger.debug("Global fitness: {}".format(fitness))

    def __repr__(self):
        ss = []
        return "\n".join(ss)

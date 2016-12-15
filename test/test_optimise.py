import unittest
import numpy as np
import numpy.testing as nptest
from skopt.input import parse_input
from skopt.evaluate import Evaluator
from skopt.optimise import Optimiser, get_optargs
from skopt.taskdict import gettaskdict


class OptimiseTest(unittest.TestCase):
    """
    Verify basic functionality of optimiser
    """
    def get_model_data (src, dst):
        data = np.loadtxt(src)
        dst['yval'] = data

    def test_parse_input(self):
        """Can we parse input and create an optimiser instance?"""
        gettaskdict['get_model_data'] = self.get_model_data
        filename = "test_optimise.yaml"
        _input = parse_input(filename)
        tasks        = _input[0]
        objectives   = _input[1]
        optimisation = _input[2]
        algo, options, parameters = optimisation
        evaluate = Evaluator(objectives, tasks)
        optimise = Optimiser(algo, parameters, evaluate, **options)

        print ("\n### -------------------------------------------------- ###")
        print ("### ----------- Tasks -------------------------------- ###")
        print ("### -------------------------------------------------- ###")
        for tt in optimise.evaluate.tasks:
            print (tt)

        print ("\n### -------------------------------------------------- ###")
        print ("### ----------- Objectives --------------------------- ###")
        print ("### -------------------------------------------------- ###")
        for oo in optimise.evaluate.objectives:
            print (oo)

        print ("\n### -------------------------------------------------- ###")
        print ("### ----------- Parameters --------------------------- ###")
        print ("### -------------------------------------------------- ###")
        for pp in optimise.parameters:
            print (pp)

        optimout = optimise()


if __name__ == '__main__':
    unittest.main()


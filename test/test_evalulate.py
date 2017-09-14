import unittest
import logging
import numpy as np
import numpy.testing as nptest
from skpar.core import evaluate as ev


class Objv(object):
    """Barebone objective"""
    def __init__(self, ff, ww):
        self.fitness = ff
        self.weight = ww
    def __call__(self):
        return self.fitness

class Task(object):
    """Barebone task"""
    def __init__(self, exception=None):
       self.exception = exception
    def __call__(self, workroot, **kwargs):
        if self.exception is not None:
            raise self.exception
        else:
            return None

class EvaluatorTest(unittest.TestCase):
    """Check if we can create an evaluator."""

    def test_evaluator_init_dflt(self):
        """Can we instantiate evaluator?"""
        objvs = [Objv(2, 1), Objv(2, 1)]
        tasks = [Task(), Task()]
        evaluator = ev.Evaluator(objvs, tasks)
        nptest.assert_array_equal(evaluator.weights,np.array([.5, .5]))
        self.assertFalse(evaluator.verbose)
        params, iteration = 2., 1
        fitness = evaluator(params, iteration)
        self.assertEqual(fitness, 2)

    def test_evaluator_utopia(self):
        """Can we instantiate evaluator w/ different utopia point?"""
        objvs = [Objv(2, 1), Objv(2, 1)]
        tasks = [Task(), Task()]
        evaluator = ev.Evaluator(objvs, tasks, utopia=np.ones(2))
        nptest.assert_array_equal(evaluator.weights,np.array([.5, .5]))
        self.assertFalse(evaluator.verbose)
        par, ii = 2., 1
        fitness = evaluator(par, ii)
        self.assertEqual(fitness, 1)

    def test_evaluator_task_failure(self):
        """Does evaluation breaks if task fails?"""
        objvs = [Objv(2, 1), Objv(2, 1)]
        tasks = [Task(), Task(RuntimeError), Task()]
        evaluator = ev.Evaluator(objvs, tasks, utopia=np.ones(2))
        par, ii = 2., 1
        self.assertRaises(RuntimeError, evaluator, parameters=par, iteration=ii)


if __name__ == '__main__':
    unittest.main()


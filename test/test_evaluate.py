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
    def __call__(self, database):
        return self.fitness

def printwrapper(env, db, msg):
    print (env, db, msg)

def fexception(env, db, exception=None):
    """pass or except depending on the `exception`"""
    if exception is not None:
        raise exception
    else:
        return None


class EvaluatorTest(unittest.TestCase):
    """Check if we can create an evaluator."""

    def test_evaluator_init_dflt(self):
        """Can we instantiate evaluator?"""
        objvs = [Objv(2, 1), Objv(2, 1)]
        tasklist = [['t1',['task2']], ['t2', ['task2']]]
        taskdict = {'t1': printwrapper,
                    't2': printwrapper}
        parnames = ['p0']
        evaluator = ev.Evaluator(objvs, tasklist, taskdict, parnames)
        nptest.assert_array_equal(evaluator.weights,np.array([.5, .5]))
        params, iteration = [2.], 1
        fitness = evaluator(params, iteration)
        self.assertEqual(fitness, 2)

    def test_evaluator_utopia(self):
        """Can we instantiate evaluator w/ different utopia point?"""
        objvs = [Objv(2, 1), Objv(2, 1)]
        tasklist = [['t1',['task2']], ['t2', ['task2']]]
        taskdict = {'t1': printwrapper,
                    't2': printwrapper}
        parnames = ['p0']
        evaluator = ev.Evaluator(objvs, tasklist, taskdict, parnames,
                                 utopia=np.ones(2))
        nptest.assert_array_equal(evaluator.weights,np.array([.5, .5]))
        par, ii = [2.], 1
        fitness = evaluator(par, ii)
        self.assertEqual(fitness, 1)

    def test_evaluator_task_failure(self):
        """Does evaluation breaks if task fails?"""
        objvs = [Objv(2, 1), Objv(2, 1)]
        tasklist = [['t1',['task1']], ['t2',[RuntimeError]], ['t1', ['task3']]]
        taskdict = {'t1': printwrapper,
                    't2': fexception,}
        parnames = ['p0']
        evaluator = ev.Evaluator(objvs, tasklist, taskdict, parnames)
        par, ii = [2.], 1
        self.assertRaises(RuntimeError, evaluator, par, ii)


if __name__ == '__main__':
    unittest.main()


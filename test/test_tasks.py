import unittest
import logging
import yaml
from pprint import pprint, pformat
from skopt import tasks
from subprocess import CalledProcessError


class TasksCreationTest(unittest.TestCase):
    """Check if we can create and execute tasks."""

    def test_passtask(self):
        """Can we declare and execute a task successfully"""
        t1 = tasks.RunTask(exe='python', wd='testtasks', inp='pass.py')
        self.assertListEqual(t1.cmd,['python', 'pass.py'])
        self.assertEqual(t1.wd, 'testtasks')
        self.assertTrue(isinstance(t1.logger,logging.Logger))
        t1()
        self.assertEqual(t1.out, "Running to pass!\n")

    def test_passtask_listcmd_listinp(self):
        """Can we declare tasks with multiple input arguments?"""
        t1 = tasks.RunTask(exe=['python', 'pass.py'])
        self.assertListEqual(t1.cmd,['python', 'pass.py'])
        t2 = tasks.RunTask(exe=['python', 'pass.py'], inp=['monkey','boogie'])
        self.assertListEqual(t2.cmd,['python', 'pass.py', 'monkey', 'boogie'])

    def test_task_fail(self):
        """Can we fail a task due to non-zero return status of executable?"""
        t1 = tasks.RunTask(exe='python', wd='testtasks', inp='fail.py')
        self.assertRaises(CalledProcessError, t1)
        self.assertEqual(t1.out, "About to fail...\n")


class TasksParsingTest(unittest.TestCase):
    """Check if we can create and execute tasks."""

    yamldata="""
        tasks:
            #- set: [exe, workdir, [argslist] # different from run due to
            #                                 # intrinsic handling of parameters
            #                                 # at the level of __call__()
            #- run: [exe, workdir, [argslist] 
            #- get: [what, [from], [to]]
            - set: [skdefs, skf, ]
            - run: [skgen, skf, ]
            - run: [bs_dftb, Si, ]
            - run: [bs_dftb, SiO2, ]
            - get: [get_dftb, Si, ]
            - get: [get_dftb, SiO2, ]
            - get: [get_meff, Si/bs, ]
        """
    taskmapper = {'run': tasks.RunTask, 'set': None, 'get': None}

    def test_parsetask(self):
        """Can we parse task declarations successfully"""
        spec = yaml.load(self.yamldata)['tasks']
        tasklist = []
        for tt in spec:
            # we should be getting 1 dict entry only!
            (_t, _args), = tt.items()
            try:
                a0 = _args.pop(0)
                a1 = _args.pop(0)
                tasklist.append(self.taskmapper[_t](a0, a1, *_args))
            except TypeError:
                self.assertEqual(self.taskmapper[_t], None)
                pass
        cmd = ['skgen', 'bs_dftb', 'bs_dftb']
        wd = ['skf', 'Si', 'SiO2']
        for ii, tt in enumerate(tasklist):
            self.assertListEqual(tt.cmd, [cmd[ii]])
            self.assertEqual(tt.wd, wd[ii])



if __name__ == '__main__':
    unittest.main()



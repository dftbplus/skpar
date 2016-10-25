import unittest
import logging
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

if __name__ == '__main__':
    unittest.main()



"""Test import of user modules and taskdict update by user-defined tasks"""
import unittest
import yaml

from skpar.core.usertasks import import_taskdict, update_taskdict
from skpar.core.taskdict import TASKDICT as coretd
from skpar.dftbutils.taskdict import TASKDICT as dftbtd

class UserTaskTest(unittest.TestCase):
    """Can we obtain taskdict from user modules"""

    def test_import_taskdict(self):
        """Check we can import TASKDICT from a module"""
        # skpar.core
        modname, taskdict = import_taskdict('skpar.core.taskdict')
        self.assertEqual(modname, 'skpar.core.taskdict')
        self.assertDictEqual(coretd, taskdict)
        # skpar.dftbutils
        modname, taskdict = import_taskdict('skpar.dftbutils')
        self.assertEqual(modname, 'skpar.dftbutils')
        self.assertDictEqual(dftbtd, taskdict)
        # fail module import (modulenotfounderror is py3.6+)
        self.assertRaises((ImportError, ModuleNotFoundError),
                          import_taskdict, 'skpar.missing')
        # fail no TASKDICT (core.__init__.py is empty)
        self.assertRaises(AttributeError, import_taskdict, 'skpar.core')

    def test_update_taskdict(self):
        """Check we can update taskdict from user module"""
        yamlinput = """
            usermodules:
                - skpar.core.taskdict
        """
        userinp = yaml.load(yamlinput)['usermodules']
        taskdict = {}
        update_taskdict(taskdict, userinp)
        tag = 'skpar.core.taskdict'
        self.assertEqual(len(coretd), len(taskdict))
        for key, val in coretd.items():
            self.assertTrue('.'.join([tag, key]) in taskdict)
            self.assertEqual(val, taskdict[tag+'.'+key])

    def test_update_taskdict_multiple(self):
        """Check we can update taskdict from multiple modules"""
        yamlinput = """
            usermodules:
                - [skpar.core.taskdict, [set, get, run, plot]]
                - [skpar.dftbutils, [get_bs]]
        """
        userinp = yaml.load(yamlinput)['usermodules']
        taskdict = {}
        update_taskdict(taskdict, userinp)
        self.assertEqual(len(taskdict), 5)
        for key in ['set', 'get', 'run', 'plot']:
            self.assertTrue(key in taskdict)
            self.assertEqual(coretd[key], taskdict[key])
        for key in ['get_bs']:
            self.assertTrue(key in taskdict)
            self.assertEqual(dftbtd[key], taskdict[key])

    def test_update_taskdict_string(self):
        """Check we can update taskdict from user module"""
        tag = 'skpar.core.taskdict'
        taskdict = {}
        update_taskdict(taskdict, tag)
        self.assertEqual(len(coretd), len(taskdict))
        for key, val in coretd.items():
            self.assertTrue('.'.join([tag, key]) in taskdict)
            self.assertEqual(val, taskdict[tag+'.'+key])

    def test_update_taskdict_alias(self):
        """Check we can update taskdict from user module with alias"""
        yamlinput = """
            usermodules:
                - [skpar.dftbutils, dftb]
        """
        userinp = yaml.load(yamlinput)['usermodules']
        taskdict = {}
        update_taskdict(taskdict, userinp)
        tag = 'dftb'
        self.assertEqual(len(dftbtd), len(taskdict))
        for key, val in dftbtd.items():
            self.assertTrue('.'.join([tag, key]) in taskdict)
            self.assertEqual(val, taskdict[tag+'.'+key])

    def test_update_taskdict_explicit(self):
        """Check we can update taskdict from user module with explicit tasks"""
        yamlinput = """
            usermodules:
                - [skpar.core.taskdict, [set, get, run, plot]]
        """
        taskdict = {}
        userinp = yaml.load(yamlinput)['usermodules']
        update_taskdict(taskdict, userinp)
        self.assertEqual(4, len(taskdict))
        for key in ['set', 'get', 'run', 'plot']:
            self.assertTrue(key in taskdict)
            self.assertEqual(coretd[key], taskdict[key])
        # check failing with missing task
        yamlinput = """
            usermodules:
                - [skpar.core.taskdict, [set, mambo]]
        """
        taskdict = {}
        userinp = yaml.load(yamlinput)['usermodules']
        self.assertRaises(KeyError, update_taskdict, taskdict, userinp)


if __name__ == '__main__':
    unittest.main()

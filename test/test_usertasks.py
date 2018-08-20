"""Test import of user modules and taskdict update by user-defined tasks"""
import unittest
import os
import sys
import shutil
import yaml
import skpar

from skpar.core.usertasks import import_user_module, import_modules, update_taskdict

class UserTaskTest(unittest.TestCase):
    """Can we obtain taskdict from user modules"""

    PKGPATH = os.path.dirname(os.path.dirname(skpar.__file__))

    def check_core_import(self, name):
        """check helper for core modules belonging to skpar"""
        filename = os.path.join(self.PKGPATH, *name.split('.'))+'.py'
        self.check_import(name, filename)

    def check_import(self, name, filename, path=None):
        """check helper"""
        module = import_user_module(name, path)
        print('Imported module: {}'.format(module))
        print('Expected file  : {}'.format(filename))
        if path is None:
            path = os.getcwd()
        self.assertEqual(module.__name__, name)
        self.assertEqual(module.__file__, os.path.join(path, filename))

    def test_userinp_yaml_singlemodule(self):
        """Check import module from yaml; module on sys.path."""
        userinp = """
            modules: skpar.core.taskdict
        """
        sys.path.insert(4, '/Users/smarkov/Library/Python/3.6/lib/python/site-packages')
        modulesinp = yaml.load(userinp)
        name = modulesinp['modules']
        self.check_core_import(name)

    def test_userinp_yaml_list(self):
        """Check import module from yaml; multiple modules on sys.path"""
        userinp = """
            modules:
                - skpar.core.taskdict
                - skpar.dftbutils.taskdict
        """
        modulesinp = yaml.load(userinp)
        for name in modulesinp['modules']:
            self.check_core_import(name)

    def test_import(self):
        """Can we import a user module?"""
        name = 'usermodule'
        filename = 'usermodule.py'
        # from .
        path = '.'
        self.check_import(name, filename, None)
        # from explicit path
        path = './temp'
        if not os.path.exists(path):
            os.makedirs(path)
        shutil.copy(filename, path)
        self.check_import(name, filename, path)
        shutil.rmtree(path)

    def test_import_modules(self):
        """can we import several modules given a namelist?"""
        namelist = [('usermodule', '.')]
        modulefile = './usermodule.py'
        modules = import_modules(namelist)
        self.assertEqual(len(modules), 1)
        mod = modules[0]
        self.assertEqual(mod.__name__, namelist[0][0])
        self.assertEqual(mod.__file__, modulefile)

    def test_update_taskdict(self):
        """can we update taskdict from usermodule?"""
        taskdict = {}
        userinp = ['usermodule']
        update_taskdict(taskdict, userinp)
        func = sys.modules['usermodule'].userfunc
        self.assertDictEqual(taskdict, {'greet': func})
        tasklist = [taskdict['greet']]
        greeting = tasklist[0]('Hello!')
        self.assertEqual(greeting, 'SKPAR says Hello!')

if __name__ == '__main__':
    unittest.main()

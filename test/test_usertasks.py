"""Test import of user modules and taskdict update by user-defined tasks"""
import unittest
import os
import shutil

from skpar.core.usertasks import import_user_module #, import_modules, update_taskdict

class UserTaskTest(unittest.TestCase):
    """Can we obtain taskdict from user modules"""

    def check_import(self, name, filename, path=None):
        """check helper"""
        module = import_user_module(name, path)
        print(module)
        if path is None:
            path = '.'
        self.assertEqual(module.__name__, name)
        self.assertEqual(module.__file__, os.path.join(path, filename))

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


if __name__ == '__main__':
    unittest.main()

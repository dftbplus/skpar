import unittest
import logging
import yaml
import os
from pprint import pprint, pformat
from os.path import abspath, normpath, expanduser
from os.path import join as joinpath
import numpy as np
import numpy.testing as nptest
from subprocess import CalledProcessError
from skpar.core.tasks import SetTask, RunTask, GetTask, set_tasks
from skpar.core.parameters import Parameter
from skpar.core.query import Query
from skpar.core.taskdict import gettaskdict

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(format='%(message)s')
logger = logging.getLogger(__name__)

class TasksParsingTest(unittest.TestCase):
    """Check if we can create and execute tasks."""

    yamldata="""
        tasks:
            #- set: [parfile, workdir, optional_arguments]
            #- run: [exe, workdir, arguments] 
            #- get: [what, source, destination, optional_arguments]
            - set: [current.par, skf, ]
            - run: [skgen, skf, ]
            - run: [bs_dftb, Si, ]
            - run: [bs_dftb, SiO2, ]
            - get: [get_dftbp_data, Si, Si]
            - get: [get_dftbp_data, SiO2, SiO2]
            - get: [get_dftbp_meff, Si/bs, Si]
        """
    taskmapper = {'run': RunTask, 'set': SetTask, 'get': GetTask}

    def test_parsetask(self):
        """Can we parse task declarations successfully"""
        Query.flush_modelsdb()
        spec = yaml.load(self.yamldata)['tasks']
        tasklist = []
        for tt in spec:
            # we should be getting 1 dict entry only!
            (tasktype, args), = tt.items()
            if tasktype.lower() == 'set':
                tasklist.append(SetTask(*args))
            if tasktype.lower() == 'run':
                tasklist.append(RunTask(*args))
            if tasktype.lower() == 'get':
                func = gettaskdict[args[0]]
                args[0] = func
                tasklist.append(GetTask(*args))
        self.assertTrue(isinstance(tasklist[0], SetTask))
        fun = ['get_dftbp_data', 'get_dftbp_data', 'get_dftbp_meff']
        cmd = ['skgen', 'bs_dftb', 'bs_dftb']
        wd  = ['skf', 'Si', 'SiO2']
        for ii, tt in enumerate(tasklist[1:4]):
            self.assertTrue(isinstance(tt, RunTask))
            self.assertListEqual(tt.cmd, [cmd[ii]])
            self.assertEqual(tt.wd, wd[ii])
        src = ['Si', 'SiO2', 'Si/bs']
        dst = ['Si', 'SiO2', 'Si']
        for ii, tt in enumerate(tasklist[4:]):
            self.assertTrue(isinstance(tt, GetTask))
            self.assertTrue(fun[ii], tt.func.__name__)
            self.assertEqual(src[ii], tt.src_name)
            self.assertEqual(dst[ii], tt.dst_name)


class RunTaskTest(unittest.TestCase):
    """Check if we can create and execute tasks."""

    def test_inittask_exe_nopath(self):
        """Can we initialise stating the command directly"""
        # Executable assumed on the path
        t1 = RunTask(cmd='python')
        self.assertEqual(t1.wd, '.')
        self.assertEqual(t1.cmd, ['python'])
        t1 = RunTask(cmd='python', wd='other')
        self.assertEqual(t1.wd, 'other')
        self.assertEqual(t1.cmd, ['python'])
        t1 = RunTask(cmd='python -v', wd='other')
        self.assertEqual(t1.wd, 'other')
        self.assertEqual(t1.cmd, ['python', '-v'])
        t1 = RunTask(cmd=['python', '-v'], wd='other')
        self.assertEqual(t1.wd, 'other')
        self.assertEqual(t1.cmd, ['python', '-v'])

    def test_inittask_exe_withpath(self):
        """Can we initialise stating the command directly"""
        # Executable assumed on the path
        t1 = RunTask(cmd='./my/python')
        self.assertEqual(t1.wd, '.')
        self.assertEqual(t1.cmd, [os.path.abspath('./my/python')])
        # string command
        t1 = RunTask(cmd='~/my/python -v')
        self.assertEqual(t1.cmd, [os.path.abspath(os.path.expanduser('~/my/python')), '-v'])
        # list command
        t1 = RunTask(cmd=['./my/python', '-v'])
        self.assertEqual(t1.cmd, [os.path.abspath('./my/python'), '-v'])

    def test_inittask_exedict_nopath(self):
        """Can we initialise stating the command directly"""
        # Executable assumed on the path, but is aliased
        t1 = RunTask(cmd='python', exedict={'python': 'python3'})
        self.assertEqual(t1.wd, '.')
        self.assertEqual(t1.cmd, ['python3'])
        #
        t1 = RunTask(cmd='python -v', wd='other', exedict={'python': 'python3'})
        self.assertEqual(t1.wd, 'other')
        self.assertEqual(t1.cmd, ['python3', '-v'])
        #
        t1 = RunTask(cmd='python', wd='other', exedict={'python': 'python3 -v'})
        self.assertEqual(t1.wd, 'other')
        self.assertEqual(t1.cmd, ['python3', '-v'])
        #
        t1 = RunTask(cmd='python -v', wd='other', exedict={'python': 'python3 -c'})
        self.assertEqual(t1.wd, 'other')
        self.assertEqual(t1.cmd, ['python3', '-c', '-v'])

    def test_inittask_exedict_withpath(self):
        """Can we initialise stating the command directly"""
        # Executable assumed on the path, but is aliased
        t1 = RunTask(cmd='python', exedict={'python': '~/anaconda/python3'})
        self.assertEqual(t1.wd, '.')
        self.assertEqual(t1.cmd, [os.path.abspath(os.path.expanduser('~/anaconda/python3'))])
        #
        t1 = RunTask(cmd='python -v', wd='other', exedict={'python': '~/anaconda/python3'})
        self.assertEqual(t1.wd, 'other')
        self.assertEqual(t1.cmd, [os.path.abspath(os.path.expanduser('~/anaconda/python3')), '-v'])
        #
        t1 = RunTask(cmd='python', wd='other', exedict={'python': '~/anaconda/python3 -v'})
        self.assertEqual(t1.wd, 'other')
        self.assertEqual(t1.cmd, [os.path.abspath(os.path.expanduser('~/anaconda/python3')), '-v'])
        #
        t1 = RunTask(cmd='python -v', wd='other', exedict={'python': '~/anaconda/python3 -c'})
        self.assertEqual(t1.wd, 'other')
        self.assertEqual(t1.cmd, [os.path.abspath(os.path.expanduser('~/anaconda/python3')), '-c', '-v'])

    def test_passtask(self):
        """Can we declare and execute a task successfully"""
        t1 = RunTask(cmd='python pass.py', wd='test_tasks')
        #self.assertListEqual(t1.cmd,['python', 'test_tasks/pass.py'])
        #self.assertEqual(t1.wd, 'test_tasks')
        #self.assertTrue(isinstance(t1.logger,logging.Logger))
        #logger.debug(t1)
        t1(os.path.abspath('.'))
        self.assertEqual(t1.out, "Running to pass!\n")

    def test_passtask_altcmd(self):
        """Can we declare task without input file and execute a task successfully"""
        t1 = RunTask(cmd='python pass.py', wd='test_tasks')
        self.assertListEqual(t1.cmd,['python', 'pass.py'])
        self.assertEqual(t1.wd, 'test_tasks')
        self.assertTrue(isinstance(t1.logger,logging.Logger))
        logger.debug(t1)
        t1(os.path.abspath('.'))
        self.assertEqual(t1.out, "Running to pass!\n")

    def test_passtask_fromyaml(self):
        """Can we declare task without input file and execute a task successfully"""
        yamldata="""
            tasks:
                - run: [python pass.py, test_tasks]
            """
        taskmapper = {'run': RunTask, 'set': SetTask, 'get': GetTask}
        spec = yaml.load(yamldata)['tasks']
        tt = spec[0]
        (ttype, args), = tt.items()
        t1 = taskmapper[ttype](*args)
        self.assertListEqual(t1.cmd,['python', 'pass.py'])
        self.assertEqual(t1.wd, 'test_tasks')
        self.assertTrue(isinstance(t1.logger,logging.Logger))
        logger.debug(t1)
        t1(os.path.abspath('.'))
        self.assertEqual(t1.out, "Running to pass!\n")

    def test_passtask_listcmd_listinp(self):
        """Can we declare tasks with multiple input arguments?"""
        t1 = RunTask(cmd='python pass.py')
        self.assertListEqual(t1.cmd,['python', 'pass.py'])
        t2 = RunTask(cmd='python pass.py monkey boogie')
        self.assertListEqual(t2.cmd,['python', 'pass.py', 'monkey', 'boogie'])

    def test_passtask_listcmd_listinp2(self):
        """Can we declare tasks with multiple input arguments?"""
        t1 = RunTask(cmd=['python', 'pass.py'])
        self.assertListEqual(t1.cmd,['python', 'pass.py'])
        t2 = RunTask(cmd=['python', 'pass.py', 'monkey', 'boogie'])
        self.assertListEqual(t2.cmd,['python', 'pass.py', 'monkey', 'boogie'])

    def test_task_fail_subprosseserr(self):
        """Can we fail a task due to non-zero return status of executable?"""
        t1 = RunTask(cmd='python fail.py', wd='test_tasks')
        logger.debug (t1)
        self.assertRaises(CalledProcessError, t1, os.path.abspath('.'))
        self.assertEqual(t1.out, "About to fail...\n")

    def test_task_fail_oserr(self):
        """Can we fail a task due to OS error, e.g. command not found?"""
        t1 = RunTask(cmd='python_missing pass.py', wd='test_tasks')
        logger.debug (t1)
        self.assertRaises(OSError, t1, '.')

    def test_passtask_remapexe(self):
        """Test if we can redefine the executable in the yaml"""
        yamldata="""
            tasks:
                - run: [pythonspecial pass.py, test_tasks ]
            executables:
#                pythonspecial: '~/anaconda3/python'
                pythonspecial: 'python'
            """
        taskmapper = {'run': RunTask, 'set': SetTask, 'get': GetTask}
        spec = yaml.load(yamldata)
        taskspec = spec.get('tasks')
        exedict  = spec.get('executables', None)
        tt = taskspec[0]
        (ttype, args), = tt.items()
        kwargs = {"exedict": exedict}
        t1 = taskmapper[ttype](*args, **kwargs)
        #exe = normpath(expanduser('~/anaconda3/python'))
        exe = normpath(expanduser('python'))
        self.assertListEqual(t1.cmd,[exe, 'pass.py'])
        self.assertEqual(t1.wd, 'test_tasks')
        self.assertTrue(isinstance(t1.logger,logging.Logger))
        t1(os.path.abspath('.'))
        self.assertEqual(t1.out, "Running to pass!\n")

        
class GetTaskTest(unittest.TestCase):
    """Does GetTask operate correctly?"""

    def func_1(self, workdir, src, dst, *args, **kwargs):
        assert(isinstance(workdir, str))
        assert(isinstance(src, dict))
        assert(isinstance(dst, dict))
        assert('key' in src)
        dst['key'] = src['key']
        
    def func_2(self, workdir, src, dst, *args, **kwargs):
        assert(isinstance(workdir, str))
        assert(isinstance(src,dict))
        assert(isinstance(dst,dict))
        key = args[0]
        dst[key] = src[key] 

    def func_3(self, workdir, src, dst, *args, **kwargs):
        assert(isinstance(workdir, str))
        assert(isinstance(src,dict))
        assert(isinstance(dst,dict))
        keys = kwargs['query']
        if isinstance(keys, list):
          for key in keys:
              dst[key] = src[key]
        else:
            assert keys=='key'
            dst[keys] = src[keys] 

    def test_gettasks_noargs(self):
        """Can we declare and execute a GetTask?"""
        # declare: create empty model dictionaries d1 and d2
        Query.flush_modelsdb()
        src = Query.add_modelsdb('d1')
        tt = GetTask(self.func_1, 'd1', 'd2')
        self.assertEqual(tt.func, self.func_1)
        self.assertEqual(tt.src_name, 'd1')
        self.assertEqual(tt.dst_name, 'd2')
        # update source dictionary
        src['key'] = True
        src['other'] = False
        # call
        tt(os.path.abspath('.'))
        # check destination
        dst = Query.get_modeldb('d2')
        self.assertTrue(dst['key'])
        #other is not queried for... self.assertFalse(dst['other'])

    def test_gettasks_posargs(self):
        """Can we declare a GetTask with positional args and execute it?"""
        Query.flush_modelsdb()
        src = Query.add_modelsdb('d1')
        # declare: create empty model dictionaries d1 and d2
        tt = GetTask(self.func_2, 'd1', 'd1', 'key')
        self.assertEqual(tt.func, self.func_2)
        self.assertEqual(tt.src_name, 'd1')
        self.assertEqual(tt.dst_name, 'd1')
        logger.debug (tt)
        dst = Query.get_modeldb('d1')
        # update source dictionary
        src['key'] = True
        src['other'] = False
        # call
        tt(os.path.abspath('.'))
        # check destination
        self.assertTrue(dst['key'])

    def test_gettasks_kwargs(self):
        """Can we declare a GetTask with keyword args and execute it?"""
        Query.flush_modelsdb()
        src = Query.add_modelsdb('d1')
        # declare: create empty model dictionaries d1 and d2
        tt = GetTask(self.func_3, 'd1', 'd1', query=['key', 'other'])
        self.assertEqual(tt.func, self.func_3)
        self.assertEqual(tt.src_name, 'd1')
        self.assertEqual(tt.dst_name, 'd1')
        logger.debug (tt)
        dst = Query.get_modeldb('d1')
        # update source dictionary
        src['key'] = True
        src['other'] = False
        # call
        tt(os.path.abspath('.'))
        # check destination
        self.assertTrue(dst['key'])
        self.assertFalse(dst['other'])


class SetAllTasksTest(unittest.TestCase):
    """Check if we can create objectives from skpar_in.yaml"""

    def test_settasks(self):
        """Can we create a number of tasks from input spec?"""
        with open("skpar_in.yaml", 'r') as ff:
            try:
                spec = yaml.load(ff)
            except yaml.YAMLError as exc:
                logger.debug (exc)
        tasklist = set_tasks(spec['tasks'])
        for task in tasklist:
            logger.debug ("")
            logger.debug (task)
        self.assertEqual(len(tasklist), 7)
        # Set Tasks
        tt = tasklist[0]
        # Run Task
        tt = tasklist[1]
        self.assertEqual(tt.cmd, ['skgen',])
        self.assertEqual(tt.outfile, joinpath('skf', 'out.log'))
        self.assertEqual(tt.wd, 'skf')
        tt = tasklist[2]
        self.assertEqual(tt.cmd, ['bs_dftb',])
        self.assertEqual(tt.outfile, joinpath('Si', 'out.log'))
        self.assertEqual(tt.wd, 'Si')
        tt = tasklist[3]
        self.assertEqual(tt.cmd, ['bs_dftb',])
        self.assertEqual(tt.outfile, joinpath('SiO2', 'out.log'))
        self.assertEqual(tt.wd, 'SiO2')
        # GetTasks
        tt = tasklist[4]
        self.assertEqual(tt.func.__name__, 'get_dftbp_data')
        self.assertEqual(tt.src_name, 'Si')
        self.assertEqual(tt.dst_name, 'altSi')
        tt = tasklist[5]
        self.assertEqual(tt.func.__name__, 'get_dftbp_data')
        self.assertEqual(tt.src_name, 'SiO2')
        self.assertEqual(tt.dst_name, 'SiO2')
        tt = tasklist[6]
        self.assertEqual(tt.func.__name__, 'get_effmasses')
        self.assertEqual(tt.src_name, 'Si/bs')
        self.assertEqual(tt.dst_name, 'Si/bs')
        self.assertEqual(tt.args, ())
        self.assertTrue(all([item in tt.kwargs.items() for item in 
            {'directions': ['G-X', 'GK'], 'nb': 4, 'Erange': 0.002}.items()]))


class GetTaskDFTBpTest(unittest.TestCase):
    """Do DFTB query tasks work well?"""
    yamlspec = yaml.load("""
        tasks:
            - get: [get_dftbp_bs, test_dftbutils/Si/bs, Si.bs, {latticeinfo: {'type': 'FCC', 'param': 5.431}}]
            - get: [get_dftbp_meff, Si.bs, {directions: ['Gamma-X', 'Gamma-K'], nb: 1, Erange: 0.005}]
            - get: [get_dftbp_Ek, Si.bs]
        """)
    def test_execution_get_dftbp(self):
        """Can we execute the declared get_dftbp_* tasks?"""
        Query.flush_modelsdb()
        tasks = set_tasks(self.yamlspec['tasks'])
        for tt in tasks:
            tt(os.path.abspath('.'))
        db = Query.get_modeldb('Si.bs')
        self.assertAlmostEqual(db['Egap'],   1.129, places=3)
        self.assertAlmostEqual(db['Ef'],   -3.0621, places=4)
        self.assertAlmostEqual(db['me_GX'],  0.935, places=3)
        self.assertAlmostEqual(db['mh_GK'], -1.891, places=3)
        self.assertAlmostEqual(db['Ec_L_0'], 0.4  , places=3)
        self.assertAlmostEqual(db['Ec_G_0'], 1.6156, places=3)
        self.assertAlmostEqual(db['Ec_X_0'], 0.2025, places=3)
        self.assertAlmostEqual(db['Ec_U_0'], 0.6915, places=3)
        self.assertAlmostEqual(db['Ec_K_0'], 0.6915, places=3)
        # logger.debug(pformat(db))

if __name__ == '__main__':
    unittest.main()



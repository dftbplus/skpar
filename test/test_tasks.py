"""Test if we can initialise tasks and execute them"""
import sys
import unittest
import logging
import json
import yaml
import os
import shutil
from pprint import pprint, pformat
from os.path import abspath, normpath, expanduser
from os.path import join as joinpath
import numpy as np
import numpy.testing as nptest
from subprocess import CalledProcessError
from skpar.core.tasks import get_tasklist, initialise_tasks
from skpar.core.parameters import Parameter
from skpar.core.query import Query
from skpar.core.usertasks import update_taskdict
import skpar.core.taskdict as coretd
import skpar.dftbutils.taskdict as dftbtd

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(format='%(message)s')
LOGGER = logging.getLogger(__name__)

class TaskParsingTest(unittest.TestCase):
    """Check if we can create and execute tasks."""

    yamldata = """
        tasks:
            #- set: [parfiles]
            #- run: [cmd, workdir, outfile]
            #- get: [what, from-source, optional-to-destination, optional_arguments]
            - set: [skf/current.par]
            - run: [skgen, skf]
            # get_data is from dftbutils here; accepts no 'what' argument
            - get_data: [Si, Si]
            - get_meff: [Si/bs, Si]
        """

    def test_parsetask(self):
        """Can we parse task declarations successfully"""
        taskdict = {}
        update_taskdict(taskdict, 'skpar.core.taskdict', tag=False)
        update_taskdict(taskdict, 'skpar.dftbutils.taskdict', tag=False)
        userinp = yaml.load(self.yamldata)['tasks']
        tasklist = []
        tasklist = get_tasklist(userinp)
        tasks = initialise_tasks(tasklist, taskdict)
        #
        tasknames = ['set', 'run', 'get_data', 'get_meff']
        self.assertListEqual([task.name for task in tasks], tasknames)
        #
        functions = [coretd.substitute_parameters, coretd.execute,
                     dftbtd.get_dftbp_data, dftbtd.get_effmasses]
        self.assertListEqual([task.func for task in tasks], functions)


class CoreTaskExecutionTest(unittest.TestCase):
    """Check we can execute core tasks"""

    def test_simple(self):
        """Can we parse task declarations successfully"""
        jsondata = """ {
            "tasks": [
                    {"sub": [["./tmp/template.parameters.dat"]]} ,
                    {"run": ["cp parameters.dat value.dat", "./tmp"]} ,
                    {"get": ["value", "tmp/value.dat", "model"]}
                ]
            }
        """
        yamldata = """
            tasks:
                - sub: [[./tmp/template.parameters.dat]]
                - run: ["cp parameters.dat value.dat", ./tmp]
                - get: [value, tmp/value.dat, model]
            """
        taskdict = {}
        update_taskdict(taskdict, 'skpar.core.taskdict', tag=False)
        yamldata = yaml.load(yamldata)
        # print('yaml data')
        # pprint(yamldata)
        jsondata = json.loads(jsondata)
        # print('json data')
        # pprint(jsondata)
        # self.assertTrue(jsondata == yamldata) # fails for whatever reason
        tasklist = []
        userinp = yamldata
        tasklist = get_tasklist(userinp['tasks'])
        tasks = initialise_tasks(tasklist, taskdict)
        #
        var = 10
        database = {}
        par = Parameter('p0', value=var)
        workroot = './'
        coreargs = {'workroot': workroot, 'parameters': [par]}
        os.makedirs('./tmp')
        with open('./tmp/template.parameters.dat', 'w') as template:
            template.writelines("%(p0)f\n")
        # with open('./tmp/template.parameters.dat', 'r') as template:
        #     tmplstr = template.readlines()
        # print(tmplstr)
        LOGGER.info('Executing tasks')
        for task in tasks:
            # LOGGER.info(task)
            task(coreargs, database)
        self.assertEqual(np.atleast_1d(var), database['model.value'])
        shutil.rmtree('./tmp')

    def test_twopartemplates(self):
        """Can we parse task declarations successfully"""
        yamldata = """
            tasks:
                - sub: [[./tmp/template.par1.dat, ./tmp/template.par2.dat]]
                - run: ['bash run.sh', ./tmp]
                - get: [value, tmp/values.dat, model]
            """
        taskdict = {}
        update_taskdict(taskdict, 'skpar.core.taskdict', tag=False)
        yamldata = yaml.load(yamldata)['tasks']
        tasklist = []
        tasklist = get_tasklist(yamldata)
        tasks = initialise_tasks(tasklist, taskdict)
        #
        var1 = 10
        var2 = 20
        database = {}
        params = [Parameter('p0', value=var1), Parameter('p1', value=var2)]
        workroot = './'
        coreargs = {'parameters': params}
        os.makedirs('./tmp')
        with open('./tmp/template.par1.dat', 'w') as template:
            template.writelines("%(p0)f\n")
        with open('./tmp/template.par2.dat', 'w') as template:
            template.writelines("%(p1)f\n")
        with open('./tmp/run.sh', 'w') as template:
            template.writelines('cat par*.dat > values.dat\n')
        for task in tasks:
            LOGGER.info(task)
            task(coreargs, database)
        self.assertListEqual([var1, var2], list( database['model.value'] ))
        shutil.rmtree('./tmp')


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
        #self.assertTrue(isinstance(t1.LOGGER,logging.LOGGER))
        #LOGGER.debug(t1)
        t1(os.path.abspath('.'))
        self.assertEqual(t1.out, "Running to pass!\n")

    def test_passtask_altcmd(self):
        """Can we declare task without input file and execute a task successfully"""
        t1 = RunTask(cmd='python pass.py', wd='test_tasks')
        self.assertListEqual(t1.cmd,['python', 'pass.py'])
        self.assertEqual(t1.wd, 'test_tasks')
        self.assertTrue(isinstance(t1.LOGGER,logging.LOGGER))
        LOGGER.debug(t1)
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
        self.assertTrue(isinstance(t1.LOGGER,logging.LOGGER))
        LOGGER.debug(t1)
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
        LOGGER.debug (t1)
        self.assertRaises(CalledProcessError, t1, os.path.abspath('.'))
        self.assertEqual(t1.out, "About to fail...\n")

    def test_task_fail_oserr(self):
        """Can we fail a task due to OS error, e.g. command not found?"""
        t1 = RunTask(cmd='python_missing pass.py', wd='test_tasks')
        LOGGER.debug (t1)
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
        self.assertTrue(isinstance(t1.LOGGER,logging.LOGGER))
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
        LOGGER.debug (tt)
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
        LOGGER.debug (tt)
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
                LOGGER.debug (exc)
        tasklist = set_tasks(spec['tasks'])
        for task in tasklist:
            LOGGER.debug ("")
            LOGGER.debug (task)
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
        # LOGGER.debug(pformat(db))

if __name__ == '__main__':
    unittest.main()



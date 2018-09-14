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
from skpar.core.database import Database
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
            #- set: [[parfiles]]
            #- run: [cmd, workdir, outfile]
            #- get: [what, from-source, to-destination, options]
            - set: [[skf/current.par]]
            - run: [skgen, skf]
            # get_data is from dftbutils here; accepts no 'what' argument
            - get_data: [Si, Si]
            - get_meff: [Si/bs, Si]
        """

    def test_parsetask(self):
        """Can we parse task declarations successfully"""
        taskdict = {}
        update_taskdict(taskdict,
                        [['skpar.core.taskdict', ['set', 'run']]])
        update_taskdict(taskdict,
                        [['skpar.dftbutils', ['get_meff','get_data']]])
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
        update_taskdict(taskdict,
                        [['skpar.core.taskdict', ['get', 'sub', 'run']]])
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
        database = Database()
        par = Parameter('p0', value=var)
        workroot = './'
        coreargs = {'workroot': workroot, 'parametervalues': [par.value],
                    'parameternames': [par.name]}
        try:
            shutil.rmtree('./tmp')
        except FileNotFoundError:
            pass
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
        self.assertEqual(np.atleast_1d(var), database.get('model', {}).get('value'))
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
        update_taskdict(taskdict,
                        [['skpar.core.taskdict', ['get', 'sub', 'run']]])
        yamldata = yaml.load(yamldata)['tasks']
        tasklist = []
        tasklist = get_tasklist(yamldata)
        tasks = initialise_tasks(tasklist, taskdict)
        #
        var1 = 10
        var2 = 20
        database = Database()
        params = [Parameter('p0', value=var1), Parameter('p1', value=var2)]
        workroot = './'
        coreargs = {'parametervalues': [p.value for p in params],
                    'parameternames': [p.name for p in params]}
        try:
            shutil.rmtree('./tmp')
        except FileNotFoundError:
            pass
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
        self.assertListEqual([var1, var2],
                             list(database.get('model', {}).get('value')))
        shutil.rmtree('./tmp')


class GetTaskDFTBpTest(unittest.TestCase):
    """Do DFTB query tasks work well?"""
    yamlin = """
        tasks:
            - get_bs: [test_dftbutils/Si/bs, Si.bs,
                       {latticeinfo: {'type': 'FCC', 'param': 5.431}}]
            - get_meff: [Si.bs,
                         {directions: ['Gamma-X', 'Gamma-K'],
                                       nb: 1, Erange: 0.005}]
            - get_Ek: [Si.bs]
        """
    def test_execution_get_dftbp(self):
        """Can we execute the declared get_dftbp_* tasks?"""
        taskdict = {}
        update_taskdict(taskdict,
                        [['skpar.core.taskdict', ['get', 'sub', 'run']]])
        update_taskdict(taskdict,
                        [['skpar.dftbutils', ['get_bs', 'get_meff', 'get_Ek']]])
        userinp = yaml.load(self.yamlin)
        tasklist = get_tasklist(userinp['tasks'])
        tasks = initialise_tasks(tasklist, taskdict)
        #
        database = Database()
        env = {'workroot': '.', }
        for task in tasks:
            print(task)
            task(env, database)
        # 'Si.bs' should be added through the task execution
        db = database.get('Si.bs')
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



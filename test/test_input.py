"""Test correct parsing of input file"""
import os
import unittest
import logging
from skpar.core.input import parse_input, get_input, get_config
from skpar.core.usertasks import update_taskdict
from skpar.core.tasks import initialise_tasks, get_tasklist

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(format='%(message)s')
LOGGER = logging.getLogger(__name__)

class ReadInputTest(unittest.TestCase):
    """Check if we can read input file"""

    def test_import(self):
        """Can we import json?
        """
        infile = 'test_input.yaml'
        # check we handle yaml with new routine
        data1 = get_input(infile)
        #print('data1:')
        #print (data1)

        # check we handle json with new routine
        infile = 'test_input.json'
        data2 = get_input(infile)
        #print('data2:')
        #print (data2)
        self.assertDictEqual(data1, data2)

    def test_parse_nonexistent(self):
        """Can we report neatly that input file is missing?"""
        filename = "skpar_noinput.yaml"
        def wrapper():
            parsed = parse_input(filename)
            return parsed
        self.assertRaises(FileNotFoundError, wrapper)


class ParseConfigTest(unittest.TestCase):
    """Check configuration is interpreted properly"""

    def test_parse_config(self):
        """Can we read config well?"""
        skparin = 'example-tasks.yaml'
        userinp = get_input(skparin)
        config = get_config(userinp['config'])
        refdict = {
            'templatedir': os.path.abspath('./test_optimise'),
            'workroot': os.path.abspath('./_workdir/test_optimise'),
            'keepworkdirs': True,
        }
        self.assertDictEqual(refdict, config)
        return config

    def test_parse_tasks_core(self):
        """Can we read tasks well and initialise correctly?"""
        taskdict = {}
        update_taskdict(taskdict,
                        [['skpar.core.taskdict', ['sub', 'get', 'run']]])
        skparin = 'example-tasks.yaml'
        userinp = get_input(skparin)
        tasklist = get_tasklist(userinp['tasks'])
        for i, task in enumerate(tasklist):
            LOGGER.info('task %i : %s', i, task)
        tasks = initialise_tasks(tasklist, taskdict, report=True)
        self.assertEqual(len(tasks), 6)


if __name__ == '__main__':
    unittest.main()

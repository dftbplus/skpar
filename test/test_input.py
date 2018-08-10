import unittest
import logging
import json
from skpar.core.input import parse_input, get_input_yaml, get_input
from skpar.core.taskdict import gettaskdict

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(format='%(message)s')
logger = logging.getLogger(__name__)

class ParseInputTest(unittest.TestCase):
    """Check if we can handle skpar_in.yaml"""

    def test_import_yaml(self):
        """Can we import yaml?
        """
        infile = 'test_in.yaml'
        data = get_input_yaml(infile)
        with open('test_in.json', 'w') as outfile:
            json.dump(data, outfile)

    def test_import(self):
        """Can we import json?
        """
        # since we know this works from previous releases
        infile = 'test_in.yaml'
        data = get_input_yaml(infile)

        # check we handle yaml with new routine
        data1 = get_input(infile)
        self.assertTrue(data,data1)

        # check we handle json with new routine
        infile = 'test_in.json'
        data2 = get_input(infile)
        self.assertTrue(data,data2)

    def test_parse_input(self):
        """Can we parse input and create all tasks, objectives, etc.?"""
        filename = "skpar_in.yaml"
        filename = "test_optimise.yaml"
        _input = parse_input(filename)
        tasklist     = _input[0]
        objectives   = _input[1]
        optimisation = _input[2]
        for task in tasklist:
            logger.debug (task)
        for objv in objectives:
            logger.debug (objv)
        # we should print here the queries, but how do we get them?
        # and we should put assertions; currently this test cannot fail!

    def test_parse_nonexistent(self):
        """Can we report neatly that input file is missing?"""
        filename = "skpar_noinput.yaml"
        def wrapper():
            parsed = parse_input(filename)
            return parsed
        self.assertRaises(FileNotFoundError, wrapper)

if __name__ == '__main__':
    unittest.main()



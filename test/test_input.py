import unittest
import logging
import json
from skpar.core.input import parse_input, get_input
from skpar.core.taskdict import gettaskdict

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(format='%(message)s')
logger = logging.getLogger(__name__)

class ParseInputTest(unittest.TestCase):
    """Check if we can parse input data"""

    def test_import(self):
        """Can we import json?
        """
        infile = 'test_in.yaml'
        # check we handle yaml with new routine
        data1 = get_input(infile)
        print('data1:')
        print (data1)

        # check we handle json with new routine
        infile = 'test_in.json'
        data2 = get_input(infile)
        print('data2:')
        print (data2)
        self.assertDictEqual(data1,data2)


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



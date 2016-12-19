import unittest
import logging
from skopt.input import parse_input
from skopt.taskdict import gettaskdict

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(format='%(message)s')
logger = logging.getLogger(__name__)

def get_model_data (src, dst, *args, **kwargs):
    assert isinstance(src, str), type(src)
    data = np.loadtxt(src)
    dst['yval'] = data


class ParseInputTest(unittest.TestCase):
    """Check if we can handle skopt_in.yaml"""

    def test_parse_input(self):
        """Can we parse input and create all tasks, objectives, etc.?"""
        filename = "skopt_in.yaml"
        filename = "test_optimise.yaml"
        gettaskdict['get_model_data'] = get_model_data
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
        filename = "skopt_noinput.yaml"
        def wrapper():
            parsed = parse_input(filename)
            return parsed
        self.assertRaises(FileNotFoundError, wrapper)

if __name__ == '__main__':
    unittest.main()



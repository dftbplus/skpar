import unittest
from skopt.input import parse_input


class ParseInputTest(unittest.TestCase):
    """Check if we can handle skopt_in.yaml"""

    def test_parse_input(self):
        """Can we parse input and create all tasks, objectives, etc.?"""
        filename = "skopt_in.yaml"
        _input = parse_input(filename)
        tasklist   = _input[0]
        objectives = _input[1]
        for task in tasklist:
            print (task)
        for objv in objectives:
            print (objv)
        # we should print here the queries, but how do we get them?

    def test_parse_nonexistent(self):
        """Can we report neatly that input file is missing?"""
        filename = "skopt_noinput.yaml"
        def wrapper():
            parsed = parse_input(filename)
            return parsed
        self.assertRaises(FileNotFoundError, wrapper)

if __name__ == '__main__':
    unittest.main()



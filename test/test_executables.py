import unittest
import yaml
import logging

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(format='%(message)s')
logger = logging.getLogger(__name__)


class ExecutablesTest(unittest.TestCase):
    """Check if we can get the map of executables"""

    def test_getexemap(self):
        """Can we construct the dictionary for executables?"""
        yamldata = """executables:
            atom: gridatom
            skgen: skgen.sh
            lammps: mpirun -n 4 lmp_mpi
            bands: dp_bands band.out bands
        """
        exedict = yaml.load(yamldata).get('executables', None)
        try:
            for key, val in exedict.items():
                logger.debug ("{:>10s} : {}".format(key, " ".join(val.split())))
        except AttributeError:
            # assume no executables are remapped
            pass

if __name__ == '__main__':
    unittest.main()

import os
import sys
import logging
from skopt import queryDFTB as qdp
from skopt import queryBands as qbands
from skopt.extras.bandstructure_Si import ref_Si, analyseEk_Si, analyseEkst_Si, analyseMeff_Si
from skopt.system import Analyser, System, queryData

testdir = os.getcwd()
logging.basicConfig(level=logging.DEBUG,
                    format='%(name)s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename=os.path.join(testdir,'test.log'),
                    filemode='w')
log=logging.getLogger("test")
# define a Handler which writes INFO messages or higher to the sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
# set a format which is simpler for console use
formatter = logging.Formatter('%(name)s: %(levelname)-8s %(message)s')
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('test').addHandler(console)

log.debug('Testing queryBands in {0}'.format(testdir))

workdir = os.path.join(testdir,'../test.Si/Si/bs')
assert os.path.exists(workdir)

assert os.path.exists(os.path.join(workdir,'detailed.out'))
assert os.path.exists(os.path.join(workdir,'bands_tot.dat'))

data = qdp.DFTBOutput(workdir=workdir)

assert not data.sccConverged() # calculation along symmetry lines is essentially non-SCC
assert data.getOutputElectrons() == 8
assert not data.withSOC()

withSOC = data.withSOC()
nElectrons = data.getOutputElectrons()

bs = qbands.Bands(workdir, nElectrons=nElectrons, SOC=withSOC, log=log)

Eg,Ecb,Evb = bs.getEgap()
log.debug('Egap = {0:n}, Ecb = {1:n}, Evb = {2:n}, [eV]'.format(Eg, Ecb, Evb))

# part two of the test
bsdata={'lattice': 'FCC', 'equivkpts': [('U', 'K'), ]}
calculated = {}
tasks = []
tasks.append(qdp.QueryDataDFTB(bsdata, workdir=workdir, Eref='VBtop', 
                               getBands=True, getHOMO=True, 
                               getkLines=True, prepareforplot=True, log=log))
tasks.append(Analyser(analyse=analyseEk_Si, data=bsdata, results=calculated, log=log))
for t in tasks:
    t()


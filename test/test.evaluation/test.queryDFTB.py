import os
import sys
from skopt import queryDFTB as qdp

testdir = os.getcwd()
print ('Testing queryDFTB in {0}'.format(testdir))

workdir = os.path.join(testdir,'Si/scc')
assert os.path.exists(workdir)

assert os.path.exists(os.path.join(workdir,'detailed.out'))

data = qdp.DFTBOutput(workdir=workdir)

assert data.sccConverged()
assert data.getCurrent() is None
assert (data.getCurrent(contacts=(2,3)) is None)
assert (data.getNeutralCharge() is None)
assert data.getOutputElectrons() == 8
assert data.getOutputCharge() == 8
assert data.getInputElectrons() == 8
assert data.getInputCharge() == 8

print ('Total energy {0:n}'.format(data.getEnergy('Total energy')))
print ('Total electronic energy {0:n}'.format(data.getEnergy('Total Electronic energy')))
print ('Band energy {0:n}'.format(data.getEnergy('Band energy')))
print ('Repulsive energy {0:n}'.format(data.getEnergy('Repulsive energy')))
print ('Fermi energy {0:n}'.format(data.getEnergy('Fermi energy')))

assert not data.withSOC()
if not data.withSOC():
    assert data.getEnergy('Energy L.S') is None

print ('Test queryDFTB: PASSED')

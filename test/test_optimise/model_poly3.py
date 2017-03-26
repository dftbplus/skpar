"""Model for testing the optimiser.

It consists of a 3rd order polynomial.
"""
import numpy as np
from numpy.polynomial.polynomial import polyval

# read the parameters of the model
#                    names: ['keys', 'values']
#                    formats: ['S15', 'float']
raw = np.loadtxt('parameters.dat', dtype=[('keys', 'S15'), ('values', 'float')])
c = np.array([pair[1] for pair in raw])
#print(c)

# do the calculations
xmin, xmax = -10, 10
nref = 5
x = np.linspace(xmin+1, xmax-1, nref)
y = polyval(x, c)

# write the output
#print (y)
with open('model_poly3_out.dat', 'wb') as fh:
    np.savetxt(fh, y)
with open('model_poly3_xval.dat', 'wb') as fh:
    np.savetxt(fh, x)

#!/usr/bin/env python3
################################################################################
#
# Simple tool for fitting repulsives on data
#
# (c) Bálint Aradi, 2016
#
################################################################################
import sys
import argparse
import numpy as np
import scipy.interpolate as spinter
import scipy.optimize as spopt
import scipy.linalg as linalg

################################################################################

# Minimal and maximal power of fitted polynomial
MINPOW = 3
MAXPOW = 11

# Lenght of 5th order polymial tail
POLY5LEN = 0.2

# Fine and coarse grids
GRID_FINE = 0.001
GRID_COARSE = 0.02

# Numerical tolerance
EPSILON = 1e-12

# Spline header tag
SPLINETAG = 'Spline'


def get_data(fname):
    data = np.loadtxt(fname)
    xx = data[:,0]
    yy = data[:,1]
    return xx, yy


def polynomial(cc, minpow, rr, rcut):
    'Polynomial of the form sum_n c_n * (rcut - r)^n'
    dr = rcut - rr
    res = cc[-1]
    for ii in range(len(cc) - 2, -1, -1):
        res = res * dr + cc[ii]
    for ii in range(minpow):
        res *= dr
    return res


def get_polyderiv(nderiv, cc, minpow):
    'Derivative of a polynomial of the form sum_n c_n (rcut - r)^n'
    for ideriv in range(1, nderiv + 1):
        cc = np.array([ -cc[ii] * (ii + minpow) for ii in range(len(cc)) ])
        minpow = minpow - 1
        if minpow == -1:
            cc = cc[1:]
            minpow = 0
    return cc, minpow



def damping_cos(r0, r1, rr):
    return np.where(rr >= r0, np.cos((rr - r0) / (r1 - r0) * np.pi / 2.0), 1.0)


def get_spline_coeffs(xx, yy, derivs=None, boundary='natural'):
    'Spline coefficients for a spline with given 1st derivatives at its ends.'

    assert boundary in ['natural', 'clamped', 'not-a-knot']
    assert (boundary == 'clamped') == (derivs is not None)
    if derivs is not None:
        deriv0, deriv1 = derivs
    nn = len(xx)
    hh = xx[1:] - xx[:-1]
    mu = hh[:-1] / (hh[:-1] + hh[1:])
    nu = 1.0 - mu
    dd = 6.0 / (hh[:-1] + hh[1:]) * ((yy[2:] - yy[1:-1]) / hh[1:] 
                                     - (yy[1:-1] - yy[0:-2]) / hh[:-1])
    if boundary == 'clamped':
        nu0 = 1.0
        mun = 1.0
        d0 = 6.0 / hh[0] * ((yy[1] - yy[0]) / hh[0] - deriv0)
        dn = 6.0 / hh[-1] * (deriv1 - (yy[-1] - yy[-2]) / hh[-1])
    else:
        nu0 = 0.0
        mun = 0.0
        d0 = 0.0
        dn = 0.0
    mu = np.hstack((mu, [ mun ]))
    nu = np.hstack(([ nu0 ], nu))
    dd = np.hstack((d0, dd, dn))
    mtx = 2.0 * np.identity(nn, dtype=float)
    for ii in range(nn - 1):
        mtx[ii,ii+1] = nu[ii]
        mtx[ii+1,ii] = mu[ii]
    if boundary == 'not-a-knot':
        mtx[0,0] = 1.0
        mtx[0,1] = -1.0
        mtx[-1,-2] = 1.0
        mtx[-1,-1] = -1.0
    mm = linalg.solve(mtx, dd)
    c0 = yy[:-1]
    c1 = (yy[1:] - yy[:-1]) / hh - (2.0 * mm[:-1] + mm[1:]) / 6.0 * hh
    c2 = mm[:-1] / 2.0
    c3 = (mm[1:] - mm[:-1]) / (6.0 * hh)
    mtx = np.array([ c0, c1, c2, c3 ])
    return np.transpose(mtx)


def get_spline_values(splcoeffs, r0, rr):
    left = r0[:-1] - EPSILON
    right = r0[1:] + EPSILON
    values = np.zeros((len(rr), ), dtype=float)
    for ir, rcur in enumerate(rr):
        intervals = np.nonzero(np.logical_and(rcur >= left, rcur < right))[0]
        ispline = intervals[0]
        dr = rcur - r0[ispline]
        cc = splcoeffs[ispline]
        values[ir] = ((cc[3] * dr + cc[2]) * dr + cc[1]) * dr + cc[0]
    return values


def get_splineval012(splcoeffs, r0, rr):
    alpha, beta, gamma, delta = splcoeffs
    dr = rr - r0
    f0 = ((delta * dr + gamma) * dr + beta) * dr + alpha
    f1 = (3.0 * delta * dr + 2.0 * gamma) * dr + beta
    f2 = 6.0 * delta * dr + 2.0 * gamma
    return f0, f1, f2


def get_poly5coeffs(derivs, r0, rcut):
    aa, bb, cc = derivs
    alpha = aa
    beta = bb
    gamma = cc / 2.0
    dr = rcut - r0
    dr2 = dr * dr
    dr3 = dr2 * dr
    mtx = np.array([[ dr**3, dr**4, dr**5 ],
                    [ 3.0 * dr**2, 4.0 * dr**3, 5.0 * dr**4 ],
                    [ 6.0 * dr, 12.0 * dr**2, 20.0 * dr**3 ]])
    rhs = np.array([ -(alpha + beta * dr + gamma * dr**2),
                     -(beta + 2 * gamma * dr),
                     -(2.0 * gamma) ])
    delta, epsilon, phi = linalg.solve(mtx, rhs)
    return alpha, beta, gamma, delta, epsilon, phi


def get_poly5_values(coeffs, r0, rr):
    dr = rr - r0
    res = coeffs[-1]
    for ii in range(len(coeffs) - 2, -1, -1):
        res = res * dr + coeffs[ii]
    return res
    

def get_expcoeffs(derivs, r0):
    aa, bb, cc = derivs
    alpha = -cc / bb
    beta = alpha * r0 + np.log(cc / alpha**2)
    gamma = aa - np.exp(-alpha * r0 + beta)
    return alpha, beta, gamma


def get_exp_values(coeffs, rr):
    aa, bb, cc = coeffs
    return np.exp(-aa * rr + bb) + cc


def write_splinerep(fname, expcoeffs, splcoeffs, poly5coeffs, rr, rcut):
    fp = open(fname, 'w')
    fp.write('Spline\n')
    fp.write('{:d} {:.4f}\n'.format(len(rr), rcut))
    fp.write('{:15.8E} {:15.8E} {:15.8E}\n'.format(*expcoeffs))
    splcoeffs_format = ' '.join(['{:6.3f}'] * 2 + ['{:15.8E}'] * 4) + '\n'
    for ir in range(len(rr) - 1):
        rcur = rr[ir]
        rnext = rr[ir + 1]
        fp.write(splcoeffs_format.format(rcur, rnext, *splcoeffs[ir]))
    poly5coeffs_format = ' '.join(['{:6.3f}'] * 2 + ['{:15.8E}'] * 6) + '\n'
    fp.write(poly5coeffs_format.format(rr[-1], rcut, *poly5coeffs))
    fp.close()
    print_io_log(fname, 'Repulsive in spline format')


def write_as_nxy(fname, datadesc, vectors, column_names):
    header_parts = []
    for ii, colname in enumerate(column_names):
        header_parts.append('Column {}: {}'.format(ii + 1, colname))
    header = '\n'.join(header_parts)
    data = np.array(vectors).transpose()
    np.savetxt(fname, data, header=header)
    print_io_log(fname, datadesc)


def print_io_log(fname, fcontent):
    print("{} -> '{}'".format(fcontent, fname))

def append_spline (fin, fspl, fout):
    """Take electronic part from fin add fspl and write to fout."""
    with open(fspl, 'r') as f:
        spline = f.readlines()
    with open(fin, 'r') as f:
        skf = f.readlines()
    newskf = []
    for line in skf:
        if line == SPLINETAG:
            break
        else:
            newskf.append(line)
    with open(fout, 'w') as f:
        f.writelines(newskf)
        f.write('\n')         # do we need this line?
        f.writelines(spline)  # assuming fspl already has SPLINETAG


#if __name__ == '__main__':
def splinerepfit(ftargets='fitpoints.dat', fout='repulsive.spl'):
    """Repulsive potential fit, based on spline over given target points."""
    data = np.loadtxt(ftargets)
    rfit = data[0:-1,0]
    yfit = data[0:-1,1]
    rmin, rcut = data[-1,0:2]
    print('FIT-r', rfit)
    print('FIT-y', yfit)
    print('rmin:', rmin)
    print('rcut:', rcut)

    # Fit spline
    rspline = rfit
    erepc = yfit
    rrange = rspline[-1] - rspline[0]
    rr = np.linspace(rspline[0], rspline[-1], int(rrange/GRID_FINE)+1)
    splcoeffs = get_spline_coeffs(rspline, erepc, boundary='not-a-knot')
    splval = get_spline_values(splcoeffs, rspline, rr)
    write_as_nxy('splinefit.dat', 'Spline fitted on polynomial fit',
                 (rr, splval), ('rr', 'fitted spline'))

    # Fit exponential start to spline
    splderivs = get_splineval012(splcoeffs[0], rspline[0], rspline[0])
    expcoeffs = get_expcoeffs(splderivs, rspline[0])
    expbuf = 0.5
    rexp = np.linspace(rspline[0]-expbuf, rspline[0], int(expbuf/GRID_FINE)+1)
    expvals = get_exp_values(expcoeffs, rexp)
    write_as_nxy('headfit.dat', 'Exponentail head', (rexp, expvals),
                 ('rr', 'exponential head'))

    # Fit 5th order polynomial tail
    derivs = get_splineval012(splcoeffs[-1], rspline[-2], rspline[-1])
    poly5coeffs = get_poly5coeffs(derivs, rspline[-1], rcut)
    p5range = rcut - rspline[-1]
    rpoly5 = np.linspace(rspline[-1], rcut, int(p5range/GRID_FINE)+1)
    poly5vals = get_poly5_values(poly5coeffs, rspline[-1], rpoly5)
    write_as_nxy('tailfit.dat', '5th order spline tail', (rpoly5, poly5vals),
                 ('rr', '5th order spline'))

    # Write SK-compatible representation
    write_splinerep(fout, expcoeffs, splcoeffs, poly5coeffs, 
                    rspline, rcut)

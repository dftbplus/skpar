"""
    This module lists the component vectors of the direct and reciprocal lattices
    for different crystals.
    It is based on the following publication:
    Wahyu Setyawan and Stefano Curtarolo, "High-throughput electronic band 
    structure calculations: Challenges and tools", Comp. Mat. Sci. 49 (2010),
    pp. 291--312.
    """
import sys
import numpy as np
from numpy import pi, sqrt
from fractions import Fraction
import logging
from pprint import pprint, pformat

logger = logging.getLogger(__name__)


class Lattice(object):
    """Generic lattice class."""
    def __init__(self, info):
        try:
            self.name = info['type']
        except KeyError:
            logger.critical('Cannot continue without lattice type')
            sys.exit(2)
        self.scale = info.get('scale', 2*pi)
        try:
            self.param = info['param']
        except:
            logger.critical('Cannot continue without lattice parameter(s)')
            sys.exit(2)
        try:
            self.setting = info['setting']
            lat = get_lattice[self.name](self.param, self.setting)
        except KeyError:
            lat = get_lattice[self.name](self.param)
        self.constants = lat.constants
        self.primv = lat.primv
        self.convv = lat.convv
        self.SymPts_k = lat.SymPts_k
        self.path = info.get('path', lat.standard_path)
        #
        self.reciprv = get_recipr_cell(self.primv, self.scale)
        self.SymPts = {}
        for k,v in self.SymPts_k.items():
            self.SymPts[k] = get_kvec(v, self.reciprv)

    def get_kcomp(self, string):
        """Return the k-components given a string label or string set of fraction.

        Example of string:

            s = 'X'
            s = '1/2 0 1/2'
            s = '1/2, 0, 1/2'
            s = '0.5 0 0.5'
        """
        try:
            # assume it is a label
            comp = self.SymPts_k[string]
        except KeyError:
            # assume it is a triplet of fractions (string)
            # i.e. '1/3 1/2 3/8' or '1/4, 0.5, 0'
            frac = string.replace(',', ' ').split()
            assert len(frac) == 3
            comp = [Fraction(f) for f in frac]
        return np.array(comp)

    def get_kvec(self, kpt):
        """Return the real space vector corresponding to a k-point.
        """
        return get_kvec(kpt, self.reciprv)

    def __repr__(self):
        return repr_lattice(self)

class CUB(object):
    """
    This is CUBic, cP lattice
    """
    def __init__(self, param, setting=None):
        try:
            a = param[0]
        except TypeError:
            a = param
        self.setting = setting
        self.constants = [a, a, a, pi/2, pi/2, pi/2]
        self.a = a
        self.primv =  [ np.array((a, 0., 0.)),
                        np.array((0., a, 0.)),
                        np.array((0., 0., a)) ]
        self.convv = self.primv
        self.SymPts_k =\
            { 'Gamma': (0,0,0),
                  'M': (1./2., 1./2., 0.),
                  'R': (1./2., 1./2., 1./2.),
                  'X': (0., 1./2., 0.), }
        self.standard_path = "Gamma-X-M-Gamma-R-X|M-R"


class FCC(object):
    """
    This is Face Centered Cubic lattice (cF)
    """
    def __init__(self, param, setting='curtarolo'):
        try:
            a = param[0]
        except (TypeError, IndexError) as e:
            a = param
        self.constants = [a, a, a, pi/2, pi/2, pi/2]
        self.a = a
        self.setting = setting
        if setting == 'curtarolo':
            self.primv =  [np.array((0   , a/2., a/2.)),
                           np.array((a/2., 0   , a/2.)),
                           np.array((a/2., a/2., 0   ))]
            self.convv = [ np.array((a, 0, 0,)),
                           np.array((0, a, 0,)),
                           np.array((0, 0, a,)) ]
            # symmetry points in terms of reciprocal lattice vectors
            self.SymPts_k = \
                { 'Gamma': (0.,0.,0.),
                    'K': (3./8.,3./8.,3./4.),
                    'L': (1./2.,1./2.,1./2.),
                    'U': (5./8.,1./4.,5./8.),
                    'W': (1./2.,1./4.,3./4.),
                    'X': (1./2.,0.,1./2.),  }
            self.standard_path = "Gamma-X-W-K-Gamma-L-U-W-L-K|U-X"
        else:
            logger.error('Unsupported setting {} for {} lattice'.format(setting, self.__name__))
            sys.exit(2)


class BCC(object):
    """
    This is Body Centered Cubic lattice (cF)
    """
    def __init__(self, param, setting='curtarolo'):
        try:
            a = param[0]
        except (TypeError, IndexError) as e:
            a = param
        self.constants = [a, a, a, pi/2, pi/2, pi/2]
        self.a = a
        self.setting = setting
        if setting == 'curtarolo':
            self.primv = [ np.array((-a/2.,  a/2.,  a/2.)),
                           np.array(( a/2., -a/2.,  a/2.)),
                           np.array(( a/2.,  a/2., -a/2.)) ]
            self.convv = [ np.array((a, 0, 0,)),
                           np.array((0, a, 0,)),
                           np.array((0, 0, a,)) ]
            self.SymPts_k = \
                { 'Gamma': (0.,0.,0.),
                    'H': (1./2., -1./2., 1./2.),
                    'P': (1./4.,  1./4., 1./4.),
                    'N': (   0.,     0., 1./2.) }
            self.standard_path = "Gamma-H-N-Gamma-P-H|P-N"
        else:
            logger.error('Unsupported setting "{}" for {} lattice'.format(setting, self.__name__))
            sys.exit(2)


class HEX(object):
    """
    This is HEXAGONAL, hP lattice
    """
    def __init__(self, param, setting='curtarolo'):
        a, c = param[:2]
        self.constants = [a, a, c, pi/2, pi/2, 2*pi/3]
        self.a = a
        self.c = c
        self.setting = setting
        if setting == 'curtarolo':
            self.primv =  [ np.array((a/2., -a*np.sqrt(3)/2., 0.)),
                            np.array((a/2., +a*np.sqrt(3)/2., 0.)),
                            np.array((0, 0, c)) ]
            self.convv = self.primv
            self.SymPts_k =\
                { 'Gamma': (0,0,0),
                    'A': (0., 0., 1./2.),
                    'H': (1./3., 1./3., 1./2.),
                    'K': (1./3., 1./3., 0.),
                    'L': (1./2., 0., 1./2.),
                    'M': (1./2., 0., 0.), }
            self.standard_path = "Gamma-M-K-Gamma-A-L-H-A|L-M|K-H"
        else:
            logger.error('Unsupported setting "{}" for {} lattice'.format(setting, self.__name__))
            sys.exit(2)


class TET(object):
    """
    This is TETRAGONAL, tP lattice
    """
    def __init__(self, param, setting='curtarolo'):
        a, c = param[:2]
        self.constants = [a, a, c, pi/2, pi/2, pi/2]
        self.a = a
        self.c = c
        self.setting = setting
        if setting == 'curtarolo':
            self.primv = [ np.array((a, 0., 0.)),
                           np.array((0., a, 0.)),
                           np.array((0.,0., c)) ]
            self.convv = self.primv
            self.SymPts_k =\
                { 'Gamma': (0,0,0),
                    'A': (1./2., 1./2., 1./2.),
                    'M': (1./2., 1./2., 0.),
                    'R': (0., 1./2., 1./2.),
                    'X': (0., 1./2., 0.),
                    'Z': (0., 0., 1./2.), }
            self.standard_path = "Gamma-X-M-Gamma-Z-R-A-Z|X-R|M-A"
        else:
            logger.error('Unsupported setting {} for {} lattice'.format(setting, self.__name__))
            sys.exit(2)


class ORC(object):
    """
    This is ORTHOROMBIC, oP lattice
    """
    def __init__(self, param, setting='curtarolo'):
        a, b, c = param[:3]
        self.constants = [a, b, c]
        self.a = a
        self.b = b
        self.c = c
        self.setting = setting
        if setting == 'curtarolo':
            self.primv = [ np.array((a, 0., 0.)),
                           np.array((0., b, 0.)),
                           np.array((0., 0., c)) ]
            self.convv = self.primv
            self.SymPts_k =\
                { 'Gamma': (0,0,0),
                    'R': (1./2., 1./2., 1./2.),
                    'S': (1./2., 1./2., 0.),
                    'T': (0., 1./2., 1./2.),
                    'U': (1./2., 0., 1./2.),
                    'X': (1./2., 0.,  0.),
                    'Y': (0., 1./2., 0.),
                    'Z': (0., 0., 1./2.), }
            self.standard_path = "Gamma-X-S-Y-Gamma-Z-U-R-T-Z|Y-T|U-X|S-R"
        else:
            logger.error('Unsupported setting {} for {} lattice'.format(setting, self.__name__))
            sys.exit(2)


class RHL(object):
    """
    This is Rhombohedral RHL, hR lattice
    Primitive lattice defined via:
    a = b = c, and alpha = beta = gamma <> 90 degrees
    Two variations exists: RHL1 (alpha < 90) and RHL2 (alpha > 90)
    """
    def __init__(self, param, setting=None):
        """
        Initialise the lattice parameter(s) upon instance creation, and
        calculate the direct and reciprocal lattice vectors, as well
        as the components of the k-vectors defining the high-symmetry
        points known for the given lattice.
        Note that RHL has two variants:
        RHL1, where alpha < 90 degrees
        RHL2, where alpha > 90 degrees
        Symmetry points (SymPts_k) and standard_path are from:
        W. Setyawan, S. Curtarolo / Computational Materials Science 49 (2010) 299-312
        """
        a, alpha = param[:2]
        self.setting = setting
        assert not abs(alpha - 90.0) < 1.e-5
        self.alpha_rad = np.radians(alpha)
        self.constants = [a, a, a, alpha, alpha, alpha]
        self.a = a
        self.angle = alpha
        c1 = np.cos(self.alpha_rad)
        c2 = np.cos(self.alpha_rad/2.)
        s2 = np.sin(self.alpha_rad/2.)
        self.primv =  [ self.a*np.array([c2, -s2, 0.]),
                        self.a*np.array([c2, +s2, 0.]),
                        self.a*np.array([c1/c2, 0., np.sqrt(1-(c1/c2)**2)]) ]
        self.convv = self.primv
        # The fractions defining the symmetry points in terms of reciprocal vectors
        # are dependent on the angle alpha of the RHL lattice 
        # So we cannot use the dictionary SymPts_k to get them.
        if self.alpha_rad < pi/2.:
            eta = (1 + 4 * np.cos(self.alpha_rad)) / (2 + 4 * np.cos(self.alpha_rad))
            nu  = 3./4. - eta/2.
            self.SymPts_k =\
                { 'Gamma': (0, 0, 0), 
                    'B' : (eta, 1./2., 1-eta),
                    'B1': (1./2., 1-eta, eta-1),
                    'F' : (1./2., 1./2., 0),
                    'L' : (1./2., 0, 0),
                    'L1': (0, 0, -1./2.),
                    'P' : (eta, nu, nu),
                    'P1': (1-nu, 1-nu, 1-eta),
                    'P2': (nu, nu, eta-1),
                    'Q' : (1-nu, nu, 0),
                    'X' : (nu, 0, -nu),
                    'Z' : (1./2., 1/2., 1./2.), }
            self.standard_path = "Gamma-L-B1|B-Z-Gamma-X|Q-F-P1-Z|L-P"
        else:
            self.name = 'RHL2'
            eta = 1./(2 * (np.tan(self.alpha_rad/2.))**2)
            nu  = 3./4. - eta/2.
            self.SymPts_k =\
                { 'Gamma':  (0, 0, 0),
                    'F' : (1./2., -1./2., 0),
                    'L' : (1./2., 0, 0),
                    'P' : (1-nu, -nu, 1-nu),
                    'P1': (nu, nu-1, nu-1),
                    'Q' : (eta, eta, eta),
                    'Q1': (1-eta, -eta, -eta),
                    'Z' : (1./2., -1/2., 1./2.), }
            self.standard_path = "Gamma-P-Z-Q-Gamma-F-P1-Q1-L-Z"
        self.eta = eta
        self.nu  = nu


class MCL(object):
    """
    This is simple Monoclinic MCL_* (mP) lattice, set via
    a, b <= c, and alpha < 90 degrees, beta = gamma = 90 degrees as in
    W. Setyawan, S. Curtarolo / Computational Materials Science 49 (2010) 299-312.
    Setting=ITC should work for the standard setting (angle>90) of ITC-A, 
    but is not currently implemented.
    Note that conventional and primitive cells are the same.
    """
    def __init__(self, param, setting='curtarolo'):
        """
        The default setting assumes that alpha < 90 as in 
        W. Setyawan, S. Curtarolo / Computational Materials Science 49 (2010) 299-312
        TODO: support for setting='ITC'
        """
        a, b, c, beta = param[:4]
        self.beta_rad = np.radians(beta)
        self.constants = [a, b, c, pi/2, self.beta_rad, pi/2]
        self.a = a
        self.b = b
        self.c = c
        self.angle = beta
        self.setting = setting
        if setting == 'curtarolo':
            assert (a<=c) and (b<=c) and (beta < 90) 
            a1c = a * np.array([1, 0, 0])
            a2c = b * np.array([0, 1, 0])
            a3c = c * np.array([0, np.cos(self.beta_rad), np.sin(self.beta_rad)])
            self.convv = np.array([a1c, a2c, a3c])
            # primitive cell
            self.primv = self.convv
            #
            eta = ( 1 - self.b * np.cos(self.beta_rad) / self.c ) / ( 2 * (np.sin(self.beta_rad))**2 )
            nu  = 1./2. - eta * self.c * np.cos(self.beta_rad) / self.b 
            self.SymPts_k =\
                { 'Gamma': (0., 0., 0.),
                    'A'  : (1./2., 1./2., 0.), 
                    'C'  : (0., 1./2., 1./2.), 
                    'D'  : (1./2., 0., 1./2.), 
                    'D1' : (1./2., 0., -1./2.), 
                    'E'  : (1./2., 1./2., 1./2.), 
                    'H'  : (0., eta, 1-nu), 
                    'H1' : (0., 1-eta, nu), 
                    'H2' : (0., eta, -nu), 
                    'M'  : (1./2., eta, 1-nu), 
                    'M1' : (1./2., 1-eta, nu), 
                    'M2' : (1./2., eta, -nu), 
                    'X'  : (0., 1./2., 0.), 
                    'Y'  : (0., 0., 1./2.), 
                    'Y1' : (0., 0., -1./2.), 
                    'Z'  : (1./2., 0., 0.), }
            self.standard_path = "Gamma-Y-H-C-E-M1-A-X-H1|M-D-Z|Y-D"
        else:
            logger.error('Unsupported setting {} for {} lattice'.format(setting, self.__name__))
            sys.exit(2)


class MCLC(object):
    """
    This is base-centered Monoclinic MCLC_* mS,  lattice
    Primitive lattice defined via:
    a <> b <> c, and alpha <> 90 degrees, beta = gamma = 90 degrees
    """
    def __init__(self, param, setting='ITC'):
        """
        Note that MCLC has several variants, depending on abc ordering and
        face(base) centering or not:
        Additionally, ITC stipulates alpha > 90 degrees, while in 
        W. Setyawan, S. Curtarolo / Computational Materials Science 49 (2010) 299-312
        alpha < 90 is used.
        """
        a, b, c, angle = param[:4]
        self.a     = a
        self.b     = b
        self.c     = c
        self.angle_rad = np.radians(angle)
        self.angle = angle
        self.constants = [a, b, c, angle]
        self.setting = setting
        if setting == 'ITC' and self.angle_rad > pi/2.:
            assert (a >= b) and (a >= c) and (angle > 90) 
            # conventional cell
            a1c = self.a * np.array([1, 0, 0])
            a2c = self.b * np.array([0, 1, 0])
            a3c = self.c * np.array([np.cos(self.angle_rad), 0, np.sin(self.angle_rad)])
            self.convv = np.array([a1c, a2c, a3c])
            # primitive cell
            a1p = (+a1c + a2c) / 2.
            a2p = (-a1c + a2c) / 2.
            a3p = a3c
            self.primv = np.array([a1p, a2p, a3p])

            # The fractions defining the symmetry points in terms of reciprocal 
            # cell-vectors are dependent on the angle alpha of the MCLC lattice 
            # So we cannot use the dictionary SymPts_k to get them.
            psi = 3./4. - (self.b / (2 * self.a * np.sin(self.angle_rad)))**2
            phi = psi - ( 3./4. - psi ) * (self.a / self.c) * np.cos(self.angle_rad)
            ksi = ( 2 + (self.a/self.c) *  np.cos(self.angle_rad) ) / ( 2 * np.sin(self.angle_rad) )**2
            eta = 1./2. - 2 * ksi * (self.c/self.a) *  np.cos(self.angle_rad)
            #logger.debug ((psi, phi, ksi, eta))
            self.SymPts_k =\
                { 'Gamma': (0., 0., 0.),
                    'N' : (0., 1./2., 0.),
                    'N1': (1./2., 0, 0),
                    'F' : (ksi-1, 1-ksi, 1-eta),
                    'F1': (-ksi, ksi, eta),
                    'F2': (ksi, -ksi, 1-eta),
                    'I' : (phi-1, phi, 1./2.),
                    'I1': (1-phi, 1-phi, 1./2.),
                    'Y' : (-1./2., 1./2., 0),
                    'Y1': (1./2., 0., 0.),
                    'L' : (-1./2., 1./2., 1./2.),
                    'M' : (0., 1./2., 1./2.),
                    'X' : (1-psi, 1-psi, 0.),
                    'X1': (psi-1, psi, 0.),
                    'X2': (psi, psi-1, 0.),
                    'Z' : (0., 0., 1./2.), }
            self.standard_path = "X1-Y-Gamma-N-X-Gamma-M-I-L-F-Y-Gamma-Z-F1-Z-I1"
        else:
            logger.error('Unsupported setting {} for {} lattice'.format(setting, self.__name__))
            sys.exit(2)



def get_kvec(comp_rc, recipr_cell):
    """
    *comp_rc* are the components of a vector expressed in terms of
    reciprocal cell vectors *recipr_cell*.
    Return the components of this vector in terms of reciprocal
    unit vectors.
    """
    kvec = np.dot(np.array(comp_rc), np.array(recipr_cell))
# the above is equivalent to: kvec = np.sum([beta[i]*Bvec[i] for i in range(3)], axis=0)
    return kvec

def get_recipr_cell (A,scale):
    """
    Given a set of set of three vectors *A*, assumed to be that defining
    the primitive cell, return the corresponding set of vectors that define
    the reciprocal cell, *B*, scaled by the input parameter *scale*, 
    which defaults to 2pi. The B-vectors are computed as follows:
    B0 = scale * (A1 x A2)/(A0 . A1 x A2)
    B1 = scale * (A2 x A0)/(A0 . A1 x A2)
    B2 = scale * (A0 x A1)/(A0 . A1 x A2)
    and are returnd as a list of 1D arrays.
    Recall that the triple-scalar product is invariant under circular shift,
    and equals the (signed) volume of the primitive cell.
    """
    volume = np.dot(A[0],np.cross(A[1],A[2]))
    B = []
    # use this to realise circular shift
    index = np.array(list(range(len(A))))
    for i in range(len(A)):
        (i1,i2) = np.roll(index,-(i+1))[0:2]
        B.append( scale * np.cross(A[i1],A[i2]) / volume )
    return B

def getSymPtLabel(kvec, lattice):
    """Return the symbol corresponding to a given k-vector, if named.

    This routine returns the symbol of a symmetry point that is 
    given in terms of reciprocal cell-vectors (*kvec* -- a 3-tuple)
    of the *lattice* object.
    """
    kLabel = None
    
    # the tollerance bellow (atol) defines how loosely we can define the
    # k-points in the dftb_in.hsd. 1.e-4 means we need 3 digits after the dot.
    for lbl, kpt in list(lattice.SymPts_k.items()):
        if np.allclose(kvec, kpt, atol=1.e-4):
            kLabel = lbl
            
    if not kLabel:
        logger.warning("Unable to match k-vector {0} to a symmetry point of {1} lattice".
                    format(kvec,lattice))
        logger.warning("\tReturning fractions of reciprocal unit vectors")
        kx = Fraction(kvec[0]).limit_denominator()
        ky = Fraction(kvec[1]).limit_denominator()
        kz = Fraction(kvec[2]).limit_denominator()
        kLabel = '({0}/{1}, {2}/{3}, {4}/{5})'.format(kx.numerator, kx.denominator,
                                                      ky.numerator, ky.denominator,
                                                      kz.numerator, kz.denominator)
    return kLabel

def getkLineLength(kpt0,kpt1,Bvec,scale):
    """
    Given two k-points in terms of unit vectors of the reciprocal lattice, Bvec,
    return the distance between the two points, in terms of reciprocal length.
    """
    k0 = np.dot(np.array(kpt0),np.array(Bvec))
    k1 = np.dot(np.array(kpt1),np.array(Bvec))
    klen = scale*np.linalg.norm(k0-k1)
    return klen


def repr_lattice(lat):
    """
    Report cell vectors, reciprocal vectors and standard path
    """
    s = ["\n"]
    s.append("------ {} lattice ------".format(lat.name))
    s.append("-------------------------")
    s.append("Lattice constants: {}".format(
        " ".join(["{:.4f}".format(c) for c in lat.constants])))
    s.append("Assumed Conventional vectors:")
    for cvec in lat.convv:
        s.append("{}".format(cvec))

    s.append("Corresponding Primitive vectors:")
    for pvec in lat.primv:
        s.append("{}".format(pvec))

    s.append("Corresponding Reciprocal vectors:")
    for rvec in lat.reciprv:
        s.append("{}".format(rvec))

    s.append("Symmetry points in terms of reciprocal lattice vectors:")
    for pt in list(lat.SymPts_k.items()):
        s.append("{:>6s}: {}".format(pt[0], pt[1]))

    s.append("Symmetry points in reciprocal lengths:")
    for pt in list(lat.SymPts.items()):
        s.append("{:>6s}: {}".format(pt[0], pt[1]))

    s.append("Symmetry points in 2pi/a units:")
    for pt in list(lat.SymPts.items()):
        s.append("{:>6s}: {}".format(pt[0],pt[1]/(2*pi/lat.constants[0])))

    s.append("Lengths along a standard path [2pi/a]:")
    s.append("{}".format(len_pathsegments(lat)))
    s2 = get_dftbp_klines(lat)
    return "\n".join(s) + "\n" + s2


def len_pathsegments(lattice, scale=None, path=None):
    """
    Report the lenth in terms of _scale_ (2pi/a if None) of the BZ _path_
    (default for the lattice chosen if None) of a given _lattice_ object
    """
    if path is None:
        path = lattice.path
    if scale is None:
        scale = (lattice.constants[0]/(2.*pi))
    s = [path, ]
    for subpath in path.split('|'):
        segments = subpath.split('-')
        for i, pt in enumerate(segments[:-1]):
            nextpt = segments[i+1]
            s.append("{:>6s}-{:<6s}: {:.3f}".format(pt, nextpt, 
                scale*np.linalg.norm(lattice.SymPts[pt]-lattice.SymPts[nextpt])))
    return '\n'.join(s)


def get_dftbp_klines(lattice, delta=None, path=None):
    """
    Print out the number of points along each segment of the BZ *path*
    (default for the lattice chosen if None) of a given *lattice* object
    """
    if path is None:
        path = lattice.path #standard_path
    if delta is None:
        delta = 0.01 # reciprocal units
    s = ["DFTB kLines stanza:", ]
    s.append("# {:s}".format(path))
    for subpath in path.split('|'):
        segments = subpath.split('-')
        pt = segments[0]
        npts = 1
        len = 0
        s.append("{:>8d} {:s}  # {:<6s}  {:<8.3f}".format(npts,
            "".join(["{:>10.5f}".format(comp) for comp in lattice.SymPts_k[pt]]), pt, len))
        for i, pt in enumerate(segments[:-1]):
            nextpt = segments[i+1]
            len = np.linalg.norm(lattice.SymPts[pt]-lattice.SymPts[nextpt])
            npts = int(len/delta)
            s.append("{:>8d} {:s}  # {:<6s}  {:<8.3f}".format(npts,
                "".join(["{:>10.5f}".format(comp) for comp in lattice.SymPts_k[nextpt]]), nextpt, len))
    return "\n".join(s)

# lattice types are as per curtarolo's article.
get_lattice = {
        'CUB': CUB,
        'FCC': FCC,
        'BCC': BCC,
        'TET': TET,
        'ORC': ORC,
        'HEX': HEX,
        'RHL': RHL,
        'MCL': MCL,
        'MCLC': MCLC,
        }

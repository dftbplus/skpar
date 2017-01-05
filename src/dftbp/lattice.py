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
from fractions import Fraction


class FCC(object):
    """
    This is Face Centered Cubic lattice (cF)
    """
    def __init__(self,a,scale=2*np.pi,primvec=None):
        """
        Initialise the lattice parameter(s) upon instance creation, and
        calculate the direct and reciprocal lattice vectors, as well
        as the components of the k-vectors defining the high-symmetry
        points known for the given lattice.
        """
        
        self.name = 'FCC'
        self.a = a
        self.scale = scale
        self.constants = [a,]

        if primvec is not None:
            self.prim = primvec
        else:
            self.prim =  [ np.array((0   , a/2., a/2.)),
                           np.array((a/2., 0   , a/2.)),
                           np.array((a/2., a/2., 0   )) ]

            self.conv =  [ np.array((a, 0, 0,)),
                           np.array((0, a, 0,)),
                           np.array((0, 0, a,)) ]


        # reciprocal lattice vectors
        self.recipr = get_recipr_cell(self.prim,self.scale)
        self.bvec = self.recipr

        # symmetry points in terms of reciprocal lattice vectors
        # and in terms of reciprocal length, e.g. 1/a
        self.SymPts_k = {} # in terms of reciprocal cell-vectors
        self.SymPts = {}   # in terms of reciprocal unit-vectors

        self.SymPts_k = \
            { 'Gamma': (0.,0.,0.),
                'K': (3./8.,3./8.,3./4.),
                'L': (1./2.,1./2.,1./2.),
                'U': (5./8.,1./4.,5./8.),
                'W': (1./2.,1./4.,3./4.),
                'X': (1./2.,0.,1./2.),  }

        for k,v in self.SymPts_k.items():
            self.SymPts[k] = self.get_kvec(v)

        self.standard_path = "Gamma-X-W-K-Gamma-L-U-W-L-K|U-X"

    def get_kvec (self, beta):
        return get_kvec(beta, self.recipr)


class HEX(object):
    """
    This is HEXAGONAL, hP lattice
    """
    def __init__(self,a,c,scale=2*np.pi,primvec=None):
        """
        Initialise the lattice parameter(s) upon instance creation, and
        calculate the direct and reciprocal lattice vectors, as well
        as the components of the k-vectors defining the high-symmetry
        points known for the given lattice.
        """
        
        self.name = 'HEX'
        self.a,self.c = a,c
        self.scale = scale
        self.constants = [a, c]

        if primvec is not None:
            self.prim = primvec
            self.conv = primvec
        else:
            self.prim =  [ np.array((a/2., -a*np.sqrt(3)/2., 0.)),
                           np.array((a/2., +a*np.sqrt(3)/2., 0.)),
                           np.array((0, 0, c)) ]
            self.conv = self.prim

        self.recipr = get_recipr_cell(self.prim,self.scale)

        self.SymPts_k = {} # in terms of k-vectors
        self.SymPts = {}   # in terms of reciprocal length

        self.SymPts_k =\
            { 'Gamma': (0,0,0),
                  'A': (0., 0., 1./2.),
                  'H': (1./3., 1./3., 1./2.),
                  'K': (1./3., 1./3., 0.),
                  'L': (1./2., 0., 1./2.),
                  'M': (1./2., 0., 0.), }

        for k,v in self.SymPts_k.items():
            self.SymPts[k] = self.get_kvec(v)

        self.standard_path = "Gamma-M-K-Gamma-A-L-H-A|L-M|K-H"

    def get_kvec (self, beta):
        return get_kvec(beta, self.recipr)


class CUB(object):
    """
    This is CUBic, cP lattice
    """
    def __init__(self,a,scale=2*np.pi,primvec=None):
        """
        Initialise the lattice parameter(s) upon instance creation, and
        calculate the direct and reciprocal lattice vectors, as well
        as the components of the k-vectors defining the high-symmetry
        points known for the given lattice.
        """
        
        self.name = 'CUB'
        self.a = a
        self.scale = scale
        self.constants = [a]

        if primvec is not None:
            self.prim = primvec
            self.conv = primvec
        else:
            self.prim =  [ np.array((a, 0., 0.)),
                           np.array((0., a, 0.)),
                           np.array((0., 0., a)) ]
            self.conv = self.prim

        self.recipr = get_recipr_cell(self.prim,self.scale)

        self.SymPts_k = {} # in terms of k-vectors
        self.SymPts = {}   # in terms of reciprocal length 1/a

        self.SymPts_k =\
            { 'Gamma': (0,0,0),
                  'M': (1./2., 1./2., 0.),
                  'R': (1./2., 1./2., 1./2.),
                  'X': (0., 1./2., 0.), }

        for k,v in self.SymPts_k.items():
            self.SymPts[k] = self.get_kvec(v)

        self.standard_path = "Gamma-X-M-Gamma-R-X|M-R"

    def get_kvec (self, beta):
        return get_kvec(beta, self.recipr)



class TET(object):
    """
    This is TETRAGONAL, tP lattice
    """
    def __init__(self,a,c,scale=2*np.pi,primvec=None):
        """
        Initialise the lattice parameter(s) upon instance creation, and
        calculate the direct and reciprocal lattice vectors, as well
        as the components of the k-vectors defining the high-symmetry
        points known for the given lattice.
        """
        
        self.name = 'TET'
        self.a,self.c = a,c
        self.scale = scale
        self.constants = [a, c]

        if primvec is not None:
            self.prim = primvec
            self.conv = primvec
        else:
            self.prim =  [ np.array((a, 0., 0.)),
                           np.array((0., a, 0.)),
                           np.array((0, 0, c)) ]
            self.conv = self.prim

        self.recipr = get_recipr_cell(self.prim,self.scale)

        self.SymPts_k = {} # in terms of reciprocal lattice vectors
        self.SymPts = {}   # in terms of reciprocal unit vectors

        self.SymPts_k =\
            { 'Gamma': (0,0,0),
                  'A': (1./2., 1./2., 1./2.),
                  'M': (1./2., 1./2., 0.),
                  'R': (0., 1./2., 1./2.),
                  'X': (0., 1./2., 0.),
                  'Z': (0., 0., 1./2.), }

        for k,v in self.SymPts_k.items():
            self.SymPts[k] = self.get_kvec(v)

        self.standard_path = "Gamma-X-M-Gamma-Z-R-A-Z|X-R|M-A"

    def get_kvec (self, beta):
        return get_kvec(beta, self.recipr)



class ORC(object):
    """
    This is ORTHOROMBIC, oP lattice
    """
    def __init__(self, a, b, c, scale=2*np.pi,primvec=None):
        """
        Initialise the lattice parameter(s) upon instance creation, and
        calculate the direct and reciprocal lattice vectors, as well
        as the components of the k-vectors defining the high-symmetry
        points known for the given lattice.
        """
        
        self.name = 'ORC'
        self.a, self.b, self.c = a, b, c
        self.scale = scale
        self.constants = [a, b, c]

        if primvec is not None:
            self.prim = primvec
            self.conv = primvec
        else:
            self.prim =  [ np.array((a, 0., 0.)),
                           np.array((0., b, 0.)),
                           np.array((0., 0., c)) ]
            self.conv = self.prim

        self.recipr = get_recipr_cell(self.prim,self.scale)

        self.SymPts_k = {} # in terms of k-vectors
        self.SymPts = {}   # in terms of reciprocal length vectors

        self.SymPts_k =\
            { 'Gamma': (0,0,0),
                  'R': (1./2., 1./2., 1./2.),
                  'S': (1./2., 1./2., 0.),
                  'T': (0., 1./2., 1./2.),
                  'U': (1./2., 0., 1./2.),
                  'X': (1./2., 0.,  0.),
                  'Y': (0., 1./2., 0.),
                  'Z': (0., 0., 1./2.), }

        for k,v in self.SymPts_k.items():
            self.SymPts[k] = self.get_kvec(v)

        self.standard_path = "Gamma-X-S-Y-Gamma-Z-U-R-T-Z|Y-T|U-X|S-R"

    def get_kvec (self, beta):
        return get_kvec(beta, self.recipr)



class RHL(object):
    """
    This is Rhombohedral RHL, hR lattice
    Primitive lattice defined via:
    a = b = c, and alpha = beta = gamma <> 90 degrees
    Two variations exists: RHL1 (alpha < 90) and RHL2 (alpha > 90)
    """
    def __init__(self, a, alpha, scale=2*np.pi, primvec=None):
        """
        Initialise the lattice parameter(s) upon instance creation, and
        calculate the direct and reciprocal lattice vectors, as well
        as the components of the k-vectors defining the high-symmetry
        points known for the given lattice.
        Note that RHL has two variants:
        RHL1, where alpha < 90 degrees
        RHL2, where alpha > 90 degrees
        The instance is initialised appropriately.
        Symmetry points (SymPts_k) and standard_path are from:
        W. Setyawan, S. Curtarolo / Computational Materials Science 49 (2010) 299-312
        """
        
        assert not abs(alpha - 90.0) < 1.e-5
        self.a     = a
        self.alpha_rad = np.radians(alpha)
        self.scale = scale
        self.constants = [a, alpha]

        if primvec is not None:
            self.prim = primvec
            self.conv = primvec
        else:
            c1 = np.cos(self.alpha_rad)
            c2 = np.cos(self.alpha_rad/2.)
            s2 = np.sin(self.alpha_rad/2.)
            self.prim =  [ self.a*np.array([c2, -s2, 0.]),
                           self.a*np.array([c2, +s2, 0.]),
                           self.a*np.array([c1/c2, 0., np.sqrt(1-(c1/c2)**2)]) ]
            self.conv = self.prim

        self.recipr = get_recipr_cell(self.prim,self.scale)

        self.SymPts_k = {} # in terms of k-vectors
        self.SymPts = {}   # in terms of reciprocal length

        # The fractions defining the symmetry points in terms of reciprocal vectors
        # are dependent on the angle alpha of the RHL lattice 
        # So we cannot use the dictionary SymPts_k to get them.

        if self.alpha_rad < np.pi/2.:
            self.name = 'RHL1'
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

        for k,v in self.SymPts_k.items():
            self.SymPts[k] = np.dot(np.array(v), np.array(self.recipr))


    def get_kvec (self, beta):
        return get_kvec(beta, self.recipr)



class MCL(object):
    """
    This is simple Monoclinic MCL_* (mP) lattice, set via
    a, b <= c, and alpha < 90 degrees, beta = gamma = 90 degrees as in
    W. Setyawan, S. Curtarolo / Computational Materials Science 49 (2010) 299-312.
    Setting ITC flat to True should work for the standard setting
    of ITC-A, but is not currently implemented.
    Note that conventional and primitive cells are the same.
    """
    def __init__(self, a, b, c, angle, ITC=False, scale=2*np.pi, primvec=None):
        """
        Initialise the lattice parameter(s) upon instance creation, and
        calculate the direct and reciprocal lattice vectors, as well
        as the components of the k-vectors defining the high-symmetry
        points known for the given lattice.
        The default setting (ITC=False) assumes that alpha < 90 as in 
        W. Setyawan, S. Curtarolo / Computational Materials Science 49 (2010) 299-312
        TODO: If _ITC_ is True, the ITC convention is followed for 
              direct and reciprocal lattice.
        """
        
        # only Curtarolo's setting is supported for now
        assert (ITC == False) and (a<=c) and (b<=c) and (angle < 90) 

        self.name = 'MCL'

        self.a     = a
        self.b     = b
        self.c     = c
        self.angle_rad = np.radians(angle)
        self.scale = scale
        self.constants = [a, b, c, angle]

        if primvec is not None:
            self.prim = primvec
        else:
            if ITC:
                log.critical("Unsupported MCL(mP) setting")
                sys.exit(1)
            else:
                # conventional cell
                a1c = self.a * np.array([1, 0, 0])
                a2c = self.b * np.array([0, 1, 0])
                a3c = self.c * np.array([0, np.cos(self.angle_rad), np.sin(self.angle_rad)])
                self.conv = np.array([a1c, a2c, a3c])
                # primitive cell
                self.prim = self.conv

        self.recipr = get_recipr_cell(self.prim,self.scale)

        self.SymPts_k = {} # in terms of reciprocal cell-vectors
        self.SymPts = {}   # in terms of reciprocal unit-vectors

        # The fractions defining the symmetry points in terms of reciprocal 
        # cell-vectors are dependent on the angle alpha of the MCL lattice 
        # So we cannot use the dictionary SymPts_k to get them.

        if not ITC and self.angle_rad < np.pi/2.:
            eta = ( 1 - self.b * np.cos(self.angle_rad) / self.c ) / ( 2 * (np.sin(self.angle_rad))**2 )
            nu  = 1./2. - eta * self.c * np.cos(self.angle_rad) / self.b 
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
            log.critical("Not supported MCL setting with ITC or w/ angle > 90degrees")
            sys.exit(1)

        for k, v in self.SymPts_k.items():
            self.SymPts[k] = self.get_kvec(v) #np.dot(np.array(v), np.array(self.recipr))


    def get_kvec (self, comp_rc):
        return get_kvec(comp_rc, self.recipr)


class MCLC(object):
    """
    This is base-centered Monoclinic MCLC_* mS,  lattice
    Primitive lattice defined via:
    a <> b <> c, and alpha <> 90 degrees, beta = gamma = 90 degrees
    """
    def __init__(self, a, b, c, angle, ITC=True, scale=2*np.pi, primvec=None):
        """
        Initialise the lattice parameter(s) upon instance creation, and
        calculate the direct and reciprocal lattice vectors, as well
        as the components of the k-vectors defining the high-symmetry
        points known for the given lattice.
        Note that MCLC has several variants, depending on abc ordering and
        face(base) centering or not:
        Additionally, ITC stipulates alpha > 90 degrees, while in 
        W. Setyawan, S. Curtarolo / Computational Materials Science 49 (2010) 299-312
        alpha < 90 is used.
        If _ITC_ is True (default), the ITC convention is followed for 
        direct and reciprocal lattice.
        If _ITC_ is False, then the convention in 
        W. Setyawan, S. Curtarolo / Computational Materials Science 49 (2010) 299-312
        is followed.
        """
        
        # only ITC supported for now, and only for MCLC1
        assert (ITC == True) and (a >= b) and (a>=c) and (angle > 90) 

        self.a     = a
        self.b     = b
        self.c     = c
        self.angle_rad = np.radians(angle)
        self.scale = scale
        self.constants = [a, b, c, angle]

        if primvec is not None:
            self.prim = primvec
        else:
            if ITC:
                # conventional cell
                a1c = self.a * np.array([1, 0, 0])
                a2c = self.b * np.array([0, 1, 0])
                a3c = self.c * np.array([np.cos(self.angle_rad), 0, np.sin(self.angle_rad)])
                self.conv = np.array([a1c, a2c, a3c])
                # primitive cell
                a1p = (+a1c + a2c) / 2.
                a2p = (-a1c + a2c) / 2.
                a3p = a3c
                self.prim = np.array([a1p, a2p, a3p])
            else:
                log.critical("Unsupported MCLC setting")
                sys.exit(1)

        self.recipr = get_recipr_cell(self.prim,self.scale)

        self.SymPts_k = {} # in terms of reciprocal cell-vectors
        self.SymPts = {}   # in terms of reciprocal unit-vectors

        # The fractions defining the symmetry points in terms of reciprocal 
        # cell-vectors are dependent on the angle alpha of the MCLC lattice 
        # So we cannot use the dictionary SymPts_k to get them.

        if ITC and self.angle_rad > np.pi/2.:
            self.name = 'MCLC1.ITC'
            psi = 3./4. - (self.b / (2 * self.a * np.sin(self.angle_rad)))**2
            phi = psi - ( 3./4. - psi ) * (self.a / self.c) * np.cos(self.angle_rad)
            ksi = ( 2 + (self.a/self.c) *  np.cos(self.angle_rad) ) / ( 2 * np.sin(self.angle_rad) )**2
            eta = 1./2. - 2 * ksi * (self.c/self.a) *  np.cos(self.angle_rad)
            print (psi, phi, ksi, eta)
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
            log.critical("Not supported (MCLC) non ITC or w/ angle < 90degrees")
            sys.exit(1)

        for k, v in self.SymPts_k.items():
            self.SymPts[k] = self.get_kvec(v) #np.dot(np.array(v), np.array(self.recipr))


    def get_kvec (self, comp_rc):
        return get_kvec(comp_rc, self.recipr)



def get_kvec(comp_rc, recipr_cell):
    """
    *comp_rc* are the components of a vector expressed in terms of
    reciprocal call vectors *recipr_cell*.
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

def getSymPtLabel(kvec, lattice, log):
    """ 
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
        log.warning("Unable to match k-vector {0} to a symmetry point of {1} lattice".
                    format(kvec,lattice))
        log.warning("\tReturning fractions of reciprocal unit vectors")
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
    print(("\n\n *** {0} lattice ***".format(lat.name)))
    print("\nLattice constants: ", lat.constants)
    print("\nAssumed Conventional vectors:")
    for cvec in lat.conv:
        print(cvec)

    print("\nCorresponding Primitive vectors:")
    for pvec in lat.prim:
        print(pvec)

    print("\nCorresponding Reciprocal vectors:")
    for rvec in lat.recipr:
        print(rvec)

    print("\nSymmetry points in terms of reciprocal lattice vectors:")
    for pt in list(lat.SymPts_k.items()):
        print(pt)

    print("\nSymmetry points in reciprocal lengths:")
    for pt in list(lat.SymPts.items()):
        print(pt)

    print("\nSymmetry points in 2pi/a units:")
    for pt in list(lat.SymPts.items()):
        print(pt[0],pt[1]/(2*np.pi/lat.a))

    print("\nLengths along a standard path [2pi/a]:")
    len_pathsegments(lat)


def len_pathsegments(lattice, scale=None, path=None):
    """
    Report the lenth in terms of _scale_ (2pi/a if None) of the BZ _path_
    (default for the lattice chosen if None) of a given _lattice_ object
    """
    if path is None:
        path = lattice.standard_path
    if scale is None:
        scale = (lattice.a/(2.*np.pi))
    print(path)
    for subpath in path.split('|'):
        segments = subpath.split('-')
        for i, pt in enumerate(segments[:-1]):
            nextpt = segments[i+1]
            print("{:>6s}-{:<6s}: {:.3f}".format(pt, nextpt, 
                scale*np.linalg.norm(lattice.SymPts[pt]-lattice.SymPts[nextpt])))


def get_dftbp_klines(lattice, delta=None, path=None):
    """
    Print out the number of points along each segment of the BZ *path*
    (default for the lattice chosen if None) of a given *lattice* object
    """
    if path is None:
        path = lattice.standard_path
    if delta is None:
        delta = 0.01 # reciprocal units
    print("# {:s}".format(path))
    for subpath in path.split('|'):
        segments = subpath.split('-')
        pt = segments[0]
        npts = 1
        len = 0
        print("{:>8d} {:s}  # {:<6s}  {:<8.3f}".format(npts,
            "".join(["{:>10.5f}".format(comp) for comp in lattice.SymPts_k[pt]]), pt, len))
        for i, pt in enumerate(segments[:-1]):
            nextpt = segments[i+1]
            len = np.linalg.norm(lattice.SymPts[pt]-lattice.SymPts[nextpt])
            npts = int(len/delta)
            print("{:>8d} {:s}  # {:<6s}  {:<8.3f}".format(npts,
                "".join(["{:>10.5f}".format(comp) for comp in lattice.SymPts_k[nextpt]]), nextpt, len))


if __name__ == "__main__":

    a = 5.431
    lat = CUB(a)
    repr_lattice(lat)
    get_dftbp_klines(lat)

    a, c = 4.916, 5.4054
    lat = HEX(a,c)
    repr_lattice(lat)
    get_dftbp_klines(lat)

#    a, c = 5.431, 59.50225 
#    test_TET(a,c)


    a, b, c = 8.77, 9.06, 12.80
    lat = ORC(a, b, c)
    repr_lattice(lat)
    get_dftbp_klines(lat)

    a, alpha = 5.32208613808, 55.8216166097
    lat = RHL(a, alpha)
    repr_lattice(lat)
    get_dftbp_klines(lat)

    # GaO2 
    a, b, c, beta = 12.23, 3.04, 5.8, 103.70
    lat = MCLC(a, b, c, angle=beta)
    repr_lattice(lat)
    get_dftbp_klines(lat)

    # HfO2-m (mP)
    a, b, c, alpha = 5.17500, 5.17500, 5.29100, 80.78
    lat = MCL(a, b, c, angle=alpha)
    repr_lattice(lat)
    get_dftbp_klines(lat)

    # HfO2-t (mP)
    a, c = 5.15, 5.29
    lat = TET(a, c)
    repr_lattice(lat)
    get_dftbp_klines(lat)

    # HfO2-c (cF)
    a = 5.08
    lat = FCC(a, c)
    repr_lattice(lat)
    get_dftbp_klines(lat)
    
    getSymPtLabel([0.5, 0.25, 0.75], FCC(5.08), log=None)

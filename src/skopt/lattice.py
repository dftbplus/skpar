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

# The following dictionary contains the symmetry points, for a given lattice
# in terms of the reciprocal vectors.
# The first entry in the list for a symmetry point comes from the above mentioned publication.
# Eventually, we could expand the list for each SymPt, e.g. (0,1/2,1/2) is also X, etc; Another
# option being generate the permutations of the components on the fly, in order to expand the list...
SymPts_k = { 'FCC': { 'Gamma': [(0.,0.,0.),],
                    'K': [(3./8.,3./8.,3./4.), (3./8., 3./4., 3./8.),],
                    'L': [(1./2.,1./2.,1./2.),],
                    'U': [(5./8.,1./4.,5./8.), (1./4., 5./8., 5./8.), ],
                    'W': [(1./2.,1./4.,3./4.),],
                    'X': [(1./2.,0.,1./2.), (0., 1./2., 1./2.)],  } ,

             'HEX': { 'Gamma': [(0,0,0),],
                      'A': [(0., 0., 1./2.),],
                      'H': [(1./3., 1./3., 1./2.),],
                      'K': [(1./3., 1./3., 0.),],
                      'L': [(1./2., 0., 1./2.),],
                      'M': [(1./2., 0., 0.),], },

             'CUB': { 'Gamma': [(0,0,0),],
                      'M': [(1./2., 1./2., 0.),],
                      'R': [(1./2., 1./2., 1./2.),],
                      'X': [(0., 1./2., 0.),], },

             'TET': { 'Gamma': [(0,0,0),],
                      'A': [(1./2., 1./2., 1./2.),],
                      'M': [(1./2., 1./2., 0.),],
                      'R': [(0., 1./2., 1./2.),],
                      'X': [(0., 1./2., 0.),],
                      'Z': [(0., 0., 1./2.),], },
            }
        

class FCC(object):
    """
    This is Face Centered Cubic lattice
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
        self.recipr = get_recipr_unitvectors(self.prim,self.scale)
        self.bvec = self.recipr

        # symmetry points in terms of reciprocal lattice vectors
        # and in terms of reciprocal length, e.g. 1/a
        self.SymPts_k = {} # in terms of k-space unit vectors
        self.SymPts = {}   # in terms of reciprocal length

        for k,v in list(SymPts_k[self.name].items()):
            self.SymPts_k[k] = np.array(v[0])
            self.SymPts[k] = np.dot(np.array(v[0]),np.array(self.recipr))

        self.SymPts_b = self.SymPts_k
        self.SymPts_inva = self.SymPts


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

        if primvec is not None:
            self.prim = primvec
        else:
            self.prim =  [ np.array((a/2., -a*np.sqrt(3)/2., 0.)),
                           np.array((a/2., +a*np.sqrt(3)/2., 0.)),
                           np.array((0, 0, c)) ]

        self.recipr = get_recipr_unitvectors(self.prim,self.scale)

        self.SymPts_k = {} # in terms of k-vectors
        self.SymPts = {}   # in terms of reciprocal length

        for k,v in list(SymPts_k[self.name].items()):
            self.SymPts_k[k] = np.array(v[0])
            self.SymPts[k] = np.dot(np.array(v[0]),np.array(self.recipr))


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

        if primvec is not None:
            self.prim = primvec
        else:
            self.prim =  [ np.array((a, 0., 0.)),
                           np.array((0., a, 0.)),
                           np.array((0., 0., a)) ]

        self.recipr = get_recipr_unitvectors(self.prim,self.scale)

        self.SymPts_k = {} # in terms of k-vectors
        self.SymPts = {}   # in terms of reciprocal length 1/a

        for k,v in list(SymPts_k[self.name].items()):
            self.SymPts_k[k] = np.array(v[0])
            self.SymPts[k] = np.dot(np.array(v[0]),np.array(self.recipr))


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

        if primvec is not None:
            self.prim = primvec
        else:
            self.prim =  [ np.array((a, 0., 0.)),
                           np.array((0., a, 0.)),
                           np.array((0, 0, c)) ]

        self.recipr = get_recipr_unitvectors(self.prim,self.scale)

        self.SymPts_k = {} # in terms of k-vectors
        self.SymPts = {}   # in terms of reciprocal length vectors

        for k,v in list(SymPts_k[self.name].items()):
            self.SymPts_k[k] = np.array(v[0])
            self.SymPts[k] = np.dot(np.array(v[0]),np.array(self.recipr))

    def get_kvec (self, beta):
        return get_kvec(beta, self.recipr)




def get_kvec(beta, Bvec):
    """
    Return a vector of reciprocal space with *beta* being the components
    and *Bvec* being the unit vectors (list of three np.arrays). 
    """
    kvec = np.dot(np.array(beta),np.array(Bvec))
# the above is equivalent to: kvec = np.sum([beta[i]*Bvec[i] for i in range(3)], axis=0)
    return kvec

def get_recipr_unitvectors (A,scale):
    """
    Given a set of set of three vectors *A*, assumed to be that of the 
    primitive lattice, return the corresponding set of reciprocal lattice
    vectors *B*, scaled by the input parameter *scale*, which defaults to 2pi.
    The B-vectors are computed as follows:
    B0 = scale * (A1 x A2)/(A1 . A2 x A3)
    B1 = scale * (A2 x A0)/(A1 . A2 x A3)
    B2 = scale * (A0 x A1)/(A1 . A2 x A3)
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
    This routine returns the label of a k-space symmetry point, given a tupple, representing the corresponding
    k-vector.
    __NOTA BENE:__ The symmetry points are defined as a dictionary for a given lattice type.
    This dictionary, for each lattice type, is constructed from the tables in 
    W.Setyawan and S.Curtarolo, _Comp. Mat. Sci._ __49__ (2010) pp.299-312
    see the lattice.py module for the implementation details
    """
    kLabel = None
    
    try:
        for l,klist in list(SymPts_k[lattice].items()):
            if tuple(kvec)  in klist:
                kLabel = l
    except KeyError:
        log.critical("ERROR : No symmetry point definition for the {lattice} lattice are defined.".format(lattice))
        log.critical("        Please, extend the SymPts dictionary in lattice.py module before continuing.")
        sys.exit(1)
            
    if not kLabel:
        log.warning("Unable to match k-vector {0} to a symmetry point of {1} lattice".
                    format(kvec,lattice))
        log.warning("\tReturnning fractions of reciprocal unit vectors")
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


def test_FCC(a,scale=None):
    """
    test for FCC lattice, printing also the lengths of the 
    k-lines between points of symmetry, in units of 2pi/a
    """
    if scale is not None:
        test = FCC(a,scale)
    else:
        test = FCC(a)   
    print(("\n\n *** {0} lattice ***".format(test.name)))
    print("\nPrimitive vectors:")
    for pvec in test.prim:
        print(pvec)

    print("\nReciprocal vectors:")
    for rvec in test.recipr:
        print(rvec)

    print("\nSymmetry points in terms of k vectors:")
    for pt in list(test.SymPts_k.items()):
        print(pt)

    print("\nSymmetry points in reciprocal lengths:")
    for pt in list(test.SymPts.items()):
        print(pt)

    print("\nLength of lines L-Gamma-X-U,K-Gamma, [2pi/a]")
    scale = (a/(2.*np.pi))
    print(scale*np.linalg.norm(test.SymPts['L']))
    print(scale*np.linalg.norm(test.SymPts['X']))
    print(scale*np.linalg.norm(test.SymPts['X']-test.SymPts['U']))
    print(scale*np.linalg.norm(test.SymPts['K']))


def test_HEX(a,c,scale=None):
    """
    test for HEX lattice, printing also the lengths of the 
    k-lines between points of symmetry, in units of 2pi/a
    """
    if scale is not None:
        test = HEX(a,c,scale)
    else:
        test = HEX(a,c)   
    print(("\n\n *** {0} lattice ***".format(test.name)))
    print("\nLattice constants: ", a, c)
    print("\nPrimitive vectors:")
    for pvec in test.prim:
        print(pvec)

    print("\nReciprocal vectors:")
    for rvec in test.recipr:
        print(rvec)

    print("\nSymmetry points in terms of k vectors:")
    for pt in list(test.SymPts_k.items()):
        print(pt)

    print("\nSymmetry points in reciprocal lengths:")
    for pt in list(test.SymPts.items()):
        print(pt)

    print("\nSymmetry points in 2pi/a units:")
    for pt in list(test.SymPts.items()):
        print(pt[0],pt[1]/(2*np.pi/a))

    print("\nLength of lines A-L-M-Gamma-A-H-K-Gamma, [2pi/a]")
    scale = (a/(2.*np.pi))
    print(scale*np.linalg.norm(test.SymPts['L']-test.SymPts['A']))
    print(scale*np.linalg.norm(test.SymPts['M']-test.SymPts['L']))
    print(scale*np.linalg.norm(test.SymPts['M']))
    print(scale*np.linalg.norm(test.SymPts['A']))
    print(scale*np.linalg.norm(test.SymPts['H']-test.SymPts['A']))
    print(scale*np.linalg.norm(test.SymPts['K']-test.SymPts['H']))
    print(scale*np.linalg.norm(test.SymPts['K']))

def test_TET(a,c,scale=None):
    """
    test for TET lattice, printing also the lengths of the 
    k-lines between points of symmetry, in units of 2pi/a
    """
    if scale is not None:
        test = TET(a,c,scale)
    else:
        test = TET(a,c)   
    print(("\n\n *** {0} lattice ***".format(test.name)))
    print(("\nLattice constants: ", a, c))
    print("\nPrimitive vectors:")
    for pvec in test.prim:
        print(pvec)

    print("\nReciprocal vectors:")
    for rvec in test.recipr:
        print(rvec)

    print("\nSymmetry points in terms of B-vectors, and corresp, kvectors:")
    for pt in list(test.SymPts_k.items()):
        print (pt, test.get_kvec(pt[1]))

    print("\nSymmetry points in reciprocal lengths:")
    for pt in list(test.SymPts.items()):
        print(pt)

    print("\nSymmetry points in 2pi/a units:")
    for pt in list(test.SymPts.items()):
        print((pt[0],pt[1]/(2*np.pi/a)))

    print("\nLength of lines along a standard path,")
    print("Gamma--X--M--Gamma--Z--R--A--Z|X--R|M--A, in [2pi/a]:")
    scale = (a/(2.*np.pi))
    print((scale*np.linalg.norm(test.SymPts['X'])))
    print((scale*np.linalg.norm(test.SymPts['M']-test.SymPts['X'])))
    print((scale*np.linalg.norm(test.SymPts['M'])))
    print((scale*np.linalg.norm(test.SymPts['Z'])))
    print((scale*np.linalg.norm(test.SymPts['Z']-test.SymPts['R'])))
    print((scale*np.linalg.norm(test.SymPts['R']-test.SymPts['A'])))
    print((scale*np.linalg.norm(test.SymPts['A']-test.SymPts['Z'])))
    print((scale*np.linalg.norm(test.SymPts['X']-test.SymPts['R'])))
    print((scale*np.linalg.norm(test.SymPts['M']-test.SymPts['A'])))

if __name__ == "__main__":

    a = 5.431
    test_FCC(a)

    a, c = 4.916, 5.4054
    test_HEX(a,c)

    a, c = 5.431, 59.50225 
    test_TET(a,c)



"""
Stuff realated to the Band Structure of Ge. Includes reference data, routine for plotting. 
Also for analysing k-points of symmetry -- what are the calculated energies.

Assumptions for the reference data:
Reference data comes from publications, where E-k pairs are quoted typically using crystallographic 
notation for the k-points, rather than fractions of $2\pi$ over a lattice constant. 
It convenes therefore, to store them as a dictionary. Some translation is necessary when evaluation 
and visualisation is done, since each dictionary key (k-point name) must become a k-point index or 
a value in $[m^{-1}]$, but this translation is specific to the tool used to calculate the band-structure; 
hence the translation will happen further down in the code.  
Additional reference data may include effective masses or location of band extrema, and explicit band-gaps 
(e.g. $E_{c,min}-E_{v,max}$).
"""
import logging
# Reference E-k points for Ge, as cited in 
# Boykin et al Phys Rev B 69, 115201 (2004); 
# Crystallographic (k-) points vs. energy in [eV]
refEk = {'G25pr_v': 0.77,   # Top of the valence band, 2-fold degeneracy (lh,hh)
         'Gso_v': -0.3,     # VB Split-off at k=0, due to SOC
#         'G1_v': -12.5,     # Not known from above ref
         'G15_c': 1.575,    # 
         'G2pr_c': 3.5,     # 
#         'X1_c': 1.35,      # 
         'X4_v': -2.8,      # 
#         'X1_v': -8.01,     # 
         'L3_c': 4.5,       # 
         'L1_c': 1.434,       # 
         'L3pr_v': -0.5,    # 
#         'L1_v': -7.0,      # 
#         'L2pr_v': -9.3,    # 
#         'K1_v2': -8.15,    # 
#         'K3_v': -7.16,     # 
         'K1_v1': -3.95,    # 
         'K2_v': -2.2,     # 
         'K3_c1': 2.2,      # 
         'K3_c2': 5.2,     # 
         }

refEgap = {'Egap': 1.434,}   # [eV], fundamental band-gap
           
refEk_st = {'Dmin_c': 1.675,     # CB min, 85% along Gamma-X (Delta direction)
            'Dmin_c_pos': 0.85, # relative position of the Delta min of CB, along Gamma-X
           }

refmeff = {'me_Xl': 0.900, 'me_Xt': 0.200, # CB meff for the Delta-valley
           'm_lh_001': -0.0457, 
           'm_lh_110': -0.0417,
           'm_lh_111': -0.0406,
           'm_hh_001': -0.211,
           'm_hh_110': -0.383,
           'm_hh_111': -0.502,
           'm_so_001': -0.095,
           'm_so_111': -0.095,
           'm_so_110': -0.095,
          }

ref_Ge = dict(list(refEk.items()) + list(refEgap.items()) + list(refEk_st.items()) + list(refmeff.items()))


def analyseEk_Ge(data, log=logging.getLogger(__name__)):
    """
    Analyses the calculated 'bands' values in the data dictionary, 
    and return a dictionary in the same format as the reference data for Ge,
    but populated with the information obtained from the calculation.
    """
    import numpy as np

    kLinesDict = data['kLinesDict']
    bands      = data['bands']
    nVBtop     = data['nVBtop']
    SOfactor   = data['SOfactor']

    calcEk = dict()

    calcEk['G25pr_v'] = bands[kLinesDict['Gamma'][0],nVBtop]
    calcEk['Gso_v'] = bands[kLinesDict['Gamma'][0],nVBtop-2*SOfactor]
    calcEk['G1_v'] = bands[kLinesDict['Gamma'][0],nVBtop-nVBtop]
    calcEk['G15_c'] = bands[kLinesDict['Gamma'][0],nVBtop+1*SOfactor-1]
    calcEk['G2pr_c'] = bands[kLinesDict['Gamma'][0],nVBtop+3*SOfactor-1]

    calcEk['X1_c'] = bands[kLinesDict['X'][0],nVBtop+1*SOfactor-1]
    calcEk['X4_v'] = bands[kLinesDict['X'][0],nVBtop]
    calcEk['X1_v'] = bands[kLinesDict['X'][0],nVBtop-nVBtop]

    calcEk['L3_c'] = bands[kLinesDict['L'][0],nVBtop+3*SOfactor-1]
    calcEk['L1_c'] = bands[kLinesDict['L'][0],nVBtop+1*SOfactor-1]
    calcEk['L3pr_v'] = bands[kLinesDict['L'][0],nVBtop]
    calcEk['L1_v'] = bands[kLinesDict['L'][0],nVBtop-2*SOfactor]
    calcEk['L2pr_v'] = bands[kLinesDict['L'][0],nVBtop-nVBtop]

    calcEk['K1_v2'] = bands[kLinesDict['K'][0],nVBtop-nVBtop]
    calcEk['K3_v'] = bands[kLinesDict['K'][0],nVBtop-2*SOfactor]
    calcEk['K1_v1'] = bands[kLinesDict['K'][0],nVBtop-1*SOfactor]
    calcEk['K2_v'] = bands[kLinesDict['K'][0],nVBtop]
    calcEk['K3_c1'] = bands[kLinesDict['K'][0],nVBtop+1*SOfactor-1]
    calcEk['K3_c2'] = bands[kLinesDict['K'][0],nVBtop+2*SOfactor-1]

    return calcEk


def analyseEkst_Ge(data, log=logging.getLogger(__name__)):
    """
    Analyse the 'bands' values in the data dictionary and return the properties of
    the stationary points in a dictionary, following the format of the refGe data.
    """
    import numpy as np

    kLinesDict = data['kLinesDict']
    bands      = data['bands']
    nVBtop     = data['nVBtop']
    SOfactor   = data['SOfactor']

    calcEk_st  = dict()

    # Note that it may be more accurate to obtain the band minima/maxima by parabolic fitting
    # This would require a separate routine, which should return both the value of the extremum
    # and its position in terms of 2pi/a, since the fitted extremum is unlikely to 
    # coincide with a sampling point, and indexing will be meaningless.
    # Alternatively, a noninteger "index" may be returned.
    calcEk_st['Dmin_c'] = np.min(bands[kLinesDict['Gamma'][0]:kLinesDict['X'][0]+1,nVBtop+1])
    nkDmin_c = np.where(bands[kLinesDict['Gamma'][0]:kLinesDict['X'][0]+1,nVBtop+1]==calcEk_st['Dmin_c'])[0][0]
    calcEk_st['Dmin_c_pos'] = ((1.*nkDmin_c)/(kLinesDict['X'][0]-kLinesDict['Gamma'][0]))
    calcEk_st['Smin_v'] = np.min(bands[kLinesDict['K'][0]:kLinesDict['Gamma'][1]+1,nVBtop-1])

    return calcEk_st
    
def analyseMeff_Ge(data, log = logging.getLogger(__name__)):
    """
    """
    # This routine must be split, to permit the evaluation of all masses,
    # which require different 'bands' input, obtained from calculations with different klines.
    # For now we can only calculate masses along Delta, Sigma and Lambda.
    # This is sufficient for the valence bands, but not for the conduction band masses.
    import numpy as np

    kLinesDict = data['kLinesDict']
    bands      = data['bands']
    nVBtop     = data['nVBtop']
    SOfactor   = data['SOfactor']

    calcmeff = dict()

#    from skopt.lattice import SymPts_k
# The following are in terms of the reciprocal lattice vectors b1,b2,b3
# But we need to translate them to 2*pi/a*_the_unit_vectors_ (i,j,k)
#    G = SymPts['FCC']['Gamma'][0]
#    X = SymPts['FCC']['X'][0]
#    L = SymPts['FCC']['L'][0]
#    K = SymPts['FCC']['K'][0]
# The results is (taking into account the definition of primitive lattice vectors
# and the definition of reciprocal lattice vectors, for FCC:
# (see Cardona, PhysRev 1966, and my own derivation, which confirms the values)
    G = (0,0,0)
    X = (0,1,0)
    L = (1./2.,1./2.,1./2.) 
    K = (3./4.,3./4.,0) 
    W = (1./2.,1.,0)

    # Masses along Delta (Gamma -- X)
    kline = range(kLinesDict['Gamma'][0],kLinesDict['X'][0]+1)
    m = ('me_Xl',min)
    band = bands[min(kline):max(kline)+1,nVBtop + 1] # note the +1 for the lowest CB
    calcmeff[m[0]] = calc_masseff(band,kline,m[1],[G,X],log,m[0],0.04)

    mass = [('m_hh_001',max),('m_lh_001',max),('m_so_001',max)]
    Erange = [0.026, 0.045, 0.01]
    for i,m in enumerate(mass):
        band = bands[min(kline):max(kline)+1,nVBtop - 2*i]  
        calcmeff[m[0]] = calc_masseff(band,kline,m[1],[G,X],log,m[0],Erange[i])

    # Masses along Lambda [111] (Gamma -- L)
    kline = range(kLinesDict['L'][0],kLinesDict['Gamma'][0]+1)
    mass = [('m_hh_111',max),('m_lh_111',max),('m_so_111',max)]
    Erange = [0.04, 0.025, 0.008]
    for i,m in enumerate(mass):
        band = bands[min(kline):max(kline)+1,nVBtop - 2*i]
        calcmeff[m[0]] = calc_masseff(band,kline,m[1],[L,G],log,m[0],Erange[i])

    # Masses along Sigma [110] (Gamma -- K)
    kline = range(kLinesDict['K'][0],kLinesDict['Gamma'][1]+1)
    mass = [('m_hh_110',max),('m_lh_110',max),('m_so_110',max)]
    Erange = [0.008, 0.03, 0.008]
    for i,m in enumerate(mass):
        band = bands[min(kline):max(kline)+1,nVBtop - 2*i]
        calcmeff[m[0]] = calc_masseff(band,kline,m[1],[K,G],log,m[0],Erange[i])

    return calcmeff

def analyseBS_Ge(bands,logger,kLinesDict,nVBtop,SOfactor=1):
    """
    Analyses the bands argument, and returns a dictionary in the same format as
    the reference data for Ge, but populated with the information obtained from
    the calculation (contained in the bands argument).
    Requires two additional arguments: kLinesDict and nVBtop (see BS.py for their
    meaning).
    """
    import numpy as np
    import logging
#    logger = logging.getLogger('analysis')
    calcEk = dict()
    logger.debug(kLinesDict)
    logger.debug(nVBtop)
    logger.debug(kLinesDict['Gamma'][0])

    calcEk['G25pr_v'] = bands[kLinesDict['Gamma'][0],nVBtop]
    calcEk['Gso_v'] = bands[kLinesDict['Gamma'][0],nVBtop-2*SOfactor]
    calcEk['G1_v'] = bands[kLinesDict['Gamma'][0],nVBtop-nVBtop]
    calcEk['G15_c'] = bands[kLinesDict['Gamma'][0],nVBtop+1*SOfactor-1]
    calcEk['G2pr_c'] = bands[kLinesDict['Gamma'][0],nVBtop+3*SOfactor-1]

    calcEk['X1_c'] = bands[kLinesDict['X'][0],nVBtop+1*SOfactor-1]
    calcEk['X4_v'] = bands[kLinesDict['X'][0],nVBtop]
    calcEk['X1_v'] = bands[kLinesDict['X'][0],nVBtop-nVBtop]

    calcEk['L3_c'] = bands[kLinesDict['L'][0],nVBtop+3*SOfactor-1]
    calcEk['L1_c'] = bands[kLinesDict['L'][0],nVBtop+1*SOfactor-1]
    calcEk['L3pr_v'] = bands[kLinesDict['L'][0],nVBtop]
    calcEk['L1_v'] = bands[kLinesDict['L'][0],nVBtop-2*SOfactor]
    calcEk['L2pr_v'] = bands[kLinesDict['L'][0],nVBtop-nVBtop]

    calcEk['K1_v2'] = bands[kLinesDict['K'][0],nVBtop-nVBtop]
    calcEk['K3_v'] = bands[kLinesDict['K'][0],nVBtop-2*SOfactor]
    calcEk['K1_v1'] = bands[kLinesDict['K'][0],nVBtop-1*SOfactor]
    calcEk['K2_v'] = bands[kLinesDict['K'][0],nVBtop]
    calcEk['K3_c1'] = bands[kLinesDict['K'][0],nVBtop+1*SOfactor-1]
    calcEk['K3_c2'] = bands[kLinesDict['K'][0],nVBtop+2*SOfactor-1]

    # Note that it may be more accurate to obtain the band minima/maxima by parabolic fitting
    # This would require a separate routine, which should return both the value of the extremum
    # and its position in terms of 2pi/a, since the fitten extremum is unlikely to 
    # coincide with a sampling point, and indexing will be meaningless.
    # Alternatively, a noninteger "index" may be returned.
    calcEk_st = dict()
    calcEk_st['Dmin_c'] = np.min(bands[kLinesDict['Gamma'][0]:kLinesDict['X'][0]+1,nVBtop+1])
    nkDmin_c = np.where(bands[kLinesDict['Gamma'][0]:kLinesDict['X'][0]+1,nVBtop+1]==calcEk_st['Dmin_c'])[0][0]
    calcEk_st['Dmin_c_pos'] = ((1.*nkDmin_c)/(kLinesDict['X'][0]-kLinesDict['Gamma'][0]))
    calcEk_st['Smin_v'] = np.min(bands[kLinesDict['K'][0]:kLinesDict['Gamma'][1]+1,nVBtop-1])
    
    calcEgap = dict()
    calcEgap['Egap'] = np.min(bands[:,nVBtop+1:])

    # This routine must be split, to permit the evaluation of all masses,
    # which require different 'bands' input, obtained from calculations with different klines.
    # For now we can only calculate masses along Delta, Sigma and Lambda.
    # This is sufficient for the valence bands, but not for the conduction band masses.
    calcmeff = dict()

#    from skopt.lattice import SymPts_k
# The following are in terms of the reciprocal lattice vectors b1,b2,b3
# But we need to translate them to 2*pi/a*_the_unit_vectors_ (i,j,k)
#    G = SymPts['FCC']['Gamma'][0]
#    X = SymPts['FCC']['X'][0]
#    L = SymPts['FCC']['L'][0]
#    K = SymPts['FCC']['K'][0]
# The results is (taking into account the definition of primitive lattice vectors
# and the definition of reciprocal lattice vectors, for FCC:
# (see Cardona, PhysRev 1966, and my own derivation, which confirms the values)
    G = (0,0,0)
    X = (0,1,0)
    L = (1./2.,1./2.,1./2.) 
    K = (3./4.,3./4.,0) 
    W = (1./2.,1.,0)

    # Masses along Delta (Gamma -- X)
    kline = range(kLinesDict['Gamma'][0],kLinesDict['X'][0]+1)
    m = ('me_Xl',min)
    band = bands[min(kline):max(kline)+1,nVBtop + 1] # note the +1 for the lowest CB
    calcmeff[m[0]] = calc_masseff(band,kline,m[1],[G,X],logger,m[0],0.04)

    mass = [('m_hh_001',max),('m_lh_001',max),('m_so_001',max)]
    Erange = [0.026, 0.045, 0.01]
    for i,m in enumerate(mass):
        band = bands[min(kline):max(kline)+1,nVBtop - 2*i]  
        calcmeff[m[0]] = calc_masseff(band,kline,m[1],[G,X],logger,m[0],Erange[i])

    # Masses along Lambda [111] (Gamma -- L)
    kline = range(kLinesDict['L'][0],kLinesDict['Gamma'][0]+1)
    mass = [('m_hh_111',max),('m_lh_111',max),('m_so_111',max)]
    Erange = [0.04, 0.025, 0.008]
    for i,m in enumerate(mass):
        band = bands[min(kline):max(kline)+1,nVBtop - 2*i]
        calcmeff[m[0]] = calc_masseff(band,kline,m[1],[L,G],logger,m[0],Erange[i])

    # Masses along Sigma [110] (Gamma -- K)
    kline = range(kLinesDict['K'][0],kLinesDict['Gamma'][1]+1)
    mass = [('m_hh_110',max),('m_lh_110',max),('m_so_110',max)]
    Erange = [0.008, 0.03, 0.008]
    for i,m in enumerate(mass):
        band = bands[min(kline):max(kline)+1,nVBtop - 2*i]
        calcmeff[m[0]] = calc_masseff(band,kline,m[1],[K,G],logger,m[0],Erange[i])

    calc_Ge = dict(list(calcEk.items()) + list(calcEgap.items()) + list(calcEk_st.items()) + list(calcmeff.items()))
    
    return calc_Ge

def calc_masseff(band,kline,extremum_type,kLineEnds,log,meff_name,Erange=0.026):
    """Extract the value of the parabolic effective mass at the extremum within the given
       E-kline, if the extremum is not at the boundary of the given k-line."""
    from math import pi,ceil
    import numpy as np
    import sys
    kline = np.array(kline)
    band = np.array(band)
    ## Scale the k-vector in [A^{-1}], taking into account direction and lattice parameter
    a = 5.658 # Ge lattice constant, [A] 
# NOTA BENE
# We should get this automatically the lattice parameter a, ideally from the UnitCell.gen file.
# This is particularly important for strain simulations, where the lattice will be distorted, or if
# someone decides to use slightly different lattice parameter (e.g. less precise or something).
# For strain, however, we will end up with a different lattice... how are we going to extract
# masses then? or if we simulate ultra-thin film confined by oxide or Hydrogen -- again, the 
# periodicity in at least one direction is lost...
    scale = 2*pi/a # first brillouin zone extends from -pi/a to +pi/a
    vk1 = scale*np.array(kLineEnds[0]) # e.g. Gamma = (0,0,0)
    vk2 = scale*np.array(kLineEnds[1]) # e.g. X = (1,0,0)
    k1 = np.sqrt(np.dot(vk1,vk1)) # length of k1 vector
    k2 = np.sqrt(np.dot(vk2,vk2)) # length of k2 vector
    klen=np.sqrt(np.dot(vk2-vk1,vk2-vk1)) # length of the vector from k1 to k2 = scale for X-Gamma
    nk = len(kline)
    dk = klen/(nk-1) # distance between available k-points
    kline = dk * np.array(range(nk)) # reconstruction of kline, in terms of scale. i.e. in units of A^{-1}

    # Find the extremum (min or max, as appropriate) to fit a parabola around it
    extr = extremum_type(band)
    #log.debug(np.where(band==extr)[0])
    iextr  = np.where(band==extr)[0][0]
    ## Special treatment is required if the point is right at the boundary, or very near it
    ## in which case we must extend the band by mirror symmetry around the extremum,
    ## before we attempt to fit
    ## Ideally, this should not happen, if we provide carefully selected paths that surround the
    ## band extrema; but this may not be possible at all to control when masses are roughly 
    ## estimated in the course of optimisation process, where it is better to minimize the 
    ## calculation of k-lines.
    if iextr == 0:
        log.debug('\tMirroring the band, since its {extr} is at {iextr}'.format(extr=extremum_type,iextr=iextr))
        kline = np.concatenate((-kline[:0 :-1],kline))
        band = np.concatenate((band[:0 :-1],band))
    if iextr == nk-1:
        log.debug('\tMirroring the band, since its {extr} is at {iextr}'.format(extr=extremum_type,iextr=iextr))
        band = np.concatenate((band,band[len(band)-2: :-1]))
        kline = np.concatenate((-kline[: :-1],kline[1:]))
    #log.debug(np.array(zip(kline,band)))
    #log.debug((len(band),len(kline)))
    #log.debug(np.where(band==extr)[0])
    iextr  = np.where(band==extr)[0][0]
    if (len(kline) != len(band)):
        log.critical('\tMismatch in the lengths of kline {0}, and band {1}, while trying to fit effective mass. Likely a bug, cannot continue.'.format(len(kline),len(band)))
        sys.exit()
    nk = len(kline)
    # Select how many points to use around the extremum, in order to make the fit.
    krange = np.where(abs(band-extr)<=Erange)
    nlow = min(krange[0])
    nhigh = max(krange[0])

    log.debug('\tFitting eff.mass on {n:3d} points around {i:3d}-th k; extremum value {v:7.3f} at {p:5.2f} of k-line'.
            format(n=nhigh-nlow+1,i=iextr+1,v=extr,p=kline[iextr]/kline[nk-1]*100))
    if nhigh-iextr < 3:
        log.debug('\tToo few points to the right of extremum -- Poor meff fit likely.')
        log.debug('\tConsider enlarting Erange. If it does not work, problem may be the extremum being too close to end of k-line')
    if iextr-nlow < 3:
        log.debug('\tToo few points to the left of extremum -- Poor meff fit likely. Consider enlarging Erange')
        log.debug('\tIf it does not work, problem may be the extremum being too close to end of k-line.')
        log.debug('\tThe best solution is to resolve the k-line with more k-points during simulation.')

    # fit 2nd order polynomial over a few points surrounding the selected band extremum
    x = kline[nlow:nhigh+1]
    y = band[nlow:nhigh+1]
    c = np.polyfit(x,y,2)
    fit = np.poly1d(c)
# NOTA BENE:
# We need the c[0] coefficient when we use numpy.poly[fit|1d]

    # report the effective mass as the inverse of the curvature (i.e. inverse of the 2nd derivative, which is a const.)
    # recall that meff = (h_bar**2) / (d**2E/dk**2), in [kg]
    # meff is needed in terms of m0 - the mass of free electron at rest;
    # in atomic units h_bar is 1, m0 is 1 => we need to convert E and k in atomic units and we're done
    # our E and k are in eV and A-1, respectively and d**2E/dk**2 = 2*c[0] = const. [eV/A^-2] = const. [eV*A^2] = const/(Eh*aB^2)[a.u.]
    # the relevant fundamental constants
    Eh = 27.2114 # [eV] Hartree energy
    aB = 0.52918 # [A]  Bohr radius
    #m0 = 9.10938e-31 # [kg] electron rest mass
    #hbar = 1.054572e-34 # [J.s]
    #q0 = 1.602176e-19 # [C] electron charge
    #meff = (hbar*hbar)/((2*c[0])*(q0*(1.e-10)**2))/m0
    meff = 1./(2.*c[0])*(Eh*aB**2)
    log.debug("\tFitted {name:8s}: {m:8.3f}".format(name=meff_name,m=meff))
    return meff


# References:
# [1] Wahiduzzaman et al, JCTC 2013 _9_, exponent for Si is 12.8, and r0 is 4.4 a.u.
# [2] Elstner et al, Phys Rev B 98
# [3] A. Sieck, PhD. Thesis, University of Paderborn, 2000 

atomconfigs = {
    "Si": AtomConfig(
        # Data from http://www.rsc.org/periodic-table/element/14/silicon
        # ----------------------------------------------------------------------
        # [Ne].3s2.3p2  (Ne: [He].2s2.2p6)
        # Atomic Radius (non-bonded) [A]: 2.1
        # Covalent Radius [A]: 1.14
        # Electron Affinity [kJ/mol]: 134.068
        # Electronegativity (Pauling scale): 1.9
        # Ionisation energies [kJ/mol]: 1st 786.518; 2nd 1577.134; 3rd 3231.585; 4th 4355.523; 5th 16090.571; 6th 19805.55; 7th 23783.6; 8th 29287.16;
        znuc=14,
        mass=28.085,
        # [Ne].3s2.3p2  (Ne: [He].2s2.2p6)
        occupations=[
            [ [ 1.0, 1.0 ], [ 1.0, 1.0 ], [ 1.0, 1.0 ], ],  # s
            [               [ 3.0, 3.0 ], [ 1.0, 1.0 ], ],  # p
            [                             [ 0.0, 0.0 ], ],  # d
            ],
        valenceqns=[
            [3, ],  # s
            [3, ],  # p
            [3, ],  # d
            ],
        relativistic=True,
        orbitalresolved=True,
        # override the d onsite with the value in [1]
        # note that gridatom yields very low d-eigenstate
        # ideally, we should be able to optimise that
        override_onsite={ (3, 2): 0.113134 },
        ),
}

skbases = {
    "Si": SlaterBasis(
        exponents=[
        # Geometric progression, very similar to the one used in PBC
            [0.4, 0.97, 2.37, 5.75, 14.0], # s
            [0.4, 0.97, 2.37, 5.75, 14.0], # p
            [0.4, 0.97, 2.37, 5.75, 14.0], # d
            ],
        maxpowers= [
            3,  # s
            3,  # p 
            3,  # d
            ]
        ),
}

compressions = {
    "Si": Compression(
        # According to [1], exponent for Si is 12.8, and r0 is 4.4 a.u.
        # The rule of thumb [2] gives: 1.8*r_cov = 3.88 a.u.
        # According to [3], power=4, r0=5.4 is best for 3s3p3d4s basis
        potcomp="potential",
        potcomp_parameters= [ (4, 5.4), # s
                              (4, 5.4), # p
                              (4, 5.4), # d
                            ],
        wavecomp="potential",
        wavecomp_parameters=[ (4, 5.4), # s
                              (4, 5.4), # p
                              (4, 5.4), # d
                            ],
        ),
} 

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
        # Unit cell: a=5.4315A, space group Fd3bm
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
        override_onsite={ },
        ),


    "O": AtomConfig(
        # Data from http://www.rsc.org/periodic-table/element/8/oxygen
        # ----------------------------------------------------------------------
        # [He].2s2.2p4
        # Atomic Radius (non-bonded) [A]: 1.52
        # Covalent Radius [A]: 0.64
        # Electron Affinity [kJ/mol]: 140.976
        # Electronegativity (Pauling scale): 3.44
        # Ionisation energies [kJ/mol]: 1st 1313.942; 2nd 3388.671; 3rd 5300.47; 4th7469.271 ; 5th 10989.584; 6th 13326.526; 7th 71330.65; 8th 84078.3;
        znuc=8,
        mass=15.999,
        # [He].2s2.2p4
        occupations=[
            [ [ 1.0, 1.0 ], [ 1.0, 1.0 ], ],  # s
            [               [ 2.0, 2.0 ], ],  # p
            ],
        valenceqns=[
            [2, ],  # s
            [2, ],  # p
            ],
        relativistic=True,
        orbitalresolved=True,
        override_onsite={ },
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

    "O": SlaterBasis(
        exponents=[
            [0.5, 1.26, 3.17, 8.0], # s
            [0.5, 1.26, 3.17, 8.0], # p
            ],
        maxpowers= [
            3,  # s
            3,  # p 
            ]
        ),

}


compressions = {

    "Si": Compression(
        # according to Wahiduzzaman et al, JCTC 2013 _9_, exponent for Si is 12.8, and r0 is 4.4 a.u.
        # 1.8*r_cov = 3.88 a.u.
        # power=4, r0=5.4 as reportedly best for 3s3p3d4s basis in 
        # A. Sieck, PhD. Thesis, University of Paderborn, 2000 
        potcomp="potential",
        potcomp_parameters= [ (4, %(Si_R0_spd), # s
                              (4, %(Si_R0_spd), # p
                              (4, %(Si_R0_spd), # d
                            ],
        wavecomp="potential",
        wavecomp_parameters=[ (4, %(Si_R0_spd), # s
                              (4, %(Si_R0_spd), # p
                              (4, %(Si_R0_spd), # d
                            ],
                    ),

    "O": Compression(
        # according to Wahiduzzaman et al, JCTC 2013 _9_, exponent for O is 12.4, r0 is 3.1 a.u.
        # 1.8*r_cov = 2.17 a.u.
        potcomp="potential",
        potcomp_parameters= [ (4, %(O_R0_sp), # s
                              (4, %(O_R0_sp), # p
                            ],
        wavecomp="potential",
        wavecomp_parameters=[ (4, %(O_R0_sp), # s
                              (4, %(O_R0_sp), # p
                            ],
                    ),

} 


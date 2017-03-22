atomconfigs = {

    "Si": AtomConfig(
        znuc=14,
        mass=28.0855,
        occupations=[
            [ [ 1.0, 1.0 ], [ 1.0, 1.0 ], [ 1.0, 1.0 ]],  # s
            [ [ 3.0, 3.0 ], [ 1.0, 1.0 ]],  # p
            [ [ 0.0, 0.0 ]], # d
            ],
        valenceqns=[
            [3, ],  # s
            [3, ],  # p
            [3, ],  # d
            ],
        relativistic=True,
        orbitalresolved=True,
        override_onsite={ 
#	    (3, 2): %(DeltaE_Si_3s, 0, -0.1, 0.1)f,
#	    (3, 2): %(DeltaE_Si_3p, 0, -0.1, 0.1)f,
	    (3, 2): %(DeltaE_Si_3d, -0.1, 0.2)f,
	    }
        ),
    }


skbases = {
    "Si": SlaterBasis(
		exponents = [[1, 2.41, 5.81, 14], [1, 2.41, 5.81, 14], [3.0, 5.01, 8.38, 14]],
		maxpowers = [3, 3, 3],
    ),
    }


compressions = {
    "Si": Compression(
        potcomp="potential",
        potcomp_parameters= [ 
		(4, %(PotCompRad_Si_sp, 4, 12)f ),
		(4, %(PotCompRad_Si_sp, 4, 12)f ),
		(4, %(PotCompRad_Si_d,  6, 15)f ), ],
        wavecomp="potential",
        wavecomp_parameters=[ 
		(4, %(PotCompRad_Si_sp, 4, 12)f ),
		(4, %(PotCompRad_Si_sp, 4, 12)f ),
		(4, %(PotCompRad_Si_d,  6, 15)f ), ],
        ),
    }

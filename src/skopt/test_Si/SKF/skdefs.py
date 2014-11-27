atomconfigs = {

    "Si": AtomConfig(
        znuc=14,
        mass=28.0855,
        occupations=[
            [ [ 1.0, 1.0 ], [ 1.0, 1.0 ], [ 1.0, 1.0 ]],  # s
            [ [ 3.0, 3.0 ], [ 2.0, 0.0 ]],  # p
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
	    (3, 1): 0.007822,
	    (3, 2): 0.219827 
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
		(4, 3.490626 ),
		(4, 6.479860 ),
		(4, 6.459532 ), ],
        wavecomp="potential",
        wavecomp_parameters=[ 
		(4, 3.490626 ),
		(4, 6.479860 ),
		(4, 6.459532 ), ],
        ),
    }

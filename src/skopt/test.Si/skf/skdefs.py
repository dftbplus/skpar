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
	    (3, 2): 0.071476 
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
            (4, 5.609722 ),
            (4, 4.201230 ),
            (4, 6.990160 ), ],
        wavecomp="potential",
        wavecomp_parameters=[ 
            (4, 5.609722 ),
            (4, 4.201230 ),
            (4, 6.990160 ), ],
        ),
    }

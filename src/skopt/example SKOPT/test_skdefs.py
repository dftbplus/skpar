
compressions = {
	"Si": Compression(
		potcomp = "potential",
		potcomp_parameters = [[4, 3.45], 
                          [5, 
#                       [%( Dummy_1 ,1,7)i, 
#                        %(Dummy_2, 2,3)f,
                           3.670000 ], 
                           [4, 7.67]],
		wavecomp = "potential",
		wavecomp_parameters = [[4, 3.45], [4, 6.44], [4, 7.67]],
		),
	"O": Compression(
		potcomp = "potential",
		potcomp_parameters = [[ 4, 4.000000], 
                          [4, 4.000000]],
		wavecomp = "potential",
		wavecomp_parameters = [[12, 3.1], [12, 3.1]],
		),
    }


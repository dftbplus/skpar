import os
import logging
from os.path import normpath, expanduser, isdir
from os.path import join as joinpath

class DetailedOut (dict):
    """A subclass of dictionary, automatically initialised from file.
    
    Useage:

        destination_dict = DetailedOut.fromfile(filename)
    """
    energy_tags = [
            ("Fermi energy:", "Ef"), 
            ("Band energy:", "Eband"),
            ("TS:", "Ets"),
            ("Band free energy (E-TS):", "Ebf"),
            ("Extrapolated E(0K):", "E0K"),
            ("Energy H0:", "Eh0"),
            ("Energy SCC:", "Escc"),
            ("Energy L.S:", "Els"),
            ("Total Electronic energy:", "Eel"),
            ("Repulsive energy:", "Erep"),
            ("Total energy:", "Etot"),
            ("Total Mermin free energy:", "Emermin"), ]
    # float values, allowing for fractional number [input, output]
    nelec_tags = [
            ("Input/Output electrons (q):", ("nei", "neo")) ]
    # logical value
    conv_tags = [
            ("iSCC", ('nscc', 'scc_err')),
            ("SCC converged", True),
            ("SCC is NOT converged", True), ]

    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    @classmethod
    def fromfile(cls, fp):
        fname = isinstance(fp, str)
        if fname:
            fp = open(fp, "r")
        tagvalues = {}
        with fp:
            for line in fp:
                words = line.split()
                # Energies
                for tag in cls.energy_tags:
                    if tag[0] in line:
                        # Energies are returned in [eV] (note the [-2], since 
                        # the penultimate word is the value in eV)
                        tagvalues[tag[1]] = float(words[-2])
                # Number of electrons (note this may be fractional!)
                for tag in cls.nelec_tags:
                    if tag[0] in line:
                        tagvalues[tag[1][0]] = float(words[-2])
                        tagvalues[tag[1][1]] = float(words[-1])
                # Convergence
                for tag in cls.conv_tags[1:]:
                    if tag[0] in line:
                        tagvalues[tag[0]] = tag[1]
        if fname:
            fp.close()
        # post process
        tagvalues['converged'] = 'SCC converged' in tagvalues
        tagvalues['withSOC'] = 'Els' in tagvalues
        # Remove SCC converged and SCC is NOT converged; otherwise, udpates
        # may end up with both, which will be a source of trouble.
        # Only one flag should operate: 'converged'!
        tagvalues.pop('SCC converged', None)
        tagvalues.pop('SCC is NOT converged', None)
        return cls(tagvalues)


def get_dftbp_data(source, destination, workdir='.', *args, **kwargs):
    """Load whatever data can be obtained from detailed.out of dftb+.
    """
    assert isinstance(source, str), \
        "src must be a string (filename or directory name), but is {} instead.".format(type(src))
    if isdir(source):
        ff = normpath(expanduser(joinpath(source, 'detailed.out')))
    else:
        ff = normpath(expanduser(joinpath(workdir, source)))
    data = DetailedOut.fromfile(ff)
    destination.update(data)



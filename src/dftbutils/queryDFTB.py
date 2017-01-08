import os
import logging
from os.path import normpath, expanduser, isdir
from os.path import join as joinpath

class DetailedOut (dict):
    """A dictionary initialised from file with the detailed output of dftb+.
    
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


class BandsOut (dict):
    """A dictionary initialised with the bands from dp_bands or similar tool.

    Useage:

        destination_dict = BandsOut.fromfile(file)
    """
    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    @classmethod
    def fromfile(cls, fp, enumeration=True):
        fname = isinstance(fp, str)
        if fname:
            fp = open(fp, "r")
        values = {}
        bands = np.loadtxt(fp, dtype=float)
        if enumeration:
            k = bands[:,0].astype(int)
            # removing the kpoint-index, we get a 2D array of energies
            bands = np.delete(bands,0,1)
        if fname:
            fp.close()
        # post process
        nk, nb = bands.shape
        values['bands'] = bands
        values['nkpts'] = nk
        values['nbands'] = nb
        return cls(values)


class Bandstructure(dict):
    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    @classmethod
    def fromfiles(cls, fp1, fp2, enumeration=True):
        data = DetailedOut.fromfile(fp1)
        banddata = BandsOut.fromfile(fp2)
        data.update(banddata)
        # post process
        if data['withSOC']:
            ivbtop = int(data['neo']) - 1
        else:
            ivbtop = int(data['neo']/2.) - 1
        evb = max(data['bands'][:, ivbtop])
        ecb = min(data['bands'][:, ivbtop + 1])
        egap = ecb - evb
        data['Egap'] = egap
        data['Ecb']  = ecb
        return cls(values)


def get_bandstructure(source, destination, workdir='.', *args, **kwargs):
    """Load whatever data can be obtained from detailed.out of dftb+ and bands_tot.dat of dp_bands.
    """
    assert isinstance(source, str), \
        "src must be a string (filename or directory name), but is {} instead.".format(type(src))
    if isdir(source):
        f1 = normpath(expanduser(joinpath(source, 'detailed.out')))
        f2 = normpath(expanduser(joinpath(source, 'bands_tot.dat')))
    else:
        # band_tot.dat can be controled from command line during execution of dp_bands
        # while 'detailed.out' cannot be controled by user
        f1 = normpath(expanduser(joinpath(workdir, 'detailed.out')))
        f2 = normpath(expanduser(joinpath(workdir, source)))
    data = Bandstructure(f1, f2)
    destination.update(data)



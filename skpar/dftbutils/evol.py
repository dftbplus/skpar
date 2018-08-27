"""Executable for calculating Energy versus Strain with DFTB+"""
import os
from os.path import abspath, expanduser
from os.path import join as joinpath
import logging
import argparse
from skpar.dftbutils.utils import get_logger, execute

def set_evol_parser(parser=None):
    """Define parser options specific for energy-volume scan.

    Parameters:

        parser: python parser
            Typically, that will be a sub-parser passed from top executable.
    """
    # Initialise argument parser if not provided
    if parser is None:
        parser = argparse.ArgumentParser(
            description="Calculate total energy vs volume dependence.")
        subparser = False
    else:
        subparser = True
    # Once we have a parser, we can add arguments to it
    parser.add_argument(
            "-v", dest="verbose", default=False, action="store_true",
            help="Raise verbosity level from INFO to DEBUG for the console.")
    parser.add_argument(
            '-p', "--plot", dest="plot", default=False, action="store_true",
            help="Unsupported: Plot the energy-volume curve.")
    parser.add_argument(
            "-wd", dest='workdir', type=str, default='.', action="store",
            help="(default: .) Working directory with sub-folders, "
                 "each sub-folder is for an scc calculation at a "
                 "specific volume. The execution is in workdir/strain/scc/)")
    parser.add_argument(
            "-sccdir", dest='sccdir', type=str, default='.', action="store",
            help="(default: the strain folder) Sub-directory under the "
                 "strain-folders, where the scc calculation for a specific "
                 "strain is performed. ")
    parser.add_argument(
            "-dftb", type=str, default='dftb+', action="store",
            help="(default: dftb+) dftb executable")
    if subparser:
        parser.set_defaults(func=main_evol)
        return None
    else:
        return parser

def main_evol(args):
    """
    Chain the relevant tasks for scanning an energy-volume dependence.

    The key concept/assumption is that we pass only a main directory under
    which there are a set of sub-directories named by three digits,
    e.g. 099/ 100/ 101/ 102/, where the calculation for a specific volume
    is set up in advance.

    Currently this implies serial operation. MPI parallelism over the
    different volumes is necessary, but not implemented yet.
    """
    # setup logger
    # -------------------------------------------------------------------
    loglevel = logging.DEBUG if args.verbose else logging.INFO
    logger   = get_logger(name='dftbutils', filename='dftbutils.evol.log',
                          verbosity=loglevel)

    # any arguments related to the dftb executable
    dftb    = args.dftb
    dftblog = 'dftb.log'

    # deal with e-vol-specific arguments if any
    # --------------------------------------------------
    # `workdir` is the main directory; under it there should be a
    # sub-folder for each volume.
    workdir = abspath(expanduser(args.workdir))
    sccdir  = args.sccdir
    cwd = os.getcwd()
    os.chdir(workdir)
    # Automatically establish the available directories for different volumes.
    # We are imposing that under strain directory there is an `scc` directory,
    # which may not be such a good idea, but allows to have also `bs` for a
    # given strain.
    strain_dirs = [dd for dd in os.listdir() if dd.isdigit()]
    for _dir in strain_dirs:
        calcdir = joinpath(workdir, _dir, sccdir)
        execute(cmd=dftb, workdir=calcdir, outfile=dftblog)
        # Note that dftb+ (at least v1.2) exits with 0 status even if there are
        # ERRORS. Therefore, below we ensure we stop in such case, rather than
        # diffusing the problem through attempts of subsequent operations.
        # check_dftblog is a bash script in skpar/bin/ but this can be moved to
        # python instead
        execute(cmd=['check_dftblog', dftblog], workdir=sccdir, outfile='chk.log')
    os.chdir(cwd)

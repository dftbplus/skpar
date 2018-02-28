import logging
import argparse
import sys, os
from os.path import abspath, normpath, expanduser
from os.path import join as joinpath
from skpar.dftbutils.utils import get_logger
from skpar.core.tasks import RunTask

def set_evol_parser(parser=None):
    """Define parser options specific for energy-volume scan.

    Parameters:

        parser: python parser
            Typically, that will be a sub-parser passed from top executable.
    """
    myname = 'evol'
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
            '-n', "--dry_run", dest="dry_run", default=False, action="store_true", 
            help="Do not execute the tasks but print the tasklist.")
    parser.add_argument(
            '-p', "--plot", dest="plot", default=False, action="store_true", 
            help="Plot the energy-volume curve.")
    parser.add_argument(
            "-wd", dest='workdir', type=str, default='.', action="store", 
            help="(dflt: .) Working directory with sub-folders, " 
                "each sub-folder is for an scc calculation at a "
                "specific volume")
    parser.add_argument(
            "-dftb", type=str, default='dftb+', action="store", 
            help="(dflt: dftb+) dftb executable")
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

    Currently this implies serial operation. MPI parallelisation over the
    different volumes is necessary, but not implemented yet.
    """
    # setup logger
    # -------------------------------------------------------------------
    loglevel = logging.DEBUG if args.verbose else logging.INFO
    logger   = get_logger(name='dftbutils', filename='dftbutils.evol.log',  
                          verbosity=loglevel)

    # deal with e-vol-specific arguments if any
    # --------------------------------------------------
    # Word dir is the main directory; under it there should be a
    # sub-folder for each volume.
    workdir = abspath(expanduser(args.workdir))
    # Automatically establish the available directories for different 
    # volumes, and create a list of sub-directories where actual
    # calculations will happen.
    cwd = os.getcwd()
    os.chdir(workdir)
    sccdirs = [dd for dd in os.listdir() if dd.isdigit()]
    os.chdir(cwd)
    # any arguments related to the dftb executable
    dftb    = args.dftb
    dftblog = 'dftb.log'

    # Create the task list
    tasks = []
    for dd in sccdirs:
        wd = joinpath(workdir, dd)
        tasks.append(RunTask(cmd=dftb, wd=wd, out=dftblog))
    # Note that dftb+ (at least v1.2) exits with 0 status even if there are ERRORS
    # Therefore, below we ensure we stop in such case, rather than diffusing the 
    # problem through attempts of subsequent operations.
    # check_dftblog is a bash script in skpar/bin/
        tasks.append(RunTask(cmd=['check_dftblog', dftblog] , wd=wd, out='chk.log'))

    # align the loggers (could be done above in the initialization)
    for tt in tasks:
        tt.logger = logger

    # execute
    for tt in tasks:
        logger.debug(tt)
        if not args.dry_run:
            tt(workroot='.')

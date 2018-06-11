import logging
import argparse
import json
import sys, os
import numpy as np
from os.path import abspath, normpath, expanduser
from os.path import join as joinpath
from skpar.dftbutils.utils import get_logger
from skpar.core.tasks import RunTask, GetTask
from skpar.dftbutils.queryDFTB import get_bandstructure
from skpar.dftbutils.plot import plot_bs

def set_bands_parser(parser=None):
    """Define parser options specific for band-structure calculations.

    Parameters:

        parser: python parser
            Typically, that will be a sub-parser passed from top executable.
    """
    myname = 'bands'
    # Initialise argument parser if not provided
    if parser is None:
        parser = argparse.ArgumentParser(
            description="Calculate band-structure.")
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
            help="Plot the band-structure.")
    parser.add_argument(
            '-q', "--plot_only", dest="plot_only", default=False, action="store_true", 
            help="Only plot the band-structure, do not run calculation.")
    parser.add_argument(
            '-y', "--ylimit", dest="ylim", nargs=2, default=(-25, 15), 
            action="store", type=float,
            help="A tuple: Y axis limits if -p is specified (dftt.: [-25, 15]).")
    parser.add_argument(
            '-l', '--latticeinfo', dest='latticeinfo', default=None, 
            action='store', type=json.loads, help='Lattice info, e.g.:'
            '{"type": FCC, "param": 5.43}')
    parser.add_argument(
            "-wd", dest='workdir', type=str, default='.', action="store", 
            help="(dflt: .) Working directory with atoms, scc/ and bs/")
    parser.add_argument(
            "-dftb", type=str, default='dftb+', action="store", 
            help="(dflt: dftb+) dftb executable")
    parser.add_argument(
            "-bands", type=str, default='dp_bands', action="store", 
            help="(dflt: dp_bands) Tool to convert the output to "
                 "bandstructure file for plotting ")
    parser.add_argument(
            "-dos", type=str, nargs='?', const='dp_dos', action="store", 
            help="(dflt: dp_dos) Tool to convert the output to "
                 "DoS file for plotting ")
    if subparser:
        parser.set_defaults(func=main_bands)
        return None
    else:
        return parser

def main_bands(args):
    """
    Chain the relevant tasks for obtaining band-structure and execute.
    """
    # setup logger
    # -------------------------------------------------------------------
    loglevel = logging.DEBUG if args.verbose else logging.INFO
    logger   = get_logger(name='dftbutils', filename='dftbutils.bands.log',  
                          verbosity=loglevel)

    #logger.info(args)
    # deal with bands-specific arguments if any
    # --------------------------------------------------
    workroot = '.'
    workdir = abspath(expanduser(args.workdir))
    sccdir  = abspath(joinpath(workdir, 'scc'))
    sccchg  = abspath(joinpath(sccdir, 'charges.bin'))
    bsdir   = abspath(joinpath(workdir, 'bs'))
    dftb    = args.dftb
    dftblog = 'dftb.log'
    bands   = normpath(expanduser(args.bands))
    if args.dos:
        dos     = normpath(expanduser(args.dos))
    bandslog = 'dp_bands.log'
    # Create the task list
    tasks = []
    tasks.append(RunTask(cmd=dftb, wd=sccdir, out=dftblog))
    # Note that dftb+ (at least v1.2) exits with 0 status even if there are ERRORS
    # Therefore, below we ensure we stop in such case, rather than diffusing the 
    # problem through attempts of subsequent operations.
    # check_dftblog is a bash script in skpar/bin/
    tasks.append(RunTask(cmd=['check_dftblog', dftblog] , wd=sccdir, out='chk.log'))
    if args.dos:
        tasks.append(RunTask(cmd=[dos, 'band.out', 'dos_total.dat'], wd=sccdir, out=bandslog))

    tasks.append(RunTask(cmd=['cp', '-f', sccchg, bsdir], out=None))
    tasks.append(RunTask(cmd=dftb, wd=bsdir, out=dftblog))
    tasks.append(RunTask(cmd=['check_dftblog', dftblog] , wd=sccdir, out='chk.log'))
    tasks.append(RunTask(cmd=[bands, 'band.out', 'bands'], wd=bsdir, out=bandslog))

    # align the loggers (could be done above in the initialization)
    for tt in tasks:
        tt.logger = logger

    # execute
    if not args.plot_only:
        for tt in tasks:
            logger.debug(tt)
            if not args.dry_run:
                tt(workroot=workroot)

    if args.plot or args.plot_only:
        # hack the plotting directly, not via tasks, to avoid needing objectives
        bsdata = {}
        get_bandstructure(workroot, bsdir, bsdata, latticeinfo=args.latticeinfo)
        logger.info('Band-gap (eV) = {:.3f}'.format(bsdata['Egap']))
        yy1 = bsdata['bands'] - bsdata['Evb']
        if args.latticeinfo:
            xx1 = bsdata['kvector']
            xtl = bsdata['kticklabels']
        else:
            xx1 = np.asarray(range(yy1.shape[1]))
            xtl = None
        filename = os.path.join(workroot, workdir, 'bs.pdf')
        fig, ax = plot_bs(xx1, yy1, filename=filename, ylim=args.ylim, 
                        xticklabels=xtl)

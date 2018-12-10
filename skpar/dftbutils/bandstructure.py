"""Bandstructure calculation by DFTB"""
import sys
import os
from os.path import abspath, normpath, expanduser
from os.path import join as joinpath
import logging
import argparse
import json
import numpy as np
from skpar.dftbutils.utils import get_logger, execute
from skpar.dftbutils.queryDFTB import get_bandstructure
from skpar.dftbutils.plot import plot_bs

def set_bands_parser(parser=None):
    """Define parser options specific for band-structure calculations.

    Parameters:

        parser: python parser
            Typically, that will be a sub-parser passed from top executable.
    """
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
            '{"type": "TET", "param": [5.43, 100.0]}')
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
    bands   = args.bands
    if args.dos:
        dos = args.dos
    bandslog = 'dp_bands.log'

    if not args.plot_only:
        # Execute the necessary commands
        # scc calculation
        execute(cmd=dftb, workdir=sccdir, outfile=dftblog)
        # check log
        execute(cmd=['check_dftblog', dftblog], workdir=sccdir,
                outfile='chk.log')
        # extract dos for plotting
        if args.dos:
            execute(cmd=[dos, 'band.out', 'dos_total.dat'], workdir=sccdir,
                    outfile=bandslog)
        # copy charges for klines calculation
        execute(cmd=['cp', '-f', sccchg, bsdir], workdir='.', outfile=None)
        # klines calculation
        execute(cmd=dftb, workdir=bsdir, outfile=dftblog)
        # check log
        execute(cmd=['check_dftblog', dftblog], workdir=sccdir,
                outfile='chk.log')
        # extract bands for plotting
        execute(cmd=[bands, 'band.out', 'bands'], workdir=bsdir,
                outfile=bandslog)

    if args.plot or args.plot_only:
        # hack the plotting directly, not via tasks, to avoid needing objectives
        database = {}
        implargs = {'workroot': workroot}
        get_bandstructure(implargs, database, bsdir, 'dftb', latticeinfo=args.latticeinfo)
        bsdata = database.get('dftb')
        logger.info('Band-gap (eV) = {:.3f}'.format(bsdata['Egap']))
        yy1 = bsdata['bands'] - bsdata['Evb']
        if args.latticeinfo:
            xx1 = bsdata['kvector']
            xtl = bsdata['kticklabels']
        else:
            xx1 = np.asarray(range(yy1.shape[1]))
            xtl = None
        filename = os.path.join(workroot, workdir, 'bs.pdf')
        plot_bs(xx1, yy1, filename=filename, ylim=args.ylim, xticklabels=xtl)

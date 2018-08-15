"""Dictionary with default tasks and their underlying functions."""
import os.path
import matplotlib
import numpy as np
from skpar.core.utils import get_ranges, get_logger
from skpar.core.plot import skparplot
from skpar.dftbutils.queryDFTB import get_dftbp_data, get_bandstructure
from skpar.dftbutils.queryDFTB import get_dftbp_evol
from skpar.dftbutils.queryDFTB import get_effmasses, get_special_Ek
from skpar.dftbutils.plot import magic_plot_bs
matplotlib.use("Agg")

LOGGER = get_logger(__name__)

def execute(workroot, cmd, cdir='.', outfile='out.log', logger=LOGGER, **kwargs):
    """Wrapper over external executables.

    Args:
        workroot: root directory related to the task, typically not controlled
            by user, but explicitly passed by caller.
        cmd(list): command to be executed [0] and command line arguments [1:]
        cdir: directory, relative to workroot, where executable should be run
        outfile: output log file
        logger: python logging logger

    No kwargs are parsed or processed.
    
    Raises:
        subprocess.CalledProcessError: if command fails during its execution
        OSError: if command cannot be executed for some reason
    """
    def write_out(out, outfile):
        """Write subprocess output to a file"""
        if outfile is not None:
            with open(outfile, 'w') as filep:
                filep.write(out)
            logger.debug("Output is in %s.\n", outfile)
    #
    origdir = os.getcwd()
    workdir = os.path.normpath(os.path.join(workroot, cdir))
    try:
        os.chdir(workdir)
    except:
        # this should not happen; typically, the workdir should already
        # be there and contain some input file and data
        logger.critical("Cannot change to working directory %s", workdir)
        raise
    #
    if outfile is not None:
        outfile = os.path.normpath(os.path.join(workdir, outfile))
    #
    try:
        logger.debug("Running %s in %s...", cmd, workdir)
        out = subprocess.check_output(
            cmd, universal_newlines=True, stderr=subprocess.STDOUT)
        logger.debug('Done.')
        write_out(out, outfile)
    #
    except subprocess.CalledProcessError as exc:
        logger.critical('The following task failed with exit status %s:\n',
                        exc.returncode)
        write_out(exc.output, outfile)
        raise
    #
    except OSError as exc:
        logger.critical("Abnormal termination: OS could not execute %s in %s",
                        cmd, cdir)
        logger.critical("If the command is a script, make sure there is a shebang!")
        raise
    #
    finally:
        # make sure we return to where we started from in any case!
        os.chdir(origdir)

def get_model_data (workroot, src, dst, data_key, *args, **kwargs):
    """Get data from file and put it in a dictionary under a given key.

    Use numpy.loadtxt to get the data from `src` file and
    write the data to `dst` dictionary under `data_key`.

    Applicable kwargs:

        * loader_args: dictionary of np.loadtxt kwargs

        * process: dictionary of kwargs:
            + rm_columns: [ index, index, [ilow, ihigh], otherindex, [otherrange]]
            + rm_rows   : [ index, index, [ilow, ihigh], otherindex, [otherrange]]
            + scale : float=1
    """
    assert isinstance(src, str), \
        "src must be a filename string, but is {} instead.".format(type(src))
    assert isinstance(data_key, str), \
        "data_key must be a string naming the data, but is {} instead.".format(type(data_key))

    fname = os.path.normpath(os.path.join(workroot, os.path.expanduser(src)))
    loader_args = {} #{'unpack': False}
    # overwrite defaults and add new loader_args
    loader_args.update(kwargs.get('loader_args', {}))
    # make sure we don't try to unpack a key-value data
    if 'dtype' in loader_args.keys() and\
        'names' in loader_args['dtype']:
        loader_args['unpack'] = False
    # read file
    try:
        array_data = np.loadtxt(fname, **loader_args)
    except ValueError:
        # `fname` was not understood
        LOGGER.critical('np.loadtxt cannot understand the contents of %s'+\
            'with the given loader arguments: %s', fname, **loader_args)
        raise
    except (IOError, FileNotFoundError):
        # `fname` was not understood
        LOGGER.critical('Data file %s cannot be found', fname)
        raise
    # do some filtering on columns and/or rows if requested
    # note that file to 2D-array mapping depends on 'unpack' from
    # loader_args, which transposes the loaded array.
    postprocess = kwargs.get('process', {})
    if postprocess:
        if 'unpack' in loader_args.keys() and loader_args['unpack']:
            # since 'unpack' transposes the array, now row index
            # in the original file is along axis 1, while column index
            # in the original file is along axis 0.
            key1, key2 = ['rm_columns', 'rm_rows']
        else:
            key1, key2 = ['rm_rows', 'rm_columns']
        for axis, key in enumerate([key1, key2]):
            rm_rngs = postprocess.get(key, [])
            if rm_rngs:
                indexes = []
                # flatten, combine and sort, then delete corresp. object
                for rng in get_ranges(rm_rngs):
                    indexes.extend(list(range(*rng)))
                indexes = list(set(indexes))
                indexes.sort()
                array_data = np.delete(array_data, obj=indexes, axis=axis)
        scale = postprocess.get('scale', 1)
        array_data = array_data * scale
    dst[data_key] = array_data

TASKDICT = {'exe': execute}

GETTASKDICT = {
    'get_model_data': get_model_data,
    'get_dftbp_data': get_dftbp_data,
    'get_dftbp_evol': get_dftbp_evol,
    'get_dftbp_bs'  : get_bandstructure,
    'get_dftbp_meff': get_effmasses,
    'get_dftbp_Ek'  : get_special_Ek,
    }

PLOTTASKDICT = {
    'plot_objvs': skparplot,
    'plot_bs'   : magic_plot_bs
    }

TASKDICT.update(GETTASKDICT)
TASKDICT.update(PLOTTASKDICT)

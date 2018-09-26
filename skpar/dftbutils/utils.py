"""
General utility functions
"""
import subprocess
import os
import shutil
import shlex
import glob
import logging

def parse_cmd(cmd):
    """Parse shell command for globbing and environment variables.
    """
    if not isinstance(cmd, list):
        cmd = shlex.split(cmd)
    parsed_cmd = [cmd[0],]
    for word in cmd[1:]:
        if word[0] == '$':
            var = word[1:].strip('{').strip('}')
            varval = os.environ.get(var, word)
            parsed_cmd.append(varval)
        else:
            if '*' in word:
                items = glob.glob(word)
                for item in items:
                    parsed_cmd.append(item)
            else:
                parsed_cmd.append(word)
    return parsed_cmd

def execute(cmd, workdir='.', outfile='run.log', purge_workdir=False, **kwargs):
    """Execute external command in workdir, streaming output/error to outfile.

    Args:
        cmd (str): command; executed in `workir`; if it contains `$` or 
                   `*`-globbing, these are shell-expanded
        workdir (path-like): execution directory relative to workroot
        outfile (str): output file for the stdout/stderr stream; continuously
                       updated during execution
        purge_workdir (bool): if true, any existing working directory is purged
        kwargs (dict): passed directly to the underlying `subprocess.call()`

    Returns:
        None

    Raises:
        OSError: if `cmd` cannot be executed
        RuntimeError: if `cmd` returncode is nonzero
        SubprocessError: other possible circumstances
    """
    # prepare workdir
    origdir = os.getcwd()
    try:
        os.makedirs(workdir)
    except OSError:
        # directory exists
        if purge_workdir:
            # that's a bit brutal, but saves to worry of links and subdirs
            shutil.rmtree(workdir)
            os.makedirs(workdir)
    os.chdir(workdir)
    # prepare out/err handling
    filename = kwargs.pop('stdout', outfile)
    if filename:
        kwargs['stdout'] = open(filename, 'w')
    filename = kwargs.pop('stderr', None)
    if filename:
        kwargs['stderr'] = open(filename, 'w')
    else:
        kwargs['stderr'] = subprocess.STDOUT
    # execute the command, make sure output is not streamed
    _cmd = parse_cmd(cmd)
    try:
        returncode = subprocess.call(_cmd, **kwargs)
        if returncode:
            LOGGER.critical('Execution of {:s} FAILED with exit status {:d}'.
                            format(_cmd, returncode))
            raise RuntimeError
    #
    except subprocess.SubprocessError:
        LOGGER.critical('Subprocess call of {:s} FAILED'.format(_cmd))
        raise
    #
    except (OSError, FileNotFoundError) as exc:
        LOGGER.critical("Abnormal termination: OS could not execute %s in %s",
                        _cmd, workdir)
        LOGGER.critical("If the command is a script ,"\
                        "check permissions and that is has a shebang!")
        raise
    #
    finally:
        # make sure we return to where we started from in any case!
        os.chdir(origdir)

def configure_logger(name, filename=None, verbosity=logging.INFO):
    """Get parent logger: logging INFO on the console and DEBUG to file.
    """
    if filename is None:
        filename = name+'.debug.log'
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    # may need this if running within ipython notebook, to avoid duplicates
    logger.propagate = False
    # console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(verbosity)
    # file handler with full debug info
    fh = logging.FileHandler(filename, mode='w')
    fh.setLevel(logging.DEBUG)
    # message formatting
    fileformat = logging.Formatter('%(name)s - %(levelname)s: %(message)s')
    consformat = logging.Formatter('%(levelname)7s: %(message)s')
    fh.setFormatter(fileformat)
    ch.setFormatter(consformat)
    # add the configured handlers
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

def get_logger(name, filename=None, verbosity=logging.INFO):
    """Return a named logger with file and console handlers.

    Get a `name`-logger. Check if it is(has) a parent logger.
    If parent logger is not configured, configure it, and if a child logger
    is needed, return the child.
    The check for parent logger is based on `name`: a child if it contains '.',
    i.e. looking for 'parent.child' form of `name`.
    A parent logger is configured by defining a console handler at `verbosity`
    level, and a file handler at DEBUG level, writing to `filename`.
    """
    parent = name.split('.')[0]
    if filename is None:
        filename = parent+'.debug.log'
    parent_logger = logging.getLogger(parent)
    if not parent_logger.handlers:
        configure_logger(parent, filename, verbosity)
    return logging.getLogger(name)


LOGGER = get_logger(__name__)

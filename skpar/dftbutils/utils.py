"""
General utility functions
"""
from subprocess import check_output, STDOUT, check_call
import os
import shutil
import shlex
import glob
import numpy as np
import logging

LOGGER = get_logger(__name__)

def write_output(out, outfile):
    """Write subprocess output to a file"""
    if outfile is not None:
        with open(outfile, 'w') as filep:
            filep.write(out)
            LOGGER.debug("Output is in {:s}.\n".format(outfile))

def call(cmd, outfile='out.log', **kwargs):
    """Execute `cmd` via `subproces.check_output`.

    `kwargs` are those of subprocess.check_output.
    `stderr` is forwarded to outfile unless in `kwargs`

    Exceptions shall be handled by caller.
    """
    if not isinstance(cmd, list):
        cmd = shlex.split(cmd)
        parsed_cmd = [cmd[0],]
        for i, word in enumerate(cmd[1:]):
            if word[0]=='$':
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
        cmd = parsed_cmd
    out=check_output(cmd, universal_newlines=True, stderr=STDOUT, **kwargs)
    outfile = kwargs.get('stdout', out.log)
    write_out(out, outfile)
    return out

def execute(cmd, workdir, outfile='out.log', purge_workdir=False, **kwargs):
    origdir = os.getcwd()
    try:
        os.mkdirs(workdir)
    except OSError:
        # directory exists
        if purge_workdir:
            # that's a bit brutal, but saves to worry of links and subdirs
            shutil.rmtree(workdir)
            os.mkdirs(workdir)
    os.chdir(workdir)
    try:
        output = call(cmd, **kwargs)
    #
    except subprocess.CalledProcessError as exc:
        LOGGER.critical('Execution of {:s} FAILED with exit status {:d}'.
                        format(cmd, exc.returncode))
        write_out(exc.output, outfile)
        raise
    #
    except OSError as exc:
        LOGGER.critical("Abnormal termination: OS could not execute %s in %s",
                        cmd, cdir)
        LOGGER.critical("If the command is a script,"\
                        " check permissions and that is has a shebang!")
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

def update(database, model, data):
    """Update model database with input data items.

    Args:
        database(obj): database, supporting get(), update() and a way to check
                       if item is contained
        model(str): model name
        data(dict): new data to be put in the model-own database
    """
    try:
        # assume model already exists in the DB
        modeldb = database.get_model(model)
        modeldb.update(data)
    except AttributeError:
        database.add_model(model, data)


class Database():
    """A database object providing several methods to access/modify the data.

    The public methods for accessing the internal database are:
        * update_modeldb -- add data to a model (create the model if missing)
        * query -- get data from a model
        * purge -- clear the internal database
    """
    def __init__(self):
        """Yield an object for data storage, NOT to be accessed directly."""
        self._database = {}

    def purge(self):
        """Clear the contents of DB"""
        self._database = {}

    def get_model(self, model):
        """Get a reference to a specific model in the database"""
        try:
            modelref = self._database[model]
            return modelref
        except KeyError:
            return None

    def add_model(self, model, data=None):
        """Add model to the database and return its reference.

        If data is not None, initialise the data for the model.
        If model happens to be already in the database and data is not None,
        its data is being replaced with the input argument.
        """
        if data is not None:
            self._database[model] = data
        else:
            if model not in self._database:
                self._database[model] = {}
        return self._database[model]

    def update(self, model, data):
        """Update the data of a given model in the database"""
        update(self, model, data)

    def get(self, model, item):
        """Get a particular data item from a particular model."""
        return self._database[model][item]

    def all(self):
        """Yield internal database object"""
        return self._database

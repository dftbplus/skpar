"""
Module for handling parameters in the context of SKF optimisation for DFTB via SKOPT.
The following assumptions are made:

    * whatever optimiser is used, it is unaware of the actual meaning of 
      the parameters
    * from the perspective of the optimiser, parameters are just a list of values.
    * the user must create an OrderedDict of parameter name:value pairs; 
      the OrderedDict eliminates automatically duplicate definitions of parameters,
      yielding the minimum possible number of degrees of freedom for the optimiser
    * the OrderedDictionary is built by parsing an skdefs.template file that
      contains parameter-strings (conveying the name, initial value and range).
    * skdefs.template is parsed by functions looking for a given format from which
      parameter-strings are extracted
    * the Class Parameter is initialised from a parameter-string.
    * a reduced skdefs.template is obtained, by removing the initial value and range
      from the input skdefs.template which is ready for creating the final skdefs
      file by string.format(dict(zip(ParNames,Parvalues)) substitution.
"""
import logging
from os.path import normpath, expanduser
from os.path import join as joinpath
from os.path import split as splitpath
import os.path
from skopt.core.utils import get_logger

DEFAULT_PARAMETER_FILE='current.par'

module_logger = get_logger('skopt.parameters')

def get_parameters(spec):
    """
    """
    params=[]
    for pardef in spec:
        # module_logger.debug(pardef)
        try:
            (pname, pdef), = pardef.items()
        except AttributeError:
            # pardef is cannot be itemised => assume just pname
            pname = pardef
            pdef  = ""
        try:
            parstring = " ".join([pname,] + pdef.split())
        except AttributeError:
            # pdef turns out to not be a string
            try:
                # assume it is a list of floats
                parstring = " ".join([pname,] + ["{}".format(v) for v in pdef])
            except TypeError:
                # pdef not iterable; assume it is a single float
                parstring = " ".join([pname, str(pdef)])
        # module_logger.debug(parstring)
        newpar = Parameter(parstring)
        # module_logger.debug(newpar)
        params.append(newpar)
    return params

class Parameter(object):
    """
    A parameter object, that is initialised from a string.

    ParmaeterName InitialValue MinValue Maxvalue [ParameterType]
    ParmaeterName MinValue Maxvalue [ParameterType]
    ParmaeterName InitialValue [ParameterType]
    ParmaeterName [ParameterType]

    ParameterName must be alphanumeric, allowing _ too.
    Iinit/Min/MaxValue can be integer or float
    ParameterType is optional (float by default), and indicated 
    by either 'i'(int) or 'f'(float)
    White space separation is mandatory.
    """
    # permitted parameter types
    typedict = {'i': int, 'f': float}

    def __init_from_kwargs(self, name, **kwargs):
        """
        Look for one obligatory argument -- name, and 
        the rest is optional.
        """
        self.name = name
        for key in ['value', 'minv', 'maxv']:
            _val = kwargs.get(key, None)
            setattr(self, key, _val)

    def __init_from_string(self, parameterstring):
        """
        assume S is a string of one of the following forms:
        ParName initial min max partype
        ParName min max partype
        ParName initial partype
        ParName partype
        Permit only 'i' or 'f' for partype and make it optional
        """
        # take away spaces, check format consistency and get type
        assert isinstance(parameterstring, str)
        words = parameterstring.split()
        #module_logger.debug(len(words))
        if len(words) > 1:
            if words[-1] in list(Parameter.typedict.keys()):
                self.ptype = Parameter.typedict[words[-1]]
                words = words[:-1]
            else:
                self.ptype = float
            # extract data, converting values to appropriate type
            self.name = words[0]
            # the conversion from words to float to type allows one to do
            # %(name,1.0,2.0,3.0)i; otherwise map(int,'3.0') gives valueerror
            floats = list(map(float, words[1:]))
            try:
                self.value, self.minv, self.maxv = list(map(self.ptype, floats))
            except ValueError:
                try:
                    self.minv, self.maxv = list(map(self.ptype, floats))
                    self.value = 0.
                except ValueError:
                    # note at this stage value is a single item, not a list
                    self.value = list(map(self.ptype, floats))[0]
                    self.minv = None
                    self.maxv = None
                except:
                    print ("Parameter string not understood: {}".format(parstring))
            except:
                print ("Parameter string not understood: {}".format(parstring))
        else:
            self.ptype = float
            self.name  = words[0]
            self.value = None
            self.minv  = None
            self.maxv  = None

    def __init__(self, string, **kwargs):
        """wrapper init method

        The whole thing became patchy. It needs a careful revision.
        """
        if string.split() == [string,] and kwargs:
            self.__init_from_kwargs(string, **kwargs)
        else:
            self.__init_from_string(string)

    def __repr__(self):
        return "Parameter {name} = {val}, range=[{minv},{maxv}]". \
            format(name=self.name, val=self.value, minv=self.minv, maxv=self.maxv)


def read_par_template(fileobj):
    """
    Returns a single string joining the lines of the fileobject,
    including line breaking chars etc.
    fileobj is either a file ID or a filename (possibly including path).
    """
    with open(fileobj, 'r') as fh:
        ss = "".join(fh.readlines())
    return ss

def update_template(template, pardict):
    """Update a template string with parameter values in placeholders.
    
    Assume %(Name)[type] represents a placeholder.
    Substitute placeholders with values from pardict.
    Placeholders in commented lines (first non-white space char being #)
    are untouched.
    Return the updated string.
    """
    assert isinstance(pardict, dict)
    #module_logger.debug("Updating template according to {}".format(pardict))
    lines_in = template.split('\n')
    #module_logger.debug(lines_in)
    lines_out = []
    for line in lines_in:
        if line.strip().startswith('#'):
            # do not touch comments, even if they have a placeholder
            lines_out.append(line)
        else:
            lines_out.append(line % pardict)
    return "\n".join(lines_out)

def write_parameters(fileobj, template, parameters, parnames=None):
    """Update a template with actual parameter values and write to file.

    The `template` is a string with placeholders, which are updated
    from the `pardict` dictionary, and the result is written to `fileobj`.
    Placeholders should be Python's old string formatting: %(Name)Type
    """
    try:
        pardict = dict([(p.name, p.value) for p in parameters])
    except AttributeError:
        pardict = dict([(name, val) for (name, val) in zip(parnames, parameters)])
        #module_logger.critical(('Cannot update parameters. Ensure parameters are objects',
        #        'with name and value attributes'))
    updated = update_template(template, pardict)
    # nota bene: since template contains '\n', updated contains them too
    with open(fileobj, 'w') as fh:
        fh.writelines(updated)

def update_parameters(parameters, iteration=None, *args, **kwargs):
    """Update relevant file(s) with new parameter values.

    ARGS:
        parameters (list): Either a list of floats, or a list of objects
            (each having .value and .name attributes)
        parnames (list): If `parameters` is a list of floats, then 
            parnames is the list of corresponding names.
        parfile (string): Filename where the list of parameters is written
            in a very plain format (one or two column, as per the absence 
            or presence of parameter names.
        templates (list): List of ascii filenames containing placeholders
            for inserting parameter values. The place holders must follow
            the old string formatting of Python: $(ParameterName)ParameterType.
    """
    parfile   = kwargs.get('parfile', DEFAULT_PARAMETER_FILE)
    templates = kwargs.get('templates', None)
    parnames  = kwargs.get('parnames', None)
    logger    = module_logger
    #logger.debug('Updating parameters')
    #logger.debug(parameters)
    #logger.debug(iteration)
    #logger.debug(parfile)
    #logger.debug(parnames)
    #logger.debug(templates)
    # Update parameter file
    parout = []
    # Overwrite parnames with the names of the parameter objects, if available
    try:
        parnames  = [p.name  for p in parameters]
    except AttributeError:
        # parameters is a list of floats
        assert all([isinstance(p, (float, int)) for p in parameters]), "{}".format(parameters)
        # test consistency if parnames is given (may be None)
        if parnames:
            assert len(parameters) == len(parnames)
        pass
    except TypeError:
        assert parameters is None
        parnames = None
        pass
    # Prepare the values to write
    try:
        parvalues = [p.value for p in parameters]
    except AttributeError:
        parvalues = parameters
    except TypeError:
        assert parameters is None
        parvalues = None
        pass
    # Prepare the output and write
    if parnames:
        parout = ["{:>20s}  {}".format(name, value) 
                for (name, value) in zip(parnames, parvalues)]
    else:
        try:
            parout = ["{}".format(p) for p in parvalues]
        except TypeError:
            assert parvalues is None
            parout = ""
    with open(parfile, 'w') as fp:
        if iteration is not None:
            fp.writelines('#{}\n'.format(iteration))
        fp.writelines('\n'.join(parout))
    # Udpate (fill in) template files
    if templates:
        assert (parnames is not None)
        for ftempl in templates:
            fin = normpath(expanduser(ftempl))
            # remove 'template.' tag from filename to form destination
            # make sure you do this on the filename, not on the path!
            path, name = splitpath(fin)
            fout = normpath(joinpath(path, name.replace('template.','')))
            # read template and substitute values for placeholders
            # make sure you do not substitute in comments
            templ = read_par_template(fin)
            write_parameters(fout, templ, parvalues, parnames)

"""***Parameters***

Module for handling parameters in the context of optimisation.

The following assumptions are made:

    * parameters have no meaning to the optimiser engine
    * for the optimiser, parameters are just a list of values to be manipulated
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
import os.path
from skpar.core.utils import get_logger

LOGGER = get_logger('__name__')

def get_parameters(userinp):
    """Parse user input for definitions of parameters.

    The definitions should be of the form ('name', 'optionally_something').
    The optional part could in principle be one or more str/float/int.
    """
    params = []
    for pardef in userinp:
        try:
            # Due to yaml/json representation, each parameter definition is a
            # dictionary on its own, with one item. Using (key, val), we
            # extract the one and only item in this dict.
            (pname, pdef), = pardef.items()
        except AttributeError:
            # pardef cannot be itemised => assume just pname
            pname = pardef
            pdef = ""
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
        # initialise from string
        newpar = Parameter(parstring)
        params.append(newpar)
    return params

class Parameter(object):
    """
    A parameter object, that is initialised from a string.

    ParameterName InitialValue MinValue Maxvalue [ParameterType]
    ParameterName MinValue Maxvalue [ParameterType]
    ParameterName InitialValue [ParameterType]
    ParameterName [ParameterType]

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
        return "Parameter {name} = {val}, range=[{minv},{maxv}]".\
            format(name=self.name, val=self.value,
                   minv=self.minv, maxv=self.maxv)


def substitute_template(parameters, parnames, templatefile, resultfile):
    """Substitute a template with actual parameter values.

    Args:
        parameters (list): Parameter list, items being either floats or objects
            with .value and .name attributes.
        parnames (list): If `parameters` is a list of floats, then
            parnames is the list of corresponding names.
        templatefile (str): Name of template file with substitution patterns.
        resultfile (str): Name of file to contain the substituted result.
    """
    with open(templatefile, 'r') as fin:
        template = fin.read()
    try:
        pardict = dict([(p.name, p.value) for p in parameters])
    except AttributeError:
        pardict = dict([(name, val)
                        for (name, val) in zip(parnames, parameters)])
    updated = update_template(template, pardict)
    with open(resultfile, 'w') as fout:
        fout.write(updated)


def update_template(template, pardict):
    """Makes variable substitution in a template.

    Args:
        template (str): Template with old style Python format strings.
        pardict (dict): Dictionary of parameters to substitute.

    Returns:
        str: String with substituted content.
    """
    return template % pardict


def update_parameters(workroot, templates, parameters, parnames=None):
    """Update relevant templates with new parameter values.

    Args:
        workroot (str): Root working directory, template names are relative
            to this directory.
        templates (list): List of ascii filenames containing placeholders
            for inserting parameter values. The place holders must follow
            the old string formatting of Python: %(ParameterName)ParameterType.
        parameters (list): Either a list of floats, or a list of objects
            (each having .value and .name attributes)
        parnames (list): If `parameters` is a list of floats, then
            parnames is the list of corresponding names.
    """
    # Overwrite parnames with the names of the parameter objects, if available
    try:
        parnames = [p.name  for p in parameters]
    except AttributeError:
        # parameters is a list of floats; double check!
        assert all([isinstance(p, (float, int)) for p in parameters]), "{}".format(parameters)
        # test consistency if parnames is given (may be None)
        if parnames is not None:
            assert len(parameters) == len(parnames)
    except TypeError:
        assert parameters is None
        parnames = None

    # Prepare the values to write
    try:
        parvalues = [p.value for p in parameters]
    except AttributeError:
        parvalues = parameters
    except TypeError:
        assert parameters is None
        parvalues = None

    # Udpate (fill in) template files
    if templates:
        for ftempl in templates:
            assert parnames is not None
            fin = os.path.normpath(os.path.join(workroot, ftempl))
            path, templname = os.path.split(fin)
            name = templname.replace('template.', '')
            fout = os.path.join(path, name)
            substitute_template(parvalues, parnames, fin, fout)

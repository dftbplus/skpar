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
from collections import OrderedDict
import re

logger = logging.getLogger(__name__)

class Parameter(object):
    """A parameter object, that is initialised from a string.
    
    The format is:

        %(ParameterName), or %(ParameterName)ParameteterType

        or,
        %(ParameterName, InitialValue),

        or,
        %( ParmaeterName, MinValue, Maxvalue )

        or,
        %( ParmaeterName, InitialValue, MinValue, Maxvalue )

    ParameterType is indicated by either 'i'(int) or 'f'(float) and is optional,
    default is 'f'
    Iinit/Min/MaxValue can be integer or float
    ParameterName must be alphanumeric, allowing _ too.
    Spaces are optional within the brackets, but
    NOTABENE: NO space is allowed between %( nor between )i or )f.
    """
    # permitted parameter types
    typedict = {'i': int, 'f': float}

    def __init__(self, parameterstring):
        """
        assume S is a string of the form:
        %(ParName), or %(ParName)ParType, or
        %(ParName, dflt, min, max)ParType, or
        %(ParName, min, max)ParType
        Permit only i(int) or f(float) values
        """
        # take away spaces, check format consistency and get type
        assert isinstance(parameterstring, str)
        # remove all white space
        parstr = "".join(parameterstring.split())
        assert parstr[0:2] == '%('
        if parstr[-1] == ')':
            # default type
            self.ptype = float
        else:
            assert parstr[-2] == ')'
            assert parstr[-1] in list(Parameter.typedict.keys())
            self.ptype = Parameter.typedict[parstr[-1]]
            # remove type
            parstr = parstr[:-1]
        # remove %( and )
        parstr = parstr[2:-1]

        # extract data, converting values to appropriate type
        words = parstr.split(',')
        self.name = words[0]
        # the conversion from words to float to type allows one to do
        # %(name,1.0,2.0,3.0)i; otherwise map(int,'3.0') gives valueerror
        floats = list(map(float, words[1:]))
        if len(floats) == 0: # name only
            self.value = None
            self.minv = None
            self.maxv = None
        if len(floats) == 1: # default_value
            self.value, = list(map(self.ptype, floats))
            self.minv = None
            self.maxv = None
        if len(floats) == 2: # min, max
            self.value = None
            self.minv, self.maxv = list(map(self.ptype, floats))
        if len(floats) == 3: # dflt, min, max
            self.value, self.minv, self.maxv = list(map(self.ptype, floats))
        try:
            if self.minv > self.maxv:
                self.minv, self.maxv = self.maxv, self.minv
        except TypeError:
            # minv, maxv are None if not provided
            pass

    def __repr__(self):
        return "Parameter {name} = {val}, range=[{minv},{maxv}]". \
            format(name=self.name, val=self.value, minv=self.minv, maxv=self.maxv)


def update_template(template, pardict):
    """Update a template string with parameter values in placeholders.
    
    Return the updated template.
    """
    assert isinstance(pardict, dict)
    lines_in = template.split('\n')
    lines_out = []
    for line in lines_in:
        if line.strip().startswith('#'):
            # do not touch comments, even if they have a placeholder
            lines_out.append(line)
        else:
            lines_out.append(line % pardict)
    return "\n".join(lines_out)

def write_parameters(fileobj, template, pardict):
    """Update a template with actual parameter values and write to file.

    The `template` is a string with placeholders, which are updated
    from the `pardict` dictionary, and the result is written to `fileobj`.
    """
    if isinstance(fileobj, str):
        fileobj = open(fileobj, 'w')
    updated = update_template(template, pardict)
    # nota bene: since template contains '\n', updated contains them too
    fileobj.writelines(updated)

def read_par_template(fileobj):
    """
    Returns a single string joining the lines of the fileobject,
    including line breaking chars etc.
    fileobj is either a file ID or a filename (possibly including path).
    """
    if isinstance(fileobj, str):
        fileobj = open(fileobj)

    return "".join(fileobj.readlines())

def get_par_template(fileobj):
    """Read parameter template; return it with any necessary modifications.

    Since SKGEN's skdefs.py is a python file, it uses dict and list constructs.
    For parameter placeholders we use the old string formatting, as the new one
    relies on {} (as dictionaries) and likely requires more elaborate parsing.
    Therefore the parameters placeholders are defined as %(Name), with or without
    specifying the type of the value (permitted here are f and i).
    The necessary modification of the template is to append 'f' to those
    parameter declarations that omit the type, i.e. %(Name) becomes %(Name)f.
    """
    template = read_par_template(fileobj)
    # no parsing at the moment.
    return template


# OLD STUFF!
def stripall(ss):
    """
    Assume SS is a string or a list of strings and
    return the same but stripped off all whitespaces,
    leading, trailing and in between, based on regular expressions.
    why not "".join(split()) on ss? but re?
    """
    if isinstance(ss, str):
        return re.sub(r'\s*', '', ss)
    else:
        return [re.sub(r'\s*', '', s) for s in ss]


def parse_par_template(pardefs):
    """
    Take the input pardefs string and return a list of substings,
    each of which conveys the info related to a single parameter.
    Each of the substrings that are returned is assumed to have
    the format described in the Parameter Class above.
    However, currently, we have hardcoded the format here, rather
    than reusing whatever is defined in the Parameter class....
    """
    # get all substrings of the form
    # %(ParName, initialvalue, minvalue, maxvalue)ParType
    pattern = re.compile(r"%\(.+?\)[fi]")

    # The pattern below serves to remove the optional initial value, and
    # the min and max values from the output string template, 
    # leaving only %(ParName)ParType format strings
    # note the use of named group in the matching pattern, so later we
    # form the replacement by selecting only the matching elements of interest
    grouppattern = re.compile(r'(?P<pOpen>%[(])\s*' +  # %( 
                              r'(?P<pName>\w+)\s*,(?P<pData>.+?)' +  # Parameter name and Data
                              r'(?P<pClose>[)][fi])')  # )i or )f closing/type definition
    # this is how the output should look like %(ParName)[fi]
    outpattern = re.compile(r'%\(\w+\)[fi]')

    # it may be nice to check if we're not already given list of lines, but how?
    lines_in = pardefs.split('\n')
    lines_out = []
    parstr = []

    for line in lines_in:
        if line.strip().startswith('#'):
            line_out = line
        else:
            newparstr = pattern.findall(line)

            if newparstr is not None:
                parstr.extend(newparstr)

            try:
                line_out = re.sub(grouppattern,
                                  "\g<pOpen>\g<pName>\g<pClose>",
                                  line)
            except AttributeError:
                line_out = line

        lines_out.append(line_out)

    reduced_pardefs = '\n'.join(lines_out)
                              
    # note that parstr is a list of strings, 
    # each string describing one parameter
    parstr = stripall(parstr)

    if parstr == []:
        logger.warning("The given parameter template contains no parameter definitions")
    else:
        found = re.findall(outpattern, reduced_pardefs)
        assert len(found) == len(parstr), "ERROR: given parameter string was incorrectly parsed."

    parameters = [Parameter(ps) for ps in parstr]

    # get back the neat skdefs template and the list of Parameter objects
    return reduced_pardefs, parameters


def read_parameters(fileobj):
    """
    encapsulates reading the file containing the skdefs.template
    and parameter info, and the parsing of the parameter info;
    :param fileobj: fileobj or a string filename
    :return: a tuple, consisting of
            0) a string (skdefs_template_out), which is the template
            with format placeholders for the values of the parameters,
            but no parameter info anymore,
            1) an OrderedDict of Par.Name,Par.Value
            2) an OrderedDict of Par.Name,(Par.min, Par.max)
    """
    par_template_out, parameters = parse_par_template(read_par_template(fileobj))
    pardict = OrderedDict([(p.name, p.value) for p in parameters])
    parrange = OrderedDict([(p.name, (p.minv, p.maxv)) for p in parameters])
    return par_template_out, pardict, parrange

    
def update_pardict(pardict, values):
    for p,v in zip(list(pardict.keys()),values):
        pardict[p] = v
    return pardict


def report_parameters(iteration, pardict, tag=''):
    """
    """
    logger.info('')
    logger.info('{0}Iteration {1}'.format(tag, iteration))
    logger.info('============================================================')
    for key,val in list(pardict.items()):
        logger.info('\t{name:<15s}:\t{val:n}'.format(name=key,val=val))


def write_parameters_old(par_template, pardict, fileobj):
    """
    Write parameters to file, updating the named parameter placeholders
    in the given template with the parameter values supplied in the pardict
    :param fileobj: sting (filename) or file object to write to
    :param par_template: string with named placeholders for formatting the
                         supplied values of parameters
    :param pardict: ordered dictionary of (parameter_name,parameter_value) pairs
    :return: none
    """
    assert isinstance(pardict, OrderedDict)
    if isinstance(fileobj, str):
        fileobj = open(fileobj, 'w')
    lines_in = par_template.split('\n')
    lines_out = []
    for line in lines_in:
        if line.strip().startswith('#'):
            lines_out.append(line)
        else:
            lines_out.append(line % pardict)

    fileobj.writelines('\n'.join(lines_out))



if __name__ == "__main__":

    print ("Testing skdefs.template parsing (looking for ./example SKOPT/test_skdefs.template file):")
    print ("------------------------------------------------------------------------")
    skdefs = read_par_template("./example SKOPT/test_skdefs.template")
    reduced_skdefs, parameters = parse_par_template(skdefs)
    print()
    print ('Reduced skdefs.template (no info of parameter values, only formatting slots):')
    print (reduced_skdefs)

    print()
    print ('Extracted parameters:')
    for p in parameters:
        print (p)

    print()
    print ('Writing skdefs output string based on the supplied initial values:')
    # NOTABENE: we use OrderedDict which automatically eliminates duplicate parameters
    # at the same time, the format dictionary automatically uses the same value
    # no matter how many times we have the same parameter defined.
    skdefs, skpar, skparrange = read_parameters("./example SKOPT/test_skdefs.template")
    write_parameters(skdefs, skpar, "./example SKOPT/test_skdefs.py")
    report_parameters(None, skpar)

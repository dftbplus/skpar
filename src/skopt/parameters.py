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


class Parameter(object):
    """
    A parameter object, that is initialised from a string
    with the following format:

    %( ParmaeterName, InitialValue, MinValue, Maxvalue )ParameterType

    Iinit/Min/MaxValue can be integer or float
    ParameterName must be alphanumeric allowing _ too.
    ParameterType is indicated by either 'i'(int) or 'f'(float)
    Spaces are optional.
    NOTABENE: NO space is allowed between %( nor between )i or )f.
    TODO: Eliminate the need to have a default value!
    """
    # permitted parameter types
    typedict = {'i': int, 'f': float}

    def __init__(self, parameterstring):
        """
        assume S is a string of the form:
        %(ParName, dflt, min, max)ParType
        Permit only i(int) or f(float) values
        """
        # take away spaces, check format consistency and get type
        assert isinstance(parameterstring, basestring)
        parstr = parameterstring.strip()
        assert parstr[0:2] == '%('
        assert parstr[-2] == ')'
        assert parstr[-1] in Parameter.typedict.keys()
        self.ptype = Parameter.typedict[parstr[-1]]

        # extract data, converting values to appropriate type
        words = parstr[2:-2].split(',')
        self.name = words[0]
        # the conversion from words to float to type allows one to do
        # %(name,1.0,2.0,3.0)i; otherwise map(int,'3.0') gives valueerror
        floats = map(float, words[1:])
        self.value, self.minv, self.maxv = map(self.ptype, floats)

    def __repr__(self):
        return "Parameter {name} = {val}, range=[{minv},{maxv}]". \
            format(name=self.name, val=self.value, minv=self.minv, maxv=self.maxv)


def stripall(ss):
    """
    Assume SS is a string or a list of strings and
    return the same but stripped off all whitespaces,
    leading, trailing and in between, based on regular expressions.
    """
    if isinstance(ss, str):
        return re.sub(r'\s*', '', ss)
    else:
        return [re.sub(r'\s*', '', s) for s in ss]


def read_par_template(fileobj):
    """
    Returns a single string joining the lines of the fileobject,
    including line breaking chars etc.
    fileobj is either a file ID or a filename (possibly including path).
    """
    if isinstance(fileobj, str):
        fileobj = open(fileobj)

    return "".join(fileobj.readlines())


def parse_par_template(pardefs, log=logging.getLogger(__name__)):
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
    pattern = re.compile(r'%\(.+?\)[fi]')
    try:
        parstr = re.findall(pattern, pardefs)
    except:
        parstr = ""
    # note that parstr is a list of strings, 
    # each string describing one parameter
    parstr = stripall(parstr)

    # update the pardefs template by eliminating the initial,min,max values
    # and leaving only %(ParName)ParType format strings
    # note the use of named group in the matching pattern, so later we
    # form the replacement by selecting only the matching elements of interest
    grouppattern = re.compile(r'(?P<pOpen>%[(])\s*' +  # %( 
                              r'(?P<pName>\w+)\s*,.+?' +  # Parameter name
                              r'(?P<pClose>[)][fi])')  # )i or )f closing/type definition
    try:
        assert isinstance(pardefs, basestring)
        reduced_pardefs = re.sub(grouppattern,
                                "\g<pOpen>\g<pName>\g<pClose>",
                                pardefs)
    except AttributeError:
        reduced_pardefs = pardefs

        # check integrity
    outpattern = re.compile(r'%\(\w+\)[fi]')
    if parstr == "":
        log.warning("The given parameter template contains no parameter definitions")
    else:
        found = re.findall(outpattern, reduced_pardefs)
        assert len(found) == len(parstr), "ERROR: given parameter string was incorrectly parsed."

    parameters = [Parameter(ps) for ps in parstr]

    # get back the neat skdefs template and the list of Parameter objects
    return reduced_pardefs, parameters


def read_parameters(fileobj, log=logging.getLogger(__name__)):
    """
    encapsulates reading the file containing the skdefs.template
    and parameter info, and the parsing of the parameter info;
    :param fileobj: fileobj or a string filename
    :param log: logger for messages from the parser of fileobj
    :return: a tuple, consisting of
            0) a string (skdefs_template_out), which is the template
            with format placeholders for the values of the parameters,
            but no parameter info anymore,
            1) an OrderedDict of Par.Name,Par.Value
            2) an OrderedDict of Par.Name,(Par.min, Par.max)
    """
    par_template_out, parameters = parse_par_template(read_par_template(fileobj), log)
    pardict = OrderedDict([(p.name, p.value) for p in parameters])
    parrange = OrderedDict([(p.name, (p.minv, p.maxv)) for p in parameters])
    return par_template_out, pardict, parrange

    
def update_pardict(pardict, values):
    for p,v in zip(pardict.keys(),values):
        pardict[p] = v
    return pardict


def report_parameters(iteration, pardict, log, tag=''):
    """
    """
    log.info('')
    log.info('{0}Iteration {1}'.format(tag, iteration))
    log.info('============================================================')
    for key,val in pardict.items():
	log.info('\t{name:<15s}:\t{val:n}'.format(name=key,val=val))


def write_parameters(par_template, pardict, fileobj):
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
    fileobj.writelines(par_template % pardict)



if __name__ == "__main__":

    log=logging.getLogger("SKOPT")
    logging.basicConfig(level=logging.DEBUG)
    print ("Testing Parameter Class:")
    print ("------------------------")

    s1 = "%(New,1.,2.,3.)i"
    print ('Test string 1: ' + s1)
    p1 = Parameter(s1)
    print (p1)

    s2 = "%(Newer,1.,2.,3.)f"
    print ('Test string 2: ' + s2)
    p2 = Parameter(s2)
    print (p2)

    print ("Testing skdefs.template parsing (looking for ./example SKOPT/test_skdefs.template file):")
    print ("------------------------------------------------------------------------")
    skdefs = read_par_template("./example SKOPT/test_skdefs.template")
    reduced_skdefs, parameters = parse_par_template(skdefs)
    print
    print ('Reduced skdefs.template (no info of parameter values, only formatting slots):')
    print (reduced_skdefs)

    print
    print ('Extracted parameters:')
    for p in parameters:
        print p

    print
    print ('Writing skdefs output string based on the supplied initial values:')
    # NOTABENE: we use OrderedDict which automatically eliminates duplicate parameters
    # at the same time, the format dictionary automatically uses the same value
    # no matter how many times we have the same parameter defined.
    skdefs, skpar, skparrange = read_parameters("./example SKOPT/test_skdefs.template")
    write_parameters(skdefs, skpar, "./example SKOPT/test_skdefs.py")
    report_parameters(None, skpar, log)

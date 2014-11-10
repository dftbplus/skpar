"""
Module for handling parameters in the context of SKF optimisation for DFTB via SKOPT.
The following assumptions are made:
    * whatever optimiser is used, it is unaware of the actual meaning of 
      the parameters
    * from the perspective of the optimiser, parameters are just a list of values.
    * the user must create an OrderedDict of parameter name:value pairs; 
      the OrderedDict eliminates atuomatically duplicate definitions of parameters,
      yeilding the minimum possible number of degrees of freedom for the optimiser
    * the OrderedDictionary is built by parsing an skdefs.template file that
      contains parameter-strings (conveying the name, initial value and range).
    * skdefs.template is parsed by functions looking for a given format from which
      parameter-strings are extracted
    * the Class Parameter is initialised from a parameter-string.
    * a reduced skdefs.template is obtained, by removing the initial value and range
      from the input skdefs.template which is ready for creating the final skdefs
      file by string.format(dict(zip(ParNames,Parvalues)) substitution.
"""
import os, sys, logging
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
    """
    # permitted parameter types
    typedict = {'i':int, 'f':float}
    
    def __init__(self,S):
        """
        assume S is a string of the form:
        %(ParName, dflt, min, max)ParType
        Permit only i(int) or f(float) values
        """
        # take away spaces, check format consistency and get type
        parStr = S.strip()
        assert parStr[0:2] == '%('
        assert parStr[-2] == ')'
        assert parStr[-1] in Parameter.typedict.keys()
        self.ptype = Parameter.typedict[parStr[-1]]
        
        # extract data converting values to appropriate type
        words = parStr[2:-2].split(',')
        self.name = words[0]
        # the conversion from words to float to type allows one to do
        # %(name,1.0,2.0,3.0)i; otherwise map(int,'3.0') gives valueerror
        floats = map(float,words[1:])
        self.value, self.minv, self.maxv = map(self.ptype,floats)
 
    def __repr__(self):
        return "Parameter {name} = {val}, range=[{minv},{maxv}]".\
                format(name=self.name, val=self.value, minv=self.minv, maxv=self.maxv)

def stripall(SS):
    """
    Assume SS is a string or a list of strings and
    return the same but stripped off all whitespaces,
    leading, trailing and inbetween, based on regular expressions.
    """
    if isinstance(SS, str):
        return re.sub(r'\s*','',SS)
    else:
        return [re.sub(r'\s*','',s) for s in SS]
    
    
def read_skdefs(fileobj):
    """
    Returns a single string joining the lines of the fileobject,
    including line breaking chars etc.
    fileobj is either a file ID or a filename (possibly including path).
    """
    if isinstance(fileobj, str):
        fileobj = open(fileobj)

    return "".join(fileobj.readlines())

def write_skdefs(fileobj,skdefs):
    if isinstance(fileobj, str):
        fileobj = open(fileobj,'w')

    fileobj.writelines(skdefs)


def get_skpar(skdefs, log=logging.getLogger(__name__)):
    """
    Take the input skdefs string and return a list of substings,
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
        parstr = re.findall(pattern, skdefs)
    except:
        parstr = ""
    # note that parstr is a list of strings, 
    # each string describing one parameter
    parstr = stripall(parstr)
    
    # update the skdefs template by eliminating the initial,min,max values
    # and leaving only %(ParName)ParType format strings
    # note the use of named group in thematching patern, so later we
    # form the replacement by selecting only the matching elements of interest
    grouppattern = re.compile(r'(?P<pOpen>%[(])\s*'+        # %( 
                              r'(?P<pName>\w+)\s*,.+?'+     # Parameter name
                              r'(?P<pClose>[)][fi])')       # )i or )f closing/type definition
    try:
        skdefsout = re.sub(grouppattern,
                           '\g<pOpen>\g<pName>\g<pClose>',
                           skdefs)
    except AttributeError:
        skdefsout = skdefs 
        
    # check integrity
    outpattern = re.compile(r'%\(\w+\)[fi]')
    if parstr == "":
        log.warning("The given skdefs templeate contains no parameter definitions")
    else:
        found = re.findall(outpattern, skdefsout)
        assert len(found)==len(parstr), "ERROR: given skdefs string was incorrectly parsed."
    
    # get back the neat skdefs template and the list of parameter strings
    return skdefsout, parstr


if __name__ == "__main__":
   
    print ("Testing Parameter Class:")
    print ("------------------------")

    s1 = "%(New,1.,2.,3.)i"
    print ('Test string 1: '+s1)
    p1 = Parameter(s1)
    print (p1)

    s2 = "%(Newer,1.,2.,3.)f"
    print ('Test string 2: '+s2)
    p2 = Parameter(s2)
    print (p2)
   
    print ("Testing skdefs.template parsing (looking for ./example SKOPT/test_skdefs.template file):")
    print ("------------------------------------------------------------------------")
    skdefs = read_skdefs("./example SKOPT/test_skdefs.template")
    reduced_skdefs, parstr = get_skpar(skdefs)
    print
    print ('Reduced skdefs.template (no info of parameter values, only formatting slots):')
    print (reduced_skdefs)

    print
    print ('Extracted parameter strings:')
    for ps in parstr:
	print ps, Parameter(ps)

    print
    print ('Writing skdefs output string based on the supplied initial values:')
    # NOTABENE: we use OrderedDict which automatically eliminates duplicate parameters
    #           at the same time, the format dictionary atuomatically uses the same value
    #           no matter how many times we have the same parameter defined.
    pardict = OrderedDict([(p.name,p.value) for p in [Parameter(s) for s in parstr]])
    skdefsout = reduced_skdefs % pardict
    print (skdefsout)

    print ('Writing skdefs file. (check ./example SKOPT/test_skdefs.out)')
    write_skdefs('./example SKOPT/test_skdefs.out',skdefsout)

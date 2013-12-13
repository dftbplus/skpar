"""
## From skdefs-*.py to skdefs.py

This module makes it possible to encode which parameters should be optimized and what is their range
(e.g. initial range for the PSO) within a file, e.g. `skdefs.py`, without changing the structure or 
interpreter of the conventional `skdefs.py` input to `skgen`.  

To specify a parameter, one must input a 2-tuple or 3-tuple instead of a single value in the 'skdef.py'. 
These tuples are interpreted as (lower,upper,[index]) -- the lower and upper initial range of the parameter 
to be optimized, and an optional parameter index. The parameter index enables one to group two or more 
parameters and vary them with the same value (effectively having one and the same variable representative 
of several parameters). This is important if one wants to optimize a single value e.g. for confinement radii
of _s_ and _p_, but a different optimized value for the _d_ orbital.

Therefore, we must be able to:

1. read the skdefs and look for parameters that are specified as tupples (strict format is assumed for `skdefs*.py`)
2. create a mapping between a specific parameter in the sk configuration and a parameter of the optimizer
3. update (assign a unique value to) the parameters in the sk configuration (i.e. propagating the optimal values)
4. write a new `skdefs.py` for use by `skgen`, i.e. all parameters have single value assigned to them; 
    this last step is not needed if we integrate the optimization within the `skgen` wrapper, since we can directly 
    access the configurations.
"""
# Modified copy of .../skgen/bin/skgen's get_elemdefs which reads the skdefs.py and 
# initializes the classes in skgen.sk; 
# The only modification is that config_file is now an input argument (lower cased to highlight the difference)
# This routine will be redundant, if we merge the modules in skgen/src/ but the corresponding
# routine in skgen/bin/skgen must be updated with the modification done here.
def get_elemdefs(config_file,extraincludes):
    ### --------------------------------------------------------------------------------
    ### to disappear
    # this section should disappear once we pull all modules in the skgen/src/ directory
    # and only 'import sk' will be left.
    import sys,os
    if os.path.isdir(os.path.join(os.path.expanduser("~"),'Desktop/Dropbox/')):
        skpath = os.path.join(os.path.expanduser("~"),'Desktop/Dropbox/Projects/QMEM/DFTB+/SKF/skgen/src')
    elif os.path.isdir(os.path.join(os.path.expanduser("~"),'Dropbox/')):
        skpath = os.path.join(os.path.expanduser("~"),'Dropbox/Projects/QMEM/DFTB+/SKF/skgen/src')
    else:
        skpath = None
        
    try:
        sys.path.append(skpath)
        import skgen.sk as sk
    except:
        raise('ERROR: Cannot import sk. Cannot continue.')
    ### end to disappear 
    ### --------------------------------------------------------------------------------
    atomconfigs = {}
    skbases = {}
    compressions = {}
    elemdirs = {}
    includedirs = [ ".", ] + extraincludes
    for includedir in includedirs:
        fname = os.path.join(includedir, config_file)
        fp = open(fname, "r")
        txt = fp.read()
        fp.close()
        globalvars = {"SlaterBasis": sk.SlaterBasis,
                      "AtomConfig": sk.AtomConfig,
                      "Compression": sk.Compression, }
        localvars = {}
        try:
            exec(txt, globalvars, localvars)
        except Exception as ex:
            sys.exit("Error during executing '{}':\n{}".format(fname, ex))
        if not "atomconfigs" in localvars or not "skbases" in localvars:
            sys.exit("File '{}' must contain variables ".format(fname)
                     +  "atomconfigs and skbases")
        newatoms = localvars["atomconfigs"]
        newsks = localvars["skbases"]
        if not isinstance(newatoms, dict) or not isinstance(newsks, dict):
            sys.exit("Variables atomconfigs and skbases in file "
                     + "'{}' must be of type dictionary".format(fname))
        newatomkeys = set(newatoms)
        newskkeys = set(newsks)

        # Get compression (optional)
        if "compressions" in localvars:
            newcompressions = localvars["compressions"]
            if not isinstance (newcompressions, dict):
                sys.exit("Variable compressions in file "
                         + "'{}' must be of type dictionary".format(fname))
        else:
            newcompressions = {}

        # Check compatibility of settings
        if newatomkeys != newskkeys:
            sys.exit("Differing keys in atomconfigs and skbases in file "
                     + "'{}'".format(fname))
        if set(newcompressions) - newatomkeys:
            sys.exit("Found compression definition for an element for which"
                     "no atom definition is present (file '{}')".format(fname))
        commonkeys = newatomkeys & set(atomconfigs)
        if commonkeys:
            sys.exit("Duplicate definitions in file '{}': ".format(
                fname,  str(commonkeys)))

        # Update database
        atomconfigs.update(newatoms)
        skbases.update(newsks)
        compressions.update(newcompressions)
        for dirname in newatoms:
            elemdirs[dirname] = includedir

    return atomconfigs, skbases, compressions, elemdirs
####

class Parameter(object):
    """
    A class holding the value of a parameter and associated attributes.
    A very explicit __repr__ method is added for debug purposes.
    """
    def __init__(self,value=0.0,range=[],link=None,map=None):
        self.value = value
        self.range = range
        self.link = link
        self.map = map
        self.root = None

    def __repr__(self):
        return "value: {0},\t range: {1},\t link: {2},\t map: {3},\t root: {4}".\
            format(self.value,self.range,self.link,self.map,self.root)

        
class SKConfiguration(object):
    """ 
    The attributes and methods of this class enable the interpretation of the 'skbases' and 'compressions'
    data (e.g. obtained from get_elemdefs of skgen), in order to find out which are the free parameters
    for optimization. Therefore, an instance of the class is obtained by supplying 'skbases' and 'compressions'
    as input arguments to it __init__() method.

    Typical usage is as follows:
    
        from skconfig import SKConfiguration, write_skdefs
    
        # read the skdefs file
        CONFIG_FILE = "skdefs-PSO.py"
        atomconfigs, skbases, compressions, elemdirs = get_elemdefs(CONFIG_FILE,[])

        # find out what are the parameters
        SKdef = SKConfiguration(skbases,compressions)
        parameters = SKdef.parameters()
    
        # change the value of the parameters somehow:
        if len(parameters):
            for p in parameters:
                p.value = round(sum(p.range)/2.0,2)
        
        # update the configuration
        SKdef.update(parameters)
        skbases = SKdef.skbases
        compressions = SKdef.compressions
        
        # write updated configuration to a new skdefs file for use as an input to skgen
        configList = [("atomconfigs",atomconfigs), ("skbases",skbases), ("compressions",compressions)]
        write_skdefs("./skdefs.py",configList)        
    """
    import logging
    
    def __init__(self,SKconfigList):
        self.SKconfigList = SKconfigList
        self.SKconfigDict = dict(SKconfigList)
        self.atomconfigs = self.SKconfigDict["atomconfigs"]
        self.skbases = self.SKconfigDict["skbases"]
        self.compressions = self.SKconfigDict["compressions"]
        self.atoms = self.compressions.keys()
        # Note that the order of items in the following two lists must be matched
        self.keys = ["skbases","potcomp","wavecomp"]
        self.updateRoutines = [self.set_skbases, self.set_potcomp, self.set_wavecomp]
        
    def atomcfg(self,atom):
        """
        Given an atomic element name, e.g. "Si", return its configuration data in the
        form of a list of lists. 
        The order lists must match the order of self.keys and
        self.updateRoutines.
        """
        return [self.skbases[atom].exponents,
                self.compressions[atom].potcomp_params,
                self.compressions[atom].wavecomp_params]
        
    def set_skbases(self,p):
        """
        This routine sets the value of p back to the skconfiguartion to which the parameter
        is mapped, as indicated by p.map.
        Note that if a parameter is mapped to what was a tuple in the skdefs file, then
        we cannot modify its value directly (tuples being immutable), so we transform to 
        list through the temp variable.
        """
        (atom,L,i),value = p.map[1:4],p.value
        temp = list(self.skbases[atom].exponents[L])
        temp[i] = value
        self.skbases[atom].exponents[L] = temp
    
    def set_wavecomp(self,p):
        (atom,L,i),value = p.map[1:4],p.value
        temp = list(self.compressions[atom].wavecomp_params[L])
        temp[i] = value
        self.compressions[atom].wavecomp_params[L] = temp

    def set_potcomp(self,p):
        (atom,L,i),value = p.map[1:4],p.value
        temp = list(self.compressions[atom].potcomp_params[L])
        temp[i] = value
        self.compressions[atom].potcomp_params[L] = temp
        
    def update(self,NewParameters):
        """
        Update the configuration according to the values and mapping of the input argument `parameters`.
        Works on the strict assumption that each parameter is an instance of the Parameter class above.
        The appropriate update routine depends on the type of the parameter, as established
        through the setPar dictionary
        """
        import logging
        log = logging.getLogger(__name__)
        # Frist, we have to set the value of linked parameters by looking at the .root list
        try:
            # this will work if we passed a list of instances of the Parameter class
            for p in NewParameters:
                for i in p.root:
                    self.Parameters[i].value = p.value
        except AttributeError:
            # this will work if we passed a list of floats with the same length as self.FreeParameters
            for p,value in zip(self.FreeParameters,NewParameters):
                p.value = value
                for i in p.root:
                    self.Parameters[i].value = p.value
        except:
            # this should really not happen!
            log.critical('Problem with the update of parameters. Cannot continue.')
            sys.exit()
        
        setPar = dict(zip(self.keys,self.updateRoutines))
        for p in self.Parameters:
            setPar[p.map[0]](p)
            
        # Finally, we recompose the self.SKconfigList
        self.SKconfigList = [("atomconfigs",self.atomconfigs), ("skbases",self.skbases), ("compressions",self.compressions)]
            
    def parameters(self):
        """
        Functions that analyses the skbases and compression configurations (held now in self)
        and returns descriptors of the free parameters for optimization, if any are encoded within
        the given configurations. 
        The routine works on the fundamental assumptions that configuaration data of a given type
        is represented by lists of sublists (or tuples): one list per angular momentum and one 
        sublist (or tuple) for the indexed parameters for the given angular momentum
        Returns: 
            parameters -- a list of instances of the Parameter class, having 0. as value, but the
                            rest of the attributes being properly assigned.
        """
        import logging
        log=logging.getLogger(__name__)
        self.Parameters = []
        for atom in self.atoms:
            for pType,pList in zip(self.keys,self.atomcfg(atom)):
                for L,pListPerL in enumerate(pList):
                    for i,p in enumerate(pListPerL):
                        try:
                            n = len(p) # This is just a test, basically, to see if we have iterable p[j]
                                       # If we can iterate it means we have a range, and therefore the
                                       # the current parameter is free for optimization
                            par = Parameter(value=0,range=tuple(p[:2]),map=(pType,atom,L,i))
                            try:
                                par.link = p[2]
                            except IndexError:
                                pass
                            self.Parameters.append(par)
                        except TypeError:
                            pass
                        
        # Now we have to eliminate the duplication arising from linked parameters,
        # but keep track of the link, so that later we can populate all linked parameters
        # with the same optimized value
        log.debug("\nSKConfiguraton.Parameters ({0}):".format(len(self.Parameters)))
        for i,p in enumerate(self.Parameters):
            log.debug('\t{0}: {1}'.format(i,p.__repr__()))
        
        # Make a list of the links, excluding None and create a dictionary of 
        # link numbers and the indexes of the linked parameters.
        # The list of parameter indexes for a given link is sorted integers, e.g.
        # { 1: [3,4,5], 5: [6,7], 3: [0,1] }, although the link numbers themselves are
        # arbitrary integers
        LinkedParameters = {}
        for link in [p.link for p in self.Parameters if p.link]:
            LinkedParameters[link] = [i for i,p in enumerate(self.Parameters) if p.link == link]
               
        FreeParameters = []
        for i,p in enumerate(self.Parameters):
            if not p.link:
                p.root = [i,]
                FreeParameters.append(p)
            else:
                p.root = LinkedParameters[p.link]
                if i == LinkedParameters[p.link][0]:
                    FreeParameters.append(p)
        
        self.FreeParameters = FreeParameters
        return self.FreeParameters

    
def reprSKconfigs(configList):
    s = []
    for (name,config) in configList:
        s.append(name+" = {\n")
        for k in config.keys():
            s.append("\t\"{}\": ".format(k))
            s.append(config[k].__repr__())
        s.append("\t}\n\n")
    return s


def write_skdefs(skdefsFile,configList):
    with open(skdefsFile,'wb') as f:
        f.write("".join(reprSKconfigs(configList)))


class SKdefs(object):
    """
    """
    def __init__(self, skdefs_in='skdefs.py', skdefs_out='skdefs.py'):
        """
        Read skdefsfile and determine the configuration and parameters for 
        optimisation, if any.
        """
        self.skdefs_in = skdefs_in
        self.skdefs_out = skdefs_out

        atomconfigs, skbases, compressions, elemdirs = get_elemdefs(skdefs_in,[])
        self.skconfig = [("atomconfigs",atomconfigs), 
                         ("skbases",skbases), ("compressions",compressions)]
        self.configuration = SKConfiguration(self.skconfig)

        # __NOTA BENE:__ This field (self.parameters) should NOT be
        #                updated. If non-empty, it holds ranges,
        #                links, and parameter maps. Even if changed,
        #                the changes will not be propagated to the
        #                self.skdefs_out. See self.update() and self.write().
        self.parameters = self.configuration.parameters()
        

    def update(self,parameters=None):
        """
        Update the configuration based on the parameter update.
        Note that the aim is to update the self.configuration,
        not self.parameters.
        The former can be written to an skdefs.py. (see self.__call__())
        The latter is meant to hold parameter ranges, maps, etc.
        It should not be touched! 
        """
        self.configuration.update(parameters)
        self.skconfig = self.configuration.SKconfigList
        

    def write(self):
        write_skdefs(self.skdefs_out,self.skconfig)        



if __name__ == "__main__":

    import os,sys
    import logging

    logging.basicConfig(level=logging.DEBUG)
    os.chdir('test-skdefs')

    skdefs = SKdefs('skdefs-PSO.py','skdefs-test.py')
    pars = skdefs.parameters
    print('\nFree parameters:')
    print('\n\t'+'\n\t'.join(['{0}: {1}'.format(i,p.__repr__()) for i,p in enumerate(skdefs.parameters)]))
    
    pars[0].value = 3.88
    skdefs.update([p.value for p in pars])
    pars[1].value = 5.67
    skdefs.update(pars)
    print('\nUpdated parameters:')
    print('\n\t'+'\n\t'.join(['{0}: {1}'.format(i,p.__repr__()) for i,p in enumerate(skdefs.configuration.Parameters)]))
    skdefs.write()

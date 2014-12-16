import logging, os, sys
from collections import OrderedDict
from skopt.utils import flatten

class Analyser(object):
    """
    """
    def __init__(self, analyse, data, results, log=logging.getLogger(__name__), **kwargs):
        self.analyse = analyse
        self.data = data
        self.results = results
        self.kwargs = kwargs
        self.log = log
        

    def execute(self):
        # this allows external parties to modify the logger
        # between the __init__() and execute() calls, and yet have
        # a default
        if 'log' not in self.kwargs.keys():
            self.kwargs['log'] = self.log

        self.output = self.analyse(self.data, **self.kwargs)

        for key,val in self.output.items():
            self.results[key] = val
            

    def __call__(self):
        self.execute()

    
    
def skipSystemUpdate(*args,**kwargs):
    pass

    

def queryData(data,keys):
    """ 
    A query function that returns a sub-dictionary of 
    data based on keys.
    data is the input dictionary
    keys determine the key,value pairs returned in the
    output dictionary
    """
    assert all(key in data for key in keys)
    odict = dict()
    for key in keys:
        odict[key]=data[key]
    return odict



class System (object):
    """
    A system is a named ('name' attribute) abstraction layer of the 
    calculations and analysis that can be performed over a given well
    defined entity, for example an atomic structure.
    Properties are calculated by 'tasks' (a list of functions).
    Tasks are a mixture of auxiliary executable and analyser functions
    (typically user provided functions for post-processing the
    data output from auxiliary executable).
    The sequence of task execution is predefined by the user, and
    the actual execution of the tasks populates the 'calculated' 
    dictionary of the system (could be a nested dictionary).
    A system has by default 'refdata' and 'weights', defining the
    reference data and weights of each reference datum.
    The 'updatesystem' method can optionally be supplied, permitting
    the system's environment to be updated based on some call arguments.
    Note that updatesystem is user provided and can have whatever
    interface, unlike tasks, which would typically not accept 
    arguments supplied at runtime. Default method is skipSystemUpdate (pass).
    Additional attributes can be supplied as keyword arguments.
    """
    def __init__(self, workdir='./', name=None, 
                 refdata = None, weights = None,
                 updatesystem = None,
                 tasks = None,
                 log=None,
                 **optattr):
        self.workdir = workdir
        self.refdata = refdata or OrderedDict({})
        self.weights = weights or OrderedDict({})
        self.name = name or os.path.basename(os.path.normpath(workdir))
        self.tasks = tasks or []
        self.update = updatesystem or skipSystemUpdate
        self.calculated = {} # better not be ordered dict
                             # because different analysers will
                             # put data in unpredictable order
        self.log = log

        for key,val in optattr.items():
            setattr(self,key,val)
    
    def subdir(self,*pathfragments):
        return os.path.join(self.workdir,*pathfragments)
            
    def execute(self):
        """
        """
        if self.log is None:
            self.log = logging.getLogger(__name__)

        for task in self.tasks:
            self.log.debug('{0}.{1}'.format(self.name,task))
            try:
                if task.log is None:
                    task.log is self.log
            except AttributeError:
                pass
            task()
        return None
            
    def __call__(self):
        return self.execute()



if __name__ == "__main__":
    s1 = System(workdir='SiO2')
    s2 = System(workdir='Si')
    def f1(data):
        output={}
        for k,v in list(data.items()):
            output[k]=v*2
        return output
    a1 = Analyser(analyse=f1, data={'p':3.}, results=s1.calculated)
    a2 = Analyser(analyse=f1, data={'q':1.}, results=s2.calculated)
    s1.tasks.append(a1)
    s2.tasks.append(a2)
    s1()
    s2()
    print(s1.refdata)
    print(s1.calculated)
    print(s2.refdata)
    print(s2.calculated)


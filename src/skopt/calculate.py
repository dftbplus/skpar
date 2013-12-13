"""
Routines for performing calculations and evaluating deviations from targets
"""
import logging,sys

class Task(object):
    """
    An abstract object of a task, where the actual task is the execution
    of exe. Exe is a function to which the arguments of class instantiation
    are passed as is.
    The output of the task is stored in self.output.
    """
    def __init__(self, exe, *args, **kwargs):
        self.exe = exe
        self.args = args
        self.kwargs = kwargs
        
    def execute(self,**kwargs):
        self.kwargs.update(kwargs)
        self.output = self.exe(*self.args, **self.kwargs)
        return self.output

    def __call__(self, **kwargs):
        return self.execute(**kwargs)
        


class Calculator(object):
    """
    This class is effectively a wrapper to the tasks, allowing appending
    of new tasks to the tasks.
    It also contains the loop for executing the tasks in a callable method.
    Additionally, the calculations can be run in their own directory, 
    the calculator becomes specific to a subset of tasks that need to share
    a directory and logger and must be supplied upon initialisation or 
    otherwise later, explicitly.
    """
    import logging
    
    def __init__(self, workdir='', log=logging.getLogger(__name__), name=''):
        """
        Initialise the task list with an empty one, and set a logger
        Tasks should be filled in by the instantiator, using self.append()
        or directly appending calleable objects to the takslist
        """
        import os
        self.tasks = []
        self.data = {}
        self.log = log
        self.name, self.directory = set_name_directory(name, workdir)

    def chwdir(self):
        """
        Remember where we're called from, chack if the working directory of the calculator exists; 
        exit if not.
        """
        import os,sys
        self.callerdir = os.getcwd()
        if not os.path.isdir(self.directory):
            self.log.critical('Directory {d} for {c} calculator does not exist in {cwd}. Cannot continue.'.
                    format(d=self.directory, c=self.name, cwd=self.callerdir))
            sys.exit()
        os.chdir(self.directory)
        

    def append(self, exe, *args, **kwargs):
        append_task(self, exe, *args, **kwargs)
        

    def calculate(self):
        """
        The following will work only if tasks are independent from each other.
        Dependency must be handled by introduction of intemediary tasks, at the
        level where tasks are appended by the instantiator of the calculator.
        """
        import os
        self.chwdir()
        self.log.info('Executing tasks for {c} calculator in {d} directory'.format(c=self.name,d=self.directory))
        for task in self.tasks:
            """
            Assume that any report of the activity is done by the task itself.
            At the end of the execution, if the output of the task is not None,
            assume it is a dictionary, and add the corresponding items to the
            calculator.data.
            """
            self.log.debug('Executing {0} of {1}'.format(task, self))
            output = task()
            if output is not None:
                self.data.update(output)
                self.log.debug('\t{n} data was updated:'.format(n=self.name))
                for k,v in output.items():
                    self.log.debug('\t\t{0}: {1}'.format(k,v))
        os.chdir(self.callerdir)


    def __call__(self):
        self.calculate()



class Analyser(object):
    """
    This class is effectively a wrapper to tasks analysing data.
    It also contains the loop for executing the tasks in a callable method.
    """
    import logging
    
    def __init__(self, name, data, datakey=None, log=logging.getLogger(__name__)):
        """
        Initialise the task list with an empty one, and set a logger
        Tasks should be filled in by the instantiator, using self.append()
        or directly appending calleable objects to the takslist
        The name of the analyser will be used as a key in the data dictionary
        unless explicit key is passed to an analyser task upon instantiation
        """
        self.tasks = []
        self.log = log
        self.name = name
        self.datain = data
        self.datakey = name if datakey is None else datakey
        self.dataout = {}

    def append(self, exe, *args, **kwargs):
        append_task(self, exe, *args, **kwargs)
        

    def analyse(self):
        """
        The following will work only if tasks are independent from each other.
        Dependency must be handled by introduction of intemediary tasks, at the
        level where tasks are appended by the instantiator of the calculator.
        """
        import os
        self.log.debug('Analyser {0} at work.'.format(self.name))
        self.log.debug('\tUsing {0} as key to system data.'.format(self.datakey))
        for task in self.tasks:
            """
            Assume that any report of the activity is done by the task itself.
            At the end of the execution, if the output of the task is not None,
            assume it is a dictionary, and add the corresponding items to the
            calculator.data.
            """
            self.log.debug('\tExecuting {0} of {1}'.format(task, self))

            output = task(data=self.datain[self.datakey])

            if output is not None:
                self.dataout.update(output)

    def __call__(self):
        self.analyse()



class System(object):
    """
    An abstraction layer above calculators, offering the opportunity to include and analyse
    data from several calculators and their taksks.
    It naturally refers to a directory that is above the directories of the calculators themselves.
    By systems is understood an atomic configuration, for example, whose properties we need to
    calculate with several calculators (associated  with different properties).
    """
    import logging
    def __init__(self, workdir='', name='', log=logging.getLogger(__name__), tasks=None, 
                 calculators = None, plotters = None, targets = None, analysers = None):
        """
        The most important input arguments here are the name or working directory.
        The calculators and plotters could be configured post-instantiation.
        The targets and analysers are optional anyway.
        """
        import os
        self.log = log
        self.name, self.directory = set_name_directory(name,workdir)
        # some system level tasks -- these are functions only, do file or io involved
        # but may serve e.g. to set filenames per iteration or something
        self.tasks = [] if tasks is None else tasks

        # calculators is a list of callable objects 
        # items should be appended to the list after instantiation of a system
        self.calculators = [] if calculators is None else calculators

        # data is a dictionary of named data objects that are assigned
        # by calculators upon their execution
        self.data = {}
        self.data['calculated'] = {}

        # plotters is a list of callable objects that plot data extracted from self.data, so
        # plotters must be knowledgeable and anticipating certain keys in the self.data dictionary
        self.plotters = [] if plotters is None else plotters

        # target and analysers are lists necessary to obtain the deviations between
        # the calculated properties of the system, and some reference (target) values
        # however, these should be optional, specifically if we want to use this without optimization loop
        self.targets = [] if targets is None else targets
        self.analysers = [] if analysers is None else analysers

        # useful for tagging
        self.iteration = None


    def chwdir(self):
        """
        Remember where we're called from, chack if the working directory of the system exists; 
        exit if not; change to it if it does
        """
        import os,sys
        self.callerdir = os.getcwd()
        if not os.path.isdir(self.directory):
            self.log.critical('Directory {d} for {c} system does not exist. Cannot continue.'.
                    format(d=self.directory, c=self.name))
            sys.exit()
        os.chdir(self.directory)

    
    def append(self, exe, *args, **kwargs):
        append_task(self, exe, *args, **kwargs)
        

    def __call__(self, iteration=None):
        """
        This is just a dummy capsule that runs all calculators, plotters and analyser.
        iteration allows to label plots and other saved items if system is iteratively called
        """
        import os, inspect
        self.chwdir()
        self.iteration = iteration
        self.log.debug('\nSYSTEM: {n} executed in {d} directory. Iteration {i}.'.
                       format(n=self.name, d=self.directory, i=self.iteration))

        for task in self.tasks:
            self.log.debug(task) # this is not very infomative, because during scheduling we see
                            # only the reference of the function that is converted to a
                            # task, and not the reference of the task itself.
            task()

        for C in self.calculators:
            C()
            # note that here we add a new entry to the system.data dictionary
            # so data provenance is known, and even if there's a duplicate key
            # e.g. Etot may come from BS or SCC calculation, we can still
            # distinguish and find the right one to use.
            self.data[C.name] = C.data

        for A in self.analysers:
            A()
            # note that here we add the contents of the analyser.data to the
            # 'calculated' data for the system. no tracing where data come from
            # but the idea is that all items are representative of the system, 
            # and are not duplicable
            # the values in 'calculated' data are accessible to subsequent
            # analysers too, and will be used directly for error and cost evaluation
            self.data['calculated'].update(A.dataout)
            self.log.debug('\t{n} data["calculated"] was updated:'.format(n=self.name))
            for k,v in A.dataout.items():
                self.log.debug('\t\t{0}: {1}'.format(k,v))

        # THIS IS UNTESTED LOOP!
        # note that currently, plotters (band-structure and DOS are part of the 
        # respective calculators
        for P in self.plotters:
            # plotter invokation should be last, to permit visibility over
            # data['calculated'], if necessary
            P(self.data)

        os.chdir(self.callerdir)



class AtomicSystem(System):
    """
    """
    def __init__(self, workdir='', name='', lattice=None, log=logging.getLogger(__name__)):
        """
        """
        System.__init__(self, workdir=workdir, name=name, log=log)
        self.lattice = lattice
        self.filenameBS = ''
        self.filenameDOS = ''



# auxiliary helper functions
# -------------------------------------------------------------------
def append_task(taskmaster, exe, *args, **kwargs):
    """
    Append a new task to the tasks, 
    Do not pass implicit arguments, since this will lead to errors, if
    the 'exe' function does not support such.
    """
    import inspect
    if inspect.isroutine(exe):
        # if we pass just a function, then we convert to class, storing 
        # reference to the arguments that must be passed to it at the time of call, 
        # i.e. at the time that the task must be excuted
        t = Task(exe, *args, **kwargs)
        taskmaster.tasks.append( t )
        taskmaster.log.debug('Converted {0} to {1}'.format(exe, t))
        taskmaster.log.debug('\tAppending {0} to {1}({2})'.format(t, taskmaster, taskmaster.name))
    else:
        # if exe is a class with a self.__call__() method
        taskmaster.tasks.append( exe )
        taskmaster.log.debug('Appending {0} to {1}({2})'.format(exe, taskmaster, taskmaster.name))


def set_name_directory(name='',workdir=''):
    """
    """
    # permit some liberty in omitting the name or working directory
    if workdir:
        _dir = workdir
    else:
        if name:
            _dir = name
        else:
            _dir = './'
    # 
    if name:
        _name = name
    else:
        if workdir:
            _name = os.path.basename(os.path.normpath(workdir))
        else:
            _name = '' # this may become a problem if more than one unnamed systems are added
    return _name, _dir


def tag_filename_by_iteration(fileowner, nominator, base, extension):
    """
    Compose a filename: base.iterationstr.extension, making sure
    that iteration is expanded properly.
    base and extension must be strings
    iteration must be an integer or a tupple of integers
    in case of tupple-iteration it becomes i0_i1_i2 etc.
    Assing the value to fileowner.filename
    """
    iteration = nominator.iteration
    if iteration is not None:
        try:
            # note that iteration returned from genetic algorithms may
            # be a tupple, indicating generation and individual within the 
            # generation
            iterationstr = '_'.join(['{0}'.format(i) for i in iteration])
        except TypeError:
            # this is for the straightforward case of sigle integer marking
            # the iteration
            iterationstr = '{0}'.format(iteration)
        filename = '.'.join([base,iterationstr,extension])
    else:
        filename = '.'.join([base,extension])
    fileowner.filename = filename


def get_named(named_objects,name):
    """
    Helper function that allows us to get the instance of a named object
    from a list of objects with names.... not sure about efficiency, but
    here it is intended to operate on a relatively small lists
    """
    for o in named_objects:
        if o.name == name:
            named = o
            break
    return named

if __name__ == "__main__":

    import logging
    import sys, os
    import bandstructure_Si as bsSi
    from bandstructure_Si import analyseEk_Si, analyseEkst_Si
    from bandstructure import setupCalculatorsBandStructure, analyseEelec, analyseEgap
    from plotBS import PlotterBS, preconditionEkPlt_FCC
    from runtasksDFTB import RunSKgen
    from skconfig import SKdefs
    import matplotlib
    matplotlib.use('Agg')


    #logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger('SKauto')
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler(sys.stdout)
    #ch.setFormatter(logging.Formatter('%(message)s'))
    log.addHandler(ch)

    # go to test directory
    os.chdir('./test-Si-SiO2')

    # --- Read in the skdefs file ---
    skdefs = SKdefs(skdefs_in='skdefs-PSO.py',skdefs_out='skdefs-test.py')
    pars = skdefs.parameters

    # --- generate parameter values for skdefs file --
    #     in an optimisation loop, these should be generated by the optimizer
    parameters = [i/2. for i in range(len(pars))]


    # --- Set up generation of *.skf files ---
    # ----------------------------------------
    systems = []

    S = System( name = 'SKF', log=log)
    
    C = Calculator(workdir='./', name='skgen', log=log)
    C.append(skdefs.write)
    C.append(RunSKgen(log=log))

#    S.calculators.append(C)

    systems.append(S)

    # --- Set up the calculation of atomic structures ---
    # ---------------------------------------------------
    S = AtomicSystem( name='Si', lattice='FCC', log=log)

    S.targets   = [ (k,bsSi.ref_Si[k]) for k in ['Dmin_c', 'G15_c', 'G2pr_c','L1_c', 'L3_c'] ]
    S.plotterBS = PlotterBS(Erange = [-12.5, +6.5], preconditioner =  preconditionEkPlt_FCC, log=log)
    S.append(tag_filename_by_iteration, fileowner = S.plotterBS, nominator = S,
             base='../bandstructure_{0}'.format(S.name), extension='pdf')

    S.calculators = setupCalculatorsBandStructure(S,log)

    A = Analyser( 'SCC', S.data, datakey='SCC', log=log)
    A.append(analyseEelec, log=log)
    S.analysers.append(A)
    
    A = Analyser( 'BS', S.data, log=log)
    A.append(analyseEgap, log=log)
    A.append(analyseEk_Si, log=log)
    A.append(analyseEkst_Si, log=log)
    S.analysers.append(A)

    systems.append(S)

    S = AtomicSystem( name='SiO2', lattice='HEX', log=log)
    S.targets   = [('Egap',9.65), ('Ecmin',(0,0,0))]
    S.plotterBS = PlotterBS(Erange = [-20, +20],log=log)
    S.append(tag_filename_by_iteration, fileowner = S.plotterBS, nominator = S,
             base='../bandstructure_{0}'.format(S.name), extension='pdf')

    S.calculators = setupCalculatorsBandStructure(S,log)

    #systems.append(S)
    # ----------------------------------------
    
    # bebop da boogie now
    for s in systems:
        s(iteration=(3,1))

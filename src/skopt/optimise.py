# mandatory imports
import os, sys
import logging
import numpy as np
from datetime import datetime

from collections import OrderedDict

# skopt
from skopt.runtasksDFTB import RunDFTB, RunDPbands, RunSKgen_sh
from skopt.queryDFTB import QueryDataDFTB
from skopt.plotBS import Plotter
from skopt.system import Analyser, System, queryData
from skopt.evaluate import Evaluator
from skopt.pso import PSO, pso_args, report_PSO_stats
from skopt.extras.bandstructure_Si import ref_Si, analyseEk_Si, analyseEkst_Si, analyseMeff_Si
from skopt.parameters import read_parameters, write_parameters, report_parameters, update_pardict
from deap.base import Toolbox


class SKopt(object):
    """
    """
    def __init__(self, workdir = "./", 
		 skopt_in='skdefs.template', 
		 skfdir='skf',
		 skdefs_out='skdefs.py',
		 systems=None,
		 sysweights=None,
		 reportkeys=None,
                 log=None,
		 **kwargs):
        """
        """
	if log is None:
	    """
	    Default logging is set so that skopt.debug.log gets all DEBUG
	    messages and above. At the same time console gets INFO and above.
	    """
	    logging.basicConfig(level=logging.DEBUG,
                    format='%(name)s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename=os.path.join(workdir,'skopt.debug.log'),
                    filemode='w')
	    log=logging.getLogger("SKOPT")
	    # define a Handler which writes INFO messages or higher to the sys.stderr
	    console = logging.StreamHandler()
	    console.setLevel(logging.INFO)
	    # set a format which is simpler for console use
	    formatter = logging.Formatter('%(name)s: %(levelname)-8s %(message)s')
	    # tell the handler to use this format
	    console.setFormatter(formatter)
	    # add the handler to the root logger
	    logging.getLogger('SKOPT').addHandler(console)
	self.log = log

	# Project work directory
	# -------------------------------------------------------------------
	self.workdir = workdir
	os.chdir(self.workdir)
	self.log.info('Execution directory is {0}'.format(os.getcwd()))

	# Get the parameter list first, as these are needed for the skgen system
	# -------------------------------------------------------------------

	# where SKFs go (where skgen is run), and skgen input
	self.skfdir = os.path.join(self.workdir,skfdir)        # where SKFs go
	self.skdefs_out = os.path.join(self.skfdir,skdefs_out) # skgen input
	
	# input for the optimiser, and initial/range values for parameters
	self.skopt_in = os.path.join(self.workdir, skopt_in)
	skdefs_template, pardict, parrangedict = read_parameters(skopt_in, log)
	self.skdefs_template = skdefs_template
	self.pardict = pardict
	self.parrangedict = parrangedict
	self.parrange = self.parrangedict.values()

	# this is handy as it allows to call write_parameters with implicit
	# arguments, so the caller can use it in a generic sence.
	# Note that someone must update the values in pardict (parName,parValue)
	# when these are supplied by the optimising engine; but the engine
	# need not know anything about the meaning of the parameters, so it
	# only spills a list of float and that's that.
	self.toolbox = Toolbox()
	self.toolbox.register("write_parameters", write_parameters, 
			    self.skdefs_template, self.pardict, self.skdefs_out)

	# Systems to compute for evaluation
	# ----------------------------------------------------------------------
	self.systems = []
	self.sysweights = []

	# Default system: SKF generation; 
	# SKF generation does not contribute to fitness => sysweight is 0
	s0 = System(workdir=self.skfdir, name='SKFgen', log=self.log)
	s0.tasks.append(self.toolbox.write_parameters)
	s0.tasks.append(RunSKgen_sh(workdir=s0.workdir))
	self.systems.append(s0)
	self.sysweights.append(0.)

	# Other computational systems: to be supplied as an input argument
	try:
	    self.systems.extend(systems)
	    self.sysweights.extend(sysweights)
	except TypeError:
	    self.log.critical(("You must supply systems and sysweights"
				" as lists of the same legnth, not None."))
	    self.log.debug("systems: {0}".format(systems))
	    self.log.debug("sysweights: {0}".format(sysweights))
	    sys.exit(2)

	# let's make it one thing less configureable, and use the same
	# logger for all systems
	for s in self.systems:
	    s.log = self.log

	# Evaluator
	# ----------------------------------------------------------------------
	## Configure the evaluator of fitness (cost)
	self.evaluate = Evaluator(systems=self.systems, 
				  systemweights=self.sysweights, 
				  workdir=self.workdir,
# use default cost function       costfunc=costfunc, 
				  verbose=True,
				  useRelErr=False,    # if true, would use relerr in constfunc
				  skipexecution=False, # True if you don't have skgen,dftb+,dp_bands etc.
				  log=self.log)

	## fine-tuning what should be reported at each evaluation:
	## in constructing reportkeys, recall that s0 is with 0 system-weight,
	## so nothing will be reported anyway (nothing from s0 goes to flatrefdata)
	# TODO: reconsider this bit. This is strictly evaluator functionality so
	#       it may be better to pass reortkeys as a kwarg directly to evaluator
	#       and not burden skopt with that.
        try:
	    self.evaluate.evalcost.keys = reportkeys or []
	except AttributeError:
	    self.log.critical((
		"You supply reportkeys to evaluator, "
		"but the costfunc you supplied does not support that."))
	    self.log.debug("costfunc is {0}".costfunc)
	    sys.exit(2)

	# Optimiser
	# ---------------------------------------------------------------------- 
	## Configure the optimiser itself
	## TODO: can we decouple this, so that different optimisation
	##       and possibly different configuration of the engine is possible?
	optimiserargs = {'evaluate':self.evalfitness,
	  		'parrange':self.parrange,
			'log':self.log, }
	optimiserargs.update(**kwargs)
	# self.log.debug('optimiserargs: {0}'.format(optimiserargs))
	self.optimargs = pso_args(**optimiserargs)
	self.log.debug('PSO init args: {0}'.format(self.optimargs[0]))
	self.log.debug('PSO init(opt) args: {0}'.format(self.optimargs[2]))
	self.optimise = PSO(*self.optimargs[0], **self.optimargs[2])


    def evalfitness(self, parvalues, iteration, **kwargs):
	"""
	update self.pardict with the new parvalues,
	report the values of the new pardict,
	and call the evaluator
	"""
	#for p,v in zip(self.pardict.keys(),parvalues):
	#    self.pardict[p] = v
	self.pardict = update_pardict(self.pardict,parvalues)

        report_parameters(iteration, self.pardict, self.log)
    
	fitness = self.evaluate(parvalues, iteration)

	try:
	    maxerr = self.evaluate.evalcost.maxrelerr
	except AttributeError:
	    maxerr = None
	    self.log.warning(("The costfunc supplied to evaluator does not have maxrelerr attribute.",
		        "\t\t\tTherefore, cannot use error tolerance for stopping criterion."))

	return (fitness,), maxerr


    def __call__(self):
	"""
	TODO: this should be decoupled from the fact that we use
	      a PSO engine.
	"""
	self.log.info('Logging starts at {0}'.format(datetime.now()))
	self.log.info(("Will do PSO with {np} particles for {ng} generations "
			"or until max relative error is below {err} %").
	    format(np=len(self.optimise.swarm),
		   ng=self.optimargs[1][0],
		   err=self.optimargs[3]['ErrTol']*100))

	self.swarm, self.stats =\
		self.optimise(*self.optimargs[1],**self.optimargs[3])

	report_parameters(self.swarm.gbest_iteration,
		          update_pardict(self.pardict,self.swarm.gbest.renormalized),
		          log=self.log,
			  tag='gBest-')
	self.log.info("gBest fitness is {0:n} and worstRelErr is {1:.2f} %".
		format(self.swarm.gbest.fitness.values[0],
		       self.swarm.gbest.worstErr*100.))

	report_PSO_stats(self.optimise.stats, self.optimise.wre_stats, self.log)

	self.log.info('')
	self.log.info('Logging ends at {0}'.format(datetime.now()))
	return self.swarm, self.stats
	




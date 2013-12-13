import logging

class SKopt(object):
    """
    """
    def __init__(self, systems, configfile='skdefs-PSO.py', skgen_in='skdefs.py', 
                 log=logging.getLogger(__name__)):
        """
        """
        from skconfig import SKdefs
        from evaluate import Evaluate

        # --- Read in the skdefs file ---
        # ------------------------------------------------------------
        self.skdefs = SKdefs(skdefs_in=configfile, skdefs_out=skgen_in)
        self.FreeParameters = self.skdefs.parameters
        self.pRange = [p.range for p in self.FreeParameters]
        # ------------------------------------------------------------

        self.systems = []
        self.log = log

        # --- Set up generation of *.skf files ---
        # ------------------------------------------------------------
        S = System( name = 'SKF', log=self.log)
        
        C = Calculator(workdir='./', name='skgen', log=self.log)
        C.append(skdefs.write)
        C.append(RunSKgen(log=self.log))

        S.calculators.append(C)
        # ------------------------------------------------------------

        # --- Set all systems to be calculated ---
        # ------------------------------------------------------------
        self.systems.append(S) # this is the default SKF generation
        self.systems.extend(systems) # these are the systems for DFTB calculation
        # ------------------------------------------------------------

        self.skeval = Evaluate(paramstruct = skdefs, systems = systems)


    def optPSO(self,npart=10,ngen=50,ErrTol=5.0):
        """
        """
        from pso import PSO
        self.pso = PSO(npart=npart, weights=(-1,), pRange=self.pRange, pEval=self.SKeval)
        self.swarm, self.stats = pso.buzz(ngen=ngen,ErrTol=ErrTol)
        print ""
        print self.swarm.gbest.renormalized, self.swarm.gbest_iteration, self.swarm.gbest_maxErr
        print ""
        print "\n".join(["{}".format(p.renormalized) for p in self.pso.halloffame[:self.pso.nBestKept]])


    def __call__(self, optimiser='PSO', *args, **kwargs):
        """
        """
        import sys
        if optimizer == 'PSO':
            self.optPSO(*args,**kwargs)
        else:
            print("Error: {opt} is not supported. Try PSO instead.".format(optmizer))




#if __name__ == "__main__":
#
#    import logging
#    import sys, os
#    import bandstructure_Si as bsSi
#    from bandstructure import setupCalculatorsBandStructure
#    from plotBS import PlotterBS, preconditionEkPlt_FCC
#    from runtasksDFTB import RunSKgen
#    from skconfig import SKdefs
#    import matplotlib
#    matplotlib.use('Agg')
#
#
#    #logging.basicConfig(level=logging.DEBUG)
#    log = logging.getLogger('SKauto')
#    log.setLevel(logging.DEBUG)
#    ch = logging.StreamHandler(sys.stdout)
#    #ch.setFormatter(logging.Formatter('%(message)s'))
#    log.addHandler(ch)
#
#    # go to test directory
#    os.chdir('./test-Si-SiO2')
#
#
#    systems = []
#    # --- Set up calculatons that are needed for fitness evaluation ---
#    # ----------------------------------------------------------------------
#    S = AtomicSystem( name='Si', lattice='FCC', log=log)
#
#    S.targets   = [ (k,bsSi.ref_Si[k]) for k in ['Dmin_c', 'G15_c', 'G2pr_c','L1_c', 'L3_c'] ]
#    S.plotterBS = PlotterBS(Erange = [-12.5, +6.5], preconditioner =  preconditionEkPlt_FCC, log=log)
#    S.append(tag_filename_by_iteration, fileowner = S.plotterBS, nominator = S,
#             base='../bandstructure_{0}'.format(S.name), extension='pdf')
#
#    S.calculators = setupCalculatorsBandStructure(S,log)
#
#    systems.append(S)
#
#    S = AtomicSystem( name='SiO2', lattice='HEX', log=log)
#    S.targets   = [('Egap',9.65), ('Ecmin',(0,0,0))]
#    S.plotterBS = PlotterBS(Erange = [-20, +20],log=log)
#    S.append(tag_filename_by_iteration, fileowner = S.plotterBS, nominator = S,
#             base='../bandstructure_{0}'.format(S.name), extension='pdf')
#
#    S.calculators = setupCalculatorsBandStructure(S,log)
#
#    systems.append(S)
#    # ----------------------------------------------------------------------
#    
#    # bebop da boogie now
#    for s in systems:
#        s(iteration=(3,1))
#    import sys, os
#    from BS_Si import ref_Si
#    from BandStructure import setupCalculatorsBandStructure
#    from calculator import System
#
#    #logging.basicConfig(level=logging.DEBUG)
#    log = logging.getLogger('SKauto')
#    log.setLevel(logging.DEBUG)
#    ch = logging.StreamHandler(sys.stdout)
#    #ch.setFormatter(logging.Formatter('%(message)s'))
#    log.addHandler(ch)
#
#    os.chdir('./test-Si-SiO2')
#    
#
#    # here we need to define the cost function and its evaluation
#    # it largely depends on the type of systems we must calculate
#    # several important things:
#    #    * to evaluate cost function many calculations need to be done over different system
#    #    * there must be a way to update parameter files needed for the calculations
#    #      prior to the calculation itself.
#    #    * someone must construct carefully the sequence of all tasks of the calculations
#    #    * somehow the cost function evaluation must be general, based on a collection of data
#    #skopt = SKauto(EvaluateCost=evalcost)
#    #skopt.do_PSO(npart=6,ngen=30)

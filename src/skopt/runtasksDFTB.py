"""
This module contains functions and classes that can be appended to the 
tasklist of an instance of a Calculator.
"""
import logging


class RunDFTB(object):
    """
    Perform dftb calculation
    """
    def __init__(self, workdir = '.', exe='dftb+', 
                dftb_in='dftb_in.hsd', dftb_out='dftb_log.out', chargesfile="",
                ncpu = 4, log=logging.getLogger(__name__),):
        self.workdir = workdir
        self.exe = exe
        self.dftb_in = dftb_in
        self.dftb_out = dftb_out
        self.chargesfile = chargesfile
        self.ncpu = ncpu
        self.log = log

    def execute(self):
        import subprocess 
        from subprocess import STDOUT
        import os,sys

        # prepare the shell environment
        env = os.environ.copy()
        env['OMP_NUM_THREADS'] = '{0}'.format(self.ncpu)
        
        os.chdir(self.workdir)

        # copy file with input charges, if not with the default charges.bin
        if self.chargesfile and not self.chargesfile=='charges.bin':
            subprocess.check_call(['/bin/cp','-f',self.chargesfile,
                                   os.path.join(self.workdir,'charges.bin')],stderr=STDOUT)

        # not sure if this will be effective during the subsequent Popen...
        # causes troubles anyway....
        #subprocess.check_call(['ulimit','-s','unlimited'])

        self.log.debug("Running {0} with in {1}".format(self.exe,self.workdir))
        self.log.debug("Execution log is in {0}".format(self.dftb_out))

        # execute dftb+
        process = subprocess.Popen([self.exe,], stdout=open(self.dftb_out, 'w'),stderr=STDOUT, env=env)
        process.wait()
        success = not(process.returncode)
        # if not success, then bail out crying:
        if not success:
            self.log.critical('\tERROR: dftb+ failed somehow. Check {0}!'.format(self.dftb_out))
            sys.exit()

        # success of some sort
        return success

    def __call__(self):
        return self.execute()



class RunSKgen(object):
    """
    This class encapsulates the execution of a ./skgen.sh script in the current directory.
    The relevant skdefs.py must be present in the current directory too.
    """
    def __init__(self, outfile='skgen.sh.log', log=logging.getLogger(__name__)):
        self.log = log
        self.outfile = outfile
        self.output = {}
    
    def execute(self):
        import os, subprocess, sys
        from subprocess import STDOUT
        self.log.debug('Executing skgen.sh')
        process = subprocess.Popen(['/bin/bash','skgen.sh',], stdout=open(self.outfile, 'w'),stderr=STDOUT,)
        process.wait()
        self.output['skgen_success'] = not(process.returncode)
        if process.returncode:
            self.log.error('\tERROR: skgen.sh failed somehow; should not continue. Check {log}!'.format(log=self.outfile))
            sys.exit(1)
        else:
            self.log.debug('\tDone.')
        return self.output

    def __call__(self):
        return self.execute()
    
    def fake(self):
        self.log.debug('Faking the execution of skgen.sh. No log either.')
        self.output['skgen_success'] = True
        return self.output


class RunDPbands(object):
    """
    This class encapsulates the execution of a dp_bands in the current directory
    
    Below is the result of dp_bands --help:

        Usage: dp_bands [options] INPUT OUTPREFIX

        Reads the band structure information stored in the file INPUT created by DFTB+
        (usually band.out) and converts it to NXY-data (to be visualized by gnuplot,
        xmgrace, etc.). The outputfile will be called OUTPREFIX_tot.dat and contains the
        band structure for all spin channels. If spin channel separation is specified,
        the output files OUTPREFIX_s1.dat, OUTPREFIX_s2.dat, etc. will be created for
        each spin channel.

        Options:
        -h, --help            show this help message and exit
        -N, --no-enumeration  do not use the first column of the output to enumerate
                                the k-points
        -s, --separate-spins  create separate band structure for each spin channel
    """
    def __init__(self, workdir = '.', exe='dp_bands', infile='band.out', opts = None,
	         outprefix='bands', log=logging.getLogger(__name__)):
	self.workdir = workdir
	self.exe = exe
        self.infile = infile 
        self.outprefix = outprefix
	self.options = opts or []
        self.logfile = 'dp_bands. log'
        self.log = log
    
    def execute(self):
        import subprocess 
        from subprocess import STDOUT
        self.log.debug('Executing {e} in {d} on {i}, result will be in {o}'.format(
			e=self.exe, d=self.workdir, i=self.infile, o=self.outprefix))
        process = subprocess.Popen( [self.exe, self.infile, self.outprefix], 
				    stdout=open(self.logfile, 'w'), stderr=STDOUT,)
        process.wait()
        success = not(process.returncode)
	if not success:
            self.log.critical('\tERROR: dp_bands failed somehow. Check {log}!'.format(log=self.outprefix))
	    sys.exit()
        return success
    
    def __call__(self):
        return self.execute()
    

def stringisinfile (s,txtfile):
    """
    Check that the string s is in file; boolean return value.
    """
    import mmap
    with open(txtfile) as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        found = mm.find(s)
        if found == -1:
            sinfile = False
        else:
            sinfile = True
    return sinfile

class AnalyseDFTBOut(object):
    """ 
    This class encapsulates the analysis of the detailed.out file of the DFTB+ run
    """
    def __init__(self, fileDetails='detailed.out', units="eV", log=logging.getLogger(__name__)):
        self.log = log 
        self.output = {}
        self.fileDetails = fileDetails
        self.units = units
        # Index of the word containing the energy value in desired units
        # based on the following format, and counted from the end of the line:
        # Fermi energy:  0.1203397656 H  3.2746 eV
        if units == 'eV':
            self.ixEword = 2 # len(words)-2
        else:
            self.ixEword = 4 # len(words)-4
        # Default flag/factor for spin-orbit (SO) coupling -- absent
        # These must be initialised also in the output, since they are required even
        # if the Els term is not present in the output, i.e. if SOcoupling is not accounted for
        self.output['SOcoupling'] = False
        self.output['SOfactor'] = 1
        self.output['SCC_converged'] = False
    
    def execute(self):
        with open(self.fileDetails) as f:
            for line in f:
                words = line.split()
                if 'Input/Output electrons (q):' in line:
                    self.nElectrons = int(float(words[len(words)-1])) # obviously assuming integral #of electrons
                    self.output['nElectrons'] = self.nElectrons
                if 'Energy L.S:' in line:
                    self.Els = float(words[len(words)-self.ixEword])
                    self.SOcoupling = True
                    self.SOfactor = 2
                    log.debug('\tSpin-Orbit coupling is {so}'.format(so='ON' if SOcoupling else 'OFF'))
                    self.output['Els'] = self.Els
                    self.output['SOcoupling'] = self.SOcoupling
                    self.output['SOfactor'] = self.SOfactor
                if 'Fermi energy:' in line:
                    self.Efermi = float(words[len(words)-self.ixEword])
                    self.output['Efermi'] = self.Efermi
                if 'Band energy:' in line:
                    self.Eband = float(words[len(words)-self.ixEword])
                    self.output['Eband'] = self.Eband
                if 'TS:' in line:
                    self.Ets = float(words[len(words)-self.ixEword])
                    self.output['Ets'] = self.Ets
                if 'Energy H0:' in line:
                    self.Eh0 = float(words[len(words)-self.ixEword])
                    self.output['Eh0'] = self.Eh0
                if 'Energy SCC:' in line:
                    self.Escc = float(words[len(words)-self.ixEword])
                    self.output['Escc'] = self.Escc
                if 'Total Electronic Energy:' in line:
                    self.Eelec = float(words[len(words)-self.ixEword])
                    self.output['Eelec'] = self.Eelec
                if 'Repulsive Energy:' in line:
                    self.Erep = float(words[len(words)-self.ixEword])
                    self.output['Erep'] = self.Erep
                if 'SCC converged' in line:
                    self.SCC_converged = True
                    self.output['SCC_converged'] = self.SCC_converged
                if 'SCC is NOT converged' in line:
                    self.SCC_converged = False
                    self.output['SCC_converged'] = self.SCC_converged
        self.log.debug('Analysed {f}, in [{u}]: {data}'.format(f=self.fileDetails, u=self.units, data=self.output))
        if not self.SCC_converged:
            self.log.error('ERROR: SCC did NOT converge! Check out {f} and logs'.format(f=self.fileDetails))
        return self.output

    def __call__(self):
        return self.execute()
    
    def fake(self):
        self.log.debug('Faking the analysis of {f}. No log nor data either.'.format(f=Detailed.out))
        return self.output


def check_var(var,data,value,critical,log):
    """ 
    """
    import sys
    if not data[var] == value:
        if critical: 
            log.critical('{var} ({act} ) is NOT {exp}. Cannot continue.'.format(var=var, 
                        act=data[var], exp=value))
            sys.exit(1)
        else:
            log.error('{var} ({act}) i s NOT {exp}. Check logs.'.format(var=var, 
                        act=data[var], exp=value))


if __name__ == "__main__":
    """
    """
    import os,sys
    from calculate import Task
    from BandStructure import readBandStructure, getkLines
    from plotterBS import PlotterBS, preconditionEkPlt_FCC
    os.chdir('test_calculator_1')

    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger(__name__)

    data={}
    data={'plotBSfilename': 'testPlt.pdf'}

    t1 = RunSKgen(log=log)
    t2 = RunDFTB('dftb_in.hsd.scc', 'dftb_out.log.scc', postfix='scc', log=log)
    t3 = AnalyseDetailedOut(fileDetails='detailed.out.scc', units='eV', log=log)
    t4 = Task(check_var,var='SCC_converged',data=data,value=True,critical=True,log=log)

    t5 = RunDFTB('dftb_in.hsd.bs', 'dftb_out.log.bs', postfix='', log=log)
    t3 = AnalyseDetailedOut(fileDetails='detailed.out.bs', units='eV', log=log)
    t6 = RunDPbands(outfile='band_tot.dat.bs',log=log)

    t7 = Task(readBandStructure,'band_tot.dat.bs',data,log=log,E0='Efermi')
    t8 = Task(getkLines,'dftb_in.hsd.bs','FCC',log=log)
    t9 = PlotterBS(data, preconditioner=preconditionEkPlt_FCC, Erange=[-12.5,+16.5])

    for task in [t3,t7,t8,t9]:
        task.execute()
        if task.output is not None:
            for k,v in task.output.items():
                data[k] = v
    print data

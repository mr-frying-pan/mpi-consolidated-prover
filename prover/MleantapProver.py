import subprocess
import sys
import time

from .Prover import Prover, ProverConfigError
from generator.Formula import Formula

class MleantapProver(Prover):
    def __init__(self, worldRank, logic=None, domain=None, prolog_path=None, prolog_options=None, mleantap_path=None):
        super().__init__(worldRank, 'MleanTAP')
        if logic not in ['d', 't', 's4', 's5', None]:
            raise ProverConfigError('mleantap', self.wr, "Value '%s' is not recognized as 'logic' value" % (logic,))
        if domain not in ['const', 'cumul', 'vary', None]:
            raise ProverConfigError('mleantap', self.wr, "Value '%s' is not recognized as 'domain' value" % (domain,))

        self.logic = logic or 's5'
        self.domain = domain or 'const'
        # expecting swipl to be in $PATH if not passed
        self.prolog_path = prolog_path or 'swipl'
        # copied from mleancop.py
        self.prolog_options = prolog_options or ['--no-debug']
        # just in case
        self.mleantap_path = mleantap_path or './mleantap13_swi.pl'

    def prove(self, formula: Formula, timeout: int = None) -> (Formula, bool, str):
        procStart = time.perf_counter()
        try:
            proveStart = time.perf_counter()
            mleantap = subprocess.run([self.prolog_path] + self.prolog_options
                                      + [
                                          '-g', "['%s']." % (self.mleantap_path,),
                                          '-g', "asserta(logic(%s))." % (self.logic,),
                                          '-g', "asserta(domain(%s))." % (self.domain,),
                                          '-g', "( prove( %s ) -> halt(0) ; halt(1) )." % (formula.toPrologTerm(),),
                                          '-t', "halt."
                                      ],
                                      universal_newlines=True,           # to be able to get output as a string
                                      stdout=subprocess.PIPE,            # capture stdout (remove noise)
                                      timeout=timeout or None)            # set timeout (only hard timeout)
            proveEnd = time.perf_counter()
            if mleantap.returncode == 0:
                conclusionReached = True
                return formula, True, None
            elif mleantap.returncode == 1:
                conclusionReached = True
                return formula, False, None
            else:
                conclusionReached = False
                return formula, None, None
        except subprocess.TimeoutExpired:
            proveEnd = time.perf_counter()
            conclusionReached = False
            return formula, None, None
        finally:
            procEnd = time.perf_counter()
            # save stats
            self.stats['processed'] += 1
            self.stats['conclusionReached'] += 1 if conclusionReached else 0
            self.stats['timeProcessing'] += procEnd - procStart
            self.stats['timeProving'] += proveEnd - proveStart
            
        

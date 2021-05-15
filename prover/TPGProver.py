import subprocess
import sys
import time

from .Prover import Prover, ProverConfigError
from generator.Formula import Formula

class TPGProver(Prover):
    def __init__(self, worldRank, logic=None, domain=None, node_path=None, tpg_dir=None):
        super().__init__(worldRank, 'TPG')
        if logic not in ['s5', None]: # supporting only s5 for now because I am lazy
            raise ProverConfigError('tpg', self.wr, "Value '%s' is not recognized as 'logic' value" % (logic,))
        if domain not in ['const', None]: # no other domain is supported
            raise ProverConfigError('mleantap', self.wr, "Value '%s' is not recognized as 'domain' value" % (domain,))

        # r – reflexive, m – symmetric, t – transitive
        self.accessibility = 'rmt' # no ifs because I am too lazy to implement other logics
        # expecting node to be in $PATH if not passed
        self.node_path = node_path or 'node'
        # just in case
        self.tpg_dir = tpg_dir or '.'

    def prove(self, formula: Formula, timeout: int = None) -> (Formula, bool, str):
        procStart = time.perf_counter()
        try:
            proveStart = time.perf_counter()
            tpg = subprocess.run([self.node_path, self.tpg_dir + 'index.js',
                                  formula.toUnicodeString(),
                                  self.accessibility],
                                 universal_newlines=True, # to be able to get output as a string
                                 stdout=subprocess.PIPE,  # capture stdout (remove noise)
                                 timeout=timeout or None)  # set timeout (only hard timeout)
            proveEnd = time.perf_counter()

            # if conclusion is not reached, timeout happens, exception is raised and this is not executed
            conclusionReached = True

            lines = tpg.stdout.split('\n')

            # first line, second token
            status = lines[0].split(' ')[1]
            # second line is PROOF START and last line is PROOF END
            proof = lines[2:-1]
            statusMap = {
                'Theorem' : True,
                'Non-Theorem': False
            }

            return formula, statusMap[status], proof
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

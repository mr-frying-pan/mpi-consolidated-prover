import subprocess
import sys
import tempfile
import os
import time

from .Prover import Prover, ProverConfigError
from generator.Formula import Formula

class MleancopProver(Prover):
    def __init__(self, worldRank, logic: str = 's5', domain: str = 'const', mleancop_dir: str = None):
        super().__init__(worldRank, 'MleanCoP')
        if logic not in ['d', 't', 's4', 's5', 'multi', None]:
            raise ProverConfigError('mleancop', self.wr, "Value '%s' is not recognized as 'logic' value" % (logic,))
        if domain not in ['const', 'cumul', 'vary', None]:
            raise ProverConfigError('mleancop', self.wr, "Value '%s' is not recognized as 'domain' value" % (domain,))

        self.logic = logic
        self.domain = domain
        self.mleancop_dir = mleancop_dir or './'

    def prove(self, formula: Formula, timeout: int = None) -> (Formula, bool, str, str):
        procStart = time.perf_counter()
        try:
            problemFile = self.generateProblemFile(formula)
            
            args = [self.mleancop_dir + 'mleancop.py', '-q',
                    '--mleancop-path', self.mleancop_dir or '.',
                    '--logic', self.logic,
                    '--domain', self.domain,
                    problemFile]
            if timeout != 0:
                args.append(str(timeout))

            proveStart = time.perf_counter()
            mleancop = subprocess.run(args,
                                      universal_newlines=True,           # to be able to get output as a string
                                      stdout=subprocess.PIPE,            # capture stdout
                                      stderr=subprocess.PIPE,            # capture stderr
                                      timeout=(2 * timeout or None))      # set hard timeout
            proveEnd = time.perf_counter()

            # output anything that is not a warning to stderr
            for line in mleancop.stderr.split('\n'):
                # line is not a warning and not only whitespace
                if (not line.startswith('Warning')) and line.strip():
                    print(line, file=sys.stderr)
                    
            # parse stdout
            lines = mleancop.stdout.strip().split('\n')
            status = lines[0].split(' ')[-1]
            statusMap = {
                'Theorem': True,
                'Non-Theorem': False,
                'Timeout': None
            }
            isTheorem = statusMap['Theorem']
            if isTheorem:
                proof = '\n'.join(lines[2:-1])
            else:
                proof = None
                
            return formula, isTheorem, proof, None
        except subprocess.TimeoutExpired:
            proveEnd = time.perf_counter()
            print('[WARNING] Rank: %d mleancop: swipl process left dangling!' % self.wr, file=sys.stderr)
            return formula, None, None, None
        finally:
            os.remove(problemFile)

            procEnd = time.perf_counter()
            # update stats
            self.stats['processed'] += 1
            self.stats['conclusionReached'] += 1 if isTheorem is not None else 0
            self.stats['timeProcessing'] += procEnd - procStart
            self.stats['timeProving'] += proveEnd - proveStart

    def generateProblemFile(self, formula: Formula) -> str:
        fd, filename = tempfile.mkstemp(prefix='mleancop_%d_' % (self.wr,), text=True)
        with open(fd, 'w') as probF:
            probF.write('f( %s ).' % (formula.toPrologTerm(),))
        return filename

import subprocess
import tempfile
import os
import time

from .Prover import Prover
from generator.Formula import Formula

class Leo3Prover(Prover):
    def __init__(self, worldRank: int, leo3_jar_path: str = './leo3.jar', java_path: str = 'java', logic: str = None, domain: str = None):
        super().__init__(worldRank, 'LEO-III')

        if logic not in ['k', 't', 'd', 's4', 's5', None]:
            raise ProverConfigError('leo3', self.wr, "Value '%s' is not recognized as 'logic' value" % (logic,))
        if domain not in ['const', 'cumul', 'vary', 'decr', None]:
            raise ProverConfigError('leo3', self.wr, "Value '%s' is not recognized as 'domain' value" % (domain,))

        logicTranslations = {
            'k': '$modal_system_K',
            't': '$modal_system_T',
            'd': '$modal_system_D',
            's4': '$modal_system_S4',
            's5': '$modal_system_S5',
            None: '$modal_system_S5',
        }
        domainTranslations = {
            'const': '$constant',
            'vary': '$varying',
            'cumul': '$cumulative',
            'decr': '$decreasing',
            None: '$constant',
        }
        self.logic = logicTranslations[logic]
        self.domain = domainTranslations[domain]

        self.leo3_jar_path = leo3_jar_path
        self.java_path = java_path

    def prove(self, formula: Formula, timeout: int = None) -> (Formula, bool, str):
        procStart = time.perf_counter()
        try:
            # using dash to read from stdin did not work, using temporary file instead
            problemFile = self.generateProblemFile(formula)
            args = [self.java_path, '-jar', self.leo3_jar_path,
                    # using - as filename to read the stdin did not work :( tries to find the file called -
                    problemFile,
                    '-v', '0',   # decrease output
                    '-p']        # output proof
            if timeout:
                args.append('-t')
                args.append(str(timeout))
            proveStart = time.perf_counter()
            leo3 = subprocess.run(args,
                                  universal_newlines=True,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  check=True,
                                  timeout=(2 * timeout or None))
            proveEnd = time.perf_counter()
            parsedOutput = self.parseOutput(leo3.stdout)
            return formula, parsedOutput[0], parsedOutput[1]
        except subprocess.TimeoutExpired:
            proveEnd = time.perf_counter()
            parsedOutput = None
            return formula, None, None
        finally:
            os.remove(problemFile)

            procEnd = time.perf_counter()
            self.stats['processed'] += 1
            self.stats['conclusionReached'] += 1 if parsedOutput is not None and parsedOutput[0] else 0
            self.stats['timeProcessing'] += procEnd - procStart
            self.stats['timeProving'] += proveEnd - proveStart

    def parseOutput(self, output: str) -> (bool, str, str):
        lines = output.strip().split('\n')
        proofStarted = False
        status = None
        for line in lines:
            if proofStarted and line.startswith('% SZS output end'):
                proofStarted = False
                break
            elif proofStarted:
                proof += line + '\n'
            elif line.startswith('% SZS status'):
                status = line.split(' ')[3]
                if status.endswith('Error'):
                    raise ProverError('leo3', self.wr, '%s while proving: %s' % (status, line))
            elif status is not None and status == 'Theorem' and line.startswith('% SZS output start'):
                proofStarted = True
                proofType = line.split(' ')[4]
                proof = '%% %s\n' % proofType

        if status == 'Theorem':
            return True, proof
        return None, None

    def generateProblemFile(self, formula: Formula):
        problem = '''
        thf(modal_logic_descr,logic,(
            $modal :=
                [ $constants := $rigid,
                  $quantification := %s,
                  $consequence := $global,
                  $modalities := %s ] )).
        
        thf(m_type, type, ( m: $i > $o ) ).

        thf(p_type, type, ( p: $i > $o ) ).

        thf(s_type, type, ( s: $i > $o ) ).

        thf(prob, conjecture, %s ).
        ''' % (self.domain, self.logic, formula.toTHF())
        
        fd, filename = tempfile.mkstemp(prefix='leo3_%d_' % (self.wr,), text=True)
        with open(fd, 'w') as probF:
            probF.write(problem)
        return filename

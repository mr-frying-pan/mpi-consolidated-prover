from abc import ABC, abstractmethod
from generator.Formula import Formula
import templates as tmpl
import tempfile
import subprocess
import os
import time

class Prover(ABC):
    def __init__(self, worldrank):
        self.wr = worldrank

    # Should generate a temp file for the given formula
    @abstractmethod
    def generateProblemFile(self, formula: Formula) -> str:
        pass

    @abstractmethod
    def runExternalProver(self, problemFilename: str, timeout: int = 0) -> (bool, str, str):
        pass

    def prove(self, formula: Formula, timeout: int = 0) -> (bool, str, str):
        probFile = self.generateProblemFile(formula)
        if probFile is None:
            return
        try:
            return self.runExternalProver(probFile, timeout)
        finally:
            os.remove(probFile)

class MleancopProver(Prover):
    def generateProblemFile(self, formula: Formula) -> str:
        fd, filename = tempfile.mkstemp(prefix='mleancop_%d_' % (self.wr,), text=True)
        with open(fd, 'w') as probF:
            probF.write(tmpl.mleancopProblem(formula.toPrologTerm()))
        return filename

    def runExternalProver(self, problemFilename: str, timeout: int = 0):
        args = ['./mleancop.sh', problemFilename]
        if timeout != 0:
            args.append(str(timeout))

        try:
            procStart = time.perf_counter()
            mleancop = subprocess.run(args,
                                      cwd='./prover_install/mleancop13', # change dir before run
                                      universal_newlines=True,           # to be able to get output as a string
                                      stdout=subprocess.PIPE,            # capture stdout
                                      stderr=subprocess.PIPE,            # capture stderr (not sure what for yet)
                                      timeout=(2 * timeout or None)       # set hard timeout
                                      )
            procEnd = time.perf_counter()
        except subprocess.TimeoutExpired:
            return None, None, None
        finally:
            pass
        # print(problemFilename, 'done')

        lines = mleancop.stdout.strip().split('\n')
        isTheorem = lines[0].split(' ')[-1] == 'Theorem'
        if isTheorem:
            proof = '\n'.join(lines[2:-1])
        else:
            proof = None
        return isTheorem, proof, None

class TestProver(Prover):
    def generateProblemFile(self, formula: Formula) -> str:
        return None

    def runExternalProver(self, problemFileName: str, timeout: int = 0):
        return ()

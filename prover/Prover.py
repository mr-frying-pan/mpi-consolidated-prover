from abc import ABC, abstractmethod
from generator.Formula import Formula

class Prover(ABC):
    def __init__(self, worldrank: int, name: str):
        self.wr = worldrank
        self.name = name
        self.stats = {
            'processed': 0,
            'conclusionReached': 0,
            'timeProcessing': 0,
            'timeProving': 0,
        }

    # returns: (formula, result, proof)
    @abstractmethod
    def prove(self, formula: Formula, timeout: int = None) -> (Formula, bool, str):
        pass

class TestProver(Prover):
    def __init__(self, worldRank):
        super().__init__(worldRank, 'TestProver')

    def prove(self, formula: Formula, timeout: int = None) -> (Formula, bool, str):
        return formula, None, None

class ProverConfigError(Exception):
    def __init__(prover: str, rank: int, msg: str):
        super().__init__('[%s %d] %s' % (prover, rank, msg))

class ProverError(Exception):
    def __init__(prover: str, rank: int, msg: str):
        super().__init__('[%s %d] %s' % (prover, rank, msg))

from mpi4py import MPI
from prover.Prover import TestProver
from prover.MleancopProver import MleancopProver
from prover.MleantapProver import MleantapProver
from prover.Leo3Prover import Leo3Prover
from generator import Formula
from settings import settings

import time
import math
import csv
import sys

proverBuilders = [
    lambda wr: MleancopProver(wr, mleancop_dir=settings['mleancop_dir']),
    lambda wr: MleantapProver(wr, mleantap_path=settings['mleantap_path']),
    lambda wr: Leo3Prover(wr, leo3_jar_path=settings['leo3_jar_path']),
]

def readPickle():
    import pickle
    with open(settings['formula_pickle_path'], 'rb') as f:
        return pickle.load(f)

def printStats(role, wr, time, prover, report):
    stats = '''
=======================================
    %s %d lasted for:       %.2f s
    Prover:                 %s
    Stats:
        running time:       %.2f s
        proving time:       %.2f s
        processed:          %d
        conclusion reached: %d
=======================================''' % (role, wr, time, prover,
                                              report['timeProcessing'],
                                              report['timeProving'],
                                              report['processed'],
                                              report['conclusionReached'])
    print(stats, file=sys.stderr)

def consolidateResult(*results):
    # check if all results are for the same formula
    fs = [r[0] for r in results]
    assert all([fs[0] == f for f in fs])

    # count prover results
    l = [r[1] for r in results]
    countOfTheoremResults = l.count(True)
    countOfNonTheoremResults = l.count(False)
    countOfUnknownResults = l.count(None)

    # (formula, consolidated result, prover[0] result, prover[0] proof, prover[1] result, prover[1] proof, ...)
    consolidatedResult = [results[0][0], None]

    # contradiction?
    if countOfTheoremResults > 0 and countOfNonTheoremResults > 0:
        print('Contradiction:', mleancop[1], mleantap[1], leo2[1], leo3[1], file=sys.stderr)
        consolidatedResult[1] = 'Unknown'
    elif countOfTheoremResults >= settings['theoremThreshold']:
        consolidatedResult[1] = 'Theorem'
    elif countOfTheoremResults >= settings['nonTheoremThreshold']:
        consolidatedResult[1] = 'Non-Theorem'
    else: consolidatedResult[1] = 'Unknown'

    for r in results:
        if r[1] is None:
            proverResult = 'Unknown'
        elif r[1]:
            proverResult = 'Theorem'
        else:
            proverResult = 'Non-Theorem'
        proverProof = r[2]

        consolidatedResult += [proverResult, proverProof]

    return tuple(consolidatedResult)

def main():
    execStart = time.perf_counter()
    worldRank = MPI.COMM_WORLD.Get_rank()

    assert ((MPI.COMM_WORLD.Get_size() % len(proverBuilders)) == 0 or MPI.COMM_WORLD.Get_size() == 1), 'Number of processors is not divisible by number of provers – some formulas would not be checked by all provers'

    # communicator only for leaders, there will be one leader in each work group
    if worldRank % len(proverBuilders) == 0:
        executiveColor = 1
    else:
        executiveColor = MPI.UNDEFINED
    executiveComm = MPI.COMM_WORLD.Split(color=executiveColor, key=0)

    # worker communicators: groups of processes, each for single prover, leader included
    # key makes sure group leader will get rank 0
    workComm = MPI.COMM_WORLD.Split(color=int(worldRank / len(proverBuilders)), key=worldRank % len(proverBuilders))
    
    if worldRank == 0:
        print('Start read')
        tstart = time.perf_counter()
        fs = readPickle()
        tend = time.perf_counter()
        print('End read:', tend - tstart, 's')

        print('Initial formula count:', len(fs))

        # split formulas list into as many pieces as there are groups.
        # Data being scattered must contain exactly as many elements as there are processors
        pieceSize = math.ceil(len(fs) / executiveComm.Get_size())
        formulas = [fs[i:i + pieceSize] for i in range(0, len(fs), pieceSize)]
    else:
        formulas = None

    if executiveComm != MPI.COMM_NULL:
        formulas = executiveComm.scatter(formulas, root=0)

    formulas = workComm.bcast(formulas, root=0)

    # choose a prover builder lambda and run it to obtain prover object
    prover = proverBuilders[worldRank % len(proverBuilders)](worldRank)

    # PROVE
    results = [prover.prove(f, settings['timeout']) for f in formulas]

    results = workComm.gather(results, root=0)

    zippedResults = []
    # if this is a group leader
    if executiveComm != MPI.COMM_NULL:
        assert len(results) == len(proverBuilders), 'len(results) != len(proverBuilders): %d != %d' % (len(results), len(proverBuilders))
        # get a list of tuples: (first prover res, second prover res, ...)
        zippedResults = list(zip(*results))

        # split into as many pieces as there are processors
        pieceSize = math.ceil(len(zippedResults) / workComm.Get_size())
        zippedResults = [zippedResults[i:i + pieceSize] for i in range(0, len(zippedResults), pieceSize)]

    zippedResults = workComm.scatter(zippedResults, root=0)

    consolidatedResults = [consolidateResult(*r) for r in zippedResults]

    # group leader collects consolidated results
    consolidatedResults = workComm.gather(consolidatedResults, root=0)

    # workers are done here
    if executiveComm == MPI.COMM_NULL:
        execEnd = time.perf_counter()
        printStats('Worker', worldRank, execEnd - execStart, prover.name, prover.stats)
        return

    assert len(consolidatedResults) == len(proverBuilders)
    # flatten consolidated results list
    consolidatedResults = [result for groupResults in consolidatedResults for result in groupResults]

    consolidatedResults = executiveComm.gather(consolidatedResults, root=0)

    # leaders are done, only master remains
    if worldRank != 0:
        execEnd = time.perf_counter()
        printStats('Leader', worldRank, execEnd - execStart, prover.name, prover.stats)
        return

    # flatten consolidated results
    consolidatedResults = [result for groupResults in consolidatedResults for result in groupResults]

    print('Final count of results:', len(consolidatedResults))
    with open('results.csv', 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        # write header
        csvwriter.writerow(('Formula', 'final', 'mleancop result', 'mleancop proof', 'mleantap result', 'mleantap proof', 'leo3 result', 'leo3 proof'))
        csvwriter.writerows(consolidatedResults)

    execEnd = time.perf_counter()
    printStats('Master', worldRank, execEnd - execStart, prover.name, prover.stats)
    print('Total execution time:', execEnd - execStart, 's')

if __name__ == '__main__':
    main()

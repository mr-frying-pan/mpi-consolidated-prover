from mpi4py import MPI
from prover.Prover import TestProver
from prover.MleancopProver import MleancopProver
from prover.MleantapProver import MleantapProver
from prover.Leo3Prover import Leo3Prover
from generator import Formula
import time
import math
import csv
import sys

# result format (isTheorem, proof, counter)
def mergeResults(mleancop, mleantap, leo2, leo3):
    # ensure that all results are for the same formula
    assert mleancop[0] == mleantap[0] == leo2[0] == leo3[0]
    # don't know what to call this :( l stands for list :/
    l = [mleancop[1], mleantap[1], leo2[1], leo3[1]]
    theoremResultCount = l.count(True)
    nonTheoremResultCount = l.count(False)

    # some systems contradict each other
    if theoremResultCount > 0 and nonTheoremResultCount > 0:
        print('Contradiction:', mleancop[1], mleantap[1], leo2[1], leo3[1], file=sys.stderr)
        isTheorem = 'Unknown'
    # no contradiction and enough agree
    elif theoremResultCount >= 2:
        isTheorem = 'Theorem'
    # no contradiction and enough agree
    elif nonTheoremResultCount >= 1: # lower threshold since only is capable of saying this
        isTheorem = 'Non-Theorem'
    # no contradiction but not enough agree
    else:
        isTheorem = 'Unknown'

    # proof preference:
    #     1. leo3 – best format, newest system
    #     2. leo2 – best format, quite dated (if I can make it run >:( )
    #     3. mleancop – unreadable format
    #
    #   inf. mleantap – does not generate proof
    if isTheorem and leo3[1]:
        proof = leo3[2]
    elif isTheorem and leo2[1]:
        proof = leo2[2]
    elif isTheorem and mleancop[1]:
        proof = mleancop[2]
    else:
        proof = None

    # none of the systems generate counterexamples :( Maybe with the addition of tpg that could be solved
    return mleancop[0], isTheorem, proof, None

def readPickle():
    import pickle
    with open('pickle_formulas.dat', 'rb') as f:
        return pickle.load(f)

def selectProver(worldRank):
    provers = [
        MleancopProver(worldRank, mleancop_dir='./prover_install/mleancop13/'),
        MleantapProver(worldRank, mleantap_path='./prover_install/mleantap13/mleantap13_swi.pl'),
        TestProver(worldRank),
        Leo3Prover(worldRank, leo3_jar_path='./prover_install/leo3/leo3.jar'),
    ]
    return provers[worldRank % 4]

def printStats(role, wr, time, prover, report):
    stats = '''
===========================
%s %d lasted for: %f s
Prover: %s
Stats:
%s
===========================''' % (role, wr, time, prover, report)
    print(stats, file=sys.stderr)

def main():
    execStart = time.perf_counter()
    worldRank = MPI.COMM_WORLD.Get_rank()

    # communicator only for leaders, there will be one leader in each work group
    if worldRank % 4 == 0:
        executiveColor = 1
    else:
        executiveColor = MPI.UNDEFINED
    executiveComm = MPI.COMM_WORLD.Split(color=executiveColor, key=0)

    # worker communicators: groups of 4 processes, each for single prover, leader included
    # key makes sure group leader will get rank 0
    workComm = MPI.COMM_WORLD.Split(color=int(worldRank / 4), key=worldRank % 4)
    
    if worldRank == 0:
        # take only every 500th element (less waiting time, less trash on screen, only for debug)
        print('Start read')
        tstart = time.perf_counter()
        fs = readPickle()[::500]

        tend = time.perf_counter()
        print('End read:', tend - tstart, 's')

        print('Initial formula count:', len(fs))

        # split formulas list into as many pieces as there are groups.
        # This is done because data being scattered must contain exactly as many elements as there are processors
        pieceSize = math.ceil(len(fs) / executiveComm.Get_size())
        formulas = [fs[i:i + pieceSize] for i in range(0, len(fs), pieceSize)]
    else:
        formulas = None

    if executiveComm != MPI.COMM_NULL:
        formulas = executiveComm.scatter(formulas, root=0)

    formulas = workComm.bcast(formulas, root=0)

    prover = selectProver(worldRank)
    results = [prover.prove(f, 5) for f in formulas]

    results = workComm.gather(results, root=0)

    if executiveComm == MPI.COMM_NULL:
        # workers are done here
        execEnd = time.perf_counter()
        printStats('Worker', worldRank, execEnd - execStart, prover.name, str(prover.stats))
        return

    assert len(results) == 4
    finalResults = []
    for i in range(len(results[0])): # iterate through each formula in every prover
        mleancopResult = results[0][i]
        mleantapResult = results[1][i]
        leo2Result     = results[2][i]
        leo3Result     = results[3][i]

        definiteResult = mergeResults(mleancopResult, mleantapResult, leo2Result, leo3Result)
        finalResults.append((definiteResult[0].toUnicodeString(), definiteResult[1], definiteResult[2], definiteResult[3]))

    finalResults = executiveComm.gather(finalResults, root=0)

    if worldRank != 0:
        # leaders are done, only master remains
        execEnd = time.perf_counter()
        printStats('Leader', worldRank, execEnd - execStart, prover.name, str(prover.stats))
        return

    finalResults = [result for groupResults in finalResults for result in groupResults]

    print('Final count of results:', len(finalResults))
    with open('results.csv', 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerows(finalResults)

    execEnd = time.perf_counter()
    printStats('Master', worldRank, execEnd - execStart, prover.name, str(prover.stats))
    print('Total execution time:', execEnd - execStart, 's')

if __name__ == '__main__':
    main()

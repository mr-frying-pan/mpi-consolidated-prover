from mpi4py import MPI
from Prover import TestProver, MleancopProver
from generator.Formula import Formula
import time
import math

def mergeResults(mleancop, mleantap, leo2, leo3):
    return mleancop

def readPickle():
    import pickle
    with open('pickle_formulas.dat', 'rb') as f:
        return pickle.load(f)

def selectProver(worldRank):
    if worldRank % 4 == 0:
        return MleancopProver(worldRank)
    return TestProver(worldRank)

def main():
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
        # take only every 200th element (less waiting time, less trash on screen, only for debug)
        print('Start read')
        tstart = time.perf_counter()
        fs = readPickle()[::200]

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
        return

    print('Workers went home')

    assert len(results) == 4
    finalResults = []
    for i in range(len(results[0])): # iterate through each formula in every prover
        mleancopResult = results[0][i]
        mleantapResult = results[1][i]
        leo2Result     = results[2][i]
        leo3Result     = results[3][i]

        finalResults.append(mergeResults(mleancopResult, mleantapResult, leo2Result, leo3Result))

    finalResults = executiveComm.gather(finalResults, root=0)

    if worldRank != 0:
        # leaders are done, only master remains
        return

    print('Leaders went home')

    finalResults = [result for groupResults in finalResults for result in groupResults]

    print('Final count of results:', len(finalResults))

if __name__ == '__main__':
    main()

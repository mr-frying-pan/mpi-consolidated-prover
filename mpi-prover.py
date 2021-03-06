from mpi4py import MPI
from prover.MleancopProver import MleancopProver
from prover.MleantapProver import MleantapProver
from prover.Leo3Prover import Leo3Prover
from prover.TPGProver import TPGProver
from generator import Formula
from settings import settings

import time
import math
import csv
import sys

proverBuilders = [
    lambda wr: MleancopProver(wr, mleancop_dir=settings['mleancop_dir'],
                         logic=settings['logic'],
                         domain=settings['domain']),
    lambda wr: MleantapProver(wr, mleantap_path=settings['mleantap_path'],
                         prolog_path=settings['swipl_path'],
                         logic=settings['logic'],
                         domain=settings['domain']),
    lambda wr: Leo3Prover(wr, leo3_jar_path=settings['leo3_jar_path'],
                     java_path=settings['java_path'],
                     logic=settings['logic'],
                     domain=settings['domain']),
    lambda wr: TPGProver(wr, tpg_dir=settings['tpg_dir'],
                    node_path=settings['node_path'],
                    logic=settings['logic'],
                    domain=settings['domain']),
]

def readPickle():
    import pickle
    with open(settings['formula_pickle_path'], 'rb') as f:
        return pickle.load(f)

def printStats(role, wr, time, prover, report):
    stats = '''
=======================================
    %s %d lasted for:    %.2f s
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
    print(stats)

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
    elif countOfNonTheoremResults >= settings['nonTheoremThreshold']:
        consolidatedResult[1] = 'Non-Theorem'
    else:
        consolidatedResult[1] = 'Unknown'

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

    assert (MPI.COMM_WORLD.Get_size() % len(proverBuilders)) == 0,\
        ('Number of processors is not divisible by number of provers ??? some formulas would not be checked by ' + \
        'all provers (procs: %d ; provers: %d)') % (MPI.COMM_WORLD.Get_size(), len(proverBuilders))

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

        print('Formula count:', len(fs))
        print('Base timeout:', settings['timeout'])
        print('Logic:', settings['logic'])
        print('Domain:', settings['domain'])

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

    # decreasing used timeout by multiplying by value from here
    timeoutModifiers = {
        'LEO-III': 0.6,
        'MleanTAP': 0.8,
        'MleanCoP': 1,
        'TPG': 1
    }
    # PROVE
    # ensuring that timeout is an integer, don't know how the provers would react to floating point values
    results = [prover.prove(f, int(settings['timeout'] * timeoutModifiers[prover.name])) for f in formulas]

    results = workComm.gather(results, root=0)

    # workers are done here
    if executiveComm == MPI.COMM_NULL:
        execEnd = time.perf_counter()
        printStats('Worker', worldRank, execEnd - execStart, prover.name, prover.stats)
        return

    zippedResults = []
    
    # get a list of tuples: (first prover res, second prover res, ...)
    zippedResults = list(zip(*results))
        
    # group leader consolidates results
    assert len(results) == len(proverBuilders), 'len(results) != len(proverBuilders): %d != %d' % (len(results), len(proverBuilders))
    consolidatedResults = [consolidateResult(*r) for r in zippedResults]

    consolidatedResults = executiveComm.gather(consolidatedResults, root=0)

    # leaders are done, only master remains
    if worldRank != 0:
        execEnd = time.perf_counter()
        printStats('Leader', worldRank, execEnd - execStart, prover.name, prover.stats)
        return

    # flatten consolidated results
    consolidatedResults = [result for groupResults in consolidatedResults for result in groupResults]

    # add syllogism information to formula results
    syllogismResults = [(result[0].constructionInfo['figure'],
                         result[0].constructionInfo['major'],
                         result[0].constructionInfo['majorModal'],
                         result[0].constructionInfo['minor'],
                         result[0].constructionInfo['minorModal'],
                         result[0].constructionInfo['conclusion'],
                         result[0].constructionInfo['conclusionModal']
                         ) + result for result in consolidatedResults]

    print('Final count of results:', len(consolidatedResults))
    with open(settings['output_file_path'], 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        # write header
        csvwriter.writerow(('Figure',
                            'Major', 'Major modal',
                            'Minor', 'Minor modal',
                            'Conclusion', 'Conclusion modal',
                            'Formula', 'Final',
                            'MleanCoP result', 'MleanCoP proof',
                            'MleanTAP result', 'MleanTAP proof',
                            'LEO-III result', 'LEO-III proof',
                            'TPG result', 'TPG proof'))
        csvwriter.writerows(syllogismResults)
    execEnd = time.perf_counter()
    printStats('Master', worldRank, execEnd - execStart, prover.name, prover.stats)
    print('Total execution time:', execEnd - execStart, 's')

if __name__ == '__main__':
    main()

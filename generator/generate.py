#!/usr/bin/env python3

from copy import deepcopy
from .Templates import Templates
from .Figures import Figures
from .Formula import impl, conj

n = None
m = 1
s = 0

def generate():
    letters = ["A", "E", "I", "O"]
    modalTypes = [
        "non modal",
        "accidentaly",
        "accidentaly (quod est)",
        "necessarily",
        "necessarily (quod est)",
        "possibly",
        "possibly (quod est)"
    ]

    allFormulas = set()

    for fig in range(1, 5):
        for majorType in letters:
            for minorType in letters:
                for conclusionType in letters:
                    for majorModalType in modalTypes:
                        for minorModalType in modalTypes:
                            for conclusionModalType in modalTypes:
                                major = deepcopy(Templates[majorModalType][majorType])
                                minor = deepcopy(Templates[minorModalType][minorType])
                                conclusion = deepcopy(Templates[conclusionModalType][conclusionType])
                                major.renamePreds("F", Figures[fig]["M"][0])
                                major.renamePreds("G", Figures[fig]["M"][1])
                                minor.renamePreds("F", Figures[fig]["m"][0])
                                minor.renamePreds("G", Figures[fig]["m"][1])
                                conclusion.renamePreds("F", "S")
                                conclusion.renamePreds("G", "P")
                                full = impl( conj( major, minor ), conclusion )
                                # construction information
                                full.constructionInfo = '{:s}({:s}) {:s}({:s}) {:s}({:s}) : figure: {:d}'\
                                    .format(majorType, majorModalType,\
                                            minorType, minorModalType,\
                                            conclusionType, conclusionModalType,\
                                            fig);
                                allFormulas.add(full);
                                if n is not None and len(allFormulas) >= s + n * m:
                                    return list(allFormulas)
    return list(allFormulas)

def printUnicode(fs: list):
    for f in fs:
        print(f.toUnicodeString())

def printReprs(fs: list):
    for f in fs:
        print(f.__repr__())
        assert eval(repr(f)) == f, "Formula.__repr__() is not up to date"

def printProlog(fs: list):
    for f in fs:
        print(f.toPrologTerm())

def printPickle(fs: list):
    import pickle
    import sys
    pickle.dump(fs, sys.stdout.buffer, protocol=-1)

def printTHF(fs: list):
    for f in fs:
        print(f.toTHF())

def positive_int(value):
    ival = int(value)
    if ival <= 0:
        raise argparse.ArgumentTypeError("invalid positive int value: '%s'" % (value,))
    return ival

def parseArgs():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('-n', help='number of formulas to output (taken from the start) (default behaviour is to output all formulas)', type=positive_int)
    parser.add_argument('-m', help='every which formula to output (default=1)', type=positive_int, default=1)
    parser.add_argument('-s', help='skip number of formulas from the beginning', type=int, default=0)
    outputFormatGroup = parser.add_mutually_exclusive_group(required=True)
    outputFormatGroup.add_argument('-u', '--unicode', dest='outputFormat', action='store_const', const='u')
    outputFormatGroup.add_argument('-r', '--repr', dest='outputFormat', action='store_const', const='r')
    outputFormatGroup.add_argument('-p', '--prolog', dest='outputFormat', action='store_const', const='p')
    outputFormatGroup.add_argument('-P', '--pickle', dest='outputFormat', action='store_const', const='P')
    outputFormatGroup.add_argument('-t', '--thf', dest='outputFormat', action='store_const', const='t')

    args = parser.parse_args()
    global n
    n = args.n
    global m
    m = args.m
    global s
    s = args.s
    return args.outputFormat
    
if __name__ == '__main__':
    import argparse

    # default output format is pickle
    outputFormat = parseArgs()
    fs = generate()

    if outputFormat == 'u':
        printUnicode(fs[s::m])
    elif outputFormat == 'r':
        printReprs(fs[s::m])
    elif outputFormat == 'p':
        printProlog(fs[s::m])
    elif outputFormat == 'P':
        printPickle(fs[s::m])
    elif outputFormat == 't':
        printTHF(fs[s::m])

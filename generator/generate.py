#!/usr/bin/env python3

import sys
from copy import deepcopy
from .Templates import Templates
from .Figures import Figures
from .Formula import impl, conj, Formula

class UIDParseError(Exception):
    pass

letters = ["A", "E", "I", "O"]

def generate(n, m, s, noDuplicates):
    modalTypes = [
        "non modal",
        "accidentaly",
        "accidentaly (quod est)",
        "necessarily",
        "necessarily (quod est)",
        "possibly",
        "possibly (quod est)"
    ]

    if noDuplicates:
        allFormulas = set()
    else:
        allFormulas = list() # [] would do the same but doing list() for consistency with set() above

    for fig in range(1, 5):
        for majorType in letters:
            for minorType in letters:
                for conclusionType in letters:
                    for majorModalType in modalTypes:
                        for minorModalType in modalTypes:
                            for conclusionModalType in modalTypes:
                                fla = makeFormula(fig,
                                                  majorType, majorModalType,
                                                  minorType, minorModalType,
                                                  conclusionType, conclusionModalType)
                                #if noDuplicates and full in allFormulas:
                                    #idx = allFormulas.index(full)
                                    #print('Duplicate formula:\nIn set: %s\nNew:    %s' % (allFormulas[idx].constructionInfo, full.constructionInfo), file=sys.stderr)
                                    #continue
                                if noDuplicates:
                                    allFormulas.add(fla)
                                else:
                                    allFormulas.append(fla)
                                if n is not None and len(allFormulas) >= s + n * m:
                                    return list(allFormulas)
    return list(allFormulas)

def generateSingle(uid) -> str:
    (fig, majorType, majorModalType, minorType, minorModalType, conclusionType, conclusionModalType) = parseUID(uid)
    return makeFormula(fig, majorType, majorModalType, minorType, minorModalType, conclusionType, conclusionModalType)

def makeFormula(fig, majorType, majorModalType, minorType, minorModalType, conclusionType, conclusionModalType):
    modalTypeMap = {
        "non modal": "0",
        "accidentaly": "a",
        "accidentaly (quod est)": "A",
        "necessarily": "n",
        "necessarily (quod est)": "N",
        "possibly": "p",
        "possibly (quod est)": "P"
    }

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
    full.constructionInfo = {'major': majorType, 'majorModal': majorModalType,
                             'minor': minorType, 'minorModal': minorModalType,
                             'conclusion': conclusionType, 'conclusionModal': conclusionModalType,
                             'figure': fig}
    # also contains construction information but in a much more concise form
    full.uid = "%d%c%c%c%c%c%c" % (fig, majorType, modalTypeMap[majorModalType], minorType, modalTypeMap[minorModalType], conclusionType, modalTypeMap[conclusionModalType])
    return full

def parseUID(uid: str) -> (int, str, str, str, str, str, str):
    if len(uid) != 7:
        raise UIDParseError("Passed uid is either too long or too short")
    try:
        fig = int(uid[0])
    except ValueError:
        raise UIDParseError("%s is not recognized as a valid figure")

    if fig < 1 or fig > 4:
        raise UIDParseError("%s is not recognized as a valid figure")

    modalTypeMap = {
        "0": "non modal",
        "a": "accidentaly",
        "A": "accidentaly (quod est)",
        "n": "necessarily",
        "N": "necessarily (quod est)",
        "p": "possibly",
        "P": "possibly (quod est)"
    }
    
    majorType = uid[1]
    majorModalType = modalTypeMap[uid[2]]
    minorType = uid[3]
    minorModalType = modalTypeMap[uid[4]]
    conclusionType = uid[5]
    conclusionModalType = modalTypeMap[uid[6]]

    if majorType not in letters or minorType not in letters or conclusionType not in letters:
        raise UIDParseError("Unrecognized premise type")
     # these are None when values are not among dictionary keys, therefore – invalid
    if majorModalType is None or minorModalType is None or conclusionModalType is None:
        raise UIDParseError("Unrecognized modal premise type")
    return fig, majorType, majorModalType, minorType, minorModalType, conclusionType, conclusionModalType

def printUnicode(fs: list):
    for f in fs:
        print(f.toUnicodeString())

def printReprs(fs: list):
    for f in fs:
        print(repr(f))
        assert eval(repr(f)) == f, "Formula.__repr__() is not up to date"

def printProlog(fs: list):
    for f in fs:
        print(f.toPrologTerm())

def printPickle(fs: list):
    import pickle
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
    parser.add_argument('-d', help='allow duplicate formulas. Generates all possible syllogism combinations', default=True, action='store_false')
    parser.add_argument('-i', help='generate single formula given the unique id (all other options are ignored, except for output format)')

    outputFormatGroup = parser.add_mutually_exclusive_group(required=True)
    outputFormatGroup.add_argument('-u', '--unicode', dest='outputFormat', action='store_const', const='u')
    outputFormatGroup.add_argument('-r', '--repr', dest='outputFormat', action='store_const', const='r')
    outputFormatGroup.add_argument('-p', '--prolog', dest='outputFormat', action='store_const', const='p')
    outputFormatGroup.add_argument('-P', '--pickle', dest='outputFormat', action='store_const', const='P')
    outputFormatGroup.add_argument('-t', '--thf', dest='outputFormat', action='store_const', const='t')

    args = parser.parse_args()
    return args.outputFormat, args.n, args.m, args.s, args.d, args.i
    
if __name__ == '__main__':
    import argparse

    # default output format is pickle
    (outputFormat, n, m, s, noDuplicates, uid) = parseArgs()
    if uid is not None:
        try:
            fs = [generateSingle(uid)]
        except UIDParseError as e:
            print("'%s' is not recognized as valid UID: %s" % (uid, e), file=sys.stderr)
            exit(1)
    else:
        fs = generate(n, m, s, noDuplicates)

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

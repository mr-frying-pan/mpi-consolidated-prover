#!/usr/bin/env python3

from copy import deepcopy
from .Templates import Templates
from .Figures import Figures
from .Formula import impl, conj

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
    return list(allFormulas)

def printReprs(fs: list):
    from .Formula import Formula
    for f in fs:
        print(f.__repr__())
        assert eval(repr(f)) == f, "Formula.__repr__() is not up to date"

def printPickle(fs: list):
    import pickle
    import sys
    pickle.dump(fs, sys.stdout.buffer, protocol=-1)

if __name__ == '__main__':
    fs = generate()

    #printReprs(fs)
    printPickle(fs)

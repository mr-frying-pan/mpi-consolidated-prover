#!/usr/bin/env python3

class Formula:
    def __init__(self, kind: str, lhs: 'Formula' = None, rhs: 'Formula' = None, name: str = None):
        self._kind = kind
        self._lhs = lhs
        self._rhs = rhs
        self._name = name
        self.constructionInfo = ''
        self.isTheorem = None
        self.proof = None
        self.counter = None

    def renamePreds(self, predName: str, newName: str):
        if(self._kind == 'pred' and self._name == predName):
            self._name = newName
            return
        if self._lhs is not None:
            self._lhs.renamePreds(predName, newName)
        if self._rhs is not None:
            self._rhs.renamePreds(predName, newName)

    def toUnicodeString(self):
        if(self._kind == 'pred'):
            return self._name.upper() + 'x'
        elif(self._kind == 'neg'):
            return '¬' + self._rhs.toUnicodeString()
        elif(self._kind == 'conj'):
            return '(' + self._lhs.toUnicodeString() + '∧' + self._rhs.toUnicodeString() + ')'
        elif(self._kind == 'disj'):
            return '(' + self._lhs.toUnicodeString() + '∨' + self._rhs.toUnicodeString() + ')'
        elif(self._kind == 'impl'):
            return '(' + self._lhs.toUnicodeString() + '→' + self._rhs.toUnicodeString() + ')'
        elif(self._kind == 'necc'):
            return '□' + self._rhs.toUnicodeString()
        elif(self._kind == 'poss'):
            return '◇' + self._rhs.toUnicodeString()
        elif(self._kind == 'exists'):
            return '∃x'+ self._rhs.toUnicodeString()
        elif(self._kind == 'forall'):
            return '∀x' + self._rhs.toUnicodeString()
        else:
            return 'UNDEFINED'

    def toPrologTerm(self):
        if(self._kind == 'pred'):
            return self._name.lower() + '(X)'
        elif(self._kind == 'neg'):
            return '(~ ' + self._rhs.toPrologTerm() + ')'
        elif(self._kind == 'conj'):
            return '(' + self._lhs.toPrologTerm() + ' , ' + self._rhs.toPrologTerm() + ')'
        elif(self._kind == 'disj'):
            return '(' + self._lhs.toPrologTerm() + ' ; ' + self._rhs.toPrologTerm() + ')'
        elif(self._kind == 'impl'):
            return '(' + self._lhs.toPrologTerm() + ' => ' + self._rhs.toPrologTerm() + ')'
        elif(self._kind == 'necc'):
            return '(# ' + self._rhs.toPrologTerm() + ')'
        elif(self._kind == 'poss'):
            return '(* ' + self._rhs.toPrologTerm() + ')'
        elif(self._kind == 'exists'):
            return '(ex X: ' + self._rhs.toPrologTerm() + ')'
        elif(self._kind == 'forall'):
            return '(all X: ' + self._rhs.toPrologTerm() + ')'
        else:
            return 'UNDEFINED'

    def toTHF(self):
        if self._kind == 'pred':
            return '(' + self._name.lower() + ' @ X)'
        elif self._kind == 'neg':
            return '(~ ' + self._rhs.toTHF() + ')'
        elif self._kind == 'conj':
            return '( ' + self._lhs.toTHF() + ' & ' + self._rhs.toTHF() + ' )'
        elif self._kind == 'disj':
            return '( ' + self._lhs.toTHF() + ' | ' + self._rhs.toTHF() + ' )'
        elif self._kind == 'impl':
            return '( ' + self._lhs.toTHF() + ' => ' + self._rhs.toTHF() + ' )'
        elif self._kind == 'necc':
            return '( $box @ ' + self._rhs.toTHF() + ' )'
        elif self._kind == 'poss':
            return '( $dia @ ' + self._rhs.toTHF() + ' )'
        # not sure about these :/ Could also be a combination of these: !> ?* ^ @+ @-
        elif self._kind == 'exists':
            return '( ? [X: $i] : ' + self._rhs.toTHF() + ' )'
        elif self._kind == 'forall':
            return '( ! [X: $i] : ' + self._rhs.toTHF() + ' )'

    def __repr__(self):
        return 'Formula(kind=' + repr(self._kind)\
             + ', lhs=' + repr(self._lhs)\
             + ', rhs=' + repr(self._rhs)\
             + ', name=' + repr(self._name) + ')'

    def __str__(self):
        return self.toUnicodeString()

    def __hash__(self):
        return hash((self._kind, self._rhs, self._lhs, self._name))

    def __eq__(self, other):
        return self._kind == other._kind and self._lhs == other._lhs and self._rhs == other._rhs and self._name == other._name

def pred(name: str):
    return Formula(kind='pred', name=name)

def neg(param: 'Formula'):
    return Formula(kind='neg', rhs=param)

def conj(lhs: 'Formula', rhs: 'Formula'):
    return Formula(kind='conj', lhs=lhs, rhs=rhs)

def disj(lhs: 'Formula', rhs: 'Formula'):
    return Formula(kind='disj', lhs=lhs, rhs=rhs)

def impl(lhs: 'Formula', rhs: 'Formula'):
    return Formula(kind='impl', lhs=lhs, rhs=rhs);

def necs(param: 'Formula'):
    return Formula(kind='necc', rhs=param);

def poss(param: 'Formula'):
    return Formula(kind='poss', rhs=param);

def exists(body: 'Formula'):
    return Formula(kind='exists', rhs=body)

def forall(body: 'Formula'):
    return Formula(kind='forall', rhs=body)

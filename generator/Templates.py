#!/usr/bin/env python3

from .Formula import pred, neg, conj, disj, impl, necs, poss, exists, forall

Templates = {
    "accidentaly": {
        "A": necs( forall(impl( pred("F"), conj( poss( pred("G") ), poss( neg( pred("G") ) ) ) ) ) ),
        "E": necs( forall(impl( pred("F"), conj( poss( pred("G") ), poss( neg( pred("G") ) ) ) ) ) ),
        "I": poss( exists(conj( pred("F"), conj( poss( pred("G") ), poss( neg( pred("G") ) ) ) ) ) ),
        "O": poss( exists(conj( pred("F"), conj( poss( pred("G") ), poss( neg( pred("G") ) ) ) ) ) ),
    },
    "accidentaly (quod est)": {
        "A": conj( forall(impl( pred("F"), conj( poss( pred("G") ), poss( neg( pred("G") ) ) ) ) ), exists(pred("F") ) ),
        "E": conj( forall(impl( pred("F"), conj( poss( pred("G") ), poss( neg( pred("G") ) ) ) ) ), exists(pred("F") ) ),
        "I": exists(conj( pred("F"), conj( poss( pred("G") ), poss( neg( pred("G") ) ) ) ) ),
        "O": exists(conj( pred("F"), conj( poss( pred("G") ), poss( neg( pred("G") ) ) ) ) ),
    },
    "non modal": {
        "A": conj( forall( impl( pred("F"), pred("G") ) ), exists( pred("F") ) ),
        "E": forall(impl( pred("F"), neg( pred("G") ) ) ),
        "I": exists(conj( pred("F"), pred("G") ) ),
        "O": disj( exists( conj( pred("F"), neg( pred("G") ) ) ), neg( exists( pred("F") ) ) )
    },
    "necessarily": {
        "A": conj( necs( forall( impl( pred("F"), necs( pred("G") ) ) ) ), poss( exists( pred("F") ) ) ),
        "E": necs( forall( impl( pred("F"), necs( neg ( pred("G") ) ) ) ) ),
        "I": poss( exists( conj( pred("F"), necs( pred("G") ) ) ) ),
        "O": disj( poss( exists( conj( pred("F"), necs( neg( pred("G") ) ) ) ) ), necs( neg( exists( pred("F") ) ) ) )
    },
    "necessarily (quod est)": {
        "A": conj( forall( impl( pred("F"), necs( pred("G") ) ) ), exists( pred("F") ) ),
        "E": forall( impl( pred("F"), necs( neg ( pred("G") ) ) ) ),
        "I": exists( conj( pred("F"), necs( pred("G") ) ) ),
        "O": disj( exists( conj( pred("F"), necs( neg( pred("G") ) ) ) ), necs( neg( exists( pred("F") ) ) ) )
    },
    "possibly": {
        "A": conj( necs( forall( impl( pred("F"), poss( pred("G") ) ) ) ), poss( exists( pred("F") ) ) ),
        "E": necs( forall( impl( pred("F"), poss( neg( pred("G") ) ) ) ) ),
        "I": poss( exists( conj( pred("F"), poss( pred("G") ) ) ) ),
        "O": disj( poss( exists( conj( pred("F"), poss( neg( pred("G") ) ) ) ) ), necs( neg( exists( pred("F") ) ) ) )
    },
    "possibly (quod est)": {
        "A": conj( forall( impl( pred("F"), poss( pred("G") ) ) ), exists( pred("F") ) ),
        "E": forall( impl( pred("F"), poss( neg( pred("G") ) ) ) ),
        "I": exists( conj( pred("F"), poss( pred("G") ) ) ),
        "O": disj( exists( conj( pred("F"), poss( neg( pred("G") ) ) ) ), necs( neg( exists( pred("F") ) ) ) )
    }
}

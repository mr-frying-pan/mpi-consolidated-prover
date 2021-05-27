const Parser = require('./parser.js');
const { Prover, Node } = require('./prover.js');
const SenTree = require('./sentree.js');
const XmlPainter = require('./xmlpainter.js');

function renderSymbols(str) {
    str = str.replace(/&|\^| and/ig, '∧');
    str = str.replace(/ v | or/ig, ' ∨ '); // 'v' letter => or symbol
    str = str.replace(/~| not/ig, '¬');
    str = str.replace(/<->| iff/ig, '↔');
    str = str.replace(/->/g, '→');
    str = str.replace(/\[\]/g, '□');
    str = str.replace(/<>|◊/g, '◇');
    str = str.replace(/\(A([s-z])\)/, '∀$1'); // (Ax) => ∀x
    str = str.replace(/\(E([s-z])\)/, '∃$1'); // (Ex) => ∃x
    str = str.replace(/(?:^|\W)\(([s-z])\)/, '∀$1'); // (x) => ∀x, but not f(x) => f∀x
    str = str.replace(/\\?forall[\{ ]?\}?/g, '∀');
    str = str.replace(/\\?exists[\{ ]?\}?/g, '∃');
    str = str.replace(/(\\neg|\\lnot)[\{ ]?\}?/g, '¬');
    str = str.replace(/(\\vee|\\lor)[\{ ]?\}?/g, '∨');
    str = str.replace(/(\\wedge|\\land)[\{ ]?\}?/g, '∧');
    str = str.replace(/(\\to|\\rightarrow)[\{ ]?\}?/g, '→');
    str = str.replace(/\\leftrightarrow[\{ ]?\}?/g, '↔');
    str = str.replace(/\\[Bb]ox[\{ ]?\}?/g, '□');
    str = str.replace(/\\[Dd]iamond[\{ ]?\}?/g, '◇');
    return str;
}

function translateAccessibility(constraints) {
    return constraints.map(c => {
	if (c == 'u') return "universality"; // { id: "universality", value: "∀v∀uRvu" };
	if (c == 'r') return "reflexivity";  // { id: "reflexivity",  value: "∀vRvv" };
	if (c == 'm') return "symmetry";     // { id: "symmetry",     value: "∀v∀u(Rvu→Ruv)" };
	if (c == 't') return "transitivity"; // { id: "transitivity", value: "∀v∀u∀t(Rvu→(Rut→Rvt))" };
	if (c == 'e') return "euclidity";    // { id: "euclidity",    value: "∀v∀u∀t(Rvu→(Rvt→Rut))" };
	if (c == 's') return "seriality";    // { id: "seriality",    value:"∀v∃uRvu" };
    });
}

var prover = null;
var painter = null;
function startProof(input, constraints, quiet) {
    var parser = new Parser();
    try {
	var parsedInput = parser.parseInput(input);
	var premises = parsedInput[0];
	var conclusion = parsedInput[1];
	var initFormulas = premises.concat([conclusion.negate()]);
    }
    catch (e) {
	console.error(e);
	return false;
    }
    // Now a free-variable tableau is created. When the proof is finished,
    // prover.finished() is called.
    var accessibilityConstraints = [];
    if (parser.isModal) {
	// do the accessibility constraints
	accessibilityConstraints = translateAccessibility(constraints);
    }
    prover = new Prover(initFormulas, parser, accessibilityConstraints);
    prover.onfinished = function(treeClosed) {
	let status, proof;
	// The prover has finished. Show result:
	if (treeClosed) {
	    status = "Theorem";
	    const sentree = new SenTree(this.tree, parser);
	    if (parser.isModal)
		sentree.modalize();
	    
	    const painter = new XmlPainter(sentree);
	    proof = painter.paintTree();
	    process.exitCode = 0;
	}
	else {
	    status = "Non-Theorem"
	    for(let k in this.countermodel) { console.log(k); }
	    proof = this.counterModel.toXML();
	    process.exitCode = 1
	}
	// output result and proof
	console.log(`STATUS: ${status}`);
	console.log('PROOF START');
	console.log(proof);
	console.log('PROOF END');
    }
    prover.status = function(txt) {
	// console.error(`[INFO] Status: ${txt}`);
    }
    prover.start();
    return false;
}

process.exitCode = 10;
try {
    if (process.argv.length >= 5) {
	startProof(process.argv[3], process.argv[4].split(""), process.argv[2] == "-q"); // -q formula accesibility
    }
    else if (process.argv.length == 4 && process.argv[2] != "-q") { // formula accessibility
	startProof(process.argv[2], process.argv[3].split(""), false)
    }
    else if (process.argv.length == 4) { // -q formula
	startProof(process.argv[3], [], process.argv[2])
    }
    else if (process.argv.length == 3) { // formula
	startProof(process.argv[2], [], false)
    }
    else {
	console.error("Please provide formula")
	process.exitCode = 2;
    }
}
catch (e) {
    console.error(e);
    console.error(process.argv);
    console.error();
    process.exitCode = 2;
}

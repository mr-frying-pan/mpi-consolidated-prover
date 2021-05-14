class Proof {
    constructor() {
	this.elements = []
    }

    get xml() {
	let xml = '<proof>';
	for(let element of this.elements) {
	    xml += element.xml;
	}
	xml += '</proof>';
	return xml;
    }
}

class ProofNode {
    constructor(num, formula, world, from, closed) {
	this.num = num;
	this.formula = formula;
	this.world = world;
	this.from = from;
	this.closed = closed || false;
    }

    get xml() {
	return `<node><num>${this.num}</num><formula>${this.formula}</formula><world>${this.world}</world><from>${this.from}</from><closed>${this.closed}</closed></node>`;
    }
}

class SplitColumn {
    constructor() {
	this.elements = [];
    }

    get xml() {
	let xml = '<col>';
	for(let element of this.elements) {
	    xml += element.xml;
	}
	xml += '</col>';
	return xml;
    }
}

class ProofSplit {
    constructor() {
	this.leftCol = new SplitColumn();
	this.rightCol = new SplitColumn();
    }

    get xml() {
	return `<split>${this.leftCol.xml}${this.rightCol.xml}</split>`
    }
}

class XmlPainter {
    constructor(senTree) {
	this.tree = senTree;
	this.isModal = senTree.parser.isModal;
	this.curNodeNumber = 0;
    }

    paintTree() {
	const proof = new Proof();
	this.paint(this.tree.nodes[0], proof);
	return proof.xml;
    }

    paint(node, proofNodeParent) {
	// add another node to current parent
	proofNodeParent.elements.push(this.makeProofNode(node));
	
	// proof splits, need to create new parents - columns
	if (node.children.length === 2) {
	    const split = new ProofSplit();
	    proofNodeParent.elements.push(split);
	    // paint left and right columns
	    this.paint(node.children[0], split.leftCol);
	    this.paint(node.children[1], split.rightCol);
	}
	else if (node.children.length === 1) {
	    this.paint(node.children[0], proofNodeParent);
	}
    }

    makeProofNode(node) {
	const from = node.fromNodes.map((n) => n.nodeNumber);
	
	if (node.fromRule) {
	    const fromRule = node.fromRule.toString().substr(0,3);
	    if (!['alp', 'bet', 'gam', 'del', 'mod'].includes(fromRule)) {
		from.push(fromRule+'.');
            }
	}

	this.curNodeNumber++;
	// make node number available on the node itself, needed for getting fromNodes above
	node.nodeNumber = this.curNodeNumber;
	const proofNode = new ProofNode(this.curNodeNumber,
					node.formula.string,
					node.formula.world,
					from.join(','),
					node.closedEnd)
	return proofNode;
    }
}

module.exports = XmlPainter;

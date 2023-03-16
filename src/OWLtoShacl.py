import os
import subprocess
import rdflib
from rdflib import URIRef

from .RML import *
from .SHACL import *


class OWLtoSHACL:
    def __init__(self):
        self.RML = RML()
        self.shaclNS = rdflib.Namespace('http://www.w3.org/ns/shacl#')
        self.rdfSyntax = rdflib.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
        self.XSDNS = rdflib.Namespace('http://www.w3.org/2001/XMLSchema#')
        self.AstreaArgs = []
        self.AstreaKG = str(os.getcwd()) + "\\Astrea-KG.ttl"
        self.astreajarpath = str(os.getcwd()) + "\\Astrea2SHACL.jar"

        self.onto_stats = dict()

    def get_prefix_ontologies(self):
        for namespace in self.RML.graph.namespaces():
            try:
                g = rdflib.Graph()
                g.parse(namespace[1])
                self.AstreaArgs += [str(namespace[1])]
            except:
                pass

    def get_file_ontologies(self, ontology_dir, temp_imported_onto_folder):
        if ontology_dir is not None:
            for ontology in os.listdir(ontology_dir):
                file = os.path.join(ontology_dir, ontology)
                try:
                    g = rdflib.Graph()
                    g.parse(file)
                    destination = str(temp_imported_onto_folder + "\\" + ontology)
                    g.serialize(destination=destination, format='turtle')
                except:
                    pass
            for ontology in os.listdir(temp_imported_onto_folder):
                file = os.path.join(temp_imported_onto_folder, ontology)
                self.AstreaArgs += [str(file)]

    def convert_ontologies(self, astreageneratedpath):
        subprocesscommand = ['java', '-jar', self.astreajarpath, self.AstreaKG]
        for item in self.AstreaArgs:
            subprocesscommand.append(item)
        subprocess.call(subprocesscommand, cwd=astreageneratedpath)

    def enrich_ontology(self, ontology_graph, RML2SHACLgraph):
        nodeshape_blacklist = [self.shaclNS.targetClass,
                               self.rdfSyntax.type,
                               URIRef("http://www.w3.org/2000/01/rdf-schema#label"),
                               self.shaclNS.description,
                               self.shaclNS.name]

        propertyshape_blacklist = [self.shaclNS.targetClass,
                                   self.rdfSyntax.type,
                                   URIRef("http://www.w3.org/2000/01/rdf-schema#label"),
                                   self.shaclNS.description,
                                   self.shaclNS.name]

        # Get a list of all targetClasses
        q1 = f'SELECT ?nodeshape ?targetclass {{?nodeshape a <{self.shaclNS.NodeShape}> .?nodeshape <{self.shaclNS.targetClass}> ?targetclass.}}'
        x1 = RML2SHACLgraph.query(q1)

        # Get the constraints for each targetClass and add them to the rml2shacl shapes
        for row in x1:
            q2 = f'SELECT ?p ?o {{?s a <{self.shaclNS.NodeShape}> .?s <{self.shaclNS.targetClass}> <{row.targetclass}> .?s ?p ?o}}'
            x2 = ontology_graph.query(q2)
            q3 = f'SELECT ?p ?o {{?s a <{self.shaclNS.NodeShape}> .?s <{self.shaclNS.targetClass}> \"{row.targetclass}\" .?s ?p ?o}}'
            x3 = RML2SHACLgraph.query(q3)
            property_BNodes_dict = dict()
            q5 = f'SELECT ?bnode ?p ?o {{<{row.nodeshape}> a <{self.shaclNS.NodeShape}> .<{row.nodeshape}> <{self.shaclNS.property}> ?bnode. ?bnode ?p ?o}}'
            x5 = RML2SHACLgraph.query(q5)
            for row5 in x5:
                if row5.p == self.shaclNS.path:
                    property_BNodes_dict[row5.o] = row5.bnode
            for row2 in x2:
                if row2.p not in nodeshape_blacklist:
                    if row2.p != self.shaclNS.property:
                        for row3 in x3:
                            if row2.p == row3.p:
                                break
                        else:
                            self.add_ontology_item(RML2SHACLgraph, row.nodeshape, row2.p, row2.o, ontology_graph)
                    else:
                        property_dict = dict()
                        q4 = f'SELECT ?p ?o {{<{row2.o}> a <{self.shaclNS.PropertyShape}> .<{row2.o}> ?p ?o}}'
                        x4 = ontology_graph.query(q4)
                        for row4 in x4:
                            if row4.p not in propertyshape_blacklist:
                                property_dict[row4.p] = row4.o
                        if property_dict.get(self.shaclNS.path) in property_BNodes_dict:
                            for item in property_dict:
                                for row5 in x5:
                                    if item == row5.p:
                                        break
                                else:
                                    self.add_ontology_item(RML2SHACLgraph, property_BNodes_dict[property_dict[self.shaclNS.path]], item, property_dict[item], ontology_graph)

        property_BNodes_dict = dict()
        q6 = f'SELECT ?bnode {{?s a <{self.shaclNS.NodeShape}> .?s <{self.shaclNS.property}> ?bnode.}}'
        x6 = RML2SHACLgraph.query(q6)
        BNode_list = list()
        for row6 in x6:
            if type(row6.bnode) == rdflib.term.BNode:
                BNode_list += [row6.bnode]

        for bnode in BNode_list:
            if ((bnode, self.shaclNS.nodeKind, self.shaclNS.IRIOrLiteral) in RML2SHACLgraph) and ((bnode, self.shaclNS.nodeKind,  self.shaclNS.IRI) in RML2SHACLgraph):
                RML2SHACLgraph.remove((bnode, self.shaclNS.nodeKind, self.shaclNS.IRIOrLiteral))
                self.onto_stats[self.shaclNS.nodeKind] -= 1
            elif ((bnode, self.shaclNS.nodeKind, self.shaclNS.IRIOrLiteral) in RML2SHACLgraph) and ((bnode, self.shaclNS.nodeKind, self.shaclNS.Literal) in RML2SHACLgraph):
                RML2SHACLgraph.remove((bnode, self.shaclNS.nodeKind, self.shaclNS.IRIOrLiteral))
                self.onto_stats[self.shaclNS.nodeKind] -= 1
            elif ((bnode, self.shaclNS.nodeKind, self.shaclNS.BlankNodeOrLiteral) in RML2SHACLgraph) and ((bnode, self.shaclNS.nodeKind, self.shaclNS.Literal) in RML2SHACLgraph):
                RML2SHACLgraph.remove((bnode, self.shaclNS.nodeKind, self.shaclNS.BlankNodeOrLiteral))
                self.onto_stats[self.shaclNS.nodeKind] -= 1
            elif ((bnode, self.shaclNS.nodeKind, self.shaclNS.BlankNodeOrLiteral) in RML2SHACLgraph) and ((bnode, self.shaclNS.nodeKind, self.shaclNS.BlankNode) in RML2SHACLgraph):
                RML2SHACLgraph.remove((bnode, self.shaclNS.nodeKind, self.shaclNS.BlankNodeOrLiteral))
                self.onto_stats[self.shaclNS.nodeKind] -= 1
            elif ((bnode, self.shaclNS.nodeKind, self.shaclNS.BlankNodeOrIRI) in RML2SHACLgraph) and ((bnode, self.shaclNS.nodeKind, self.shaclNS.IRI) in RML2SHACLgraph):
                RML2SHACLgraph.remove((bnode, self.shaclNS.nodeKind, self.shaclNS.BlankNodeOrIRI))
                self.onto_stats[self.shaclNS.nodeKind] -= 1
            elif ((bnode, self.shaclNS.nodeKind, self.shaclNS.BlankNodeOrIRI) in RML2SHACLgraph) and ((bnode, self.shaclNS.nodeKind, self.shaclNS.BlankNode) in RML2SHACLgraph):
                RML2SHACLgraph.remove((bnode, self.shaclNS.nodeKind, self.shaclNS.BlankNodeOrIRI))
                self.onto_stats[self.shaclNS.nodeKind] -= 1

    def add_ontology_item(self, g, s, p, o, g2=None):
        if type(o) == rdflib.term.BNode:
            new_BNode = rdflib.BNode()
            self.onto_stats_add(p)
            g.add((s, p, new_BNode))
            for p2, o2 in g2.predicate_objects(o):
                self.add_ontology_item(g, new_BNode, p2, o2, g2)
        else:
            if type(o) == rdflib.term.URIRef and str(o).startswith('https://astrea.linkeddata.es/shapes'):
                if (o, self.rdfSyntax.type, None) not in g:
                    if (o, self.rdfSyntax.type, self.shaclNS.NodeShape) in g2:
                        targetclass = g2.value(subject=o, predicate=self.shaclNS.targetClass)
                        for s2 in g.subjects(self.shaclNS.targetClass, rdflib.Literal(targetclass)):
                            self.onto_stats_add(p)
                            g.add((s, p, s2))
                    else:
                        self.onto_stats_add(p)
                        g.add((s, p, o))
                        for p2, o2 in g2.predicate_objects(o):
                            self.add_ontology_item(g, o, p2, o2, g2)
            else:
                self.onto_stats_add(p)
                g.add((s, p, o))

    def onto_stats_add(self, p):
        if p in self.onto_stats:
            self.onto_stats[p] += 1
        else:
            self.onto_stats[p] = 1

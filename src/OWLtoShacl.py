import contextlib
import os
import subprocess
import rdflib
from rdflib import URIRef

from .RML import *
from .SHACL import *
from .EnrichShacl import *


class OWLtoSHACL:
    def __init__(self):
        self.RML = RML()
        self.EnrichSHACL = EnrichSHACL()
        self.shaclNS = rdflib.Namespace('http://www.w3.org/ns/shacl#')
        self.rdfSyntax = rdflib.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
        self.XSDNS = rdflib.Namespace('http://www.w3.org/2001/XMLSchema#')
        self.AstreaArgs = []
        self.AstreaKG = f"{os.path.dirname(os.path.dirname(__file__))}/Astrea-KG.ttl"
        self.astreajarpath = (
            f"{os.path.dirname(os.path.dirname(__file__))}/Astrea2SHACL.jar"
        )


    def getPrefixOntologies(self):
        for namespace in self.RML.graph.namespaces():
            with contextlib.suppress(Exception):
                g = rdflib.Graph()
                g.parse(namespace[1])
                self.AstreaArgs += [str(namespace[1])]

    def getFileOntologies(self, ontology_dir):
        if ontology_dir is not None:
            for ontology in os.listdir(ontology_dir):
                file = os.path.join(ontology_dir, ontology)
                with contextlib.suppress(Exception):
                    g = rdflib.Graph()
                    g.parse(file)
                    self.AstreaArgs += [str(file)]

    def convertOntologies(self, RML2SHACLgraph):
        subprocesscommand = ['java', '-jar', self.astreajarpath, self.AstreaKG]
        subprocesscommand.extend(iter(self.AstreaArgs))
        result = subprocess.check_output(subprocesscommand, stderr=subprocess.STDOUT, text=True)
        graphs = result.split('Astrea2SHACLGraphDelimiter\n')
        for item in graphs:
            if item != "":
                graph = rdflib.Graph()
                graph.parse(data=item, format="turtle")
                self.enrichWithOntology(graph, RML2SHACLgraph)

    def enrichWithOntology(self, ontology_graph, RML2SHACLgraph):
        nodeshape_blacklist = [self.shaclNS.targetClass,
                               self.rdfSyntax.type]

        propertyshape_blacklist = [self.shaclNS.targetClass,
                                   self.rdfSyntax.type]

        # Get a list of all targetClasses
        q1 = f'SELECT ?nodeshape ?targetclass {{?nodeshape a <{self.shaclNS.NodeShape}> .?nodeshape <{self.shaclNS.targetClass}> ?targetclass.}}'
        x1 = RML2SHACLgraph.query(q1)

        # Get the constraints for each targetClass and add them to the rml2shacl shapes
        for row in x1:
            q2 = f'SELECT ?p ?o {{?s a <{self.shaclNS.NodeShape}> .?s <{self.shaclNS.targetClass}> <{row.targetclass}> .?s ?p ?o}}'
            x2 = ontology_graph.query(q2)
            q3 = f'SELECT ?p ?o {{?s a <{self.shaclNS.NodeShape}> .?s <{self.shaclNS.targetClass}> \"{row.targetclass}\" .?s ?p ?o}}'
            x3 = RML2SHACLgraph.query(q3)
            q5 = f'SELECT ?bnode ?p ?o {{<{row.nodeshape}> a <{self.shaclNS.NodeShape}> .<{row.nodeshape}> <{self.shaclNS.property}> ?bnode. ?bnode ?p ?o}}'
            x5 = RML2SHACLgraph.query(q5)
            property_BNodes_dict = {
                row5.o: row5.bnode for row5 in x5 if row5.p == self.shaclNS.path
            }
            for row2 in x2:
                if row2.p not in nodeshape_blacklist:
                    if row2.p != self.shaclNS.property:
                        for row3 in x3:
                            if row2.p == row3.p:
                                break
                        else:
                            self.evalOntologyConstraint(RML2SHACLgraph, row.nodeshape, row2.p, row2.o, ontology_graph)
                    else:
                        q4 = f'SELECT ?p ?o {{<{row2.o}> a <{self.shaclNS.PropertyShape}> .<{row2.o}> ?p ?o}}'
                        x4 = ontology_graph.query(q4)
                        property_dict = {
                            row4.p: row4.o
                            for row4 in x4
                            if (row4.p not in propertyshape_blacklist)
                            and (
                                row4.p
                                != rdflib.term.URIRef(
                                    'http://www.w3.org/ns/shacl#pattern'
                                )
                                or row4.o != rdflib.term.Literal('.*')
                            )
                        }
                        if property_dict.get(self.shaclNS.path) in property_BNodes_dict:
                            for item, value in property_dict.items():
                                for row5 in x5:
                                    if item == row5.p:
                                        break
                                else:
                                    self.evalOntologyConstraint(
                                        RML2SHACLgraph,
                                        property_BNodes_dict[
                                            property_dict[self.shaclNS.path]
                                        ],
                                        item,
                                        value,
                                        ontology_graph,
                                    )

    def evalOntologyConstraint(self, g, s, p, o, g2=None):
        if type(o) == rdflib.term.BNode:
            new_BNode = rdflib.BNode()
            self.EnrichSHACL.enrich(g, s, p, new_BNode)
            for p2, o2 in g2.predicate_objects(o):
                self.evalOntologyConstraint(g, new_BNode, p2, o2, g2)
        elif type(o) == rdflib.term.URIRef and str(o).startswith('https://astrea.linkeddata.es/shapes'):
            if (o, self.rdfSyntax.type, None) not in g:
                if (o, self.rdfSyntax.type, self.shaclNS.NodeShape) in g2:
                    targetclass = g2.value(subject=o, predicate=self.shaclNS.targetClass)
                    for s2 in g.subjects(self.shaclNS.targetClass, rdflib.Literal(targetclass)):
                        self.EnrichSHACL.enrich(g, s2, p, o)
                else:
                    self.EnrichSHACL.enrich(g, s, p, o)
                    for p2, o2 in g2.predicate_objects(o):
                        self.evalOntologyConstraint(g, o, p2, o2, g2)
        else:
            self.EnrichSHACL.enrich(g, s, p, o)


import argparse
import csv
import logging
import os
from pathlib import Path
import string
import time
import timeit
from typing import Any, List
import requests

import rdflib
from rdflib import URIRef
from rdflib import RDF
from requests.exceptions import HTTPError

from .RML import *
from .SHACL import *


class RMLtoSHACL:
    def __init__(self):
        self.RML = RML()
        self.shaclNS = rdflib.Namespace('http://www.w3.org/ns/shacl#')
        self.rdfSyntax = rdflib.Namespace(
            'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
        self.SHACL = SHACL()

    def helpAddTriples(self, shacl_graph: Graph, sub: Identifier,
                       pred: Identifier, obj_arr: Optional[List[Identifier]]) -> None:
        """
        This method takes an array of object terms (obj_arr)  associated with
        the given predicate (pred) and add them to the
        subject node (sub) as triples.
        """

        if obj_arr is None:
            return

        for el in obj_arr:
            shacl_graph.add(
                (sub, pred, el))

    def transformIRI(self, node: Identifier, shacl_graph: Graph) -> None:
        shacl_graph.add((node, self.shaclNS.nodeKind, self.shaclNS.IRI))

    def transformBlankNode(self, node: Identifier, shacl_graph: Graph) -> None:
        shacl_graph.add((node, self.shaclNS.nodeKind, self.shaclNS.BlankNode))

    def transformList(self, node: Identifier, arr: List[Any], shacl_graph: Graph) -> None:
        """
        Transform the given array objects into RDF compliant array list.
        The transformation is done in the manner of a functional list.
        """
        current_node = node
        next_node = rdflib.BNode()
        size = len(arr)
        for i, obj in enumerate(arr):

            shacl_graph.add(
                (current_node, self.rdfSyntax.first, rdflib.Literal(obj)))

            if i != size - 1:
                shacl_graph.add(
                    (current_node, self.rdfSyntax.rest, next_node))
            else:
                shacl_graph.add(
                    (current_node, self.rdfSyntax.rest, self.rdfSyntax.nil))
            current_node = next_node
            next_node = rdflib.BNode()

    def transformLiteral(self, node: Identifier, termMap: TermMap, shacl_graph: Graph) -> None:

        shacl_graph.add((node, self.shaclNS.nodeKind, self.shaclNS.Literal))

        # Transform rr:language
        # it can be a list of languages
        language_iri = self.RML.LANGUAGE
        if language_iri in termMap.po_dict:
            languages_arr = termMap.po_dict[language_iri]

            for language in languages_arr:
                languageBlank = rdflib.BNode()
                shacl_graph.add(
                    (node, self.shaclNS.languageIn, languageBlank))
                self.transformList(languageBlank, language.split('-'), shacl_graph)

                # Transform rr:datatype
        datatype_iri = self.RML.DATATYPE
        if datatype_iri in termMap.po_dict:
            self.helpAddTriples(shacl_graph, node,
                                self.shaclNS.datatype, termMap.po_dict[datatype_iri])

    def serializeTemplate(self, templateString: Identifier) -> Identifier:
        # we want to replace this {word} into a wildcard ='.'
        # and '*' means zero or unlimited amount of characters
        parts = templateString.split('{')
        parts2 = []
        for part in parts:
            if '}' in part:
                parts2 = parts2 + part.split('}')
            else:
                parts2 = parts2 + [part]
        string = ''
        tel = 1
        for part in parts2:
            if tel % 2 != 0:
                string = string + part
            else:
                string = string + '.*'
            # wildcard = '.' + '*'
            tel += 1
        resultaat = rdflib.Literal(string)
        return resultaat

    def createNodeShape(self, triples_map: TriplesMap, shacl_graph: Graph) -> Identifier:
        # start of SHACL shape

        subjectShape = rdflib.URIRef(triples_map.iri + "/shape")
        shacl_graph.add((subjectShape, rdflib.RDF.type, self.shaclNS.NodeShape))
        self.transformSubjectMap(subjectShape, triples_map.sm, shacl_graph)
        return subjectShape

    def transformSubjectMap(self, node: Identifier, subjectmap: SubjectMap, shacl_graph: Graph) -> None:
        """
        Transform the given SubjectMap into the corresponding SHACL shapes and
        store them in the self.SHACL's rdflib graph.
        """

        po_dict = subjectmap.po_dict

        # Start of class and targetNode shacl mapping
        self.helpAddTriples(shacl_graph, node,
                            self.shaclNS.targetNode,
                            po_dict.get(self.RML.CONSTANT, []))

        self.helpAddTriples(shacl_graph, node,
                            self.shaclNS.targetClass,
                            po_dict.get(self.RML.CLASS, []))

        self.helpAddTriples(shacl_graph, node,
                            self.shaclNS["class"],
                            po_dict.get(self.RML.CLASS, []))

        # End of class and targetNode shacl mapping

        # Shacl shl:pattern parsing
        template_strings = [self.serializeTemplate(x)
                            for x in po_dict.get(self.RML.TEMPLATE, [])]
        self.helpAddTriples(shacl_graph, node,
                            self.shaclNS.pattern, template_strings)

        # Uri or Literal parsing
        self.transformIRIorLiteralorBlankNode(po_dict, node, subjectmap, shacl_graph)

    def transformIRIorLiteralorBlankNode(self, po_dict: Dict[URIRef, List[Any]],
                                         node: Identifier, termMap: TermMap,
                                         shacl_graph: Graph) -> None:
        # Uri or Literal parsing
        type_arr = po_dict.get(self.RML.TERMTYPE)
        if type_arr:
            term_type = type_arr[0]
            if term_type == self.RML.r2rmlNS.Literal:
                self.transformLiteral(node, termMap, shacl_graph)
            elif term_type == self.RML.r2rmlNS.IRI:
                self.transformIRI(node, shacl_graph)
            elif term_type == self.RML.r2rmlNS.BlankNode:
                self.transformBlankNode(node, shacl_graph)
            else:
                print(f"WARNING: {term_type} is not a valid term type for {self}, defaulting to IRI")
                self.transformIRI(node, shacl_graph)

        # default behaviour if no termType is defined
        elif po_dict.get(self.RML.REFERENCE):
            self.transformLiteral(node, termMap, shacl_graph)
        else:
            self.transformIRI(node, shacl_graph)

    def transformPOM(self, node: Identifier, pom: PredicateObjectMap, shacl_graph: Graph) -> None:

        pm = pom.PM
        om = pom.OM

        # Find the subject's class in
        # Check if it defines the class of the subject node (node) and
        # return immediately since the pom is parsed
        pred_constant_objs = pm.po_dict.get(self.RML.CONSTANT)
        if pred_constant_objs and pred_constant_objs[0] == rdflib.RDF.type:
            om_constant_objs = om.po_dict.get(self.RML.CONSTANT)
            self.helpAddTriples(shacl_graph, node,
                                self.shaclNS.targetClass, om_constant_objs)
            return

            # Fill in the sh:property node of the given subject (@param node)
        sh_property = rdflib.BNode()
        shacl_graph.add(
            (node, self.shaclNS.property, sh_property))

        self.transformIRIorLiteralorBlankNode(om.po_dict, sh_property, om, shacl_graph)
        ptm = om.po_dict.get(self.RML.r2rmlNS.parentTriplesMap)
        if ptm:
            ptm = ptm[0] + "/shape"
            shacl_graph.add(
                (sh_property, self.shaclNS.node, ptm))

        self.helpAddTriples(shacl_graph, sh_property,
                            self.shaclNS.path, pm.po_dict.get(self.RML.CONSTANT))

    def writeShapeToFile(self, file_name, shape_dir="shapes/"):
        for prefix, ns in self.RML.graph.namespaces():
            self.SHACL.graph.bind(prefix, ns)
            # @base is used for <> in the RML ttl graph
        self.SHACL.graph.bind('sh', 'http://www.w3.org/ns/shacl#', False)
        self.SHACL.graph.bind(
            'rdfs', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')

        parent_folder = os.path.dirname(file_name)

        Path(f"%s%s" % (shape_dir, parent_folder)).mkdir(
            parents=True, exist_ok=True)

        filenNameShape = "%s%s" % (shape_dir, file_name)

        self.SHACL.graph.serialize(destination=filenNameShape, format='turtle')

        return filenNameShape

    def evaluate_files(self, rml_mapping_file, ontology_file):

        self.evaluate_mapping(rml_mapping_file)
        if ontology_file is not None:
            self.enrich_ontology(self.evaluate_ontology(ontology_file))

        outputfileName = f"{rml_mapping_file}-mapping-shape.ttl"
        self.writeShapeToFile(outputfileName)

        validation_shape_graph = rdflib.Graph()
        validation_shape_graph.parse("shacl-shacl.ttl", format="turtle")

        self.SHACL.Validation(validation_shape_graph, self.SHACL.graph)

        logging.debug("*" * 100)
        logging.debug("RESULTS")
        logging.debug("=" * 100)
        logging.debug(self.SHACL.results_text)
        print(self.SHACL.results_text)

        return None

    def evaluate_mapping(self, rml_mapping_file):
        self.RML.parseFile(rml_mapping_file)

        for _, triples_map in self.RML.tm_model_dict.items():
            subject_shape_node = self.createNodeShape(triples_map, self.SHACL.graph)

            for pom in triples_map.poms:
                self.transformPOM(subject_shape_node, pom, self.SHACL.graph)

        return None

    def evaluate_ontology(self, ontology_file):
        url = "https://astrea.linkeddata.es/api/shacl/file"
        files = {'file': (ontology_file, open(ontology_file, 'rb'))}
        params = {'format': 'Turtle'}

        r_onto = requests.post(url=url, params=params, files=files)
        g_astrea = rdflib.Graph()
        g_astrea.parse(r_onto.content)

        return g_astrea

    def enrich_ontology(self, ontology_graph):
        nodeshape_blacklist = [URIRef("http://www.w3.org/ns/shacl#targetClass"),
                               URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
                               URIRef("http://www.w3.org/2000/01/rdf-schema#label"),
                               URIRef("http://www.w3.org/ns/shacl#description"),
                               URIRef("http://www.w3.org/ns/shacl#name")]

        propertyshape_blacklist = [URIRef("http://www.w3.org/ns/shacl#targetClass"),
                                   URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
                                   URIRef("http://www.w3.org/2000/01/rdf-schema#label"),
                                   URIRef("http://www.w3.org/ns/shacl#description"),
                                   URIRef("http://www.w3.org/ns/shacl#name")]

        # Get a list of all targetClasses
        q1 = f'SELECT ?nodeshape ?targetclass {{?nodeshape a <{URIRef("http://www.w3.org/ns/shacl#NodeShape")}> .?nodeshape <{URIRef("http://www.w3.org/ns/shacl#targetClass")}> ?targetclass.}}'
        x1 = self.SHACL.graph.query(q1)

        # Get the constraints for each targetClass and add them to the rml2shacl shapes
        for row in x1:
            # print(f"{row.targetclass}")

            q2 = f'SELECT ?p ?o {{?s a <{URIRef("http://www.w3.org/ns/shacl#NodeShape")}> .?s <{URIRef("http://www.w3.org/ns/shacl#targetClass")}> <{row.targetclass}> .?s ?p ?o}}'
            x2 = ontology_graph.query(q2)
            q3 = f'SELECT ?p ?o {{?s a <{URIRef("http://www.w3.org/ns/shacl#NodeShape")}> .?s <{URIRef("http://www.w3.org/ns/shacl#targetClass")}> \"{row.targetclass}\" .?s ?p ?o}}'
            x3 = self.SHACL.graph.query(q3)
            property_BNodes_dict = dict()
            q5 = f'SELECT ?bnode ?p ?o {{<{row.nodeshape}> a <{URIRef("http://www.w3.org/ns/shacl#NodeShape")}> .<{row.nodeshape}> <{URIRef("http://www.w3.org/ns/shacl#property")}> ?bnode. ?bnode ?p ?o}}'
            x5 = self.SHACL.graph.query(q5)
            for row5 in x5:
                if row5.p not in propertyshape_blacklist:
                    if row5.p == URIRef("http://www.w3.org/ns/shacl#path"):
                        property_BNodes_dict[row5.o] = row5.bnode
            for row2 in x2:
                if row2.p not in nodeshape_blacklist:
                    if row2.p != URIRef("http://www.w3.org/ns/shacl#property"):
                        for row3 in x3:
                            if row2.p == row3.p:
                                break
                        else:
                            # print(f"added constraint to {row.nodeshape}: {row2.p} || {row2.o}")
                            self.SHACL.graph.add((row.nodeshape, row2.p, row2.o))
                    else:
                        property_dict = dict()
                        q4 = f'SELECT ?p ?o {{<{row2.o}> a <{URIRef("http://www.w3.org/ns/shacl#PropertyShape")}> .<{row2.o}> ?p ?o}}'
                        x4 = ontology_graph.query(q4)
                        for row4 in x4:
                            if row4.p not in propertyshape_blacklist:
                                property_dict[row4.p] = row4.o
                        if property_dict.get(URIRef("http://www.w3.org/ns/shacl#path")) in property_BNodes_dict:
                            for item in property_dict:
                                self.SHACL.graph.add(
                                    (property_BNodes_dict[property_dict[URIRef("http://www.w3.org/ns/shacl#path")]],
                                     item,
                                     property_dict[item]))
                                # print(f"added property to {row.nodeshape}: {item} || {property_dict[item]}")
                        else:
                            new_BNode = rdflib.BNode()
                            self.SHACL.graph.add(
                                (row.nodeshape, URIRef("http://www.w3.org/ns/shacl#property"), new_BNode))
                            for item in property_dict:
                                self.SHACL.graph.add((new_BNode, item, property_dict[item]))
                                # print(f"added property to {row.nodeshape}: {item} || {property_dict[item]}")

        property_BNodes_dict = dict()
        q6 = f'SELECT ?bnode {{?s a <{URIRef("http://www.w3.org/ns/shacl#NodeShape")}> .?s <{URIRef("http://www.w3.org/ns/shacl#property")}> ?bnode.}}'
        x6 = self.SHACL.graph.query(q6)
        BNode_list = list()
        for row6 in x6:
            if type(row6.bnode) == rdflib.term.BNode:
                BNode_list += [row6.bnode]

        for bnode in BNode_list:
            if ((bnode, URIRef("http://www.w3.org/ns/shacl#nodeKind"),
                 URIRef("http://www.w3.org/ns/shacl#IRIOrLiteral")) in self.SHACL.graph) and ((bnode,
                                                                                               URIRef(
                                                                                                   "http://www.w3.org/ns/shacl#nodeKind"),
                                                                                               URIRef(
                                                                                                   "http://www.w3.org/ns/shacl#IRI")) in self.SHACL.graph):
                self.SHACL.graph.remove((bnode, URIRef("http://www.w3.org/ns/shacl#nodeKind"),
                                         URIRef("http://www.w3.org/ns/shacl#IRIOrLiteral")))
            elif ((bnode, URIRef("http://www.w3.org/ns/shacl#nodeKind"),
                   URIRef("http://www.w3.org/ns/shacl#IRIOrLiteral")) in self.SHACL.graph) and ((bnode,
                                                                                                 URIRef(
                                                                                                     "http://www.w3.org/ns/shacl#nodeKind"),
                                                                                                 URIRef(
                                                                                                     "http://www.w3.org/ns/shacl#Literal")) in self.SHACL.graph):
                self.SHACL.graph.remove((bnode, URIRef("http://www.w3.org/ns/shacl#nodeKind"),
                                         URIRef("http://www.w3.org/ns/shacl#IRIOrLiteral")))
            elif ((bnode, URIRef("http://www.w3.org/ns/shacl#nodeKind"),
                   URIRef("http://www.w3.org/ns/shacl#BlankNodeOrLiteral")) in self.SHACL.graph) and ((bnode,
                                                                                                       URIRef(
                                                                                                           "http://www.w3.org/ns/shacl#nodeKind"),
                                                                                                       URIRef(
                                                                                                           "http://www.w3.org/ns/shacl#Literal")) in self.SHACL.graph):
                self.SHACL.graph.remove((bnode, URIRef("http://www.w3.org/ns/shacl#nodeKind"),
                                         URIRef("http://www.w3.org/ns/shacl#BlankNodeOrLiteral")))
            elif ((bnode, URIRef("http://www.w3.org/ns/shacl#nodeKind"),
                   URIRef("http://www.w3.org/ns/shacl#BlankNodeOrLiteral")) in self.SHACL.graph) and ((bnode,
                                                                                                       URIRef(
                                                                                                           "http://www.w3.org/ns/shacl#nodeKind"),
                                                                                                       URIRef(
                                                                                                           "http://www.w3.org/ns/shacl#BlankNode")) in self.SHACL.graph):
                self.SHACL.graph.remove((bnode, URIRef("http://www.w3.org/ns/shacl#nodeKind"),
                                         URIRef("http://www.w3.org/ns/shacl#BlankNodeOrLiteral")))
            elif ((bnode, URIRef("http://www.w3.org/ns/shacl#nodeKind"),
                   URIRef("http://www.w3.org/ns/shacl#BlankNodeOrIRI")) in self.SHACL.graph) and ((bnode,
                                                                                                   URIRef(
                                                                                                       "http://www.w3.org/ns/shacl#nodeKind"),
                                                                                                   URIRef(
                                                                                                       "http://www.w3.org/ns/shacl#IRI")) in self.SHACL.graph):
                self.SHACL.graph.remove((bnode, URIRef("http://www.w3.org/ns/shacl#nodeKind"),
                                         URIRef("http://www.w3.org/ns/shacl#BlankNodeOrIRI")))
            elif ((bnode, URIRef("http://www.w3.org/ns/shacl#nodeKind"),
                   URIRef("http://www.w3.org/ns/shacl#BlankNodeOrIRI")) in self.SHACL.graph) and ((bnode,
                                                                                                   URIRef(
                                                                                                       "http://www.w3.org/ns/shacl#nodeKind"),
                                                                                                   URIRef(
                                                                                                       "http://www.w3.org/ns/shacl#BlankNode")) in self.SHACL.graph):
                self.SHACL.graph.remove((bnode, URIRef("http://www.w3.org/ns/shacl#nodeKind"),
                                         URIRef("http://www.w3.org/ns/shacl#BlankNodeOrIRI")))

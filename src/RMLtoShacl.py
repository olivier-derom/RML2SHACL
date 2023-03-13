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
import json
import subprocess
import re

import rdflib
from rdflib import URIRef
from rdflib import RDF
from requests.exceptions import HTTPError

import xml.etree.ElementTree as ET

from .RML import *
from .SHACL import *


class RMLtoSHACL:
    def __init__(self):
        self.RML = RML()
        self.shaclNS = rdflib.Namespace('http://www.w3.org/ns/shacl#')
        self.rdfSyntax = rdflib.Namespace(
            'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
        self.XSDNS = rdflib.Namespace(
            'http://www.w3.org/2001/XMLSchema#')
        self.SHACL = SHACL()
        self.AstreaArgs = []
        self.astreageneratedpath = str(os.getcwd()) + "\\temp\\AstreaGenerated"
        self.temp_imported_onto_folder = str(os.getcwd()) + "\\temp\\imported_ontologies_turtle"
        self.AstreaKG = str(os.getcwd()) + "\\Astrea-KG.ttl"
        self.astreajarpath = str(os.getcwd()) + "\\Astrea2SHACL.jar"

        # temp vars
        # also see lines 268-270, 391,394,397,400,403,406,411,421,424,429, 432-437
        self.onto_stats = dict()

        # XSD related vars
        # add all the namespaces used in the XSD's here
        self.XSDNS2 = dict()
        self.named_type_constraints = dict()
        self.XSDtree = None
        self.XSD_elements = dict()
        self.named_types = None
        self.XSDtargetNamespace = "http://example.com"

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
            if pred == self.shaclNS.targetClass:
                shacl_graph.add(
                    (sub, pred, URIRef(el)))
            else:
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

    def evaluate_files(self, rml_mapping_file, ontology_dir=None, schema_dir=None):

        self.evaluate_mapping(rml_mapping_file)

        if schema_dir is not None:
            for schema in os.listdir(schema_dir):
                file = os.path.join(schema_dir, schema)
                if file.endswith(".xsd"):
                    self.import_xsd_constraints(file)

        if not os.path.exists(self.astreageneratedpath):
            os.makedirs(self.astreageneratedpath)
        if not os.path.exists(self.temp_imported_onto_folder):
            os.makedirs(self.temp_imported_onto_folder)

        self.get_file_ontologies(ontology_dir)

        self.get_prefix_ontologies()

        self.convert_ontologies()

        for astreafile in os.listdir(self.astreageneratedpath):
            file = os.path.join(self.astreageneratedpath, astreafile)
            try:
                g = rdflib.Graph()
                g.parse(file)
                self.enrich_ontology(g)
            except:
                pass

        outputfileName = f"{rml_mapping_file}-output-shape.ttl"
        self.writeShapeToFile(outputfileName)

        outputfiledict = f"shapes/{rml_mapping_file}-dict.txt"
        with open(outputfiledict, 'w') as data:
            data.write(str(self.onto_stats))

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

    def get_prefix_ontologies(self):
        for namespace in self.RML.graph.namespaces():
            try:
                g = rdflib.Graph()
                g.parse(namespace[1])
                self.AstreaArgs += [str(namespace[1])]
            except:
                pass

    def get_file_ontologies(self, ontology_dir):
        if ontology_dir is not None:
            for ontology in os.listdir(ontology_dir):
                file = os.path.join(ontology_dir, ontology)
                try:
                    g = rdflib.Graph()
                    g.parse(file)
                    destination = str(self.temp_imported_onto_folder + "\\" + ontology)
                    g.serialize(destination=destination, format='turtle')
                except:
                    pass
            for ontology in os.listdir(self.temp_imported_onto_folder):
                file = os.path.join(self.temp_imported_onto_folder, ontology)
                self.AstreaArgs += [str(file)]

    def convert_ontologies(self):
        subprocesscommand = ['java', '-jar', self.astreajarpath, self.AstreaKG]
        for item in self.AstreaArgs:
            subprocesscommand.append(item)
        subprocess.call(subprocesscommand, cwd=self.astreageneratedpath)

    def enrich_ontology(self, ontology_graph):
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
        x1 = self.SHACL.graph.query(q1)

        # Get the constraints for each targetClass and add them to the rml2shacl shapes
        for row in x1:
            q2 = f'SELECT ?p ?o {{?s a <{self.shaclNS.NodeShape}> .?s <{self.shaclNS.targetClass}> <{row.targetclass}> .?s ?p ?o}}'
            x2 = ontology_graph.query(q2)
            q3 = f'SELECT ?p ?o {{?s a <{self.shaclNS.NodeShape}> .?s <{self.shaclNS.targetClass}> \"{row.targetclass}\" .?s ?p ?o}}'
            x3 = self.SHACL.graph.query(q3)
            property_BNodes_dict = dict()
            q5 = f'SELECT ?bnode ?p ?o {{<{row.nodeshape}> a <{self.shaclNS.NodeShape}> .<{row.nodeshape}> <{self.shaclNS.property}> ?bnode. ?bnode ?p ?o}}'
            x5 = self.SHACL.graph.query(q5)
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
                            self.add_ontology_item(self.SHACL.graph, row.nodeshape, row2.p, row2.o, ontology_graph)
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
                                    self.add_ontology_item(self.SHACL.graph, property_BNodes_dict[property_dict[self.shaclNS.path]], item, property_dict[item], ontology_graph)

        property_BNodes_dict = dict()
        q6 = f'SELECT ?bnode {{?s a <{self.shaclNS.NodeShape}> .?s <{self.shaclNS.property}> ?bnode.}}'
        x6 = self.SHACL.graph.query(q6)
        BNode_list = list()
        for row6 in x6:
            if type(row6.bnode) == rdflib.term.BNode:
                BNode_list += [row6.bnode]

        for bnode in BNode_list:
            if ((bnode, self.shaclNS.nodeKind, self.shaclNS.IRIOrLiteral) in self.SHACL.graph) and ((bnode, self.shaclNS.nodeKind,  self.shaclNS.IRI) in self.SHACL.graph):
                self.SHACL.graph.remove((bnode, self.shaclNS.nodeKind, self.shaclNS.IRIOrLiteral))
                self.onto_stats[self.shaclNS.nodeKind] -= 1
            elif ((bnode, self.shaclNS.nodeKind, self.shaclNS.IRIOrLiteral) in self.SHACL.graph) and ((bnode, self.shaclNS.nodeKind, self.shaclNS.Literal) in self.SHACL.graph):
                self.SHACL.graph.remove((bnode, self.shaclNS.nodeKind, self.shaclNS.IRIOrLiteral))
                self.onto_stats[self.shaclNS.nodeKind] -= 1
            elif ((bnode, self.shaclNS.nodeKind, self.shaclNS.BlankNodeOrLiteral) in self.SHACL.graph) and ((bnode, self.shaclNS.nodeKind, self.shaclNS.Literal) in self.SHACL.graph):
                self.SHACL.graph.remove((bnode, self.shaclNS.nodeKind, self.shaclNS.BlankNodeOrLiteral))
                self.onto_stats[self.shaclNS.nodeKind] -= 1
            elif ((bnode, self.shaclNS.nodeKind, self.shaclNS.BlankNodeOrLiteral) in self.SHACL.graph) and ((bnode, self.shaclNS.nodeKind, self.shaclNS.BlankNode) in self.SHACL.graph):
                self.SHACL.graph.remove((bnode, self.shaclNS.nodeKind, self.shaclNS.BlankNodeOrLiteral))
                self.onto_stats[self.shaclNS.nodeKind] -= 1
            elif ((bnode, self.shaclNS.nodeKind, self.shaclNS.BlankNodeOrIRI) in self.SHACL.graph) and ((bnode, self.shaclNS.nodeKind, self.shaclNS.IRI) in self.SHACL.graph):
                self.SHACL.graph.remove((bnode, self.shaclNS.nodeKind, self.shaclNS.BlankNodeOrIRI))
                self.onto_stats[self.shaclNS.nodeKind] -= 1
            elif ((bnode, self.shaclNS.nodeKind, self.shaclNS.BlankNodeOrIRI) in self.SHACL.graph) and ((bnode, self.shaclNS.nodeKind, self.shaclNS.BlankNode) in self.SHACL.graph):
                self.SHACL.graph.remove((bnode, self.shaclNS.nodeKind, self.shaclNS.BlankNodeOrIRI))
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

    def get_xsd_element_info(self, element, parent_name=None, is_attribute=False):
        element_name = self.XSDtargetNamespace+'/'+str(element.get('name'))
        if element_name is None:
            return None
        if element.find('xs:complexType', self.XSDNS2) is not None:
            element_dict = {'ElementName': element_name, 'ElementType': 'Element'}
            element_dict.update(element.attrib)
            if parent_name:
                element_dict['parent'] = parent_name
            for child_element in element.findall('xs:complexType/xs:sequence/xs:element', self.XSDNS2):
                child_element_info = self.get_xsd_element_info(child_element, element_name)
                if child_element_info is not None:
                    if child_element_info != "enumeration":
                        if "children" not in element_dict:
                            element_dict["children"] = [f"{child_element_info}"]
                        else:
                            element_dict["children"] += [f"{child_element_info}"]
                    else:
                        if "enumeration" not in element_dict:
                            element_dict[f"{child_element_info}"] = [element_name]
                        else:
                            element_dict[f"{child_element_info}"] += [element_name]
            for attribute in element.findall('xs:complexType/xs:attribute', self.XSDNS2):
                child_element_info = self.get_xsd_element_info(attribute, element_name, True)
                if child_element_info is not None:
                    if child_element_info != "enumeration":
                        if "children" not in element_dict:
                            element_dict["children"] = [f"{child_element_info}"]
                        else:
                            element_dict["children"] += [f"{child_element_info}"]
                    else:
                        if "enumeration" not in element_dict:
                            element_dict[f"{child_element_info}"] = [element_name]
                        else:
                            element_dict[f"{child_element_info}"] += [element_name]
        elif element.find('xs:simpleType', self.XSDNS2) is not None:
            element_dict = {'ElementName': element_name, 'ElementType': 'Element'}
            element_dict.update(element.attrib)
            if parent_name:
                element_dict['parent'] = parent_name
            simple_type = element.find('xs:simpleType', self.XSDNS2)
            data_type = simple_type.find('xs:restriction', self.XSDNS2).get('base')
            element_dict["type"] = data_type
            for child_element in simple_type.findall('xs:restriction/*', self.XSDNS2):
                child_element_info = child_element.tag.split('}')[1]
                if child_element_info != "enumeration":
                    element_dict[f"{child_element_info}"] = child_element.get('value')
                else:
                    if "enumeration" not in element_dict:
                        element_dict[f"{child_element_info}"] = [child_element.get('value')]
                    else:
                        element_dict[f"{child_element_info}"] += [child_element.get('value')]
            for attribute in element.findall('xs:complexType/xs:attribute', self.XSDNS2):
                child_element_info = self.get_xsd_element_info(attribute, element_name, True)
                if child_element_info is not None:
                    if child_element_info != "enumeration":
                        if "children" not in element_dict:
                            element_dict["children"] = [f"{child_element_info}"]
                        else:
                            element_dict["children"] += [f"{child_element_info}"]
                    else:
                        if "enumeration" not in element_dict:
                            element_dict[f"{child_element_info}"] = [element_name]
                        else:
                            element_dict[f"{child_element_info}"] += [element_name]
        elif is_attribute:
            element_dict = {'ElementName': element_name, 'ElementType': 'Attribute'}
            if parent_name:
                element_dict['parent'] = parent_name
            element_dict.update(element.attrib)
            if "type" in element_dict:
                type_name = element.attrib["type"].split(":")[-1]
                if type_name in self.named_type_constraints:
                    element_dict.pop("type")
                    constraints = self.named_type_constraints[type_name]
                    for constraint_name, constraint_value in constraints.items():
                        element_dict[constraint_name.split('}')[1]] = constraint_value
        else:
            element_dict = {'ElementName': element_name, 'ElementType': 'Element'}
            if parent_name:
                element_dict['parent'] = parent_name
            element_dict.update(element.attrib)
            if "type" in element_dict:
                type_name = element.attrib["type"].split(":")[-1]
                if type_name in self.named_type_constraints:
                    element_dict.pop("type")
                    constraints = self.named_type_constraints[type_name]
                    for constraint_name, constraint_value in constraints.items():
                        element_dict[constraint_name.split('}')[1]] = constraint_value
        if "name" in element_dict:
            element_dict.pop("name")

        self.XSD_elements[str(element_name)] = element_dict
        return element_name

    def extract_xsd_constraints(self, named_type):
        named_type_name = named_type.attrib.get("name")
        if named_type_name is not None:
            if named_type_name in self.named_type_constraints:
                return self.named_type_constraints[named_type_name]
            constraints = {}
            restriction = named_type.find("./xs:restriction", self.XSDNS2)
            base = restriction.attrib.get("base")
            constraints["{http://www.w3.org/2001/XMLSchema}type"] = base
            for child in restriction:
                if child.tag == "{http://www.w3.org/2001/XMLSchema}restriction":
                    named_type_name = child.attrib.get("base").split(":")[-1]
                    nested_constraints = self.extract_xsd_constraints(
                        self.XSDtree.find(f".//xs:simpleType[@name='{named_type_name}']", self.XSDNS2))
                    constraints.update(nested_constraints)
                else:
                    if child.tag == "{http://www.w3.org/2001/XMLSchema}enumeration":
                        if "{http://www.w3.org/2001/XMLSchema}enumeration" not in constraints:
                            constraints[child.tag] = [child.attrib.get("value")]
                        else:
                            constraints[child.tag] += [child.attrib.get("value")]
                    else:
                        constraints[child.tag] = child.attrib.get("value")
            for named_type2 in self.named_types:
                named_type_name2 = named_type2.attrib.get("name")
                if base == named_type_name2:
                    constraints.pop("{http://www.w3.org/2001/XMLSchema}type")
                    constraints.update(self.extract_xsd_constraints(named_type2))
            self.named_type_constraints[named_type_name] = constraints
            return constraints
        else:
            return None

    def get_xsd_info(self, xsd_file):
        self.XSDtree = ET.parse(xsd_file)
        root = self.XSDtree.getroot()

        self.XSDNS2 = dict()
        self.XSDNS2 = dict([
            node for (_, node) in ET.iterparse(xsd_file, events=['start-ns'])
        ])

        self.XSDtargetNamespace = "http://example.com"  #set a default value for if no targetnamespace is defined
        for key in root.attrib:
            if key == "targetNamespace":
                self.XSDtargetNamespace = root.attrib[key]

        self.named_types = self.XSDtree.findall(".//xs:simpleType", self.XSDNS2)
        self.named_type_constraints = {}
        self.XSD_elements = dict()

        for named_type in self.named_types:
            self.extract_xsd_constraints(named_type)

        for element_node in root.findall('xs:element', self.XSDNS2):
            self.get_xsd_element_info(element_node)

    def import_xsd_constraints(self, xsd_file):
        self.get_xsd_info(xsd_file)
        for XSDelem in self.XSD_elements:
            for XSDconst in self.XSD_elements[XSDelem]:
                for namespace in self.XSDNS2:
                    if type(self.XSD_elements[XSDelem][XSDconst]) == type("string"):
                        if self.XSD_elements[XSDelem][XSDconst].startswith(namespace+':'):
                            self.XSD_elements[XSDelem][XSDconst] = self.XSDNS2[namespace]+"#"+self.XSD_elements[XSDelem][XSDconst].split(":")[-1]

        q1 = f'SELECT ?nodeshape ?targetclass {{?nodeshape a <{self.shaclNS.NodeShape}> .?nodeshape <{self.shaclNS.targetClass}> ?targetclass.}}'
        x1 = self.SHACL.graph.query(q1)
        for row in x1:
            if str(row.targetclass) in self.XSD_elements:
                # enrich nodeshape
                if "type" in self.XSD_elements[str(row.targetclass)]:
                    if not (row.nodeshape, self.shaclNS.datatype, None) in self.SHACL.graph:
                        self.SHACL.graph.add((row.nodeshape, self.shaclNS.datatype, URIRef(self.XSD_elements[str(row.targetclass)]["type"])))
                if "minInclusive" in self.XSD_elements[str(row.targetclass)]:
                    if not (row.nodeshape, self.shaclNS.minInclusive, None) in self.SHACL.graph:
                        self.SHACL.graph.add((row.nodeshape, self.shaclNS.minInclusive, rdflib.Literal(int(self.XSD_elements[str(row.targetclass)]["minInclusive"]))))
                if "maxInclusive" in self.XSD_elements[str(row.targetclass)]:
                    if not (row.nodeshape, self.shaclNS.maxInclusive, None) in self.SHACL.graph:
                        self.SHACL.graph.add((row.nodeshape, self.shaclNS.maxInclusive, rdflib.Literal(int(self.XSD_elements[str(row.targetclass)]["maxInclusive"]))))
                if "pattern" in self.XSD_elements[str(row.targetclass)]:
                    if not (row.nodeshape, self.shaclNS.pattern, None) in self.SHACL.graph:
                        xsd_pattern = self.XSD_elements[str(row.targetclass)]["pattern"]
                        shacl_pattern = "^"
                        shacl_pattern += xsd_pattern.replace("\\d", "[0-9]") \
                            .replace("\\w", "[A-Za-z0-9_]") \
                            .replace("\\s", "[ \\t\\r\\n]") \
                            .replace("\\D", "[^0-9]") \
                            .replace("\\W", "[^A-Za-z0-9_]") \
                            .replace("\\S", "[^ \\t\\r\\n]")
                        shacl_pattern += "$"
                        self.SHACL.graph.add((row.nodeshape, self.shaclNS.pattern, rdflib.Literal(shacl_pattern)))

                # go over each propertyshape and enrich it
                property_BNodes_dict = dict()
                q2 = f'SELECT ?bnode ?p ?o {{<{row.nodeshape}> a <{self.shaclNS.NodeShape}> .<{row.nodeshape}> <{self.shaclNS.property}> ?bnode. ?bnode ?p ?o}}'
                x2 = self.SHACL.graph.query(q2)
                for row2 in x2:
                    if row2.p == self.shaclNS.path:
                        property_BNodes_dict[row2.o] = row2.bnode
                for item in property_BNodes_dict:
                    if str(item) in self.XSD_elements:
                        # propertyshape constraints
                        if "type" in self.XSD_elements[str(item)]:
                            if not (property_BNodes_dict[item], self.shaclNS.datatype, None) in self.SHACL.graph:
                                self.SHACL.graph.add((property_BNodes_dict[item], self.shaclNS.datatype, URIRef(self.XSD_elements[str(item)]["type"])))
                        if "minOccurs" in self.XSD_elements[str(item)]:
                            if not (property_BNodes_dict[item], self.shaclNS.minCount, None) in self.SHACL.graph:
                                self.SHACL.graph.add((property_BNodes_dict[item], self.shaclNS.minCount, rdflib.Literal(int(self.XSD_elements[str(item)]["minOccurs"]))))
                        if "maxOccurs" in self.XSD_elements[str(item)] and self.XSD_elements[str(item)]["maxOccurs"] != "unbounded":
                            if not (property_BNodes_dict[item], self.shaclNS.maxCount, None) in self.SHACL.graph:
                                self.SHACL.graph.add((property_BNodes_dict[item], self.shaclNS.maxCount, rdflib.Literal(int(self.XSD_elements[str(item)]["maxOccurs"]))))
                        if "minLength" in self.XSD_elements[str(item)]:
                            if not (property_BNodes_dict[item], self.shaclNS.minLength, None) in self.SHACL.graph:
                                self.SHACL.graph.add((property_BNodes_dict[item], self.shaclNS.minLength, rdflib.Literal(int(self.XSD_elements[str(item)]["minLength"]))))
                        if "maxLength" in self.XSD_elements[str(item)]:
                            if not (property_BNodes_dict[item], self.shaclNS.maxLength, None) in self.SHACL.graph:
                                self.SHACL.graph.add((property_BNodes_dict[item], self.shaclNS.maxLength, rdflib.Literal(int(self.XSD_elements[str(item)]["maxLength"]))))
                        if "fractionDigits" in self.XSD_elements[str(item)]:
                            if not (property_BNodes_dict[item], self.shaclNS.datatype, None) in self.SHACL.graph:
                                self.SHACL.graph.add((property_BNodes_dict[item], self.shaclNS.datatype, self.XSDNS.decimal))
                            if int(self.XSD_elements[str(item)]["fractionDigits"]) > 0:
                                decimal_pattern = "\\.[0-9]{1," + str(int(self.XSD_elements[str(item)]["fractionDigits"])) + "}"
                            else:
                                decimal_pattern = ""
                            fractionDigitspattern = "^-?[0-9]+" + decimal_pattern + "$"
                            if not (property_BNodes_dict[item], self.shaclNS.pattern, None) in self.SHACL.graph:
                                self.SHACL.graph.add((property_BNodes_dict[item], self.shaclNS.pattern, rdflib.Literal(fractionDigitspattern)))
                        if "minInclusive" in self.XSD_elements[str(item)]:
                            if not (property_BNodes_dict[item], self.shaclNS.minInclusive, None) in self.SHACL.graph:
                                self.SHACL.graph.add((property_BNodes_dict[item], self.shaclNS.minInclusive, rdflib.Literal(int(self.XSD_elements[str(item)]["minInclusive"]))))
                        if "maxInclusive" in self.XSD_elements[str(item)]:
                            if not (property_BNodes_dict[item], self.shaclNS.maxInclusive, None) in self.SHACL.graph:
                                self.SHACL.graph.add((property_BNodes_dict[item], self.shaclNS.maxInclusive, rdflib.Literal(int(self.XSD_elements[str(item)]["maxInclusive"]))))
                        if "minExclusive" in self.XSD_elements[str(item)]:
                            if not (property_BNodes_dict[item], self.shaclNS.minInclusive, None) in self.SHACL.graph:
                                self.SHACL.graph.add((property_BNodes_dict[item], self.shaclNS.minExclusive, rdflib.Literal(int(self.XSD_elements[str(item)]["minExclusive"]))))
                        if "maxExclusive" in self.XSD_elements[str(item)]:
                            if not (property_BNodes_dict[item], self.shaclNS.maxInclusive, None) in self.SHACL.graph:
                                self.SHACL.graph.add((property_BNodes_dict[item], self.shaclNS.maxExclusive, rdflib.Literal(int(self.XSD_elements[str(item)]["maxExclusive"]))))
                        if "pattern" in self.XSD_elements[str(item)]:
                            xsd_pattern = self.XSD_elements[str(item)]["pattern"]
                            shacl_pattern = "^"
                            shacl_pattern += xsd_pattern.replace("\\d", "[0-9]") \
                                .replace("\\w", "[A-Za-z0-9_]") \
                                .replace("\\s", "[ \\t\\r\\n]") \
                                .replace("\\D", "[^0-9]") \
                                .replace("\\W", "[^A-Za-z0-9_]") \
                                .replace("\\S", "[^ \\t\\r\\n]")
                            shacl_pattern += "$"
                            if not (property_BNodes_dict[item], self.shaclNS.pattern, None) in self.SHACL.graph:
                                self.SHACL.graph.add((property_BNodes_dict[item], self.shaclNS.pattern, rdflib.Literal(shacl_pattern)))

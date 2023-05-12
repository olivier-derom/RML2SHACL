import rdflib
from rdflib import URIRef
import xml.etree.ElementTree as ET

from .RML import *
from .SHACL import *
from .EnrichShacl import *

class XSDtoSHACL:
    def __init__(self):
        self.RML = RML()
        self.EnrichSHACL = EnrichSHACL()
        self.shaclNS = rdflib.Namespace('http://www.w3.org/ns/shacl#')
        self.rdfSyntax = rdflib.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
        self.XSDNS = rdflib.Namespace('http://www.w3.org/2001/XMLSchema#')
        self.XSDNS2 = dict()
        self.named_type_constraints = dict()
        self.XSDtree = None
        self.XSD_elements = dict()
        self.named_types = None
        self.XSDtargetNamespace = "http://example.com"

    def getXSDFileInfo(self, xsd_file):
        self.XSDtree = ET.parse(xsd_file)
        root = self.XSDtree.getroot()

        self.XSDNS2 = dict()
        self.XSDNS2 = dict([
            node for (_, node) in ET.iterparse(xsd_file, events=['start-ns'])
        ])

        self.XSDtargetNamespace = "http://example.com"  # set a default value for if no targetnamespace is defined
        for key in root.attrib:
            if key == "targetNamespace":
                self.XSDtargetNamespace = root.attrib[key]

        self.named_types = self.XSDtree.findall(".//xs:simpleType", self.XSDNS2)
        self.named_type_constraints = {}
        self.XSD_elements = dict()

        for named_type in self.named_types:
            self.extractXSDConstraints(named_type)

        for element_node in root.findall('xs:element', self.XSDNS2):
            self.getXSDElementInfo(element_node)

    def getXSDElementInfo(self, element, parent_name=None, is_attribute=False):
        element_name = self.XSDtargetNamespace+'/'+str(element.get('name'))
        if element_name is None:
            return None
        if element.find('xs:complexType', self.XSDNS2) is not None:
            element_dict = {'ElementName': element_name, 'ElementType': 'Element'}
            element_dict.update(element.attrib)
            if parent_name:
                element_dict['parent'] = parent_name
            for child_element in element.findall('xs:complexType/xs:sequence/xs:element', self.XSDNS2):
                child_element_info = self.getXSDElementInfo(child_element, element_name)
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
                child_element_info = self.getXSDElementInfo(attribute, element_name, True)
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
                child_element_info = self.getXSDElementInfo(attribute, element_name, True)
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

    def extractXSDConstraints(self, named_type):
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
                    nested_constraints = self.extractXSDConstraints(
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
                    constraints.update(self.extractXSDConstraints(named_type2))
            self.named_type_constraints[named_type_name] = constraints
            return constraints
        else:
            return None

    def addXSDConstraints(self, xsd_file, g):
        self.getXSDFileInfo(xsd_file)
        for XSDelem in self.XSD_elements:
            for XSDconst in self.XSD_elements[XSDelem]:
                for namespace in self.XSDNS2:
                    if type(self.XSD_elements[XSDelem][XSDconst]) == type("string"):
                        if self.XSD_elements[XSDelem][XSDconst].startswith(namespace+':'):
                            self.XSD_elements[XSDelem][XSDconst] = self.XSDNS2[namespace]+"#"+self.XSD_elements[XSDelem][XSDconst].split(":")[-1]

        q1 = f'SELECT ?nodeshape ?targetclass {{?nodeshape a <{self.shaclNS.NodeShape}> .?nodeshape <{self.shaclNS.targetClass}> ?targetclass.}}'
        x1 = g.query(q1)
        for row in x1:
            if str(row.targetclass) in self.XSD_elements:
                # enrich nodeshape
                if "type" in self.XSD_elements[str(row.targetclass)]:
                    self.EnrichSHACL.enrich(g, row.nodeshape, self.shaclNS.datatype, URIRef(self.XSD_elements[str(row.targetclass)]["type"]))
                if "minInclusive" in self.XSD_elements[str(row.targetclass)]:
                    self.EnrichSHACL.enrich(g, row.nodeshape, self.shaclNS.minInclusive, rdflib.Literal(int(self.XSD_elements[str(row.targetclass)]["minInclusive"])))
                if "maxInclusive" in self.XSD_elements[str(row.targetclass)]:
                    self.EnrichSHACL.enrich(g, row.nodeshape, self.shaclNS.maxInclusive, rdflib.Literal(int(self.XSD_elements[str(row.targetclass)]["maxInclusive"])))
                if "minOccurs" in self.XSD_elements[str(row.targetclass)]:
                    self.EnrichSHACL.enrich(g, row.nodeshape, self.shaclNS.minCount, rdflib.Literal(int(self.XSD_elements[str(row.targetclass)]["minOccurs"])))
                if "maxOccurs" in self.XSD_elements[str(row.targetclass)] and self.XSD_elements[str(row.targetclass)]["maxOccurs"] != "unbounded":
                    self.EnrichSHACL.enrich(g, row.nodeshape, self.shaclNS.maxCount, rdflib.Literal(int(self.XSD_elements[str(row.targetclass)]["maxOccurs"])))
                if "pattern" in self.XSD_elements[str(row.targetclass)]:
                    xsd_pattern = self.XSD_elements[str(row.targetclass)]["pattern"]
                    shacl_pattern = "^"
                    shacl_pattern += xsd_pattern.replace("\\d", "[0-9]") \
                        .replace("\\w", "[A-Za-z0-9_]") \
                        .replace("\\s", "[ \\t\\r\\n]") \
                        .replace("\\D", "[^0-9]") \
                        .replace("\\W", "[^A-Za-z0-9_]") \
                        .replace("\\S", "[^ \\t\\r\\n]")
                    shacl_pattern += "$"
                    self.EnrichSHACL.enrich(g, row.nodeshape, self.shaclNS.pattern, rdflib.Literal(shacl_pattern))

                # go over each propertyshape and enrich it
                property_BNodes_dict = dict()
                q2 = f'SELECT ?bnode ?p ?o {{<{row.nodeshape}> a <{self.shaclNS.NodeShape}> .<{row.nodeshape}> <{self.shaclNS.property}> ?bnode. ?bnode ?p ?o}}'
                x2 = g.query(q2)
                for row2 in x2:
                    if row2.p == self.shaclNS.path:
                        property_BNodes_dict[row2.o] = row2.bnode
                for item in property_BNodes_dict:
                    if str(item) in self.XSD_elements:
                        # propertyshape constraints
                        if "type" in self.XSD_elements[str(item)]:
                            self.EnrichSHACL.enrich(g, property_BNodes_dict[item], self.shaclNS.datatype, URIRef(self.XSD_elements[str(item)]["type"]))
                        if "minOccurs" in self.XSD_elements[str(item)]:
                            self.EnrichSHACL.enrich(g, property_BNodes_dict[item], self.shaclNS.minCount, rdflib.Literal(int(self.XSD_elements[str(item)]["minOccurs"])))
                        if "maxOccurs" in self.XSD_elements[str(item)] and self.XSD_elements[str(item)]["maxOccurs"] != "unbounded":
                            self.EnrichSHACL.enrich(g, property_BNodes_dict[item], self.shaclNS.maxCount, rdflib.Literal(int(self.XSD_elements[str(item)]["maxOccurs"])))
                        if "minLength" in self.XSD_elements[str(item)]:
                            self.EnrichSHACL.enrich(g, property_BNodes_dict[item], self.shaclNS.minLength, rdflib.Literal(int(self.XSD_elements[str(item)]["minLength"])))
                        if "length" in self.XSD_elements[str(item)]:
                            self.EnrichSHACL.enrich(g, property_BNodes_dict[item], self.shaclNS.minLength, rdflib.Literal(int(self.XSD_elements[str(item)]["length"])))
                            self.EnrichSHACL.enrich(g, property_BNodes_dict[item], self.shaclNS.maxLength, rdflib.Literal(int(self.XSD_elements[str(item)]["length"])))
                        if "maxLength" in self.XSD_elements[str(item)]:
                            self.EnrichSHACL.enrich(g, property_BNodes_dict[item], self.shaclNS.maxLength, rdflib.Literal(int(self.XSD_elements[str(item)]["maxLength"])))
                        if "fractionDigits" in self.XSD_elements[str(item)]:
                            self.EnrichSHACL.enrich(g, property_BNodes_dict[item], self.shaclNS.datatype, self.XSDNS.decimal)
                            if int(self.XSD_elements[str(item)]["fractionDigits"]) > 0:
                                decimal_pattern = "\\.[0-9]{1," + str(int(self.XSD_elements[str(item)]["fractionDigits"])) + "}"
                            else:
                                decimal_pattern = ""
                            fractionDigitspattern = "^-?[0-9]+" + decimal_pattern + "$"
                            self.EnrichSHACL.enrich(g, property_BNodes_dict[item], self.shaclNS.pattern, rdflib.Literal(fractionDigitspattern))
                        if "minInclusive" in self.XSD_elements[str(item)]:
                            self.EnrichSHACL.enrich(g, property_BNodes_dict[item], self.shaclNS.minInclusive, rdflib.Literal(int(self.XSD_elements[str(item)]["minInclusive"])))
                        if "maxInclusive" in self.XSD_elements[str(item)]:
                            self.EnrichSHACL.enrich(g, property_BNodes_dict[item], self.shaclNS.maxInclusive, rdflib.Literal(int(self.XSD_elements[str(item)]["maxInclusive"])))
                        if "minExclusive" in self.XSD_elements[str(item)]:
                            self.EnrichSHACL.enrich(g, property_BNodes_dict[item], self.shaclNS.minExclusive, rdflib.Literal(int(self.XSD_elements[str(item)]["minExclusive"])))
                        if "maxExclusive" in self.XSD_elements[str(item)]:
                            self.EnrichSHACL.enrich(g, property_BNodes_dict[item], self.shaclNS.maxExclusive, rdflib.Literal(int(self.XSD_elements[str(item)]["maxExclusive"])))
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
                            self.EnrichSHACL.enrich(g, property_BNodes_dict[item], self.shaclNS.pattern, rdflib.Literal(shacl_pattern))

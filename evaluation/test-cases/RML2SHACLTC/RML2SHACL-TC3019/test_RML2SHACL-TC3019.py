import os
from src.RMLtoShacl import RMLtoSHACL
from rdflib.graph import Graph
from rdflib import compare

def RML2SHACL_TC3019():

    RtoS = RMLtoSHACL()
    expected_graph = Graph()
    expected_graph.parse(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'expected.ttl'), format="ttl")

    mapping_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'mapping.ttl')
    ontology_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), '/ontology/ontology.ttl')
    if not os.path.isfile(ontology_file):
         ontology_file = None
    schema_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), '/schema/schema.xsd')
    if not os.path.isfile(schema_file):
        schema_file = None
    cwd = os.getcwd()
    tempfolder = os.path.abspath(os.path.join(cwd, '../../../../temp'))
    result_graph = RtoS.evaluateFiles(mapping_file, ontology_file, schema_file, tempfolder)

    assert compare.isomorphic(expected_graph, result_graph)
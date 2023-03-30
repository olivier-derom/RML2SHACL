import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

import argparse
import logging
import time
from src.RML import *
from src.RMLtoShacl import RMLtoSHACL
from src.OWLtoShacl import OWLtoSHACL
from src.SHACL import *

if __name__ == "__main__":

    def dir_path(string):
        if os.path.isdir(string):
            return string
        else:
            raise NotADirectoryError(string)

    RtoS = RMLtoSHACL()
    SHACL = SHACL()
    parser = argparse.ArgumentParser()
    parser.add_argument("MAPPING_FILE", type=str,
                        help="RML mapping file to be converted into SHACL shapes.")
    parser.add_argument("--ONTOLOGY_DIR", "-o", type=str,
                        help="Directory with additional ontology files to be converted into SHACL shapes.")
    parser.add_argument("--SCHEMA_DIR", "-s", type=str,
                        help="Directory with schema files to be converted into SHACL shapes. (supported schemas: XSD)")
    parser.add_argument("-logLevel", "-l", type=str, default="INFO",
                        help="Logging level of this script")

    args = parser.parse_args()

    loglevel = args.logLevel
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(level=numeric_level)

    start = time.time()
    if not args.MAPPING_FILE:
        print("Please provide an RML mapping.")
        exit()
    else:
        result_graph = RtoS.evaluateFiles(args.MAPPING_FILE, args.ONTOLOGY_DIR, args.SCHEMA_DIR, str(os.getcwd()) + "/temp")


    outputfileName = f"{args.MAPPING_FILE}-output-shape.ttl"
    outputDirectory = "shapes/"
    RtoS.writeShapeToFile(outputfileName, outputDirectory)

    outputdictfile = f"shapes/{args.MAPPING_FILE}-dict.txt"
    with open(outputdictfile, 'w') as data:
        data.write(str(RtoS.OWLtoSHACL.onto_stats))

    validation_shape_graph = rdflib.Graph()
    validation_shape_graph.parse("shacl-shacl.ttl", format="turtle")

    SHACL.Validation(validation_shape_graph, result_graph)

    logging.debug("*" * 100)
    logging.debug("RESULTS")
    logging.debug("=" * 100)
    logging.debug(SHACL.results_text)
    print(args.MAPPING_FILE)
    print(SHACL.results_text)

    end = time.time()

    print(f"Elapsed time: {end - start} seconds")

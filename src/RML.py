import pprint

import rdflib
from rdflib.graph import Graph
from rdflib.term import BNode, Identifier, Literal, URIRef

from FilesGitHub import *
from rml_model import GraphMap, ObjectMap, PredicateMap, PredicateObjectMap, SubjectMap, TriplesMap, LogicalSource


class RML:
    def __init__(self):
        self.graph = rdflib.Graph()
        self.rmlNS = rdflib.Namespace('http://semweb.mmlab.be/ns/rml#')
        self.r2rmlNS = rdflib.Namespace('http://www.w3.org/ns/r2rml#')
        self.TEMPLATE = self.r2rmlNS.template
        self.REFERENCE = self.rmlNS.reference
        self.TERMTYPE = self.r2rmlNS.termType
        self.POM = self.r2rmlNS.predicateObjectMap
        self.PREDICATE = self.r2rmlNS.predicate
        self.PRED_MAP = self.r2rmlNS.predicateMap
        self.TRIPLES_MAP_CLASS = self.r2rmlNS.TriplesMap
        self.SUBJECT_MAP = self.r2rmlNS.subjectMap
        self.CLASS = self.r2rmlNS['class']
        self.OJBECT_MAP = self.r2rmlNS.objectMap
        self.IRI_CLASS = self.r2rmlNS.IRI
        self.LANGUAGE = self.r2rmlNS.language
        self.CONSTANT = self.r2rmlNS.constant
        self.OBJECT = self.r2rmlNS.object
        self.DATATYPE = self.r2rmlNS.datatype
        self.LOGICAL_SOURCE = self.rmlNS.logicalSource 

        # contains triple maps models from rml_model module 
        # the keys are the triples maps' IRI values 
        self.tm_model_dict = dict()
        self.graphs = []
        self.refgraphs = []

    def printGraph(self, keuze):
        if keuze == 1:
            for stmt in self.graph:
                print(stmt)
        else:
            for stmt in self.graph:
                pprint.pprint(stmt)

    def parseFile(self, file_name):
        self.graph.parse(file_name, format=rdflib.util.guess_format(file_name))
        self.parseTriplesMaps(self.graph)
    

    def printQuery(self, graph, query): 
        print("\n".join([ f"{s}, {p}, {o}" for s, p, o in graph.triples(query)]) )


    def parseTriplesMaps(self, graph:Graph):
        for tm_iri, _, _ in graph.triples((None, None, self.TRIPLES_MAP_CLASS)): 
            print("Printing triples for the curren TripleMap") 
            print("="*50)
            self.printQuery(self.graph, (tm_iri, None, None))
            print("-"* 50)

            # loop through the triples of the TriplesMap with IRI  == tm_iri 
            # this loop will parse the corresponding subject maps and POMs for the 
            # given TriplesMaps IRI. 

            sm = None 
            poms = []
            gm = None 
            logical_source = None 
            _, _, sm_iri = next(graph.triples((tm_iri, self.SUBJECT_MAP, None))) 
            sm = self.parseSubjectMap(sm_iri, graph)
            _, _, logical_source_iri = next(graph.triples((tm_iri, self.LOGICAL_SOURCE, None)))

            lc = self.parseLogicalSource(logical_source_iri, graph)

            print(lc)


            pass
    def parseLogicalSource(self, logs_iri:Identifier, graph:Graph) -> LogicalSource:
        po_dict = dict() 
        
        for _, p, o in graph.triples((logs_iri, None, None)): 
            po_dict[p]= o 
        return LogicalSource(logs_iri, po_dict)
        
    def parseGraphMap(self, graph_iri:Identifier, graph:Graph) -> GraphMap: 
        po_dict = dict()
        if isinstance(graph_iri, URIRef): 
            po_dict[self.CONSTANT] = graph_iri
        else: 
            for _, graph_p, graph_o in graph.triples((graph_iri, None, None)): 
                po_dict[graph_p] = graph_o
        return GraphMap(graph_iri, po_dict)

    def parseSubjectMap(self, sm_IRI:Identifier, graph:Graph) -> SubjectMap:
        po_dict = dict() 
        for _, predicate, obj in graph.triples((sm_IRI, None, None)):
            if not predicate in po_dict: 
                po_dict[predicate]= []
            if predicate == self.r2rmlNS.graph: 
                obj = self.parseGraphMap(obj, graph) 

            po_dict[predicate].append(obj)

        return SubjectMap(sm_IRI, po_dict) 

    def parseObjectMap(self, ob_iri:Identifier, graph:Graph ) -> ObjectMap: 
    
        pass

    def parsePredicateMap(self, pm_iri:Identifier, graph:Graph) -> PredicateMap: 
        pass

    def parsePredicateObjectMap(self, pom_iri, graph) -> PredicateObjectMap: 
        po_dict = dict() 
        pass

    def parseGithubFile(self, number, letter, typeInputFile):
        fileReadObj = FilesGitHub()
        filename = fileReadObj.getFile(
            number, letter, typeInputFile, fileReadObj.Mappingfile)
        self.parseFile(filename)
        # self.printGraph(1)

    def removeBlankNodesMultipleMaps(self):
        # loop over all the Triple Maps in the RML input file
        for sTM, pTM, oTM in self.graph.triples((None, None, self.r2rmlNS.TriplesMap)):
            graphHelp = {}
            graphsPOM = []
            graphTripleMap = rdflib.Graph()
            graphsubjectMap = rdflib.Graph()
            graphlogicalSource = rdflib.Graph()
            graphTripleMap.add((sTM, pTM, oTM))  # add triplesmap header
            graphHelp["TM"] = graphTripleMap
            tel = 0
            # inside one Triple Map we doe loops over:
            for s, p, o in self.graph.triples((sTM, None, None)):
                # the triples belonging to the Logical Source
                if p == self.rmlNS.logicalSource:
                    for s2, p2, o2 in self.graph.triples((o, None, None)):
                        # searching for same Blank Node
                        # add logical source info
                        graphlogicalSource.add((p, p2, o2))
                    graphHelp["LS"] = graphlogicalSource
                # the triples belonging to the Subject Map
                if p == self.SUBJECT_MAP:
                    for s2, p2, o2 in self.graph.triples((o, None, None)):
                        # searching for same Blank Node
                        graphsubjectMap.add((p, p2, o2))
                     # add subject Map  info
                    graphHelp["SM"] = graphsubjectMap
                # the multiple triples that are PredicateObject Maps
                if p == self.POM:
                    graphPredicatObjectMap = rdflib.Graph()
                    # searching for one PredicatObjectMap
                    # searching for same Blank Node
                    for s2, p2, o2 in self.graph.triples((o, None, None)):
                        if p2 == self.r2rmlNS.predicateMap:
                            for s3, p3, o3 in self.graph.triples((o2, self.CONSTANT, None)):
                                # we make the "rr:predicateMap rr:constant o" triple to sthe shurtcut "rr:PredicateObjectMap rr:predicate o2"
                                graphPredicatObjectMap.add((p, self.PREDICATE, o3))
 # add the predicateobjectMap with the constant transformed into rr:predicate instead of constant
                        else:
                            graphPredicatObjectMap.add((p, p2, o2))
                        # add the predicateobjectMap
# searching for which objectMap belongs to this PredicateObjectMap
                    for s2, p2, o2 in graphPredicatObjectMap.triples((p, self.OJBECT_MAP, None)):
                        for s3, p3, o3 in self.graph.triples((o2, None, None)):
                            graphPredicatObjectMap.add((p2, p3, o3))
# add the objectMap beloning to the predicateobjectMap added in previous loop
                        graphPredicatObjectMap.remove((s2, p2, o2))
# remove something with a blanknode in that we added too much
# if we don't have an rr:ObjectMap but an rr:object (as part of rr:predicateMap as an predicate)
# we will write this as rr:ObjectMap rr:constant (object that belonged to the rr:object)
                    for s2, p2, o2 in graphPredicatObjectMap.triples((p, self.OBJECT, None)):
                     # graphPredicatObjectMap.add((s2,p2,o2))
                     # #add the object beloning to the predicateobjectMap added in previous loop
                        graphPredicatObjectMap.add((self.OJBECT_MAP, self.CONSTANT, o2))
                        graphPredicatObjectMap.remove((s2, p2, o2))
 # remove the "rr:predicateMap rr:object o2" triple from the graph because it gets added in loop for objectMap
                    # loop to find any possible RefObjectMaps
                    for sROM, pROM, oROM in self.graph.triples((None, None, self.r2rmlNS.RefObjectMap)):
                        # if we find one we see if it belongs to the ObjectMap we are working with now
                        for s3, p3, o3 in self.graph.triples((p, self.OJBECT_MAP, sROM)):
                            # if this is the fact we search inside the RefObjectMap (sROM) for the value of rr:parentTriplesMap
                            for s4, p4, o4 in self.graph.triples((sROM, self.r2rmlNS.parentTriplesMap, None)):
                                graphPredicatObjectMap.add(
                                    (self.OJBECT_MAP, self.r2rmlNS.parentTriplesMap, o4))
# add the parentTriplesMap to the ObjectMap

                    graphHelp["POM"+str(tel)] = graphPredicatObjectMap
                    tel = tel + 1
            self.graphs.append(graphHelp)

    def printDictionary(self, keuze):
        for graphHelp in self.graphs:
            if keuze == 1:
                for g in graphHelp["TM"]:
                    print("TM graph: " + str(g))
            if keuze == 2:
                for g in graphHelp["LS"]:
                    print(g)
            if keuze == 3:
                for g in graphHelp["SM"]:
                    print(g)
            if keuze == 4:
                length = len(graphHelp)-3
# Because the dictionary inside graphHelp has first 'TM', 'LM' and 'SM' as keys
# we do the length of the dictionary minus 3
# this way we can use this newly calculated length
# for the indexes used for the possible multiple PredicateObjectsMaps (POM)
                for i in range(length):
                    print("new POM" + str(i))
                    for g in graphHelp["POM"+str(i)]:
                        print(g)
            if keuze == 5:
                for n, g in graphHelp.items():
                    for stm in g:
                        print(n, stm)
            if keuze == 6:
                for g in graphHelp.values():
                    for stm in g:
                        print(stm)

    def testmain(self):
        self.parseGithubFile(7, 'b', FilesGitHub.CSV)
        self.removeBlankNodesMultipleMaps()


if __name__ == '__main__':
    Rml = RML()
    Rml.testmain()

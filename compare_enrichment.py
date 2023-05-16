import rdflib

files = []
# files.append("shapesold/astrea_test/time/mapping.ttl-output-shape.ttl")
# files.append("shapes/evaluation/astrea_test/time/mapping.ttl-output-shape.ttl")
# files.append("evaluation/astrea_test/time/shaclgen.ttl")

# files.append("shapesold/astrea_test/ssn/mapping.ttl-output-shape.ttl")
# files.append("shapes/evaluation/astrea_test/ssn/mapping.ttl-output-shape.ttl")
# files.append("evaluation/astrea_test/ssn/shaclgen.ttl")
#
# files.append("shapesold/astrea_test/onem2m/mapping.ttl-output-shape.ttl")
# files.append("shapes/evaluation/astrea_test/onem2m/mapping.ttl-output-shape.ttl")
# files.append("evaluation/astrea_test/onem2m/shaclgen.ttl")
#
# files.append("shapesold/astrea_test/openadr/mapping.ttl-output-shape.ttl")
# files.append("shapes/evaluation/astrea_test/openadr/mapping.ttl-output-shape.ttl")
# files.append("evaluation/astrea_test/openadr/shaclgen.ttl")
#
# files.append("shapesold/astrea_test/WoT/mapping.ttl-output-shape.ttl")
# files.append("shapes/evaluation/astrea_test/WoT/mapping.ttl-output-shape.ttl")
# files.append("evaluation/astrea_test/WoT/shaclgen.ttl")
#
# files.append("shapesold/astrea_test/saref-environment/mapping.ttl-output-shape.ttl")
# files.append("shapes/evaluation/astrea_test/saref-environment/mapping.ttl-output-shape.ttl")
# files.append("evaluation/astrea_test/saref-environment/shaclgen.ttl")

files.append("shapesold/xsd_test/person/mapping.ttl-output-shape.ttl")
files.append("shapes/evaluation/xsd_test/person/mapping.ttl-output-shape.ttl")

for path in files:
    try:
        print('------------------------------------------------------------------')
        print('file:', path)
        g = rdflib.Graph()
        g.parse(path)

        q1 = f'SELECT ?nodeshape {{?nodeshape a sh:NodeShape .}}'
        x1 = g.query(q1)
        print('classes:', len(x1))

        q2 = f'SELECT ?nodeshape {{?nodeshape a sh:NodeShape .}}'
        x2 = g.query(q2)
        print('Node shapes:', len(x2))

        q3 = f'SELECT ?p ?o {{?nodeshape a sh:NodeShape . ?nodeshape ?p ?o}}'
        x3 = g.query(q3)
        print('Node restrictions:', len(x3))
        nodedict = {}
        # for item in x3:
        #     if item[0] not in nodedict:
        #         nodedict[item[0]] = 1
        #     else:
        #         nodedict[item[0]] += 1
        # for item in nodedict:
        #     print(item, ':', nodedict[item])

        q4 = f'SELECT ?property {{?nodeshape a sh:NodeShape . ?nodeshape sh:property ?property.}}'
        x4 = g.query(q4)
        print('Property shapes:', len(x4))

        q5 = f'SELECT ?p {{?nodeshape a sh:NodeShape . ?nodeshape sh:property ?propertyshape. ?propertyshape ?p ?property}}'
        x5 = g.query(q5)
        print('properties:', len(x5))
        nodedict = {}
        # for item in x5:
        #     if item[0] not in nodedict:
        #         nodedict[item[0]] = 1
        #     else:
        #         nodedict[item[0]] += 1
        # for item in nodedict:
        #     print(item, ':', nodedict[item])

        q7 = f'SELECT ?p {{?nodeshape a sh:PropertyShape . ?nodeshape sh:targetNode ?p}}'
        x7 = g.query(q7)
        print('properties2:', len(x7))

        q6 = f'SELECT $s $p $o {{ $s $p $o }}'
        x6 = g.query(q6)
        print('Total restrictions:', len(x6))
    except Exception:
        print('error')

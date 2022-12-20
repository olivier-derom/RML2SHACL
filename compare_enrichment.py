import rdflib

files = []
files.append("shapesold/astrea_test/time/mapping.ttl-output-shape.ttl")
files.append("shapes/evaluation/astrea_test/time/mapping.ttl-output-shape.ttl")

files.append("shapesold/astrea_test/ssn/mapping.ttl-output-shape.ttl")
files.append("shapes/evaluation/astrea_test/ssn/mapping.ttl-output-shape.ttl")

files.append("shapesold/astrea_test/onem2m/mapping.ttl-output-shape.ttl")
files.append("shapes/evaluation/astrea_test/onem2m/mapping.ttl-output-shape.ttl")

files.append("shapesold/astrea_test/openadr/mapping.ttl-output-shape.ttl")
files.append("shapes/evaluation/astrea_test/openadr/mapping.ttl-output-shape.ttl")

files.append("shapesold/astrea_test/WoT/mapping.ttl-output-shape.ttl")
files.append("shapes/evaluation/astrea_test/WoT/mapping.ttl-output-shape.ttl")

files.append("shapesold/astrea_test/saref-environment/mapping.ttl-output-shape.ttl")
files.append("shapes/evaluation/astrea_test/saref-environment/mapping.ttl-output-shape.ttl")

for path in files:
    print('------------------------------------------------------------------')
    g = rdflib.Graph()
    g.parse(path)
    print('file:', path)

    q1 = f'SELECT ?nodeshape {{?nodeshape a sh:NodeShape .}}'
    x1 = g.query(q1)
    print('classes:', len(x1))

    q2 = f'SELECT ?nodeshape {{?nodeshape a sh:NodeShape .}}'
    x2 = g.query(q2)
    print('Node shapes:', len(x2))

    q3 = f'SELECT ?p ?o {{?nodeshape a sh:NodeShape . ?nodeshape ?p ?o}}'
    x3 = g.query(q3)
    print('Node restrictions:', len(x3))

    q4 = f'SELECT ?property {{?nodeshape a sh:NodeShape . ?nodeshape sh:property ?property.}}'
    x4 = g.query(q4)
    print('Property shapes:', len(x4))

    q5 = f'SELECT ?property {{?nodeshape a sh:NodeShape . ?nodeshape sh:property ?propertyshape. ?propertyshape ?whatever ?property}}'
    x5 = g.query(q5)
    print('properties:', len(x5))

    q6 = f'SELECT $s $p $o {{ $s $p $o }}'
    x6 = g.query(q6)
    print('Total restrictions:', len(x6))

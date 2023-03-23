import subprocess
import os


test_folder_path = "evaluation/test-cases/RML2SHACLTC"


testcase = input("which test-case would you like to run? enter '0' for all test-cases:\nRML2SHACL-TC")

if testcase == "0":
    for subfolder_name in os.listdir(test_folder_path):
        TC_path = os.path.join(test_folder_path, subfolder_name)
        if os.path.isdir(TC_path):
            if subfolder_name.startswith("RML2SHACL-TC1"):
                mapping_path = os.path.join(TC_path, "mapping.ttl")
                ontology_path = os.path.join(TC_path, "ontology")
                schema_path = os.path.join(TC_path, "schema")
                item = ["python", "main.py", mapping_path, "-s", schema_path]
                p = subprocess.Popen(item, shell=True)

            elif subfolder_name.startswith("RML2SHACL-TC2"):
                mapping_path = os.path.join(TC_path, "mapping.ttl")
                ontology_path = os.path.join(TC_path, "ontology")
                schema_path = os.path.join(TC_path, "schema")
                item = ["python", "main.py", mapping_path, "-o", ontology_path]
                p = subprocess.Popen(item, shell=True)

            elif subfolder_name.startswith("RML2SHACL-TC3"):
                mapping_path = os.path.join(TC_path, "mapping.ttl")
                ontology_path = os.path.join(TC_path, "ontology")
                schema_path = os.path.join(TC_path, "schema")
                item = ["python", "main.py", mapping_path, "-o", ontology_path, "-s", schema_path]
                p = subprocess.Popen(item, shell=True)

            elif subfolder_name.startswith("RML2SHACL-TC0"):
                mapping_path = os.path.join(TC_path, "mapping.ttl")
                ontology_path = os.path.join(TC_path, "ontology")
                schema_path = os.path.join(TC_path, "schema")
                item = ["python", "main.py", mapping_path]
                p = subprocess.Popen(item, shell=True)


else:
    TC_path = os.path.join(test_folder_path, "RML2SHACL-TC"+testcase)
    if testcase.startswith("1"):
        mapping_path = os.path.join(TC_path, "mapping.ttl")
        ontology_path = os.path.join(TC_path, "ontology")
        schema_path = os.path.join(TC_path, "schema")
        item = ["python", "main.py", mapping_path, "-s", schema_path]
        p = subprocess.Popen(item, shell=True)
        # while p.poll() is None:
        #     pass
    elif testcase.startswith("2"):
        mapping_path = os.path.join(TC_path, "mapping.ttl")
        ontology_path = os.path.join(TC_path, "ontology")
        schema_path = os.path.join(TC_path, "schema")
        item = ["python", "main.py", mapping_path, "-o", ontology_path]
        p = subprocess.Popen(item, shell=True)
        # while p.poll() is None:
        #     pass
    elif testcase.startswith("3"):
        mapping_path = os.path.join(TC_path, "mapping.ttl")
        ontology_path = os.path.join(TC_path, "ontology")
        schema_path = os.path.join(TC_path, "schema")
        item = ["python", "main.py", mapping_path, "-o", ontology_path, "-s", schema_path]
        p = subprocess.Popen(item, shell=True)
    elif testcase.startswith("0"):
        mapping_path = os.path.join(TC_path, "mapping.ttl")
        ontology_path = os.path.join(TC_path, "ontology")
        schema_path = os.path.join(TC_path, "schema")
        item = ["python", "main.py", mapping_path]
        p = subprocess.Popen(item, shell=True)
while p.poll() is None:
    pass


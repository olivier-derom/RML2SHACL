rmdir /s /q "temp"
del /s /q ontologies\*
xcopy "evaluation\astrea_test\time\time.ttl" "ontologies"
python main.py -o "ontologies" "evaluation/astrea_test/time/mapping.ttl"
rmdir /s /q "temp"
del /s /q ontologies\*
xcopy "evaluation\astrea_test\ssn\ssn.ttl" "ontologies"
python main.py -o "ontologies" "evaluation/astrea_test/ssn/mapping.ttl"
rmdir /s /q "temp"
del /s /q ontologies\*
xcopy "evaluation\astrea_test\onem2m\base_ontology.owl" "ontologies"
python main.py -o "ontologies" "evaluation/astrea_test/onem2m/mapping.ttl"
rmdir /s /q "temp"
del /s /q ontologies\*
xcopy "evaluation\astrea_test\openadr\ontology.nt" "ontologies"
python main.py -o "ontologies" "evaluation/astrea_test/openadr/mapping.ttl"
rmdir /s /q "temp"
del /s /q ontologies\*
xcopy "evaluation\astrea_test\WoT\ontology.n3" "ontologies"
python main.py -o "ontologies" "evaluation/astrea_test/WoT/mapping.ttl"
rmdir /s /q "temp"
del /s /q ontologies\*
xcopy "evaluation\astrea_test\saref-environment\saref4envi.ttl" "ontologies"
python main.py -o "ontologies" "evaluation/astrea_test/saref-environment/mapping.ttl"
>compare_enrichment.txt (
python compare_enrichment.py
)
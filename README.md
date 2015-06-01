# neo4sbml - SBML - RDF metadata graph in neo4j

## Description
The main project focus was the generation of a graph database for curated computational models in Systems Biology Markup Language (SBML) and their available annotation information in RDF. The curated models are the 575 models from the 29th BioModels release available for downlowd from [biomodels.org](http://www.ebi.ac.uk/biomodels-main/).

The graph consists of two main components: First the SBML model structure graph which represents the `Model`, the `Compartment`, the `Species` and the `Reaction` nodes of the individual models, with model components connected to their respective `Model` via the following relationships
* `COMPARTMENT_IN_MODEL`
* `SPECIES_IN_MODEL` 
* `REACTION_IN_MODEL`
All model components have the additional label `SBase`.
The additional availabel relationships between model components can be added in a future version.

The second main components are the `RDF` annotations which are connected via their respective relationship types. Every model component can have multiple associated `RDF` nodes.
```
BQB = {
    0: 'BQB_IS',
    1: 'BQB_HAS_PART',
    2: 'BQB_IS_PART_OF',
    3: 'BQB_IS_VERSION_OF',
    4: 'BQB_HAS_VERSION',
    5: 'BQB_IS_HOMOLOG_TO',
    6: 'BQB_IS_DESCRIBED_BY',
    7: 'BQB_IS_ENCODED_BY',
    8: 'BQB_ENCODES',
    9: 'BQB_OCCURS_IN',
    10: 'BQB_HAS_PROPERTY',
    11: 'BQB_IS_PROPERTY_OF',
    12: 'BQB_HAS_TAXON',
    13: 'BQB_UNKNOWN',
}

BQM = {
    0: 'BQM_IS',
    1: 'BQM_IS_DESCRIBED_BY',
    2: 'BQM_IS_DERIVED_FROM',
    3: 'BQM_IS_INSTANCE_OF',
    4: 'BQM_HAS_INSTANCE',
    5: 'BQM_UNKNOWN'
}
```


## Implementation
The implementation is done in python using `libsbml` for parsing the SBML information and RDF annotations and `py2neo` for creating the cypher statements for creating the graph.

[py2neo](http://py2neo.org/2.0/)
[libsbml](http://www.sbml.org)

## Results
The resulting graph is available in the `graph.db` subfolder. The 575 SBML models are in the data subfolder. The graph generating script can be found in `neo2




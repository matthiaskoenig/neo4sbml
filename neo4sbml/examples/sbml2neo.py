"""
Read a given computational model in SBML format into the Neo4j graph model.

The nodes are SBML objects from the xml graph

    <bqmodel:is>
	<rdf:Bag>
	<rdf:li rdf:resource="http://identifiers.org/biomodels.db/MODEL6613849442"/>
	</rdf:Bag>
	</bqmodel:is>
	<bqmodel:is>
	<rdf:Bag>
	<rdf:li rdf:resource="http://identifiers.org/biomodels.db/BIOMD0000000001"/>
	</rdf:Bag>
	</bqmodel:is>
	<bqmodel:isDescribedBy>
	<rdf:Bag>
	<rdf:li rdf:resource="http://identifiers.org/pubmed/8983160"/>
	</rdf:Bag>
	</bqmodel:isDescribedBy>
	<bqbiol:isVersionOf>
	<rdf:Bag>
	<rdf:li rdf:resource="http://identifiers.org/go/GO:0007274"/>
	<rdf:li rdf:resource="http://identifiers.org/go/GO:0007166"/>
	<rdf:li rdf:resource="http://identifiers.org/go/GO:0019226"/>
	</rdf:Bag>
	</bqbiol:isVersionOf>
	<bqbiol:hasTaxon>
	<rdf:Bag>
	<rdf:li rdf:resource="http://identifiers.org/taxonomy/7787"/>
	</rdf:Bag>
	</bqbiol:hasTaxon>
	</rdf:Description>
	</rdf:RDF>

"""
from __future__ import print_function
# read the SBML example annotations

import libsbml
import py2neo as neo
from enum import Enum

# ------------------------------------------------------------------
# RDF relationships
# ------------------------------------------------------------------
QUALIFIER = {
    0: 'MODEL_QUALIFIER',
    1: 'BIOLOGICAL_QUALIFIER',
    2: 'UNKNOWN_QUALIFIER'
}

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


def read_rdf(sobj):
    """ Read RDF from the given SBML object. """
    cvterms = sobj.getCVTerms()    
    rdf = []    
    if not cvterms:
        return rdf
    
    for cv in cvterms:  
        qualifier_type = cv.getQualifierType() 
        
        uris = []
        for k in range(cv.getNumResources()):
            # print('URI:', cv.getResourceURI(k))
            uri = cv.getResourceURI(k)
            uris.append(uri)
        
        # model qualifier
        if qualifier_type == 0: 
            rdf.append({'QualifierType': QUALIFIER[qualifier_type],
                        'Qualifier': BQM[cv.getModelQualifierType()],
                        'URIS': uris
            })
        # biological qualifier
        if qualifier_type == 1: 
            rdf.append({'QualifierType': QUALIFIER[qualifier_type],
                        'Qualifier': BQB[cv.getModelQualifierType()],
                        'URIS': uris
            })
    return rdf

def create_rdf_nodes(rdf, object_id, graph):
    """ Creates the additional RDF nodes for the given neo_node. """
    for d in rdf:
        for uri in d['URIS']:
            # create rdf node
            # neo_rdf = neo.Node("RDF", uri=uri)
            neo_rdf = graph.cypher.execute('MERGE (r:RDF {{uri: "{}" }}) RETURN r'.format(uri))
            # print('neo_rdf', neo_rdf)

            # create the qualifier
            # TODO:
            # bqt_model = neo.Relationship(neo_rdf, d["Qualifier"], neo_node)
            # graph.create(bqt_model)

            cypher_str = '''
                MATCH (r:RDF) WHERE r.uri="{}"
                MATCH (m) WHERE m.object_id="{}"
                CREATE (r)-[:{}]->(m)
            '''.format(uri, object_id, d["Qualifier"])
            print(cypher_str)

            graph.cypher.execute(cypher_str)


def split_uri(uri):
    # TODO: get the splitted information
    pass


def sbml_2_neo(sbml_filepath):
    """ Creates the neo4j graph from SBML. """
    print('Create neo graph')
    graph = neo.Graph()

    # model
    doc = libsbml.readSBMLFromFile(sbml_filepath)
    model = doc.getModel()
    model_id = model.getId()


    # graph.schema.create_uniqueness_constraint("Model", "id")
    # neo_model = neo.Node("Model", id=model.getId())
    # neo_model = graph.merge("Model", "id", model.getId())

    # create model node
    object_id = '__'.join([model_id, model_id])
    neo_model = graph.cypher.execute('''
        MERGE (m:Model {{ object_id: "{}", id: "{}", model: "{}" }})
        RETURN m
        '''.format(object_id, model_id, model_id))

    # read the rdf information    
    rdf = read_rdf(model)
    # create rdf nodes and relationships
    create_rdf_nodes(rdf, object_id=object_id, graph=graph)

    '''
    # compartments
    for c in model.getListOfCompartments():
        neo_c = neo.Node("Compartment", id=c.getId(), name=c.getName())

        c_in_model = neo.Relationship(neo_c, "COMPARTMENT_IN_MODEL", neo_model)
        graph.create(c_in_model)
        
        # read the rdf information    
        rdf = read_rdf(c)
        # create rdf nodes and relationships
        create_rdf_nodes(rdf, neo_c, graph)

    # species
    for s in model.getListOfSpecies():
        neo_s = neo.Node("Species", id=s.getId(), name=s.getName())

        s_in_model = neo.Relationship(neo_s, "SPECIES_IN_MODEL", neo_model)
        graph.create(s_in_model)

        # read the rdf information    
        rdf = read_rdf(s)
        # create rdf nodes and relationships
        create_rdf_nodes(rdf, neo_s, graph)

    # reactions
    for r in model.getListOfReactions():
        neo_r = neo.Node("Reaction", id=r.getId())
        r_in_model = neo.Relationship(neo_r, "REACTION_IN_MODEL", neo_model)
        graph.create(r_in_model)
        
        # read the rdf information    
        rdf = read_rdf(r)
        # create rdf nodes and relationships
        create_rdf_nodes(rdf, neo_r, graph)
    '''


if __name__ == "__main__":
    from neo4sbml.data.data import example_filepath
    model = sbml_2_neo(example_filepath)

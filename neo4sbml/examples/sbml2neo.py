"""
Read a given computational model in SBML format into the Neo4j graph model.

The nodes are SBML objects from the xml graph

Some example annotations.
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
            neo_rdf = graph.cypher.execute('MERGE (r:RDF {{uri: "{}" }}) RETURN r'.format(uri))
            # print('neo_rdf', neo_rdf)

            cypher_str = '''
                MATCH (r:RDF) WHERE r.uri="{}"
                MATCH (m) WHERE m.object_id="{}"
                MERGE (r)-[:{}]->(m)
            '''.format(uri, object_id, d["Qualifier"])
            # print(cypher_str)
            graph.cypher.execute(cypher_str)


def split_uri(uri):
    # TODO: get the splitted information
    pass


def setup_graph():
    graph = neo.Graph()
    # set the indices
    cypher_str = '''
        CREATE CONSTRAINT ON (r:RDF) ASSERT r.uri IS UNIQUE
    '''
    graph.cypher.execute(cypher_str)

    labels = ['Model', 'Compartment', 'Reaction', 'Species']
    for label in labels:
        cypher_str = '''
            CREATE CONSTRAINT ON (m:{}) ASSERT m.object_id IS UNIQUE
        '''.format(label)
        graph.cypher.execute(cypher_str)

    return graph


def sbml_2_neo(sbml_filepath):
    """ Creates the neo4j graph from SBML. """
    graph = setup_graph()

    #  sbml model
    doc = libsbml.readSBMLFromFile(sbml_filepath)
    model = doc.getModel()

    md5 = hash_for_file(sbml_filepath)
    model_id = model.getId()

    def rdf_graph(obj, label):
        """ Creates the RDF graph for the given model object. """
        object_id = '__'.join([obj.getId(), md5])
        # Create the object node
        cypher_str = '''
            MERGE (m:SBase:{} {{ object_id: "{}" }})
            ON CREATE SET m.id="{}"
            ON CREATE SET m.name="{}"
            ON CREATE SET m.model="{}"
            '''.format(label, object_id, obj.getId(), obj.getName(), model_id)

        graph.cypher.execute(cypher_str)
        # read the rdf information
        rdf = read_rdf(obj)
        # create rdf nodes and relationships
        create_rdf_nodes(rdf, object_id=object_id, graph=graph)

    def link_to_model(obj, label):
        """ Link between model objects and model."""
        relation_str = "_".join([label.upper(), 'IN', 'MODEL'])
        object_id = '__'.join([obj.getId(), md5])
        cypher_str = '''
                MATCH (c:{}) WHERE c.object_id="{}"
                MATCH (m:Model) WHERE m.object_id="{}"
                MERGE (c)-[:{}]->(m)
        '''.format(label, object_id, "__".join([model_id, md5]), relation_str)

        # TODO: check with PROFILE
        # print(cypher_str)
        graph.cypher.execute(cypher_str, )

    # ----------------------------------------------------
    # model
    rdf_graph(model, 'Model')

    # compartments
    for obj in model.getListOfCompartments():
        label = 'Compartment'
        rdf_graph(obj=obj, label=label)
        link_to_model(obj=obj, label=label)

    # species
    for obj in model.getListOfSpecies():
        label = 'Species'
        rdf_graph(obj=obj, label=label)
        link_to_model(obj=obj, label=label)

    # reactions
    for obj in model.getListOfReactions():
        label = 'Reaction'
        rdf_graph(obj=obj, label=label)
        link_to_model(obj=obj, label=label)
    # ----------------------------------------------------

def get_model_paths():
    from neo4sbml.data.data import data_dir
    import os
    dir = os.path.join(data_dir, 'BioModels-r29_sbml_curated')

    # get all SBML files in folder
    files = [os.path.join(dir, f) for f in os.listdir(dir) if os.path.isfile(os.path.join(dir, f))]
    return sorted(files)


def hash_for_file(filepath, hash_type='MD5', blocksize=65536):
    """ Calculate the md5_hash for a file.

        Calculating a hash for a file is always useful when you need to check if two files
        are identical, or to make sure that the contents of a file were not changed, and to
        check the integrity of a file when it is transmitted over a network.
        he most used algorithms to hash a file are MD5 and SHA-1. They are used because they
        are fast and they provide a good way to identify different files.
        [http://www.pythoncentral.io/hashing-files-with-python/]
    """
    import hashlib

    hasher = None
    if hash_type == 'MD5':
        hasher = hashlib.md5()
    elif hash_type == 'SHA1':
        hasher == hashlib.sha1()
    with open(filepath, 'rb') as f:
        buf = f.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(blocksize)
    return hasher.hexdigest()


if __name__ == "__main__":

    # parse one test file
    # from neo4sbml.data.data import example_filepath
    # sbml_2_neo(example_filepath)

    # ----------------------------------------------------

    import time

    # parse all the models
    files = get_model_paths()

    # first 50 models
    files = files[0:50]

    print("Number of models:", len(files))
    for k, filepath in enumerate(files):
        print('[{}/{}] {}'.format(k+1, len(files), filepath))
        start = time.time()
        sbml_2_neo(filepath)
        print('Time: ', time.time()-start)


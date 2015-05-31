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

# TODO: put in model
class Relationship(Enum):
    pass


def read_rdf(sobj):
    """ Read RDF from the given SBML object. """
    cvterms = sobj.getCVTerms()    
    rdf = []    
    if not cvterms:
        return rdf
    
    for cv in cvterms:  
        # print('BQT', cv.getBiologicalQualifierType())
        # print('MQT', cv.getModelQualifierType())
        uris = []
        for k in range(cv.getNumResources()):
            # print('URI:', cv.getResourceURI(k))
            uri = cv.getResourceURI(k)
            uris.append(uri)
        rdf.append({'BQT': cv.getBiologicalQualifierType(),
                    'MQT': cv.getModelQualifierType(),
                    'URIS': uris
                   })
    return rdf

def create_rdf_nodes(rdf, neo_node, graph):
    """ Creates the additional RDF nodes for the given neo_node. """
    for d in rdf:
        for uri in d['URIS']:
            # create rdf node
            neo_rdf = neo.Node("RDF", uri=uri)
            # create the BQT relationship
            bqt_model = neo.Relationship(neo_rdf, "BQT:{}".format(d["BQT"]), neo_node)
            graph.create(bqt_model)
        
            # create the MQT relationship
            mqt_model = neo.Relationship(neo_rdf, "MQT:{}".format(d["MQT"]), neo_node)
            graph.create(mqt_model)
    

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
    neo_model = neo.Node("Model", id=model.getId())

    # read the rdf information    
    rdf = read_rdf(model)
    # create rdf nodes and relationships
    create_rdf_nodes(rdf, neo_model, graph)

    # compartments
    for c in model.getListOfCompartments():
        neo_c = neo.Node("Compartment", id=c.getId())

        c_in_model = neo.Relationship(neo_c, "COMPARTMENT_IN_MODEL", neo_model)
        graph.create(c_in_model)
        
        # read the rdf information    
        rdf = read_rdf(c)
        # create rdf nodes and relationships
        create_rdf_nodes(rdf, neo_c, graph)

    # species
    for s in model.getListOfSpecies():
        neo_s = neo.Node("Species", id=s.getId())

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

    return model
    



'''
from py2neo import Node, Relationship

alice = Node("Person", name="Alice")
bob = Node("Person", name="Bob")
alice_knows_bob = Relationship(alice, "KNOWS", bob)
graph.create(alice_knows_bob)
'''

if __name__ == "__main__":
    from neo4sbml.data.data import example_filepath
    model = sbml_2_neo(example_filepath)
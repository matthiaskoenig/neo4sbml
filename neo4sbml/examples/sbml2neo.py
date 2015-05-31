"""
Read a given computational model in SBML format into the Neo4j graph model.

The nodes are SBML objects from the xml graph

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
    """
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
    
    cvterms = sobj.getCVTerms()
    for cv in cvterms:        
        print('BQT', cv.getBiologicalQualifierType())
        print('MQT', cv.getModelQualifierType())
        resources = cv.getResources()
        print('resources', resources)
        for k in range(resources.getLength()):
            res = resources.
        # for res in resources:
        #     print('res', res)

    return resources

def sbml_2_neo(sbml_filepath):
    """ Creates the neo4j graph from SBML. """
    print('Create neo graph')
    graph = neo.Graph()

    # model
    doc = libsbml.readSBMLFromFile(sbml_filepath)
    model = doc.getModel()
    neo_model = neo.Node("Model", id=model.getId())
    # TODO: set additional attributes/properties
    
        

    # compartments
    for c in model.getListOfCompartments():
        neo_c = neo.Node("Compartment", id=c.getId())

        c_in_model = neo.Relationship(neo_c, "COMPARTMENT_IN_MODEL", neo_model)
        graph.create(c_in_model)

    # species
    for c in model.getListOfSpecies():
        neo_s = neo.Node("Species", id=c.getId())

        s_in_model = neo.Relationship(neo_s, "SPECIES_IN_MODEL", neo_model)
        graph.create(s_in_model)

    # reactions
    for c in model.getListOfReactions():
        neo_r = neo.Node("Reaction", id=c.getId())
        r_in_model = neo.Relationship(neo_r, "REACTION_IN_MODEL", neo_model)
        graph.create(r_in_model)

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

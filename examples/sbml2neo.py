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




def sbml_2_neo(sbml_filepath):
    """ Creates the neo4j graph from SBML. """
    print('Create neo graph')
    graph = neo.Graph()

    # model
    doc = libsbml.readSBMLFromFile(sbml_filepath)
    model = doc.getModel()
    neo_model = neo.Node("Model", id=model.getId())


    # compartments
    for c in model.getListOfCompartments():
        neo_c = neo.Node("Compartment", id=c.getId())

    c_in_model = Relationship(neo_c, "COMPARTMENT_IN_MODEL", bob)
    graph.create(alice_knows_bob)



    # species


    # reactions






'''
from py2neo import Node, Relationship

alice = Node("Person", name="Alice")
bob = Node("Person", name="Bob")
alice_knows_bob = Relationship(alice, "KNOWS", bob)
graph.create(alice_knows_bob)
'''

if __name__ == "__main__":
    from data.data import example_filepath
    sbml_2_neo(example_filepath)

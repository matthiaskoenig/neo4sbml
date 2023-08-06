"""Example testing py2neo.

Py2neo is a client library and comprehensive toolkit for working with 
Neo4j from within Python applications and from the command line. 
The core library has no external dependencies and has been carefully 
designed to be easy and intuitive to use.
"""
from __future__ import print_function
import py2neo
# authentication
py2neo.authenticate(host_port="localhost:7474", user_name="neo4j", password="test")

# API essentials
# http://py2neo.org/2.0/essentials.html


# The simplest way to try out a connection to the Neo4j server is via the
# console. Once you have started a local Neo4j server, open a new Python
# console and enter the following:
from py2neo import Graph

graph = Graph()

# Nodes and relationships
from py2neo import Node, Relationship
alice = Node("Person", name="Alice")
bob = Node("Person", name="Bob")
alice_knows_bob = Relationship(alice, "KNOWS", bob)
graph.create(alice_knows_bob)

# Pushing and pulling
# To illustrate synchronisation, let’s give Alice and Bob an 
# age property each. 
alice.properties["age"] = 33
bob.properties["age"] = 44
alice.push()
bob.push()

# Previous versions of py2neo have synchronised data between 
# client and server automatically, such as when setting a single 
# property value. Py2neo 2.0 will not carry out updates to client 
# or server objects until this is explicitly requested.

# Here, we add a new property to each of the two local nodes and 
# push the changes in turn. This results in two separate HTTP calls 
# being made to the server which can be seen more clearly with the 
# debugging function, watch:
from py2neo import watch
watch("httpstream")
alice.push()
bob.push()

# To squash these two separate push operations into one, 
# we can use the Graph.push method instead:
graph.push(alice, bob)

# Cypher
# Neo4j has a built-in data query and manipulation language 
# called Cypher. To execute Cypher from within py2neo, simply use the 
# cypher attribute of a Graph instance and call the execute method:
graph.cypher.execute("CREATE (c:Person {name:{N}}) RETURN c", {"N": "Carol"})

# The object returned from this call is a RecordList which is 
# rendered by default as a table of results. Each item in this list 
# is a Record instance:
for record in graph.cypher.execute("CREATE (d:Person {name:'Dave'}) RETURN d"):
    print(record)
    
# A Record exposes its values through both named attributes and numeric 
# indexes. Therefore, if a Cypher query returns a column called name, 
# that column can be accessed through the record attribute called name:
for record in graph.cypher.execute("MATCH (p:Person) RETURN p.name AS name"):
    print(record.name)

# Transactions
# Transactions such as these allow far more control over the logical 
# grouping of statements and can also offer vastly better performance 
# compared to individual statements by submitting multiple statements in a single HTTP request.

# To use this endpoint, firstly call the begin method on the Graph.cypher resource to create a transaction, then use the methods listed below on the new CypherTransaction object:
tx = graph.cypher.begin()
statement = "MATCH (a {name:{A}}), (b {name:{B}}) CREATE (a)-[:KNOWS]->(b)"
for person_a, person_b in [("Alice", "Bob"), ("Bob", "Dave"), ("Alice", "Carol")]:
    tx.append(statement, {"A": person_a, "B": person_b})
tx.commit()


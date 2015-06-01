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
from neo4sbml.data import data

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
# ------------------------------------------------------------------

class NeoGraphFactory(object):
    """ Creates the neo4j graph from SBML.

        Perform all the requests in a transaction
        http://py2neo.org/2.0/cypher.html#transactions
    """
    def __init__(self, graph, sbml_filepath):
        self.path = sbml_filepath
        self.graph = graph

        # hashing for unique id
        self.md5 = data.hash_for_file(sbml_filepath)

        #  sbml model
        self.doc = libsbml.readSBMLFromFile(sbml_filepath)
        self.model = self.doc.getModel()
        self.model_id = self.model.getId()

        # transaction
        self.tx = None

    @classmethod
    def setup_graph(cls):
        """ Setup the neo4j graph and creates the constraints and indices."""
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

    def sbml2neo(self):
        # start transaction
        self.tx = self.graph.cypher.begin()

        # model
        self.rdf_graph(self.model, 'Model')

        # compartments
        for obj in self.model.getListOfCompartments():
            label = 'Compartment'
            self.rdf_graph(obj=obj, label=label)
            self.link_to_model(obj=obj, label=label)
        self.tx.process()
        # self.tx.commit()

        # species
        # self.tx = self.graph.cypher.begin()
        for obj in self.model.getListOfSpecies():
            label = 'Species'
            self.rdf_graph(obj=obj, label=label)
            self.link_to_model(obj=obj, label=label)
        self.tx.process()
        # self.tx.commit()

        # reactions
        # self.tx = self.graph.cypher.begin()
        for obj in self.model.getListOfReactions():
            label = 'Reaction'
            self.rdf_graph(obj=obj, label=label)
            self.link_to_model(obj=obj, label=label)
        self.tx.process()

        # commit transaction
        self.tx.commit()
        # ----------------------------------------------------

    def rdf_graph(self, obj, label):
        """ Creates the RDF graph for the given model object. """
        object_id = '__'.join([obj.getId(), self.md5])
        # Create the object node
        cypher_str = '''
            MERGE (m:SBase:{} {{ object_id: "{}" }})
            ON CREATE SET m.id="{}"
            ON CREATE SET m.name="{}"
            ON CREATE SET m.model="{}"
            '''.format(label, object_id, obj.getId(), obj.getName(), self.model_id)

        # self.graph.cypher.execute(cypher_str)
        self.tx.append(cypher_str)

        # read the rdf information
        rdf = self.read_rdf(obj)
        # create rdf nodes and relationships
        self.create_rdf_nodes(rdf, object_id=object_id)

    def create_rdf_nodes(self, rdf, object_id):
        """ Creates the additional RDF nodes for the given neo_node. """
        for d in rdf:
            for uri in d['URIS']:
                # create RDF node
                cypher_str = 'MERGE (r:RDF {{uri: "{}" }})'.format(uri)
                # self.graph.cypher.execute(cypher_str)
                self.tx.append(cypher_str)

                # create RDF relationship
                # TODO: set RDF:d["QualifierType"] label on relationship
                cypher_str = '''
                    MATCH (r:RDF) WHERE r.uri="{}"
                    MATCH (m) WHERE m.object_id="{}"
                    MERGE (r)-[:{}]->(m)
                '''.format(uri, object_id, d["Qualifier"])

                # self.graph.cypher.execute(cypher_str)
                self.tx.append(cypher_str)

    def link_to_model(self, obj, label):
        """ Link between model objects and model."""
        relation_str = "_".join([label.upper(), 'IN', 'MODEL'])
        object_id = '__'.join([obj.getId(), self.md5])
        # TODO: set IN_MODEL label on relationship
        cypher_str = '''
                MATCH (c:{}) WHERE c.object_id="{}"
                MATCH (m:Model) WHERE m.object_id="{}"
                MERGE (c)-[:{}]->(m)
        '''.format(label, object_id, "__".join([self.model_id, self.md5]), relation_str)

        # self.graph.cypher.execute(cypher_str)
        self.tx.append(cypher_str)

    @staticmethod
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

    @staticmethod
    def split_uri(uri):
        # TODO: get the splitted information and create nodes from them
        raise NotImplemented


if __name__ == "__main__":
    import time

    # [A] parse one test file
    '''
    graph = NeoGraphFactory.setup_graph()
    path = data.example_filepath
    print(path)
    g_fac = NeoGraphFactory(graph, sbml_filepath=path)
    g_fac.sbml2neo()

    path = data.get_filepath(469)
    print(path)
    g_fac = NeoGraphFactory(graph, sbml_filepath=path)
    g_fac.sbml2neo()
    '''


    # ------------------------------------------------------------------------------
    # TODO: protection against cross-site scripting by providing dictionary
    # [B] parse all the models (~600s = 10min)
    files = data.get_biomodel_paths()
    print("Number of models:", len(files))

    def process_file(graph, path, k):
        print('[{}/{}] {}'.format(k+1, len(files), path))
        # start = time.time()
        graph_fac = NeoGraphFactory(graph=graph, sbml_filepath=path)
        graph_fac.sbml2neo()
        # print('Time:', time.time()-start)

    # serial solution

    graph = NeoGraphFactory.setup_graph()
    start = time.time()
    for k, path in enumerate(files):
        process_file(graph=graph, path=path, k=k)
    print('Serial:', time.time()-start)

    '''
    # parallel solution
    # not really faster (?), probably due to the full transaction per file (->smaller transactions)
    import multiprocessing as mp
    Ncores = 4
    pool = mp.Pool(processes=Ncores)
    start = time.time()
    results = [pool.apply(process_file, args=(path, k)) for (k, path) in enumerate(files)]
    print('Parallel:', time.time()-start)
    '''

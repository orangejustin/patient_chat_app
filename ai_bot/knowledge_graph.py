"""
We import Neo4jVector and OpenAIEmbeddings to work with vector embeddings.
The add_document method allows us to add documents to the vector store.
The similarity_search and hybrid_search methods enable us to perform vector-based retrieval.
We maintain existing methods for adding entities and relationships to the Neo4j graph.

python ai_bot/knowledge_graph.py
"""

import os
from dotenv import load_dotenv
from langchain_community.vectorstores import Neo4jVector
from langchain_openai import OpenAIEmbeddings
from langchain.docstore.document import Document
from langchain_community.graphs import Neo4jGraph

class KnowledgeGraph:
    def __init__(self):
        load_dotenv()
        self.uri = os.getenv('NEO4J_URI')
        self.user = os.getenv('NEO4J_USER')
        self.password = os.getenv('NEO4J_PASSWORD')

        self.embeddings = OpenAIEmbeddings(api_key=os.getenv('OPENAI_API_KEY'))
        self.vector_store = Neo4jVector(
            url=self.uri,
            username=self.user,
            password=self.password,
            embedding=self.embeddings
        )
        self.graph = Neo4jGraph(url=self.uri, username=self.user, password=self.password)

    def add_document(self, doc_id, text, metadata=None):
        # Create a document and add it to the vector store
        from langchain.docstore.document import Document
        document = Document(page_content=text, metadata=metadata or {"id": doc_id})
        self.vector_store.add_documents([document])

    def similarity_search(self, query, k=5, search_type='similarity'):
        # Perform similarity search using the vector store
        results = self.vector_store.similarity_search(query, k=k, search_type=search_type)
        return results

    def hybrid_search(self, query, k=5):
        # Perform hybrid search combining vector and full-text search
        results = self.vector_store.similarity_search(query, k=k, search_type='hybrid')
        return results

    def add_entity(self, label, properties):
        content = " ".join(f"{k}: {v}" for k, v in properties.items())
        metadata = {"label": label, **properties}
        document = Document(page_content=content, metadata=metadata)
        self.vector_store.add_documents([document])

    def add_relationship(self, label1, properties1, relation, label2, properties2):
        query = f"""
        MATCH (a:{label1} {{{', '.join(f'{k}: ${k}1' for k in properties1.keys())}}})
        MATCH (b:{label2} {{{', '.join(f'{k}: ${k}2' for k in properties2.keys())}}})
        MERGE (a)-[:{relation}]->(b)
        """
        params = {f"{k}1": v for k, v in properties1.items()}
        params.update({f"{k}2": v for k, v in properties2.items()})
        self.graph.query(query, params)

    def get_entity_info(self, label, properties):
        query = f"""
        MATCH (e:{label} {{{', '.join(f'{k}: ${k}' for k in properties.keys())}}})
        RETURN e
        """
        result = self.graph.query(query, properties)
        return result[0]['e'] if result else None

if __name__ == "__main__":
    kg = KnowledgeGraph()
    medication_info = kg.get_entity_info('Medication', {'name': 'Lisinopril'})
    if medication_info:
        print("Graph query result:", medication_info)
    else:
        print("No medication found in graph database")
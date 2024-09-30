"""
knowledge graph using Neo4jGraph to add entities and relationships 
and to query the graph using Cypher queries and LLMs from Langchain

python ai_bot/knowledge_graph.py
"""

import os
from dotenv import load_dotenv
from langchain_community.vectorstores import Neo4jVector
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.docstore.document import Document
from langchain_community.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate

from ai_bot.prompts import cypher_query_examples

SCHEMA = """
        (:Patient)
            -[:TAKES]->(:Medication {name: String, dosage: String, frequency: String})
            -[:HAS]->(:HealthIssue {description: String})  // Combines Symptoms and Conditions
            -[:SCHEDULES]->(:Appointment {time: String})
            -[:HAS_LAB_TEST]->(:LabTest {name: String})
            -[:HAS_NOTE]->(:DoctorNote {content: String})
            -[:HAS_VITAL]->(:Vital {
                weight: String, 
                height: String, 
                blood_pressure: String, 
                heart_rate: String, 
                temperature: String
            })
            -[:HAS_ALLERGY]->(:Allergy {name: String})
            -[:HAS_FAMILY_HISTORY]->(:FamilyHistory {description: String})
            -[:HAS_LIFESTYLE_FACTOR]->(:LifestyleFactor {description: String})
            -[:HAS_IMMUNIZATION]->(:Immunization {name: String, date: String})

        (:Medication)-[:HAS_DOSAGE]->(:Dosage {value: String})
        (:Medication)-[:HAS_FREQUENCY]->(:Frequency {value: String})
        """.strip()

class KnowledgeGraph:
    def __init__(self):
        load_dotenv()
        self.uri = os.getenv('NEO4J_URI')
        self.user = os.getenv('NEO4J_USER')
        self.password = os.getenv('NEO4J_PASSWORD')

        # self.embeddings = OpenAIEmbeddings(api_key=os.getenv('OPENAI_API_KEY'))
        # self.vector_store = Neo4jVector(
        #     url=self.uri,
        #     username=self.user,
        #     password=self.password,
        #     embedding=self.embeddings
        # )

        self.graph = Neo4jGraph(url=self.uri, username=self.user, password=self.password)
        
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        # Create the example prompt template
        example_prompt = PromptTemplate.from_template(
            "User input: {question}\nCypher query: {query}"
        )
        
        # Create the few-shot prompt template
        self.prompt = FewShotPromptTemplate(
            examples=cypher_query_examples[:5],
            example_prompt=example_prompt,
            prefix="You are a Neo4j expert. Given an input question, create a syntactically correct Cypher query to run.\n\nHere is the schema information\n{schema}.\n\nBelow are a number of examples of questions and their corresponding Cypher queries.",
            suffix="User input: {question}\nCypher query: ",
            input_variables=["question", "schema"]
        )

        # Initialize the QA chain with the new prompt
        self.qa_chain = GraphCypherQAChain.from_llm(
            graph=self.graph,
            llm=self.llm,
            verbose=True,
            validate_cypher=True,
            cypher_prompt=self.prompt,
            allow_dangerous_requests=True
        )

    def add_document(self, doc_id, text, metadata=None):
        # Create a document and add it to the vector store
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
        query = f"""
        MERGE (e:{label} {{{', '.join(f'{k}: ${k}' for k in properties.keys())}}})
        """
        self.graph.query(query, properties)

    def add_relationship(self, start_label, start_props, relation, end_label, end_props):
        query = f"""
        MATCH (a:{start_label} {{{', '.join(f'{k}: ${k}1' for k in start_props.keys())}}})
        MATCH (b:{end_label} {{{', '.join(f'{k}: ${k}2' for k in end_props.keys())}}})
        MERGE (a)-[:{relation}]->(b)
        """
        params = {f"{k}1": v for k, v in start_props.items()}
        params.update({f"{k}2": v for k, v in end_props.items()})
        self.graph.query(query, params)

    def get_entity_info(self, label, properties):
        query = f"""
        MATCH (e:{label} {{{', '.join(f'{k}: ${k}' for k in properties.keys())}}})
        RETURN e
        """
        result = self.graph.query(query, properties)
        return result[0]['e'] if result else None

    def refresh_schema(self):
        self.graph.refresh_schema()

    def get_schema(self):
        return self.graph.schema

    def ask(self, question):
        """
        Ask a question and get a response if we don't already have the query
        """
        return self.qa_chain.invoke({"query": question})
    
    def execute_query(self, query, params=None):
        """
        Execute a cypher query if we already have the query
        """
        result = self.graph.query(query, params)
        return result

    def clear_graph(self):
        """
        Clear all nodes and relationships from the graph.
        """
        query = """
        MATCH (n)
        DETACH DELETE n
        """
        self.graph.query(query)
        

if __name__ == "__main__":
    kg = KnowledgeGraph()
    kg.refresh_schema()
    print("Graph Schema:", kg.get_schema())
    

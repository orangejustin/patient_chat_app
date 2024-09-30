"""
prompts, query examples

refer to https://python.langchain.com/docs/how_to/graph_prompting/
"""

__all__ = ['cypher_query_examples', 'entity_extraction_prompt']


entity_extraction_prompt = """
You are a helpful AI health assistant bot. Extract health-related entities from the user's input and format them as JSON. 
Include fields for medications, dosage, frequency, symptoms, conditions, diet, and appointment_time. 
For fields with multiple items, combine them into a single string using 'and' as a separator.
""".strip()



cypher_query_examples = [
    {
        "question": "What symptoms does the patient have?",
        "query": "MATCH (p:Patient)-[:HAS]->(s:Symptoms) RETURN s.name",
    },
    {
        "question": "What medications is the patient taking?",
        "query": "MATCH (p:Patient)-[:TAKES]->(m:Medication) RETURN m.name",
    },
    {
        "question": "What is the patient's diet?",
        "query": "MATCH (p:Patient)-[:FOLLOWS]->(d:Diet) RETURN d.description",
    },
    {
        "question": "What conditions does the patient have?",
        "query": "MATCH (p:Patient)-[:HAS]->(c:Conditions) RETURN c.name",
    },
    {
        "question": "When is the patient's appointment scheduled?",
        "query": "MATCH (p:Patient)-[:SCHEDULES]->(a:Appointment) RETURN a.time",
    },
    {
        "question": "What are the dosages of the patient's medications?",
        "query": "MATCH (p:Patient)-[:TAKES]->(m:Medication)-[:HAS_DOSAGE]->(d:Dosage) RETURN m.name, d.value",
    },
    {
        "question": "How frequently does the patient take their medications?",
        "query": "MATCH (p:Patient)-[:TAKES]->(m:Medication)-[:HAS_FREQUENCY]->(f:Frequency) RETURN m.name, f.value",
    },
    {
        "question": "What medications is the patient taking for their conditions?",
        "query": "MATCH (p:Patient)-[:HAS]->(c:Conditions), (p)-[:TAKES]->(m:Medication) RETURN c.name, collect(m.name)",
    },
    {
        "question": "Does the patient have any symptoms related to their medications?",
        "query": "MATCH (p:Patient)-[:TAKES]->(m:Medication), (p)-[:HAS]->(s:Symptoms) RETURN m.name, collect(s.name)",
    },
    {
        "question": "What is the patient's complete medication regimen, including dosages and frequencies?",
        "query": "MATCH (p:Patient)-[:TAKES]->(m:Medication)-[:HAS_DOSAGE]->(d:Dosage), (m)-[:HAS_FREQUENCY]->(f:Frequency) RETURN m.name, d.value, f.value",
    },
]


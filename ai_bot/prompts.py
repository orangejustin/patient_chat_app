"""
prompts, query examples

refer to https://python.langchain.com/docs/how_to/graph_prompting/
"""

__all__ = ['cypher_query_examples', 'entity_extraction_prompt', 'QUESTIONS']


entity_extraction_prompt = """
You are a helpful AI health assistant bot. Extract health-related entities from the user's input. 
Include fields for medications, dosage, frequency, family_history, health_issues, appointment_time, lab_tests, doctor_notes, weight, height, blood_pressure, heart_rate, temperature, allergies, lifestyle_factors, immunizations.
For fields with multiple items, combine them into a single string using commas as separators. 
Do not infer any information from the user's input. Lowercase all the fields.
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
        "question": "What new appointment time is the patient requesting?",
        "query": "MATCH (p:Patient)-[:SCHEDULES]->(a:Appointment) RETURN a.time" 
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
    {
        "question": "What new appointment time is the patient requesting?",
        "query": """
        MATCH (p:Patient)
        OPTIONAL MATCH (p)-[:SCHEDULES]->(a:Appointment)
        RETURN a.time AS requested_appointment_time, 
               CASE WHEN a IS NOT NULL THEN true ELSE false END AS change_requested
        """
    }
]

# Define the QUESTIONS dictionary with follow-ups
QUESTIONS = {
    "medications": {
        "question": "Can you please list all the medications you are currently taking?",
        "follow_ups": ["dosage", "frequency"]
    },
    "dosage": {
        "question": "What is the dosage for each of your medications?",
        "follow_ups": []
    },
    "frequency": {
        "question": "How often do you take each medication?",
        "follow_ups": []
    },
    "family_history": {
        "question": "Do you have any family members with a history of medical conditions?",
        "follow_ups": []
    },
    "health_issues": {
        "question": "What current health problems or symptoms are you experiencing?",
        "follow_ups": []
    },
    # ... add other primary questions
}

if __name__ == "__main__":
    print(cypher_query_examples[:5])
# ai_bot/agent.py

from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END

from ai_bot.entity_extraction import extract_entities, store_entities_as_documents
from ai_bot.prompts import QUESTIONS
from ai_bot.langchain_integration import get_bot_response, get_bot_response_based_on_entities
from ai_bot.knowledge_graph import KnowledgeGraph
from ai_bot.models import AppointmentRequest

from neo4j.exceptions import ClientError, Neo4jError
import logging

# Adjust logging level for neo4j driver
logging.getLogger("neo4j").setLevel(logging.ERROR)

kg = KnowledgeGraph()

# Define the state
class AgentState(BaseModel):
    input: str
    entities: Dict[str, Optional[str]] = Field(default_factory=dict)
    missing_entities: List[str] = Field(default_factory=list)
    follow_up_question: Optional[str] = None
    response: Optional[str] = None
    patient: Optional[object] = None  # Replace with the patient model
    session_id: Optional[str] = None
    current_question: Optional[str] = None  # Track the current follow-up question

# Step 1: Extract entities
def extract_entities_step(state: AgentState):
    entities = extract_entities(state.input)
    # entities[state.current_question] = extracted_value or state.input
    if state.current_question:
        extracted_value = entities.get(state.current_question)
        state.entities[state.current_question] = extracted_value or state.input
    else:
        state.entities.update(entities)

    state.current_question = None

    if entities:
        patient_properties = {'name': state.patient.get_full_name()}
        patient_properties['store_medication'] = entities.get("medications") is not None
        patient_properties['store_appointment'] = entities.get("appointment_time") is not None
        # Use MERGE to avoid duplicates and update properties
        query = f"""
        MERGE (p:Patient {{name: "{state.patient.get_full_name()}"}})
        SET p.store_medication = {patient_properties['store_medication']}, p.store_appointment = {patient_properties['store_appointment']}
        """
        kg.graph.query(query)
        store_entities_as_documents(entities, state.patient.get_full_name())
    
    return {"entities": state.entities}

# Step 2: Check for missing entities
def check_missing_entities_step(state: AgentState):
    required_entities = []
    patient_name = state.patient.get_full_name()

    if state.entities.get("medications"):
        # Query the database to see if dosage and frequency for this medication already exist
        medication_name = state.entities.get("medications").strip()
        query = f"""
        MATCH (p:Patient {{name: "{patient_name}"}})-[:TAKES]->(m:Medication {{name: "{medication_name}"}})
        OPTIONAL MATCH (m)-[:HAS_DOSAGE]->(d:Dosage)
        OPTIONAL MATCH (m)-[:HAS_FREQUENCY]->(f:Frequency)
        RETURN 
            COUNT(d) AS dosage_count,
            COUNT(f) AS frequency_count
        """
        try:
            result = kg.graph.query(query)
            if result:
                record = result[0]
                dosage_count = record.get('dosage_count', 0)
                frequency_count = record.get('frequency_count', 0)
            else:
                dosage_count = 0
                frequency_count = 0
        except (ClientError, Neo4jError) as e: # UnknownLabelWarning is fine as it's not yet stored
            pass

        if not state.entities.get("dosages") and dosage_count == 0:
            required_entities.append("dosages")
        if not state.entities.get("frequencies") and frequency_count == 0:
            required_entities.append("frequencies")

    state.missing_entities = required_entities
    return {"missing_entities": state.missing_entities}

# Step 3a: Ask follow-up question
def ask_follow_up_question_step(state: AgentState):
    if state.missing_entities:
        next_entity = state.missing_entities.pop(0)
        question = QUESTIONS[next_entity]["question"]
        state.follow_up_question = question
        state.current_question = next_entity
        return {"follow_up_question": question}
    else:
        return {}

# Step 3b: Generate response
def generate_response_step(state: AgentState):

    patient_name = state.patient.get_full_name()
    query = f"""
    MATCH (p:Patient {{name: "{patient_name}"}})
    OPTIONAL MATCH (p)-[:TAKES]->(medication:Medication)
    OPTIONAL MATCH (medication)-[:HAS_DOSAGE]->(dosage:Dosage)
    OPTIONAL MATCH (medication)-[:HAS_FREQUENCY]->(frequency:Frequency)
    OPTIONAL MATCH (p)-[:HAS]->(health_issue:HealthIssue)
    OPTIONAL MATCH (p)-[:SCHEDULES]->(appointment:Appointment)
    OPTIONAL MATCH (p)-[:HAS_LAB_TEST]->(lab_test:LabTest)
    OPTIONAL MATCH (p)-[:HAS_NOTE]->(doctor_note:DoctorNote)
    OPTIONAL MATCH (p)-[:HAS_VITAL]->(vital:Vital)
    OPTIONAL MATCH (p)-[:HAS_ALLERGY]->(allergy:Allergy)
    OPTIONAL MATCH (p)-[:HAS_FAMILY_HISTORY]->(family_history:FamilyHistory)
    OPTIONAL MATCH (p)-[:HAS_LIFESTYLE_FACTOR]->(lifestyle_factor:LifestyleFactor)
    OPTIONAL MATCH (p)-[:HAS_IMMUNIZATION]->(immunization:Immunization)
    RETURN 
        CASE WHEN count(medication) > 0 THEN collect(DISTINCT medication.name) ELSE null END AS medications,
        CASE WHEN count(dosage) > 0 THEN collect(DISTINCT dosage.value) ELSE null END AS dosages,
        CASE WHEN count(frequency) > 0 THEN collect(DISTINCT frequency.value) ELSE null END AS frequencies,
        CASE WHEN count(health_issue) > 0 THEN collect(DISTINCT health_issue.description) ELSE null END AS health_issues,
        CASE WHEN count(appointment) > 0 THEN collect(DISTINCT appointment.time) ELSE null END AS appointment_time,
        CASE WHEN count(lab_test) > 0 THEN collect(DISTINCT lab_test.name) ELSE null END AS lab_tests,
        CASE WHEN count(doctor_note) > 0 THEN collect(DISTINCT doctor_note.content) ELSE null END AS doctor_notes,
        CASE WHEN count(vital) > 0 THEN collect(DISTINCT vital.weight) ELSE null END AS weight,
        CASE WHEN count(vital) > 0 THEN collect(DISTINCT vital.height) ELSE null END AS height,
        CASE WHEN count(vital) > 0 THEN collect(DISTINCT vital.blood_pressure) ELSE null END AS blood_pressure,
        CASE WHEN count(vital) > 0 THEN collect(DISTINCT vital.heart_rate) ELSE null END AS heart_rate,
        CASE WHEN count(vital) > 0 THEN collect(DISTINCT vital.temperature) ELSE null END AS temperature,
        CASE WHEN count(allergy) > 0 THEN collect(DISTINCT allergy.name) ELSE null END AS allergies,
        CASE WHEN count(family_history) > 0 THEN collect(DISTINCT family_history.condition) ELSE null END AS family_history,
        CASE WHEN count(lifestyle_factor) > 0 THEN collect(DISTINCT lifestyle_factor.description) ELSE null END AS lifestyle_factors,
        CASE WHEN count(immunization) > 0 THEN collect(DISTINCT immunization.name) ELSE null END AS immunizations
    """


    check_query = f"""
    MATCH (n:Patient {{name: "{patient_name}"}})
    WHERE n.store_appointment IS NOT NULL OR n.store_medication IS NOT NULL
    RETURN n.name AS name, n.store_appointment AS store_appointment, n.store_medication AS store_medication
    """

    try:
        result = kg.graph.query(query)
        check_result = kg.graph.query(check_query)
        if result:
            record = result[0]
            check_record = check_result[0]
            if check_record['store_medication'] and record.get("medications"):
                state.entities["dosage"] = record.get("dosages", '')
                state.entities["frequency"] = record.get("frequencies", '')
                entities_input = f'The patient is taking medications: {record.get("medications")} with dosages: {record.get("dosages")} and frequencies: {record.get("frequencies")}'
                response = get_bot_response_based_on_entities(entities_input, state.patient)
            elif check_record['store_appointment'] and record.get("appointment_time"):
                requested_time = record.get("appointment_time")[-1]
                requested_time = requested_time['time'] if isinstance(requested_time, dict) else requested_time
                # Create an AppointmentRequest
                AppointmentRequest.objects.create(
                    patient=state.patient,
                    current_time=state.patient.next_appointment_datetime,
                    requested_time=requested_time
                )
                response = f"I will convey your request to Dr. {state.patient.doctor_name}."
            else:
                response = get_bot_response(state.input, state.patient)
    except (ClientError, Neo4jError) as e:
        pass

    state.response = response
    return {"response": response}

# Conditional function: Determine next step based on missing_entities
def should_ask_follow_up(state: AgentState):
    if state.missing_entities:
        return "ask_follow_up_question"
    else:
        return "generate_response"

# Create the StateGraph
agent_graph = StateGraph(AgentState)

# Add nodes
agent_graph.add_node("extract_entities", extract_entities_step)
agent_graph.add_node("check_missing_entities", check_missing_entities_step)
agent_graph.add_node("ask_follow_up_question", ask_follow_up_question_step)
agent_graph.add_node("generate_response", generate_response_step)

# Add edges
agent_graph.add_edge(START, "extract_entities")
agent_graph.add_edge("extract_entities", "check_missing_entities")
agent_graph.add_conditional_edges(
    "check_missing_entities",
    should_ask_follow_up,
    ["ask_follow_up_question", "generate_response"]
)
agent_graph.add_edge("ask_follow_up_question", END)
agent_graph.add_edge("generate_response", END)

# Compile the graph
agent_app = agent_graph.compile()

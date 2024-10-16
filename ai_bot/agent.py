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
    patient: Optional[object] = None  # Replace with your patient model
    session_id: Optional[str] = None
    current_question: Optional[str] = None  # Track the current follow-up question

# Step 1: Extract entities
def extract_entities_step(state: AgentState):
    entities = extract_entities(state.input)
    # print(entities)
    if state.current_question:
        # Map the user's response to the entity being asked
        # state.entities[state.current_question] = entities.get(state.current_question, state.input)
        state.entities = entities
    else:
        # Update entities with the newly extracted ones
        state.entities.update(entities)

    # Clear current_question after processing
    state.current_question = None

    if state.entities:
        # Store the entities in the Neo4j database immediately
        store_entities_as_documents(state.entities, state.patient.get_full_name())

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

        if not state.entities.get("dosage") and dosage_count == 0:
            required_entities.append("dosage")
        if not state.entities.get("frequency") and frequency_count == 0:
            required_entities.append("frequency")

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
        medication AS medications,
        dosage AS dosages,
        frequency AS frequencies,
        health_issue AS health_issues,
        appointment AS appointments,
        lab_test AS lab_tests,
        doctor_note AS doctor_notes,
        vital AS vitals,
        allergy AS allergies,
        family_history AS family_histories,
        lifestyle_factor AS lifestyle_factors,
        immunization AS immunizations
    """
    try:
        result = kg.graph.query(query)
        if result:
            record = result[0]
            if record.get("medications"):
                state.entities["dosage"] = record.get("dosages", state.entities.get("dosage"))
                state.entities["frequency"] = record.get("frequencies", state.entities.get("frequency"))
                entities_input = f'The patient is taking medications: {record.get("medications")} with dosages: {record.get("dosages")} and frequencies: {record.get("frequencies")}'
                response = get_bot_response_based_on_entities(entities_input, state.patient)
            elif record.get("appointments"):
                requested_time = record.get("appointments")
                # requested_time or requested_time['time']
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

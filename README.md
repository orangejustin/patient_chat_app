# Patient Chat Application

Welcome to the Patient Chat Application! This project is a Django-based web application that allows patients to interact with an AI health assistant. The assistant provides personalized health-related information, manages patient data, and utilizes advanced AI capabilities such as entity extraction and knowledge graph integration.

---

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Setup and Installation](#setup-and-installation)
  - [Clone the Repository](#clone-the-repository)
  - [Create a Virtual Environment](#create-a-virtual-environment)
  - [Install Dependencies](#install-dependencies)
  - [Configure Environment Variables](#configure-environment-variables)
  - [Set Up the PostgreSQL Database](#set-up-the-postgresql-database)
  - [Set Up Neo4j Graph Database (Optional)](#set-up-neo4j-graph-database-optional)
  - [Create a Patient Profile](#create-a-patient-profile)
  - [Run the Application](#run-the-application)
- [Implementation Details](#implementation-details)
  - [Backend](#backend)
  - [AI Integration](#ai-integration)
  - [Database Schema](#database-schema)
  - [Entity Extraction](#entity-extraction)
  - [Knowledge Graph Integration](#knowledge-graph-integration)
- [Future Enhancements](#future-enhancements)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- Interactive chat interface for patients to communicate with an AI health assistant.
- Personalized responses based on patient data.
- Entity extraction from patient messages to update medical records.
- Knowledge graph integration using Neo4j for advanced data retrieval.
- Supports Retrieval Augmented Generation (RAG) for improved AI responses.

---

## Technology Stack

- **Backend:** Django
- **Frontend:** Django Templates (provided by Django framework)
- **AI Integration:** Langchain, Langgraph
- **Databases:**
  - **Primary Database:** PostgreSQL
  - **Graph Database:** Neo4j
- **Language Model:** OpenAI GPT models via `langchain-openai` (configurable to other LLMs)
- **Dependencies:** Listed in `requirements.txt`

---

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- Python 3.10 
- PostgreSQL
- Neo4j (for knowledge graph features)
- Git

---

## Setup and Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/patient-chat-app.git
cd patient-chat-app
```

### 2. Create a Virtual Environment

```bash
conda create -n patient_chat_app python=3.10
conda activate patient_chat_app
```

### 3. Install Dependencies

Ensure that `pip` is up to date and install the required packages:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root directory and add the following environment variables:

```env
# OpenAI API Key (or your chosen LLM provider)
OPENAI_API_KEY=sk-...

# Database Settings
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
DB_HOST=localhost # or your host
DB_PORT=5432 # or your port number

# NEO4J Settings
NEO4J_URI=neo4j+s://...io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=3g...
```

### 5. Set Up the PostgreSQL Database

- **Install PostgreSQL:**
  - Download and install PostgreSQL from [the official website](https://www.postgresql.org/download/).
- **Create a Database:**
  - Open the PostgreSQL shell or use a GUI tool like pgAdmin.
  - Create a new database named `patient_chat_db`.
- **Update Database Settings:**
  - Ensure your `.env` file contains the correct database credentials.

### 6. Set Up Neo4j Graph Database 

- **Install Neo4j:**
  - Download and install Neo4j from [the official website](https://neo4j.com/docs/operations-manual/current/installation/).
- **Create a New Instance Using AuraDB Free:**
  - Sign up for a free account at [Neo4j Aura](https://neo4j.com/cloud/aura/).
  - Create a new database instance and follow the setup instructions provided.
  - Validate that your Aura instance is available by visiting [Neo4j Console](https://console.neo4j.io).
- **Update Neo4j Settings:**
  - Ensure your `.env` file contains the correct Neo4j credentials, including the AuraDB connection URI and credentials.

### 7. Create a Patient Profile

The application requires at least one patient profile to function. You can create a patient profile using the Django shell.

- **Run Django Migrations:**

  ```bash
  python manage.py makemigrations
  python manage.py migrate
  ```

- **Open the Django Shell:**

  ```bash
  python manage.py shell
  ```

- **Create a Patient Instance:**

  ```python
  from patients.models import Patient
  from django.utils import timezone
  from datetime import datetime

  patient = Patient.objects.create(
      first_name='Michael',
      last_name='Davidson',
      date_of_birth=datetime(1980, 1, 1).date(),
      phone_number='858-539-0000',
      email='michael@example.com',
      medical_condition='Hypertension',
      medication_regimen='Lisinopril 10mg once daily',
      last_appointment_datetime=timezone.make_aware(datetime(2024, 9, 15, 10, 0)),
      next_appointment_datetime=timezone.make_aware(datetime(2024, 10, 15, 10, 0)),
      doctor_name='Dr. John Smith'
  )
  ```

- **Exit the Shell:**

  ```python
  exit()
  ```

### 8. Run the Application

Start the Django development server:

```bash
python manage.py runserver
```

Open your web browser and navigate to `http://localhost:8000` to access the application.

---

## Implementation Details

### Backend

The backend is built with Django, providing robust support for web applications and easy integration with databases.

- **Apps:**
  - `chat`: Handles the chat interface and conversation logic.
  - `patients`: Manages patient data and models.
  - `ai_bot`: Contains AI-related logic, including language model integration and knowledge graph interactions.

### AI Integration

- **Langchain and Langgraph:**
  - Used for integrating Large Language Models (LLMs) and implementing Retrieval Augmented Generation (RAG).
- **Language Model:**
  - The application uses OpenAI GPT models via `langchain-openai`.
  - Configurable to use other LLMs by modifying the `LLM_PROVIDER` and related settings in the `.env` file.

### Database Schema

#### PostgreSQL

Used as the primary relational database for storing patient data, conversation history, and other structured information.

#### Neo4j (Optional)

Utilized for the knowledge graph, enabling advanced data retrieval and relationships.

- **Graph Schema:**

  ```text
  (:Patient)
      -[:TAKES]->(:Medication {name: String, dosage: String, frequency: String})
      -[:HAS]->(:HealthIssue {description: String})
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
  ```

### Entity Extraction

- **LLM with Pydantic Model:**
  - Uses an LLM to parse user input and extract entities based on a predefined Pydantic model.
- **Chain Setup:**
  - The chain is configured as `chain = prompt | llm | json_parser` to process and extract entities.

### Knowledge Graph Integration

- **Neo4j Vector Index:**
  - Utilizes `Neo4jVector` for vector storage and retrieval.
- **Advanced RAG Strategies:**
  - Implements hybrid search combining vector similarities and contextual attributes.
- **Natural Language Interface:**
  - Leverages Langchain's `GraphCypherQAChain` to allow natural language queries against the Neo4j graph.

---

## Future Enhancements

- **Multi-Agent System:**
  - Implement coordination between multiple models to handle different tasks within the chat using Langgraph.
- **Live Conversation Summaries:**
  - Detect and output live conversation summaries and medical insights from ongoing interactions.
- **Cloud Deployment:**
  - Adapt the application for deployment on cloud platforms.

---

## Contributing

We welcome contributions from the community! Please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Commit your changes with descriptive messages.
4. Push your branch to your forked repository.
5. Open a pull request against the main repository.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

Thank you for using the Patient Chat Application! If you have any questions or need assistance, please feel free to reach out.

---

# Additional Notes

## Requirements

All dependencies are listed in the `requirements.txt` file. Ensure you have installed all required packages using:

```bash
pip install -r requirements.txt
```

## Environment Variables

Ensure all environment variables are correctly set in your `.env` file to avoid any runtime errors.

## Patient Data

Currently, the system is designed for efficiency with a single patient profile but can accommodate multiple patients as needed.

## Neo4j Setup (Optional)

If you choose to enable the knowledge graph features:

- Download and install Neo4j from [the official website](https://neo4j.com/docs/operations-manual/current/installation/).
- Start the Neo4j server and ensure it's running.
- Update the Neo4j settings in your `.env` file.

## Changing the Language Model

You can switch to other language models supported by Langchain:

- Visit [Langchain LLM Integrations](https://python.langchain.com/docs/integrations/llms/) for available options.
- Update the LLM provider and API key in your `.env` file and adjust the code in `ai_bot/langchain_integration.py` accordingly.

## Database Configurations

Ensure that your PostgreSQL and Neo4j databases are properly configured and running before starting the application.

## Running Migrations

After any changes to the models, run:

```bash
python manage.py makemigrations
python manage.py migrate
```

## Contact

For support or inquiries, please contact [email](zechengl@andrew.cmu.edu).


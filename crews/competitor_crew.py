import os
import json
import re
import agentops

from fastapi.responses import JSONResponse
from fastapi import status
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import SerperDevTool
from tools.custom_tools import DistanceCalculatorTool, CompetitorVerifierTool

load_dotenv()


agentops.init(api_key="97e22f99-24ef-4233-8e39-83f04574dc96")

# Configurar el modelo LLM
    #model='gemini/gemini-2.0-flash-lite',

llm = LLM(
    model='gemini/gemini-2.0-flash-lite',   
    api_key=os.environ["GEMINI_API_KEY"],
    temperature=0,
    verbose=True,
)

# Herramientas
serper = SerperDevTool(n_results=5)
distance_tool = DistanceCalculatorTool()
verifier_tool = CompetitorVerifierTool()

# Agentes
dealership_info_agent = Agent(
    role="Dealership Info Gatherer",
    goal="Collect key information about the target car dealership {dealership} with a zipcode {zipcode}.",
    backstory="Expert researcher skilled at finding dealership details.",
    llm=llm,
    verbose=True,
    max_iter=5
)

competitor_researcher = Agent(
    role="Competitor Researcher",
    goal="Identify competitor car dealerships for {dealership}.",
    backstory="Market research specialist focused on car dealerships.",
    llm=llm,
    verbose=True,
    max_iter=5
)

data_organizer = Agent(
    role="Data Organizer",
    goal="Structure competitor data into a table with dealership info.",
    backstory="Data analyst experienced in formatting and cleaning information.",
    llm=llm,
    verbose=True,
    max_iter=5
)

results_supervisor = Agent(
    role="Results Supervisor",
    goal="Validate dealership and competitor data for accuracy and quality.",
    backstory="Quality assurance expert reviewing all information.",
    llm=llm,
    verbose=True,
    max_iter=5
)

# Tareas
dealership_info_task = Task(
    description="Find the OEM, address, and coordinates of the dealership {dealership} with zipcode {zipcode}.",
    expected_output="Dictionary with OEM, address, and coordinates.",
    agent=dealership_info_agent,
    tools=[serper]
)

competitor_research_task = Task(
    description=(
        "Search for car dealerships that sell the same OEM as {dealership}, located within {range} miles. "
        "Return exactly 5 competitors in JSON format with the following fields for each: "
        "name, website, distance (in miles), city, state, latitude, longitude, range."
    ),
    expected_output=(
        'List of 5 competitors as JSON objects: '
        '[{"name": "...", "website": "...", "distance": "...", "city": "...", '
        '"state": "...", "latitude": "...", "longitude": "...", "range": "..."}, ...]'
    ),
    agent=competitor_researcher,
    tools=[serper, distance_tool]
)

data_organization_task = Task(
    description="Organize competitor data as JSON list.",
    expected_output=(
    'Return the same 5 competitors as JSON list: '
    '[{"name": "...", "website": "...", "distance": "...", "city": "...", '
    '"state": "...", "latitude": "...", "longitude": "...", "range": "..."}, ...]'
),
    agent=data_organizer
)

supervision_task = Task(
    description="Verify all competitor data, check OEM, website, and existence.",
    expected_output=(
    'Validate and return the final list of 5 competitors in this exact JSON format: '
    '[{"name": "...", "website": "...", "distance": "...", "city": "...", '
    '"state": "...", "latitude": "...", "longitude": "...", "range": "..."}, ...]'
),
    agent=results_supervisor,
    tools=[verifier_tool]
)

# Crew
competitor_crew = Crew(
    agents=[dealership_info_agent, competitor_researcher, data_organizer, results_supervisor],
    tasks=[dealership_info_task, competitor_research_task, data_organization_task, supervision_task],
    process=Process.sequential,
   #poner true
    verbose=True
)

# Función para ejecutar desde main.py
def run_competitor_crew(**kwargs):
    raw_output = competitor_crew.kickoff(inputs=kwargs)

    try:
        # Convertir CrewOutput a string antes de procesar
        json_candidate = str(raw_output).strip()
        if "Final Output:" in json_candidate:
            json_candidate = json_candidate.split("Final Output:")[-1].strip()

        match = re.search(r"\[.*\]", json_candidate, re.DOTALL)
        if not match:
            return {"error": "No valid JSON list found in output."}

        cleaned_json = match.group()
        return json.loads(cleaned_json)
    except Exception as e:
        return {"error": f"Failed to parse JSON: {str(e)}"}
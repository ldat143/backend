import os
import json
import re
import agentops

from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import SerperDevTool

from tools.custom_tools import DistanceCalculatorTool, PopulationDataTool

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
population_tool = PopulationDataTool()

# Agentes
dealership_info_agent = Agent(
    role="Dealership Info Gatherer",
    goal="Collect key information about the target car dealership {dealership} with a zipcode {zipcode}.",
    backstory="Expert researcher skilled at finding dealership details.",
    llm=llm,
    verbose=True,
    max_iter=5
)

opportunities_researcher = Agent(
    role="Opportunities Researcher",
    goal="Using the dealership's {dealership} info, identify cities within {range} miles with population > 1000.",
    backstory="Market research specialist for geographic business expansion.",
    llm=llm,
    verbose=True,
    max_iter=5
)

data_organizer = Agent(
    role="Data Organizer",
    goal="Structure opportunity data into as a JSON list.",
    backstory="Data analyst experienced in formatting and cleaning information.",
    llm=llm,
    verbose=True,
    max_iter=5
)

results_supervisor = Agent(
    role="Results Supervisor",
    goal="Validate all opportunity data and present final structured output.",
    backstory="Quality assurance expert reviewing all opportunity recommendations.",
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

opportunities_research_task = Task(
    description=(
        "Using the OEM, address, state and location of the dealership {dealership}, look for nearby cities and/or metro areas "
        "within a {range}-mile radius and with population greater than 1000 people. "
        "Use SerperDevTool to find city names, their states and addresses."
        "Use PopulationDataTool to verify each city has a population > 1000. "
        "Use DistanceCalculatorTool for distances in miles. "
        "Return a list of valid cities with their City/Town Name, Distance from dealer, and State."
    ),
    expected_output=(
    'Return a JSON list of up to 5 cities like this:\n'
    '[{"distance": "string", "city": "string", "state": "string", '
    '"latitude": "float", "longitude": "float", "range": "float"}]'
),
    agent=opportunities_researcher,
    tools=[serper, distance_tool, population_tool]
)

data_organization_task = Task(
    description="Take the list of nearby cities and organize the data into a markdown table.",
    expected_output=(
    'Format and return the same 5 cities as JSON: '
    '[{"distance": "...", "city": "...", "state": "...", "latitude": "...", "longitude": "...", "range": "..."}, ...]'
),
    agent=data_organizer
)

supervision_task = Task(
    description="Review the dealership info and nearby city suggestions, and present the results clearly.",
    expected_output=(
    'Final validated list of 5 cities in the following JSON format: '
    '[{"distance": "...", "city": "...", "state": "...", "latitude": "...", "longitude": "...", "range": "..."}, ...]'
),
    agent=results_supervisor
)

# Crew
opportunity_crew = Crew(
    agents=[dealership_info_agent, opportunities_researcher, data_organizer, results_supervisor],
    tasks=[dealership_info_task, opportunities_research_task, data_organization_task, supervision_task],
    process=Process.sequential,
    verbose=True
)

# Función para ejecutar desde main.py
def run_opportunity_crew(**kwargs):
    raw_output = opportunity_crew.kickoff(inputs=kwargs)

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

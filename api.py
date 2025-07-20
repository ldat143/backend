from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from crews.competitor_crew import run_competitor_crew
from crews.opportunity_crew import run_opportunity_crew
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

import tempfile
import json

load_dotenv()
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class CrewInput(BaseModel):
    zipcode: str
    dealership: str
    customer: str
    person: str

@app.post("/run-competitor")
async def competitor(data: CrewInput):
    result = run_competitor_crew(**data.dict())
    # Guardar como archivo JSON temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode='w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
        file_path = f.name

    return FileResponse(file_path, media_type="application/json", filename="competitors.json")

@app.post("/run-opportunity")
async def opportunity(data: CrewInput):
    result = run_opportunity_crew(**data.dict())

    # Guardar como archivo JSON temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode='w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
        file_path = f.name

    return FileResponse(file_path, media_type="application/json", filename="opportunities.json")

# 🤖 AI Agent API for Car Dealership Analysis

This project implements a **FastAPI-based REST API** that uses AI agents (CrewAI + Gemini) to analyze car dealerships in the U.S. The API provides two main features:

1. **Identify local competitors based on the dealership OEM and proximity**
2. **Discover locations(Cities or metro areas) considered as opportunities to target in the SEO strategy**  

## 🧠 Main Features

### `/run-competitor` – Competitor Analysis
- Takes a dealership name and ZIP code.
- Uses `Serper.dev` and Google Maps to find nearby businesses.
- Calculates the distance between the main dealership and nearby ones.
- Uses a custom `CompetitorVerifierTool` to detect real competitors.
- Returns a JSON list of valid competitors, including:
  - `name`, `website`, `city`, `state`, `distance`, `latitude`, `longitude`.

### `/run-opportunity` – Market Opportunities
- Takes dealership name, customer and ZIP code.
- The agent uses real-time web search (Serper) + Gemini LLM to analyze context.
- Suggests locations that are near the dealership. which could be opportunities to target with SEO.
- Outputs a structured JSON response with the locations.

## ⚙️ Technologies Used

- **FastAPI** – High-performance Python API framework.
- **CrewAI** – Multi-agent LLM orchestration framework.
- **Gemini** – Google’s large language model.
- **Serper.dev** – Google Search JSON API.
- **Google Maps API** – For geocoding and distance calculations.
- **Geonames** –  Geographical database covers all countries and contains over eleven million placenames 
- **Custom Tools**:
  - `DistanceCalculatorTool`: Computes miles between locations.
  - `CompetitorVerifierTool`: Determines if a business is a real competitor.
- **AgentOps** : Agent performance monitoring.

## 🔐 Environment Variables (.env)

```env
GEMINI_API_KEY=your_gemini_key
SERPER_API_KEY=your_serper_key
GOOGLE_MAP_API_KEY=your_google_maps_key
AGENTOPS_API_KEY=optional_key

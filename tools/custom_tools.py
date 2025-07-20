import time
import os
import requests
from typing import Tuple, Optional, Dict
from bs4 import BeautifulSoup
from datetime import datetime
import re

from geopy.geocoders import GoogleV3
from geopy.distance import geodesic
from crewai.tools import BaseTool

# --- Tool 1: Distance Calculator Tool ---

class DistanceCalculatorTool(BaseTool):
    name: str = "Distance Calculator"
    description: str = "Calculates the distance in miles between two addresses using geocoding."

    def _run(self, address1: str, address2: str) -> str:
        try:
            geolocator = GoogleV3(api_key=os.environ["GOOGLE_MAP_API_KEY"], timeout=10)
            location1 = geolocator.geocode(address1)
            location2 = geolocator.geocode(address2)
            if not location1 or not location2:
                return "Error: Unable to geocode one or both addresses."
            coords1: Tuple[float, float] = (location1.latitude, location1.longitude)
            coords2: Tuple[float, float] = (location2.latitude, location2.longitude)
            distance = geodesic(coords1, coords2).miles
            return f"{round(distance, 2)} miles"
        except Exception as e:
            return f"Error calculating distance: {str(e)}"

    def _arun(self, address1: str, address2: str) -> str:
        return self._run(address1, address2)

# --- Tool 2: Competitor Verifier Tool ---

class CompetitorVerifierTool(BaseTool):
    name: str = "Competitor Verifier"
    description: str = "Verifies competitor dealerships' website functionality and OEM match."

    def _run(self, competitor_name: str, competitor_website: str, target_oem: str,
             competitor_address: str, search_results: str = None) -> str:
        try:
            time.sleep(1)
            website_status = self._check_website(competitor_website)
            if website_status != "Operational":
                return f"Invalid: Website {competitor_website} is {website_status.lower()}."

            oem_verified = self._verify_oem(competitor_website, target_oem)
            if not oem_verified:
                return f"Invalid: {competitor_name} does not sell {target_oem}."

            if not search_results:
                return f"Invalid: No search results provided for {competitor_name}."

            valid, detail = self._verify_current_existence(
                competitor_name, competitor_address, target_oem, competitor_website, search_results
            )
            if not valid:
                return f"Invalid: {competitor_name} may not currently exist. {detail}"

            return "Valid: Competitor currently exists, sells target OEM, and website is operational."
        except Exception as e:
            return f"Error verifying competitor: {str(e)}"

    def _arun(self, *args, **kwargs):
        return self._run(*args, **kwargs)

    def _check_website(self, url: str) -> str:
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            return "Operational" if response.status_code == 200 else f"Non-operational (Status: {response.status_code})"
        except requests.RequestException as e:
            return f"Unreachable: {str(e)}"

    def _verify_oem(self, url: str, target_oem: str) -> bool:
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            return target_oem.lower() in soup.get_text().lower()
        except requests.RequestException:
            return False

    def _verify_current_existence(self, name: str, address: str, oem: str, website: str, search_results: str) -> tuple:
        try:
            results_lower = search_results.lower()
            if any(k in results_lower for k in ["closed", "shut down", "permanently closed", "out of business"]):
                return False, "Found indications that the dealership may be closed."

            if str(datetime.now().year) not in results_lower and oem.lower() not in results_lower:
                return False, "No recent mentions found in search results."

            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(website, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.get_text().lower()
            copyright_matches = re.findall(r"copyright.*?(\d{4})", page_text)
            if copyright_matches:
                latest = max(int(y) for y in copyright_matches)
                if latest < datetime.now().year - 1:
                    return False, f"Website appears outdated (latest copyright {latest})."
            return True, "Active and recent"
        except Exception as e:
            return False, f"Error during existence check: {str(e)}"

# --- Tool 3: Population Data Tool ---

class PopulationDataTool(BaseTool):
    name: str = "Population Data"
    description: str = "Fetch population data for U.S. cities/towns using the GeoNames API."

    def clean_place_name(self, place_name: str) -> str:
        return re.sub(r'\s+(city|town|village|borough|CDP|municipality)$', '', place_name, flags=re.IGNORECASE).strip()

    def get_population(self, place_name: str, state: str) -> Optional[Dict[str, any]]:
        try:
            valid_states = {
                "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY",
                "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND",
                "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
            }
            if state.upper() not in valid_states:
                return None

            clean_name = self.clean_place_name(place_name)
            params = {
                "q": f"{clean_name}, {state}",
                "country": "US",
                "featureClass": "P",
                "maxRows": 15,
                "username": "luchxdd"
            }

            response = requests.get("http://api.geonames.org/searchJSON", params=params)
            response.raise_for_status()
            data = response.json()

            for result in data.get("geonames", []):
                api_name = self.clean_place_name(result["name"]).lower()
                if api_name == clean_name.lower() and result.get("adminCode1") == state.upper():
                    population = result.get("population", 0)
                    if population > 0:
                        return {
                            "place_name": result["name"],
                            "state": state,
                            "population": int(population),
                            "year": "recent"
                        }
            return None
        except Exception:
            return None

    def _run(self, arguments: str) -> str:
        try:
            parts = [p.strip() for p in arguments.split(',')]
            if len(parts) != 2:
                return "Error: Input must be in 'city, state' format (e.g., 'Dallas, TX')"
            place_name, state = parts
            result = self.get_population(place_name, state)
            if result:
                return f"Population of {result['place_name']}, {result['state']}: {result['population']:,} (recent)"
            return f"No population data found for {place_name}, {state}"
        except Exception as e:
            return f"Error fetching population data: {str(e)}"

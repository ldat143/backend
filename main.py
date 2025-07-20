from crews.competitor_crew import run_competitor_crew
from crews.opportunity_crew import run_opportunity_crew


if __name__ == "__main__":
    inputs = {
        "zipcode": "83440",
        "dealership": "Liberty GMC",
        "customer": "Cox Automotive",
        "person": "Luis"
    }

    result1 = run_competitor_crew(**inputs)
    print("\n✅ Resultado Competitor Crew:")
    print(result1)

    result2 = run_opportunity_crew(**inputs)
    print("\n✅ Resultado Opportunity Crew:")
    print(result2)

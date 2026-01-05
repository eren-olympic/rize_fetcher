import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

RIZE_API_KEY = os.getenv("RIZE_API_KEY")
API_URL = "https://api.rize.io/api/v1/graphql"

def explore_schema():
    if not RIZE_API_KEY:
        print("Error: RIZE_API_KEY not found in .env")
        return

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {RIZE_API_KEY}"
    }

    # Inspect projectTimeEntries
    pte_query = """
    query PTEIntrospection {
        __type(name: "Query") {
            fields {
                name
                args {
                    name
                    type {
                        name
                        kind
                    }
                }
            }
        }
        pteType: __type(name: "ProjectTimeEntry") {
            fields {
                name
                type {
                    name
                    kind
                }
            }
        }
    }
    """
    print("\nfetching details for 'projectTimeEntries'...")
    resp = requests.post(API_URL, headers=headers, json={"query": pte_query})
    data = resp.json()
    
    if "data" in data and data["data"]["__type"]:
        # Find projectTimeEntries arg
        fields = data["data"]["__type"]["fields"]
        pte_field = next((f for f in fields if f["name"] == "projectTimeEntries"), None)
        if pte_field:
            print("projectTimeEntries args:")
            for arg in pte_field["args"]:
                print(f"- {arg['name']}")
        else:
            print("Field 'projectTimeEntries' not found in Query type.")
    
    if "data" in data and data["data"]["pteType"]:
        print("\nProjectTimeEntry fields:")
        for f in data["data"]["pteType"]["fields"]:
            print(f"- {f['name']}")

if __name__ == "__main__":
    explore_schema()

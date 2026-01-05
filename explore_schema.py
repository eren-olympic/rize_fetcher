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

    # Introspection query to get all types and query root fields
    query = """
    query IntrospectionQuery {
      __schema {
        types {
          name
          kind
          description
          fields {
            name
            description
          }
        }
        queryType {
          fields {
            name
            description
            args {
              name
              type {
                name
                kind
              }
            }
          }
        }
      }
    }
    """

    response = requests.post(API_URL, headers=headers, json={"query": query})
    
    if response.status_code != 200:
        print(f"Error: API returned status {response.status_code}")
        print(response.text)
        return

    data = response.json()
    
    if "errors" in data:
        print("GraphQL Errors:")
        print(json.dumps(data["errors"], indent=2))
        return

    schema = data["data"]["__schema"]
    query_fields = schema["queryType"]["fields"]
    
    print(f"Found {len(query_fields)} root query fields.")
    
    # Inspect 'summaries' query args details
    print("\nInspecting 'summaries' query args:")
    summaries_field = next((f for f in query_fields if f["name"] == "summaries"), None)
    if summaries_field:
        for arg in summaries_field['args']:
            type_name = arg['type']['name']
            kind = arg['type']['kind']
            # If kind is NON_NULL, get inner type
            if kind == 'NON_NULL' and 'ofType' in arg['type'] and arg['type']['ofType']:
                 type_name = arg['type']['ofType']['name']
                 kind = f"NON_NULL({arg['type']['ofType']['kind']})"
                 
            print(f"- Arg: {arg['name']}, Type: {type_name}, Kind: {kind}")

if __name__ == "__main__":
    explore_schema()

import os
import requests
from dotenv import load_dotenv

load_dotenv()

RIZE_API_KEY = os.getenv("RIZE_API_KEY")
API_URL = "https://api.rize.io/api/v1/graphql"

def test_bucket_size(bucket_val):
    print(f"Testing bucketSize: {bucket_val}")
    
    query = """
    query GetSummaries($start: ISO8601Date!, $end: ISO8601Date!, $bucket: String!) {
      summaries(startDate: $start, endDate: $end, bucketSize: $bucket) {
        workHours
      }
    }
    """
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {RIZE_API_KEY}"
    }
    
    # Use a safe date range
    variables = {
        "start": "2024-01-01",
        "end": "2024-01-01",
        "bucket": bucket_val
    }
    
    response = requests.post(API_URL, headers=headers, json={"query": query, "variables": variables})
    
    data = response.json()
    if "errors" in data:
        print(f"FAILED: {data['errors'][0]['message']}")
    else:
        print("SUCCESS!")
        print(data)

if __name__ == "__main__":
    candidates = ["DAYS", "days", "DAY", "day", "DAILY", "daily", "WEEK", "MONTH", "YEAR"]
    for c in candidates:
        test_bucket_size(c)
        print("---")

import os
import datetime
import requests
import frontmatter
from dotenv import load_dotenv

load_dotenv()

# Configuration
RIZE_API_KEY = os.getenv("RIZE_API_KEY")
OBSIDIAN_VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH")
API_URL = "https://api.rize.io/api/v1/graphql"

if not RIZE_API_KEY:
    raise ValueError("RIZE_API_KEY not found in .env")

if not OBSIDIAN_VAULT_PATH:
    raise ValueError("OBSIDIAN_VAULT_PATH not found in .env")

DAILY_LOGS_DIR = os.path.join(OBSIDIAN_VAULT_PATH, "00_COCKPIT", "Daily_Logs")

def fetch_daily_data(date_obj):
    """
    Fetches Rize metrics for a specific date.
    """
    date_str = date_obj.isoformat()
    # To get a single day, start date and end date are usually the same, or next day exclusive.
    # Rize usually treats single date ranges inclusive if start=end.
    
    query = """
    query GetDailyMetrics($start: ISO8601Date!, $end: ISO8601Date!) {
      summaries(startDate: $start, endDate: $end, bucketSize: "day") {
        workHours
        focusTime
        breakTime
        meetingTime
        trackedTime
      }
    }
    """
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {RIZE_API_KEY}"
    }
    
    variables = {
        "start": date_str,
        "end": date_str
    }
    
    response = requests.post(API_URL, headers=headers, json={"query": query, "variables": variables})
    
    if response.status_code != 200:
        print(f"Error fetching data: {response.text}")
        return None
        
    data = response.json()
    if "errors" in data:
        print(f"GraphQL Errors: {data['errors']}")
        return None
        
    summaries = data.get("data", {}).get("summaries", [])
    if not summaries:
        print("No data found for this date.")
        return None
        
    return summaries

def update_daily_note(date_obj, metrics):
    date_str = date_obj.isoformat()
    filename = f"{date_str}.md"
    filepath = os.path.join(DAILY_LOGS_DIR, filename)
    
    if not os.path.exists(filepath):
        print(f"Daily note for {date_str} does not exist. Creating it.")
        with open(filepath, "w") as f:
            f.write(f"# Daily Log: {date_str}\n\n")
            
    try:
        with open(filepath, "r") as f:
            post = frontmatter.load(f)
            
        # Update metadata
        # Rize returns times in minutes usually (checking schema description would verify, but standard is minutes or seconds)
        # Let's assume minutes for time fields based on typical API patterns, or hours.
        # Wait, usually API returns HH:MM:SS or minutes.
        # Let's write raw values first.
        
        post.metadata["rize_work_hours"] = metrics.get("workHours")
        post.metadata["rize_focus_time"] = metrics.get("focusTime")
        post.metadata["rize_meeting_time"] = metrics.get("meetingTime")
        post.metadata["rize_break_time"] = metrics.get("breakTime")
        post.metadata["rize_tracked_time"] = metrics.get("trackedTime")
        post.metadata["rize_last_sync"] = datetime.datetime.now().isoformat()
        
        with open(filepath, "w") as f:
            f.write(frontmatter.dumps(post))
            
        print(f"Successfully updated {filename}")
        
    except Exception as e:
        print(f"Error updating file: {e}")

if __name__ == "__main__":
    # improved default: fetch for today
    today = datetime.date.today()
    print(f"Fetching Rize data for {today.isoformat()}...")
    
    metrics = fetch_daily_data(today)
    if metrics:
        print(f"Metrics received: {metrics}")
        update_daily_note(today, metrics)

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
        categories {
            type: category {
                name
            }
            trackedTime: timeSpent
        }
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
        # Graceful fallback: try without projects/categories if schema fails (backward compatibility)
        print(f"GraphQL Errors: {data['errors']}")
        return None
        
    summaries = data.get("data", {}).get("summaries", [])
    if not summaries:
        print("No data found for this date.")
        return None
        
    return summaries

def fetch_project_data(date_obj):
    """
    Fetches project time entries and aggregates them by project.
    """
    date_str = date_obj.isoformat()
    # Rize expects ISO8601 strings
    start_time = f"{date_str}T00:00:00Z"
    end_time = f"{date_str}T23:59:59Z"
    
    query = """
    query GetProjectEntries($start: ISO8601DateTime!, $end: ISO8601DateTime!) {
      projectTimeEntries(startTime: $start, endTime: $end) {
        duration
        project {
          name
        }
      }
    }
    """
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {RIZE_API_KEY}"
    }
    
    variables = {
        "start": start_time,
        "end": end_time
    }
    
    response = requests.post(API_URL, headers=headers, json={"query": query, "variables": variables})
    
    if response.status_code != 200:
        print(f"Error fetching project data: {response.text}")
        return []
        
    data = response.json()
    if "errors" in data:
        print(f"GraphQL Errors (Projects): {data['errors']}")
        return []
        
    entries = data.get("data", {}).get("projectTimeEntries", [])
    
    # Aggregate by project
    project_map = {}
    for entry in entries:
        p = entry.get("project")
        if not p:
            continue
        name = p.get("name", "Unknown")
        duration = entry.get("duration", 0)
        project_map[name] = project_map.get(name, 0) + duration
        
    # Convert to list
    projects = [{"name": name, "trackedTime": duration} for name, duration in project_map.items()]
    return projects

def format_time(seconds):
    """Converts seconds to HH:MM"""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h}h {m}m"

def update_daily_note(date_obj, metrics, projects):
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
        post.metadata["rize_work_hours"] = metrics.get("workHours")
        post.metadata["rize_focus_time"] = metrics.get("focusTime")
        post.metadata["rize_meeting_time"] = metrics.get("meetingTime")
        post.metadata["rize_break_time"] = metrics.get("breakTime")
        post.metadata["rize_tracked_time"] = metrics.get("trackedTime")
        post.metadata["rize_last_sync"] = datetime.datetime.now().isoformat()
        
        # Format Body Content with Tables
        categories = metrics.get("categories", [])
        
        # Sort by time spent desc
        categories.sort(key=lambda x: x['trackedTime'], reverse=True)
        projects.sort(key=lambda x: x['trackedTime'], reverse=True)
        
        report_lines = []
        report_lines.append(f"\n## 📊 Rize Metrics ({datetime.datetime.now().strftime('%H:%M')})\n")
        
        # Category Table
        if categories:
            report_lines.append("### Top Categories")
            report_lines.append("| Category | Time |")
            report_lines.append("| :--- | :--- |")
            for c in categories[:10]: # Top 10
                name = c.get('type', {}).get('name', 'Unknown')
                time_str = format_time(c['trackedTime'])
                report_lines.append(f"| {name} | {time_str} |")
            report_lines.append("\n")
            
        # Project Table
        if projects:
            report_lines.append("### Top Projects")
            report_lines.append("| Project | Time |")
            report_lines.append("| :--- | :--- |")
            for p in projects[:10]: # Top 10
                name = p.get('name', 'Unknown')
                time_str = format_time(p['trackedTime'])
                report_lines.append(f"| {name} | {time_str} |")
            report_lines.append("\n")

        # Append to body
        post.content = post.content + "\n" + "\n".join(report_lines)
        
        with open(filepath, "w") as f:
            f.write(frontmatter.dumps(post))
            
        print(f"Successfully updated {filename} with detailed metrics.")
        
    except Exception as e:
        print(f"Error updating file: {e}")

if __name__ == "__main__":
    # improved default: fetch for today
    today = datetime.date.today()
    print(f"Fetching Rize data for {today.isoformat()}...")
    
    metrics = fetch_daily_data(today)
    projects = fetch_project_data(today)
    
    if metrics:
        print(f"Metrics received: {metrics.keys()}")
        update_daily_note(today, metrics, projects)

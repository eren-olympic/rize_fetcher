import os
import requests
import datetime
import frontmatter
import argparse
import yaml
from dotenv import load_dotenv

load_dotenv()

# We still load API KEY from env, but paths can now come from config
RIZE_API_KEY = os.getenv("RIZE_API_KEY")
API_URL = "https://api.rize.io/api/v1/graphql"

if not RIZE_API_KEY:
    raise ValueError("RIZE_API_KEY not found in .env")

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

def load_config(config_path="config.yaml"):
    """Loads configuration from yaml file."""
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r") as f:
        return yaml.safe_load(f) or {}

def update_daily_note(date_obj, metrics, projects, config):
    date_str = date_obj.isoformat()
    
    # Determine vault path
    vault_path = config.get("vault_path")
    if not vault_path:
        vault_path = os.getenv("OBSIDIAN_VAULT_PATH")
    
    if not vault_path:
        print("Error: Vault path not set in config.yaml or OBSIDIAN_VAULT_PATH env var.")
        return

    # Determine daily logs path
    daily_logs_rel = config.get("daily_logs_path", "00_COCKPIT/Daily_Logs")
    daily_logs_dir = os.path.join(vault_path, daily_logs_rel)

    if not os.path.exists(daily_logs_dir):
        try:
            os.makedirs(daily_logs_dir)
        except OSError:
            print(f"Error: Could not create directory {daily_logs_dir}")
            return
            
    filename = f"{date_str}.md"
    filepath = os.path.join(daily_logs_dir, filename)
    
    # Check if file exists, if not create
    if not os.path.exists(filepath):
        print(f"Daily note for {date_str} does not exist. Creating it.")
        with open(filepath, "w") as f:
            f.write(f"# Daily Log: {date_str}\n\n")
            
    try:
        with open(filepath, "r") as f:
            post = frontmatter.load(f)
            
        # Update metadata - Convert seconds to hours
        def to_hours(seconds):
             if not seconds: return 0.0
             return round(seconds / 3600, 2)

        post.metadata["rize_work_hours"] = to_hours(metrics.get("workHours"))
        post.metadata["rize_focus_time"] = to_hours(metrics.get("focusTime"))
        post.metadata["rize_meeting_time"] = to_hours(metrics.get("meetingTime"))
        post.metadata["rize_break_time"] = to_hours(metrics.get("breakTime"))
        post.metadata["rize_tracked_time"] = to_hours(metrics.get("trackedTime"))
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
    parser = argparse.ArgumentParser(description="Fetch Rize metrics and update Obsidian.")
    parser.add_argument("--date", help="Fetch for specific date (YYYY-MM-DD)")
    parser.add_argument("--days", type=int, help="Fetch data for the last N days")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    
    args = parser.parse_args()
    
    # Load config
    config = load_config(args.config)
    
    dates_to_fetch = []
    
    if args.date:
        try:
            target_date = datetime.date.fromisoformat(args.date)
            dates_to_fetch.append(target_date)
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")
            exit(1)
    elif args.days:
        today = datetime.date.today()
        for i in range(args.days):
             d = today - datetime.timedelta(days=i)
             dates_to_fetch.append(d)
    else:
        # Default behavior: Today (or from config default)
        lookback = config.get("default_days_lookback", 0)
        today = datetime.date.today()
        target_date = today - datetime.timedelta(days=lookback)
        dates_to_fetch.append(target_date)

    for d in dates_to_fetch:
        print(f"Fetching Rize data for {d.isoformat()}...")
        metrics = fetch_daily_data(d)
        projects = fetch_project_data(d)
        
        if metrics:
            update_daily_note(d, metrics, projects, config)
        else:
            print(f"No metrics found for {d.isoformat()}")

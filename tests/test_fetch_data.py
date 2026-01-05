import sys
import os
import pytest
import responses
import datetime
import yaml
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetch_data import fetch_daily_data, fetch_project_data, load_config
# Note: Implied import of API_URL and RIZE_API_KEY handling from logic
# Since fetch_data is a script, we might need to refactor it to a package later, 
# but for now we import directly.

API_URL = "https://api.rize.io/api/v1/graphql"

@pytest.fixture
def mock_config(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_data = {
        "vault_path": str(tmp_path / "vault"),
        "daily_logs_path": "Daily_Logs",
        "default_days_lookback": 0
    }
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)
    return str(config_file)

def test_load_config(mock_config):
    config = load_config(mock_config)
    assert config["daily_logs_path"] == "Daily_Logs"
    assert config["default_days_lookback"] == 0

@responses.activate
def test_fetch_daily_data_success():
    # Mock Response
    mock_response = {
        "data": {
            "summaries": {
                "workHours": 18000, # 5 hours
                "focusTime": 3600,
                "breakTime": 600,
                "meetingTime": 0,
                "trackedTime": 18000,
                "categories": [
                    {"type": {"name": "Coding"}, "timeSpent": 7200},
                    {"type": {"name": "Meeting"}, "timeSpent": 3600}
                ]
            }
        }
    }
    
    responses.add(responses.POST, API_URL, json=mock_response, status=200)
    
    date = datetime.date(2024, 1, 1)
    result = fetch_daily_data(date)
    
    assert result is not None
    assert result["workHours"] == 18000
    assert len(result["categories"]) == 2

@responses.activate
def test_fetch_project_data_success():
    mock_response = {
        "data": {
            "projectTimeEntries": [
                {"duration": 3600, "project": {"name": "Project A"}},
                {"duration": 1800, "project": {"name": "Project B"}}
            ]
        }
    }
    responses.add(responses.POST, API_URL, json=mock_response, status=200)
    
    date = datetime.date(2024, 1, 1)
    projects = fetch_project_data(date)
    
    assert len(projects) == 2
    # Check aggregation if duplicates present? 
    # Current mock has distinct projects.
    assert projects[0]["name"] in ["Project A", "Project B"]

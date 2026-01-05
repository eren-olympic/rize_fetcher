# 🚀 Rize Data Fetcher

A Python tool to sync your daily productivity metrics from [Rize.io](https://rize.io) directly into your [Obsidian](https://obsidian.md) Daily Logs.

## ✨ Features
- **Daily Sync**: Fetches Work Hours, Focus Time, Break Time, and more.
- **Obsidian Integration**: Automatically finds or creates your Daily Log (`YYYY-MM-DD.md`) and updates it with frontmatter data.
- **Smart Idempotency**: Can be run multiple times a day without duplicating data; simply updates the values.

## 🛠️ Prerequisites
- Python 3.12+
- [Poetry](https://python-poetry.org/)
- A Rize account with API access.

## 📦 Installation

1. **Navigate to the folder**:
   ```bash
   cd /path/to/rize_fetcher
   ```
2. **Install dependencies**:
   ```bash
   poetry install
   ```

## ⚙️ Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` and fill in your details:
   - `RIZE_API_KEY`: Get this from Rize Settings > API.
   - `OBSIDIAN_VAULT_PATH`: Environment variable fallback (optional if using `config.yaml`).

3. **(Optional) Config File**:
   Edit `config.yaml` to customize paths and defaults:
   ```yaml
   vault_path: "/path/to/custom/vault"
   daily_logs_path: "00_COCKPIT/Daily_Logs"
   default_days_lookback: 0
   ```

## 🏃 Usage

### Basic usage (Today)
```bash
poetry run python fetch_data.py
```

### Fetch specific date
```bash
poetry run python fetch_data.py --date 2024-01-01
```

### Fetch last N days
```bash
poetry run python fetch_data.py --days 3
```

### Custom Config
```bash
poetry run python fetch_data.py --config my_config.yaml
```

### Automation (Cron)
To run this automatically every night at 9 PM:

```bash
0 21 * * * cd /path/to/rize_fetcher && /path/to/poetry run python fetch_data.py >> /tmp/rize.log 2>&1
```
*(Make sure to use the absolute path to your `poetry` executable, which you can find with `which poetry`)*

## 🔍 Development 工具
- **Schema Explorer**: Run `poetry run python explore_schema.py` to inspect the Rize GraphQL schema.
- **Bucket Test**: Run `poetry run python brute_force_bucket.py` to verify valid API aggregation buckets.

## 📝 Frontmatter Fields
The tool injects the following fields into your Obsidian Daily Note:
```yaml
rize_work_hours: 4.25        # Total work hours
rize_focus_time: 2.5         # Focus time hours
rize_break_time: 0.5         # Break time hours
rize_meeting_time: 1.0       # Meeting time hours
rize_last_sync: '2026-01-05' # Timestamp
```

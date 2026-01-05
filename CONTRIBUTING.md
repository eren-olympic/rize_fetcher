# Contributing to Rize Fetcher

We welcome contributions! usage of this tool depends on the Rize API.

## Setup

1.  **Clone the repo**:
    ```bash
    git clone https://github.com/eren-olympic/rize_fetcher.git
    cd rize_fetcher
    ```

2.  **Install Dependencies**:
    We use [Poetry](https://python-poetry.org/) for dependency management.
    ```bash
    poetry install
    ```

3.  **Run Tests**:
    ```bash
    poetry run pytest
    ```

## Code Style

We use `black` and `ruff` for formatting. Please run linter before submitting PRs:
```bash
poetry run ruff check .
```

## Pull Requests

1.  Fork the repo.
2.  Create a feature branch.
3.  Add tests for your feature.
4.  Submit a PR!

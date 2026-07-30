# bonds_high_value_win_notifier

A small utility to download the NS&I Premium Bonds monthly winners sheet, filter it for potential matches based on your Premium Bonds holdings, and notify you when there are possible winning bonds.

Version: 0.1.0

**Quick summary**
- Downloads the monthly Premium Bonds winners Excel file from NS&I
- Normalises and scans the sheet for area, purchase date and bond value matches
- Emits results suitable for local use or GitHub Actions artifact creation

**Badges**
- Python: >=3.14 (see `pyproject.toml`)

## What the project does

This tool automates the process of checking the NS&I Premium Bonds monthly winners list for potential matches against your holdings. It:

- Downloads the current month winners Excel file
- Converts and normalises the sheet into CSV
- Finds the closest area matches and filters by purchase date and bond value
- Writes results and (when run in GitHub Actions) produces an artifact

The main entrypoint is `src/main.py`.

## Why this project is useful

- Saves time manually scanning large winners lists
- Makes it easy to integrate checks into CI/CD pipelines (GitHub Actions compatibility via `GITHUB_OUTPUT` handling)
- Lightweight and easy to run locally or in a scheduled runner

## Getting started

Prerequisites

- Python 3.14 or later

Using `uv` (recommended)

This project supports `uv` for dependency management. Example workflow:

```bash
# create or activate your uv environment (if you use uv's environment features)
uv init    # optional: initialise uv in the repo if not already

# add runtime dependencies from pyproject
uv sync

# add a development dependency
uv add --dev pytest

# install everything declared (runtime + dev as configured)
uv sync --dev
```

Environment variables

Set the following environment variables before running (these are required):

- `PB_AREA` — area string to match (e.g. `london`)
- `PB_DATE_OF_PURCHASE` — purchase date in `YYYY-MM-DD` format
- `PB_VAL_OF_BOND` — bond face value (e.g. `25000`)

Optional:

- `LOG_LEVEL` — logging level (default `DEBUG`)

Example (run locally):

```bash
export PB_AREA="london"
export PB_DATE_OF_PURCHASE="2024-02-26"
export PB_VAL_OF_BOND="25000"
export LOG_LEVEL=INFO
python -m src.main
```

Notes

- The script expects to fetch the winners Excel from NS&I. Ensure network access is available.
- When run on GitHub Actions, the script writes `RESULTS_PATH`, `MESSAGE` and `CREATE_ARTIFACT` to the `GITHUB_OUTPUT` file so workflows can pick up artifacts.

## Project layout

- `pyproject.toml` — project metadata and dependencies
- `src/main.py` — main application logic
- `logging/declarative-config.yaml` — logging configuration
- `tests/` — unit and resilience tests
- `tests/mock_data_frame.csv` — example CSV used by tests

## Testing

Run the test suite with `pytest` (project uses `pytest` for unit and resilience tests):

```bash
pytest -q
```

## Where to get help

- Open an issue on this repository with a clear description of the problem and steps to reproduce.
- For questions about running the project locally, open a discussion or issue.

## Who maintains and how to contribute

Maintainer: Daniel Grayburn <grayburndan@gmail.com>

Contributions are welcome via pull requests. Keep contributions focused and include tests for new behavior. If you plan larger changes, open an issue first to discuss the design.

Suggested contribution flow:

1. Fork the repository
2. Create a feature branch
3. Add tests and update documentation
4. Open a pull request

## Security and reporting

If you discover a security vulnerability, please open an issue and mark it as security-sensitive. Do not publish secrets in issues.

# Premium Bonds High Value Win Notifier
[![Python 3.14+](https://img.shields.io/badge/python-3.14%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)

This Python utility downloads the current month’s NS&I Premium Bonds high-value winners workbook and checks it for potential matches against a holding. It is designed to run locally or as a scheduled GitHub Actions workflow.

## Why use it

- Avoids manually searching the monthly winners workbook.
- Normalizes area names and uses fuzzy matching for the area input.
- Filters potential matches by area, purchase date, and bond value.
- Retries transient download failures with a timeout, exponential backoff, and jitter.
- Produces a JSON results file and ZIP artifact in GitHub Actions; the workflow can email the result.

The tool identifies potential matches only. Confirm any result with NS&I before treating it as a win.

## Requirements

- Python 3.14 or newer
- `uv` for the documented setup commands
- Network access to download the workbook from [NS&I](https://www.nsandi.com/prize-checker)

## Installation

Clone the repository and install the locked runtime and development dependencies:

```bash
git clone https://github.com/grayburnd/bonds_high_value_win_notifier.git
cd bonds_high_value_win_notifier
uv sync --frozen --all-groups
```

The committed `uv.lock` keeps dependency resolution reproducible. To install only the runtime dependencies, use `uv sync --frozen`.

## Configuration

The local entrypoint requires these environment variables. Values are treated as strings, so preserve the date and bond value formats used in the NS&I data.

| Variable | Required | Description | Example |
| --- | --- | --- | --- |
| `PB_AREA` | Yes | Area to match. Matching is case-insensitive, spaces are normalized to underscores, and the three closest data values are considered. | `london` |
| `PB_DATE_OF_PURCHASE` | Yes | Exact purchase date to match. Use the workbook format `YYYY-MM-DD`. | `2024-02-26` |
| `PB_VAL_OF_BOND` | Yes | Exact bond value to match. | `25000` |
| `LOG_LEVEL` | No | Console log level. Defaults to `DEBUG`. | `INFO` |

Run it locally with:

```bash
PB_AREA=london \
PB_DATE_OF_PURCHASE=2024-02-26 \
PB_VAL_OF_BOND=25000 \
LOG_LEVEL=INFO \
uv run python src/main.py
```

The program downloads the workbook for the current UTC month. It does not send email during a normal local run; the match count is logged and temporary processing files are removed when the run completes. The detailed JSON result is retained as a ZIP artifact only when `GITHUB_OUTPUT` is available in GitHub Actions.

## GitHub Actions

The workflow in `.github/workflows/job.yml` can be started manually or runs at 08:00 UTC on days 1 through 4 of each month. It runs the same script, uploads a `winnings-results` artifact when there are matches, and uses `dawidd6/action-send-mail` to send the outcome.

Configure these repository-level Actions variables:

| Variable | Description |
| --- | --- |
| `PB_AREA` | Area used for matching. |
| `PB_DATE_OF_PURCHASE` | Exact purchase date in `YYYY-MM-DD` format. |
| `PB_VAL_OF_BOND` | Exact bond value. |
| `LOG_LEVEL` | Optional log level; defaults to `DEBUG`. |
| `MAIL_ADDRESS` | SMTP server hostname. |
| `SERVER_PORT` | SMTP server port. |
| `MAIL_TO` | Recipient address. |
| `MAIL_FROM` | Sender address. |

Configure these repository secrets:

- `MAIL_USERNAME` — SMTP username.
- `MAIL_PASSWORD` — SMTP password.

The workflow writes `MESSAGE`, `RESULTS_PATH`, and `CREATE_ARTIFACT` through GitHub’s `GITHUB_OUTPUT` mechanism. Do not put SMTP credentials or other secrets in variables, source files, issues, or logs.

## Development

Run the tests:

```bash
uv run pytest
```

Before opening a pull request, run the same checks used by CI:

```bash
uv run black --check .
uv run ruff check .
uv run bandit -c pyproject.toml -r -ll .
uv run mypy .
uv run pytest
```

Pre-commit hooks are configured in `.pre-commit-config.yaml` and include formatting, linting, YAML/TOML checks, large-file checks, and secret scanning with Gitleaks. Dependabot checks the `uv` dependencies weekly.

## Engineering practices

- **Reproducible dependencies:** runtime and development requirements are declared in `pyproject.toml` and pinned through `uv.lock`.
- **Input and data validation:** required environment variables are checked before work starts; empty downloads and missing workbook columns fail explicitly.
- **Resilient network access:** requests use a ten-second timeout, client errors are not retried, and transient failures use bounded exponential backoff with jitter.
- **Temporary-file hygiene:** intermediate CSV and JSON files are created with secure temporary-file APIs and removed during cleanup.
- **Structured observability:** YAML-configured JSON logs include timestamps and levels, with `LOG_LEVEL` available for runtime control.
- **Automated quality gates:** CI runs Black, Ruff, Bandit, Gitleaks, mypy, and pytest on pull requests.

## Project layout

- `src/main.py` — download, normalization, matching, artifact, and cleanup logic.
- `tests/` — unit and retry/resilience tests with representative CSV and workbook data.
- `logging/declarative-config.yaml` — JSON console logging configuration.
- `.github/workflows/` — pull-request checks and the scheduled notification workflow.
- `pyproject.toml` and `uv.lock` — project metadata, tool configuration, and locked dependencies.

## Help and contributions

For usage questions or reproducible bugs, [open an issue](https://github.com/grayburnd/bonds_high_value_win_notifier/issues) with the command, relevant non-sensitive configuration details, and logs. For security concerns, avoid publishing credentials or other sensitive data in an issue.

Contributions are welcome through pull requests. Please keep changes focused, add or update tests for behavior changes, update this README when setup or configuration changes, and run the local CI checks before submitting. The project is maintained by [Daniel Grayburn](https://github.com/grayburnd).

## License

No license file is currently included in the repository. Contact the maintainer before redistributing or reusing the code.

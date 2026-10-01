# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.


## Commands

```bash
# Setup
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS/Linux
pip install -r requirements.txt

# Run the full pipeline (scrape -> analyze -> visualize -> report)
python main.py

# Tests (~90% coverage target)
pytest
pytest analytics/tests/test_analyzer.py          # single file
pytest analytics/tests/test_analyzer.py::test_name  # single test
pytest --cov                                      # with coverage (config in pyproject.toml)

# Lint (config in .flake8)
flake8
```

Requires a `.env` file (see `.env.example`) with `GEMINI_API_KEY` for the AI analysis step.


## Architecture

The pipeline runs as three sequential stages, orchestrated by `main.py`, each stage reading the previous stage's CSV output from disk (no in-memory handoff):

1. **Scraping** (`scraping/`) — a Scrapy project (`scraping/job_scraping/`) with a single spider, `DouUaSpider` (`spiders/douua.py`), that crawls `jobs.dou.ua`. The site paginates via an XHR endpoint rather than links, so the spider extracts a CSRF token from the initial page and replays it as a `FormRequest` to fetch subsequent pages, deduplicating on job URL and stopping at `MAX_ITEMS_TO_SCRAPE` (`config.py`). Output is written via Scrapy's `FEEDS` setting directly to `SCRAPING_OUTPUT_FILE` (CSV) — there are no `Item`/pipeline classes in active use (`items.py`/`pipelines.py` are the unmodified Scrapy scaffold and are excluded from lint/coverage).

2. **Analysis** (`analytics/analysis.py`) — reads all CSVs from the scraping output directory, then matches each job description against `TECHNOLOGIES_TO_ANALYZE` in `config.py`: a dict mapping a canonical technology name to a list of alias strings. Matching uses word-boundary regex (not substring) so a tech is counted at most once per job. Adding a new tracked technology means adding an entry to that dict — nothing else needs to change.

3. **Visualization & reporting** (`analytics/visualization.py`, `analytics/report_generator.py`, `analytics/ai_analyzer.py`) — `visualize_jobs()` renders the top-N tech counts (`TECHNOLOGIES_TO_DISPLAY`) as a matplotlib bar chart, then calls `generate_report()`, which renders `analytics/templates/index.html` via Jinja2 and opens it in a browser. Report generation calls `analyze_market_with_ai()`, which sends the tech-count data to the Gemini API for a natural-language market summary, falling back through a list of model names (`gemini-3.8-flash` → `gemini-3.7-flash` → `gemini-3.5-flash`) and returning `None` (never raising) if the API key is missing or every model call fails — the report must still render without an AI summary.

Central config (`config.py`) holds all file paths, scrape limits, and the technology dictionary — check there first before hardcoding a path or limit elsewhere. Logging is configured once in `logger.py` (rotating file handler at `logs/scraper.log` + stdout) and imported as the shared `logger` object everywhere; third-party loggers (scrapy, selenium, matplotlib, etc.) are tuned there too.

## Testing conventions

Tests live alongside each package (`scraping/tests/`, `analytics/tests/`). External calls are mocked rather than hit live: Gemini client calls via `@patch("analytics.ai_analyzer.genai.Client")`, file reads via `monkeypatch.setattr(pandas, "read_csv", ...)` or `@patch(".../pandas.read_csv")`, and env vars via `@patch.dict("os.environ", ...)`. `scraping/job_scraping/middlewares.py`, `settings.py`, `pipelines.py`, and `items.py` are excluded from both flake8 and coverage since they're unmodified Scrapy scaffolding.

## CI/CD

`.github/workflows/deploy.yml` runs flake8 + pytest on push/PR to `main` and `feat/gemini-ai-integration`, then deploys `analytics/data/` to GitHub Pages on `main`.


# Strict rules

- **ALWAYS run tests and linting after making changes.** Whenever you modify code, you must immediately run `pytest` and `flake8` to verify nothing is broken.
- Never present or finalize a task as complete if pytest or flake8 throw errors. Fix them first.
- **Do NOT modify any files outside the explicit scope** of the current task. Never touch files in other directories or system files without explicit user permission.
- **Do NOT run any shell commands** (other than the standard project test/lint commands) **without asking first**. Always present the proposed command and wait for confirmation before executing.

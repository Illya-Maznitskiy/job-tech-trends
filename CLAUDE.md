# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code)
when working with code in this repository.


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
pytest analytics/tests/test_analyzer.py             # single file
pytest analytics/tests/test_analyzer.py::test_name  # single test
pytest --cov  # with coverage (config in pyproject.toml)

# Lint (config in .flake8)
flake8

# Docker: build, run once, copy the report out, clean up
docker build -t job-tech-trends .
docker run --name job_tech_trends_cont --env-file .env job-tech-trends
docker cp job_tech_trends_cont:/app/analytics/data/. ./docker-output
docker rm job_tech_trends_cont
```

- Requires a `.env` file (see `.env.example`) with `GEMINI_API_KEY`
  for the AI analysis step.
- All file paths in `config.py` (and the Jinja2 template path
  in `report_generator.py`) are relative to the working directory.
  Run every command from the project root.


## Docker

- `Dockerfile`: `python:3.13-slim`, installs `requirements.txt`,
  copies the project to `/app`, runs `python main.py` once.
- `.dockerignore` keeps `.env`, `venv/`, `.git/`, caches, logs,
  and `scraping/data/` out of the image.
  - `scraping/data/` is skipped because analysis reads all CSVs there,
    so old local files would change the counts.
  - `analytics/data/` is kept: the report needs the memes and favicon.
- Secrets are never in the image. Pass them at run time
  with `--env-file .env`.
  Values in `.env` must have no quotes:
  `docker run --env-file` keeps quotes as part of the value.
- No volume: the report stays in the container.
  Copy it out with `docker cp`.
- `webbrowser.open()` does nothing in the container (no browser).
- CI does not use Docker yet.


## Architecture

The pipeline runs as three sequential stages, orchestrated by `main.py`.
Each stage reads the previous stage's CSV output from disk
(no in-memory handoff).

### 1. Scraping (`scraping/`)

- A Scrapy project (`scraping/job_scraping/`) with a single spider:
  `DouUaSpider` (`spiders/douua.py`), which crawls `jobs.dou.ua`.
- The site paginates via an XHR endpoint, not links:
  - the spider extracts a CSRF token from the initial page;
  - it replays the token as a `FormRequest` to fetch next pages;
  - it deduplicates on job URL;
  - it stops at `MAX_ITEMS_TO_SCRAPE` (`config.py`).
- Output is written via Scrapy's `FEEDS` setting
  directly to `SCRAPING_OUTPUT_FILE` (CSV).
- No `Item`/pipeline classes are in active use.
  `items.py`/`pipelines.py` are the unmodified Scrapy scaffold.
- `config.py` also lists `Scraper.DJINNI` with a scrape limit,
  but there is no Djinni spider yet.

### 2. Analysis (`analytics/analysis.py`)

- Reads all CSVs from the scraping output directory.
- Matches each job description against `TECHNOLOGIES_TO_ANALYZE`
  in `config.py`: a dict that maps a canonical technology name
  to a list of alias strings.
- Matching uses word-boundary regex (not substring),
  so a tech is counted at most once per job.
- To track a new technology, add an entry to that dict.
  Nothing else needs to change.

### 3. Visualization & reporting

Files: `analytics/visualization.py`, `analytics/report_generator.py`,
`analytics/ai_analyzer.py`.

- `visualize_jobs()` renders the top-N tech counts
  (`TECHNOLOGIES_TO_DISPLAY`) as a matplotlib bar chart.
- Then it calls `generate_report()`, which renders
  `analytics/templates/index.html` via Jinja2
  and opens it in a browser.
- Report generation calls `analyze_market_with_ai()`:
  - sends the tech-count data to the Gemini API
    for a natural-language market summary;
  - falls back through a list of model names:
    `gemini-3.8-flash` → `gemini-3.7-flash` → `gemini-3.6-flash`
    → `gemini-3.5-flash` → `gemini-3.5-flash-lite`;
  - returns `None` if the API key is missing or every model call fails.
    The report must still render without an AI summary.
- The returned HTML is inserted into the template with `| safe`.
- The report also embeds a random meme from `MEMES_FILE`
  (`analytics/data/memes/memes.json`).
  `get_memes()` loads it and returns `[]` on error.
- The rendered page is written to `HTML_PAGE_OUTPUT_FILE`
  (`analytics/data/index.html`).
  This is the page deployed to GitHub Pages.

### Config and logging

- Central config (`config.py`) holds all file paths, scrape limits,
  and the technology dictionary.
  Check there first before you hardcode a path or limit elsewhere.
- Logging is configured once in `logger.py`:
  - rotating file handler at `logs/scraper.log` + stdout;
  - imported as the shared `logger` object everywhere;
  - third-party loggers (scrapy, selenium, matplotlib, etc.)
    are tuned there too.


## Testing conventions

- Tests live alongside each package
  (`scraping/tests/`, `analytics/tests/`).
- External calls are mocked, not hit live:
  - Gemini client calls: `@patch("analytics.ai_analyzer.genai.Client")`
  - file reads: `monkeypatch.setattr(pandas, "read_csv", ...)`
    or `@patch(".../pandas.read_csv")`
  - env vars: `@patch.dict("os.environ", ...)`
- Scrapy scaffolding (in `scraping/job_scraping/`) is excluded from checks:
  - `middlewares.py`, `settings.py`, `pipelines.py`:
    from both flake8 (`.flake8`) and coverage (`pyproject.toml`);
  - `items.py`: from coverage only.


## CI/CD

`.github/workflows/deploy.yml`:

- runs flake8 + pytest on push to any branch and on PRs to `main`;
- deploys `analytics/data/` to GitHub Pages on push to `main`.
- CI does not run the pipeline.
  Pages publishes the report files that are committed in `analytics/data/`.


# Strict rules

- **ALWAYS run tests and linting after making changes.**
  Whenever you modify code, you must immediately run
  `pytest` and `flake8` to verify nothing is broken.
- Never present or finalize a task as complete
  if pytest or flake8 throw errors. Fix them first.
- **Do NOT modify any files outside the explicit scope**
  of the current task.
  Never touch files in other directories or system files
  without explicit user permission.
- **Do NOT run any shell commands**
  (other than the standard project test/lint commands)
  **without asking first**.
  Always present the proposed command
  and wait for confirmation before executing.
- **Keep lines in Markdown files at 79 characters or less**
  (same as the flake8 default for Python).
  Split long text into short lines or bullet lists.

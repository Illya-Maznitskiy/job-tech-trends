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

# Run the full pipeline (scrape -> analyze -> report)
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
- CI runs pytest in the image, and CD runs the pipeline in it
  and deploys the new report (see CI/CD).


## Architecture

The pipeline runs as three sequential stages, orchestrated by `main.py`.
Each stage reads the previous stage's CSV output from disk
(no in-memory handoff).

### Positions

- `POSITIONS` in `config.py` maps a position key to a DOU category:
  `python`, `frontend`, `devops`, `data_science`.
- Every stage loops over `POSITIONS`.
  Data is kept apart in one folder per position:
  - `scraping/data/<position>/jobs.csv`
  - `analytics/data/<position>/tech_counts.csv`
- One broken position is skipped and logged.
  It must not stop the others.
- To add a position, add an entry to `POSITIONS`.

### 1. Scraping (`scraping/`)

- A Scrapy project (`scraping/job_scraping/`) with a single spider:
  `DouUaSpider` (`spiders/douua.py`), which crawls `jobs.dou.ua`.
  It takes a `category` argument (the DOU category name).
- `scraper.py` runs the spider once per position, one at a time,
  to keep the load on DOU low.
- The site paginates via an XHR endpoint, not links:
  - the spider extracts a CSRF token from the initial page;
  - it replays the token as a `FormRequest` to fetch next pages;
  - it deduplicates on job URL;
  - it stops at `MAX_ITEMS_TO_SCRAPE` (`config.py`).
- Output is written via Scrapy's `FEEDS` setting.
  `scraper.py` sets it per position, to
  `POSITION_SCRAPING_OUTPUT_FILE` (CSV).
- No `Item`/pipeline classes are in active use.
  `items.py`/`pipelines.py` are the unmodified Scrapy scaffold.
- `config.py` also lists `Scraper.DJINNI` with a scrape limit,
  but there is no Djinni spider yet.

### 2. Analysis (`analytics/analysis.py`)

- Runs once per position.
  Reads all CSVs from that position's scraping folder
  and saves the counts to `POSITION_ANALYSIS_OUTPUT_FILE`.
- Matches each job description against `TECHNOLOGIES_TO_ANALYZE`
  in `config.py`: a dict that maps a canonical technology name
  to a list of alias strings.
- Matching uses word-boundary regex (not substring),
  so a tech is counted at most once per job.
- To track a new technology, add an entry to that dict.
  Nothing else needs to change.

### 3. Reporting

Files: `analytics/report_generator.py`, `analytics/ai_analyzer.py`.

- `generate_report()` runs once, after all positions are analyzed.
  It renders `analytics/templates/index.html` via Jinja2
  and opens it in a browser.
- For each position it builds one panel:
  job count, top skills, a top-N chart
  (`TECHNOLOGIES_TO_DISPLAY`) and an AI summary.
  A position that fails is skipped, so it has no panel.
  It raises an error only if no position has data.
- The page has a tab per position. JS shows one panel
  (`id="panel-<position>"`) at a time and keeps the choice
  in the URL hash, like `#devops`.
- Each position makes one `analyze_market_with_ai()` call:
  - sends the tech-count data to the Gemini API
    for a natural-language market summary;
  - falls back through a list of model names:
    `gemini-3.6-flash` → `gemini-3.8-flash` → `gemini-3.7-flash`
    → `gemini-3.5-flash` → `gemini-3.5-flash-lite`;
    `3.6` is first because it failed least in past runs;
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
  - third-party loggers (scrapy, selenium, etc.)
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

One workflow: `.github/workflows/deploy.yml`. Three jobs:

1. `test`: flake8 + pytest.
2. `docker`: build the image, run pytest inside it.
3. `deploy`: run the pipeline in Docker, deploy the report to Pages.
   - Runs only on `main`, and only if `test` and `docker` pass.
   - Uses the `GEMINI_API_KEY` repository secret.
   - Guards stop the deploy, so the old site stays live:
     - a position has 10 jobs or fewer in its `jobs.csv`
       (`MIN_JOBS`), or no panel in `index.html`;
     - `index.html` is not from today.
     The positions come from `POSITIONS` in `config.py`.
     Guards are needed because `main.py` never exits with an error.

When it runs:

- push to any branch, PR to `main`: `test` + `docker`;
- push to `main`, every Monday 06:00 UTC, manual button: all three.


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

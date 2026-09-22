from pathlib import Path
from unittest.mock import patch

from analytics.report_generator import get_report_data, generate_report
from config import HTML_PAGE_OUTPUT_FILE


def test_get_report_data_structure(monkeypatch):
    monkeypatch.setattr(
        "analytics.report_generator.analyze_market_with_ai",
        lambda: "Mocked summary",
    )

    data = get_report_data()
    expected_keys = {
        "total_jobs",
        "run_date",
        "scraped_url",
        "top_skill",
        "top_skill_count",
        "ai_summary",
        "plot_filename",
    }
    assert expected_keys.issubset(data.keys())


def test_generate_report_output_exists(monkeypatch):
    monkeypatch.setattr(
        "analytics.report_generator.analyze_market_with_ai",
        lambda: "Mocked summary",
    )

    with patch("webbrowser.open"):
        generate_report()

    output_file = Path(HTML_PAGE_OUTPUT_FILE)
    assert output_file.exists()
    assert output_file.stat().st_size > 0

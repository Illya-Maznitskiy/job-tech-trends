from unittest.mock import patch

import pandas

from analytics.report_generator import get_report_data, generate_report


def test_get_report_data_structure(monkeypatch):
    monkeypatch.setattr(
        "analytics.report_generator.analyze_market_with_ai",
        lambda: "Mocked summary",
    )
    mock_df = pandas.DataFrame({"Technology": ["Python"], "Count": [10]})
    monkeypatch.setattr(pandas, "read_csv", lambda path: mock_df)

    data = get_report_data()
    expected_keys = {
        "total_jobs",
        "run_date",
        "scraped_url",
        "top_skills",
        "ai_summary",
        "plot_filename",
    }
    assert expected_keys.issubset(data.keys())


def test_generate_report_output_exists(monkeypatch, tmp_path):
    output_file = tmp_path / "index.html"
    monkeypatch.setattr(
        "analytics.report_generator.HTML_PAGE_OUTPUT_FILE", str(output_file)
    )
    monkeypatch.setattr(
        "analytics.report_generator.analyze_market_with_ai",
        lambda: "Mocked summary",
    )

    with patch("webbrowser.open"):
        generate_report()

    assert output_file.exists()
    assert output_file.stat().st_size > 0

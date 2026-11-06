from unittest.mock import patch

import pandas
import pytest

from analytics.report_generator import (
    get_memes,
    get_report_data,
    generate_report,
)


def set_up_report(monkeypatch, positions=None):
    positions = positions or {"python": "Python", "devops": "DevOps"}
    monkeypatch.setattr("analytics.report_generator.POSITIONS", positions)
    monkeypatch.setattr(
        "analytics.report_generator.analyze_market_with_ai",
        lambda position, category, counts: f"Summary {position}",
    )
    mock_df = pandas.DataFrame({"Technology": ["Python"], "Count": [10]})
    monkeypatch.setattr(pandas, "read_csv", lambda path: mock_df)


def test_get_report_data_has_every_position(monkeypatch):
    set_up_report(monkeypatch)

    data = get_report_data()

    assert {"run_date", "memes", "positions"}.issubset(data.keys())
    assert [p["name"] for p in data["positions"]] == ["python", "devops"]
    assert data["positions"][1]["ai_summary"] == "Summary devops"
    assert data["positions"][1]["total_jobs"] == 1
    assert "category=DevOps" in data["positions"][1]["scraped_url"]


def test_get_report_data_keeps_old_keys_for_first_position(monkeypatch):
    # The current template still reads these, until it gets the buttons
    set_up_report(monkeypatch)

    data = get_report_data()

    old_keys = {
        "total_jobs",
        "scraped_url",
        "top_skills",
        "chart_skills",
        "ai_summary",
    }
    assert old_keys.issubset(data.keys())
    assert data["ai_summary"] == "Summary python"


def test_get_report_data_skips_position_without_data(monkeypatch):
    set_up_report(monkeypatch)
    mock_df = pandas.DataFrame({"Technology": ["Python"], "Count": [10]})

    def read_csv(path):
        if "devops" in path:
            raise FileNotFoundError(path)
        return mock_df

    monkeypatch.setattr(pandas, "read_csv", read_csv)

    data = get_report_data()

    assert [p["name"] for p in data["positions"]] == ["python"]


def test_get_report_data_fails_without_any_position(monkeypatch):
    set_up_report(monkeypatch)
    monkeypatch.setattr(
        pandas, "read_csv", lambda path: (_ for _ in ()).throw(OSError(path))
    )

    with pytest.raises(ValueError):
        get_report_data()


def test_generate_report_output_exists(monkeypatch, tmp_path):
    output_file = tmp_path / "index.html"
    monkeypatch.setattr(
        "analytics.report_generator.HTML_PAGE_OUTPUT_FILE", str(output_file)
    )
    set_up_report(monkeypatch)

    with patch("webbrowser.open"):
        generate_report()

    assert output_file.exists()
    assert output_file.stat().st_size > 0


def test_get_memes_reads_json(monkeypatch, tmp_path):
    memes_file = tmp_path / "memes.json"
    memes_file.write_text('[{"file": "a.jpg"}]', encoding="utf-8")
    monkeypatch.setattr(
        "analytics.report_generator.MEMES_FILE", str(memes_file)
    )

    assert get_memes() == [{"file": "a.jpg"}]


def test_get_memes_missing_file(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "analytics.report_generator.MEMES_FILE", str(tmp_path / "none.json")
    )

    assert get_memes() == []

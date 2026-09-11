from unittest.mock import patch

import pandas as pd

from analytics.visualization import visualize_jobs


def test_visualize_jobs_generates_png(monkeypatch, tmp_path):
    input_csv = tmp_path / "test_analysis.csv"
    output_png = tmp_path / "test_plot.png"

    df = pd.DataFrame(
        {"Technology": ["python", "docker", "ci/cd"], "Count": [52, 38, 36]}
    )
    df.to_csv(input_csv, index=False)

    monkeypatch.setattr(
        "analytics.visualization.ANALYSIS_OUTPUT_FILE", str(input_csv)
    )
    monkeypatch.setattr(
        "analytics.visualization.VISUALIZATION_OUTPUT_FILE", str(output_png)
    )

    with patch("matplotlib.pyplot.show"):
        visualize_jobs()

    assert output_png.exists()
    assert output_png.stat().st_size > 0


def test_visualize_jobs_handles_missing_file(monkeypatch, tmp_path):
    missing_csv = tmp_path / "missing.csv"
    output_png = tmp_path / "should_not_exist.png"

    monkeypatch.setattr(
        "analytics.visualization.ANALYSIS_OUTPUT_FILE", str(missing_csv)
    )
    monkeypatch.setattr(
        "analytics.visualization.VISUALIZATION_OUTPUT_FILE", str(output_png)
    )

    visualize_jobs()

    assert not output_png.exists()

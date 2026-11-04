import pandas as pd

from analytics.analysis import (
    count_technologies,
    get_job_descriptions,
    save_results,
    analyze_technologies,
)


def test_main_count_technologies_logic():
    job_descriptions = [
        "Looking for an AI Engineer with strong Python and JS background.",
        "Must have exp in Artificial Intelligence, JavaScript, and ML models.",
        "Python developer needed, AI and Node.js required.",
    ]

    counts = count_technologies(job_descriptions)

    assert counts.get("ai") == 3
    assert counts.get("python") == 2
    assert counts.get("javascript") == 3
    assert counts.get("node.js") == 1


def test_count_technologies_symbols_and_dots():
    job_descriptions = [
        "Senior C++ and C# developer needed with .NET Core experience.",
        "Full-stack role: Node.js, React, and Vue.js.",
        "C++ developer transitioning to C# and .NET microservices.",
    ]

    counts = count_technologies(job_descriptions)

    assert counts.get("c++") == 2
    assert counts.get("c#") == 2
    assert counts.get(".net") == 2
    assert counts.get("node.js") == 1
    assert counts.get("vue.js") == 1


def test_count_technologies_compound_slash_and_hyphen():
    job_descriptions = [
        "Hands-on experience with AI/ML pipelines and CI/CD automation.",
        "Deep understanding of CI/CD practices.",
    ]

    counts = count_technologies(job_descriptions)

    assert counts.get("ai") == 1
    assert counts.get("ml") == 1
    assert counts.get("ci/cd") == 2


def test_count_technologies_deduplication_per_vacancy():
    job_descriptions = [
        "AI. Only AI. CEO loves AI.",
    ]

    counts = count_technologies(job_descriptions)

    assert counts.get("ai") == 1


def test_get_job_descriptions_reads_csv_files(tmp_path):
    csv_file = tmp_path / "test_jobs.csv"
    df = pd.DataFrame(
        {
            "title": ["Dev 1", "Dev 2", "Dev 3"],
            "description": [
                "Python and AWS",
                "   ",
                "React developer needed",
            ],
        }
    )
    df.to_csv(csv_file, index=False)

    descriptions = get_job_descriptions(str(tmp_path))

    assert len(descriptions) == 2
    assert "Python and AWS" in descriptions
    assert "React developer needed" in descriptions


def test_save_results_creates_sorted_csv(tmp_path):
    output_file = tmp_path / "tech_counts.csv"
    counts = {"python": 10, "aws": 25, "docker": 5}

    save_results(counts, str(output_file))

    assert output_file.exists()

    saved_df = pd.read_csv(output_file)
    assert list(saved_df.columns) == ["Technology", "Count"]
    # Verify sorting
    assert saved_df.iloc[0]["Technology"] == "aws"
    assert saved_df.iloc[0]["Count"] == 25
    assert saved_df.iloc[2]["Technology"] == "docker"


def set_up_positions(monkeypatch, tmp_path, positions):
    monkeypatch.setattr("analytics.analysis.POSITIONS", positions)
    monkeypatch.setattr(
        "analytics.analysis.POSITION_SCRAPING_OUTPUT_FILE",
        str(tmp_path / "scraping" / "{position}" / "jobs.csv"),
    )
    monkeypatch.setattr(
        "analytics.analysis.POSITION_ANALYSIS_OUTPUT_FILE",
        str(tmp_path / "analytics" / "{position}" / "tech_counts.csv"),
    )


def write_jobs(tmp_path, position, descriptions):
    jobs_file = tmp_path / "scraping" / position / "jobs.csv"
    jobs_file.parent.mkdir(parents=True)
    pd.DataFrame({"description": descriptions}).to_csv(
        jobs_file, index=False
    )


def test_analyze_technologies_saves_each_position_separately(
    monkeypatch, tmp_path
):
    set_up_positions(
        monkeypatch, tmp_path, {"python": "Python", "frontend": "Front End"}
    )
    write_jobs(tmp_path, "python", ["Python and Django", "Python and AWS"])
    write_jobs(tmp_path, "frontend", ["React and CSS"])

    analyze_technologies()

    python_counts = pd.read_csv(
        tmp_path / "analytics" / "python" / "tech_counts.csv"
    )
    frontend_counts = pd.read_csv(
        tmp_path / "analytics" / "frontend" / "tech_counts.csv"
    )
    assert "react" not in list(python_counts["Technology"])
    assert "django" not in list(frontend_counts["Technology"])
    assert python_counts.iloc[0]["Technology"] == "python"
    assert python_counts.iloc[0]["Count"] == 2
    assert "react" in list(frontend_counts["Technology"])


def test_analyze_technologies_skips_missing_position(monkeypatch, tmp_path):
    set_up_positions(
        monkeypatch, tmp_path, {"python": "Python", "devops": "DevOps"}
    )
    write_jobs(tmp_path, "devops", ["Docker and Kubernetes"])

    analyze_technologies()

    assert not (tmp_path / "analytics" / "python").exists()
    assert (tmp_path / "analytics" / "devops" / "tech_counts.csv").exists()


def test_analyze_technologies_continues_after_position_error(
    monkeypatch, tmp_path
):
    set_up_positions(
        monkeypatch, tmp_path, {"python": "Python", "devops": "DevOps"}
    )
    write_jobs(tmp_path, "python", ["Python"])
    write_jobs(tmp_path, "devops", ["Docker"])

    real_count = count_technologies

    def broken_for_python(descriptions):
        if descriptions == ["Python"]:
            raise ValueError("boom")
        return real_count(descriptions)

    monkeypatch.setattr(
        "analytics.analysis.count_technologies", broken_for_python
    )

    analyze_technologies()

    assert not (tmp_path / "analytics" / "python").exists()
    assert (tmp_path / "analytics" / "devops" / "tech_counts.csv").exists()

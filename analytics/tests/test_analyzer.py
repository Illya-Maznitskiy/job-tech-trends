from analytics.analysis import count_technologies


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

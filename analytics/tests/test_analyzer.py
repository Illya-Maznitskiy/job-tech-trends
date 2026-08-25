import pytest

from analytics.analysis import preprocess_text


@pytest.mark.parametrize(
    "input_text, expected_tokens",
    [
        (
            "Python is great! Docker is useful.",
            ["python", "great", "docker", "useful"],
        ),
        (
            "  FASTAPI and PostgreSQL  ",
            ["fastapi", "postgresql"],
        ),
        (
            "",
            [],
        ),
        (
            "is and the, or!",
            [],
        ),
        (
            "Looking for C++ and Node.js.",
            ["looking", "c++", "node.js"],
        ),
    ],
)
def test_preprocess_text(input_text: str, expected_tokens: list[str]) -> None:
    assert preprocess_text(input_text) == expected_tokens

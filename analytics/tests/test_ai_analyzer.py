from unittest.mock import MagicMock, patch

import pandas as pd

from analytics.ai_analyzer import analyze_market_with_ai

COUNTS = pd.DataFrame({"Technology": ["Python", "Docker"], "Count": [10, 5]})


@patch.dict("os.environ", {}, clear=True)
def test_ai_analyze_market_missing_api_key():
    result = analyze_market_with_ai("python", "Python", COUNTS)
    assert result is None


@patch.dict("os.environ", {"GEMINI_API_KEY": "fake_key"})
@patch("analytics.ai_analyzer.genai.Client")
def test_ai_analyze_market_success(mock_client_cls):
    # Mock GenAI client response
    mock_client_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.output_text = "Top fields: 1. Python Dev"
    mock_client_instance.interactions.create.return_value = mock_response
    mock_client_cls.return_value = mock_client_instance

    result = analyze_market_with_ai("python", "Python", COUNTS)

    assert result == "Top fields: 1. Python Dev"
    mock_client_instance.interactions.create.assert_called_once()


@patch.dict("os.environ", {"GEMINI_API_KEY": "fake_key"})
@patch("analytics.ai_analyzer.genai.Client")
def test_ai_analyze_market_api_error(mock_client_cls):
    mock_client_instance = MagicMock()
    mock_client_instance.interactions.create.side_effect = Exception(
        "API Timeout"
    )
    mock_client_cls.return_value = mock_client_instance

    result = analyze_market_with_ai("python", "Python", COUNTS)

    assert result is None


@patch.dict("os.environ", {"GEMINI_API_KEY": "fake_key"})
@patch("analytics.ai_analyzer.genai.Client")
def test_ai_analyze_market_prompt_uses_position_data(mock_client_cls):
    mock_client_instance = MagicMock()
    mock_client_cls.return_value = mock_client_instance
    counts = pd.DataFrame({"Technology": ["react"], "Count": [30]})

    analyze_market_with_ai("frontend", "Front End", counts)

    prompt = mock_client_instance.interactions.create.call_args.kwargs[
        "input"
    ]
    assert "Front End" in prompt
    assert "react" in prompt
    assert "category=Front%20End" in prompt

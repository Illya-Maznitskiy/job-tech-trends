from unittest.mock import MagicMock, patch

import pandas as pd

from analytics.ai_analyzer import analyze_market_with_ai


@patch.dict("os.environ", {}, clear=True)
def test_ai_analyze_market_missing_api_key():
    result = analyze_market_with_ai()
    assert result is None


@patch.dict("os.environ", {"GEMINI_API_KEY": "fake_key"})
@patch("analytics.ai_analyzer.pandas.read_csv")
@patch("analytics.ai_analyzer.genai.Client")
def test_ai_analyze_market_success(mock_client_cls, mock_read_csv):
    mock_df = pd.DataFrame(
        {"Technology": ["Python", "Docker"], "Count": [10, 5]}
    )
    mock_read_csv.return_value = mock_df

    # Mock GenAI client response
    mock_client_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.output_text = "Top fields: 1. Python Dev"
    mock_client_instance.interactions.create.return_value = mock_response
    mock_client_cls.return_value = mock_client_instance

    result = analyze_market_with_ai()

    assert result == "Top fields: 1. Python Dev"
    mock_client_instance.interactions.create.assert_called_once()


@patch.dict("os.environ", {"GEMINI_API_KEY": "fake_key"})
@patch("analytics.ai_analyzer.pandas.read_csv")
@patch("analytics.ai_analyzer.genai.Client")
def test_ai_analyze_market_api_error(mock_client_cls, mock_read_csv):
    mock_read_csv.return_value = pd.DataFrame(
        {"Technology": ["Python"], "Count": [10]}
    )

    mock_client_instance = MagicMock()
    mock_client_instance.interactions.create.side_effect = Exception(
        "API Timeout"
    )
    mock_client_cls.return_value = mock_client_instance

    result = analyze_market_with_ai()

    assert result is None

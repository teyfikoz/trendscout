"""Basic tests for TrendScout package."""

import pytest
import pandas as pd


def test_import():
    """Test that trendscout can be imported."""
    import trendscout
    assert hasattr(trendscout, "__version__")
    assert trendscout.__version__ == "0.3.0"


def test_sentiment_analyzer():
    """Test SentimentAnalyzer basic functionality."""
    from trendscout import SentimentAnalyzer

    analyzer = SentimentAnalyzer()
    result = analyzer.analyze("This is a great product!")
    assert "polarity" in result
    assert "subjectivity" in result
    assert isinstance(result["polarity"], float)


def test_trend_scraper():
    """Test TrendScraper returns DataFrame."""
    from trendscout import TrendScraper

    scraper = TrendScraper(use_mock=True)
    df = scraper.get_trends("technology")
    assert isinstance(df, pd.DataFrame)
    assert "title" in df.columns
    assert len(df) > 0


def test_trendscout_facade():
    """Test TrendScout facade class."""
    from trendscout import TrendScout

    ts = TrendScout()
    result = ts.analyze_sentiment("The market is booming!")
    assert hasattr(result, "polarity")
    assert hasattr(result, "label")
    assert hasattr(result, "confidence")
    assert result.label in ("bullish", "bearish", "neutral")


def test_sentiment_dataframe():
    """Test sentiment analysis on DataFrame."""
    from trendscout import SentimentAnalyzer

    analyzer = SentimentAnalyzer()
    df = pd.DataFrame({"text": ["Great!", "Terrible!", "Okay"]})
    result = analyzer.analyze_dataframe(df, "text")
    assert "sentiment" in result.columns
    assert "sentiment_label" in result.columns

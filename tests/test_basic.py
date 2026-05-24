"""Tests for TrendScout v1.0.0."""

import pandas as pd
import pytest


def test_version():
    import trendscout
    assert trendscout.__version__ == "1.0.0"


def test_all_exports():
    from trendscout import TrendScout, TrendScraper, SentimentAnalyzer, SentimentResult
    from trendscout import TrendVelocity, VelocityResult
    assert all(cls is not None for cls in [TrendScout, SentimentAnalyzer, TrendVelocity])


# ── SentimentAnalyzer ─────────────────────────────────────────────────────────

def test_sentiment_basic():
    from trendscout import SentimentAnalyzer
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze("This is a fantastic product!")
    assert "polarity" in result
    assert "label" in result
    assert "intensity" in result
    assert "market_signal" in result
    assert isinstance(result["polarity"], float)


def test_sentiment_positive():
    from trendscout import SentimentAnalyzer
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze("Incredible growth, record profits, soaring revenue!")
    assert result["label"] == "positive"


def test_sentiment_negative():
    from trendscout import SentimentAnalyzer
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze("Terrible crash, massive loss, declining performance.")
    assert result["label"] == "negative"


def test_sentiment_rich_result():
    from trendscout import SentimentAnalyzer, SentimentResult
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze_rich("The market surged 30% today.")
    assert isinstance(result, SentimentResult)
    assert hasattr(result, "market_signal")
    assert hasattr(result, "intensity")
    assert hasattr(result, "confidence")


def test_sentiment_domain_financial():
    from trendscout import SentimentAnalyzer
    analyzer = SentimentAnalyzer()
    r_bullish = analyzer.analyze("Revenue surged 40% beating all analyst estimates.", domain="financial")
    r_bearish = analyzer.analyze("Massive crash, terrible loss, slump continues.", domain="financial")
    assert r_bullish["polarity"] > r_bearish["polarity"]


def test_sentiment_dataframe():
    from trendscout import SentimentAnalyzer
    analyzer = SentimentAnalyzer()
    df = pd.DataFrame({"text": ["Great!", "Terrible crash!", "Neutral news"]})
    result = analyzer.analyze_dataframe(df, "text")
    assert "polarity" in result.columns
    assert "sentiment_label" in result.columns
    assert "market_signal" in result.columns
    assert len(result) == 3


# ── TrendScraper (mock fallback) ──────────────────────────────────────────────

def test_trend_scraper_mock():
    from trendscout import TrendScraper
    scraper = TrendScraper(use_mock=True)
    df = scraper.get_trends("technology", limit=5)
    assert isinstance(df, pd.DataFrame)
    assert "title" in df.columns
    assert len(df) > 0


def test_trend_scraper_volatility():
    from trendscout import TrendScraper
    scraper = TrendScraper()
    v = scraper.get_volatility("AI")
    assert "keyword" in v
    assert "volatility" in v
    assert 0.0 <= v["volatility"] <= 1.0


# ── TrendVelocity ─────────────────────────────────────────────────────────────

def test_velocity_empty_stories():
    from trendscout import TrendVelocity
    tv = TrendVelocity()
    result = tv.calculate("empty topic", [])
    assert result.status == "unknown"
    assert result.score == 0.0
    assert result.article_count == 0


def test_velocity_high_engagement():
    from trendscout import TrendVelocity
    tv = TrendVelocity()
    stories = [{"score": 500, "num_comments": 100} for _ in range(25)]
    result = tv.calculate("viral topic", stories)
    assert result.score > 0.5
    assert result.status in ("emerging", "peak")


def test_velocity_low_engagement():
    from trendscout import TrendVelocity
    tv = TrendVelocity()
    stories = [{"score": 5, "num_comments": 1} for _ in range(2)]
    result = tv.calculate("niche topic", stories)
    assert result.status in ("declining", "stable", "peak")


# ── TrendScout facade ─────────────────────────────────────────────────────────

def test_trendscout_analyze_sentiment():
    from trendscout import TrendScout, SentimentResult
    ts = TrendScout()
    result = ts.analyze_sentiment("The market is booming with record highs!")
    assert isinstance(result, SentimentResult)
    assert result.label in ("positive", "negative", "neutral")
    assert 0.0 <= result.confidence <= 1.0


def test_trendscout_analyze_dataframe():
    from trendscout import TrendScout
    ts = TrendScout()
    df = pd.DataFrame({"headline": ["Great news!", "Terrible losses", "Mixed results"]})
    result = ts.analyze_dataframe(df, "headline")
    assert "sentiment_label" in result.columns
    assert len(result) == 3


def test_trendscout_backward_compat_volatility():
    from trendscout import TrendScout
    ts = TrendScout()
    result = ts.get_trend_volatility("python")
    assert "keyword" in result
    assert "volatility" in result
    assert "status" in result


def test_trendscout_emerging_trends_fallback():
    from trendscout import TrendScout
    ts = TrendScout()
    df = ts.get_emerging_trends(domain="technology", limit=5)
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0


# ── RSS Source (unit test — no network needed) ────────────────────────────────

def test_rss_parse_rss2():
    from trendscout.sources.rss import RSSFeedSource
    rss = RSSFeedSource()
    xml = """<?xml version="1.0"?>
    <rss version="2.0"><channel>
      <item><title>Test Article</title><link>https://example.com/1</link>
        <description>A test item</description><pubDate>Sat, 24 May 2026 00:00:00 GMT</pubDate></item>
    </channel></rss>"""
    items = rss._parse(xml, "test-feed", 10)
    assert len(items) == 1
    assert items[0].title == "Test Article"
    assert items[0].url == "https://example.com/1"


def test_rss_parse_atom():
    from trendscout.sources.rss import RSSFeedSource
    rss = RSSFeedSource()
    xml = """<?xml version="1.0"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <title>Atom Article</title>
        <link href="https://example.com/atom/1"/>
        <summary>An atom entry</summary>
        <updated>2026-05-24T00:00:00Z</updated>
      </entry>
    </feed>"""
    items = rss._parse(xml, "atom-feed", 10)
    assert len(items) == 1
    assert items[0].title == "Atom Article"


# ── HackerNews Source (instantiation only — no live calls in tests) ───────────

def test_hackernews_source_instantiation():
    from trendscout.sources.hackernews import HackerNewsSource
    hn = HackerNewsSource()
    assert hn is not None
    assert hn.timeout == 10

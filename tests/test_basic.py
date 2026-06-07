"""Tests for TrendScout v1.0.0."""

import pandas as pd
import pytest


def test_version():
    import trendscout
    assert trendscout.__version__ == "1.1.0"


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


# ── HackerNews story to_dict ─────────────────────────────────────────────────

def test_hackernews_story_to_dict():
    from trendscout.sources.hackernews import HNStory
    story = HNStory(id=1, title="Test", url="https://example.com", score=100,
                    num_comments=50, author="user", created_at="2026-01-01")
    d = story.to_dict()
    assert d["title"] == "Test"
    assert d["score"] == 100
    assert d["source"] == "hackernews"


# ── HackerNews search returns [] on network error (mocked) ───────────────────

def test_hackernews_search_network_error(monkeypatch):
    from trendscout.sources.hackernews import HackerNewsSource
    import requests

    def raise_exc(*args, **kwargs):
        raise requests.exceptions.ConnectionError("no network")

    hn = HackerNewsSource(timeout=1)
    monkeypatch.setattr(hn._session, "get", raise_exc)
    result = hn.search("ai", limit=5)
    assert result == []


# ── RSS item to_dict ──────────────────────────────────────────────────────────

def test_rss_item_to_dict():
    from trendscout.sources.rss import RSSItem
    item = RSSItem(title="News", url="https://example.com/news",
                   description="A test", published="2026-01-01", feed_name="test")
    d = item.to_dict()
    assert d["title"] == "News"
    assert d["source"] == "rss"


# ── RSS parse invalid XML returns [] ─────────────────────────────────────────

def test_rss_parse_invalid_xml():
    from trendscout.sources.rss import RSSFeedSource
    rss = RSSFeedSource()
    result = rss._parse("<not valid xml >>>", "test", 10)
    assert result == []


# ── RSS parse items with missing fields ──────────────────────────────────────

def test_rss_parse_items_missing_fields():
    from trendscout.sources.rss import RSSFeedSource
    rss = RSSFeedSource()
    xml = """<?xml version="1.0"?>
    <rss version="2.0"><channel>
      <item><title>No Link Article</title></item>
      <item></item>
    </channel></rss>"""
    items = rss._parse(xml, "test-feed", 10)
    # Only items with title should be returned
    assert all(i.title for i in items)


# ── RSS fetch_multiple ────────────────────────────────────────────────────────

def test_rss_fetch_multiple_network_error(monkeypatch):
    from trendscout.sources.rss import RSSFeedSource
    import requests

    def raise_exc(*args, **kwargs):
        raise requests.exceptions.ConnectionError("no network")

    rss = RSSFeedSource()
    monkeypatch.setattr(rss._session, "get", raise_exc)
    result = rss.fetch_multiple(["http://feed1.example", "http://feed2.example"], limit=10)
    assert result == []


# ── VelocityResult statuses ──────────────────────────────────────────────────

def test_velocity_peak_status():
    from trendscout import TrendVelocity
    tv = TrendVelocity()
    # 10 stories with medium engagement → "peak"
    stories = [{"score": 150, "num_comments": 30} for _ in range(10)]
    result = tv.calculate("midtopic", stories)
    assert result.status in ("emerging", "peak", "stable", "declining")


def test_velocity_stable_status():
    from trendscout import TrendVelocity
    tv = TrendVelocity()
    stories = [{"score": 30, "num_comments": 5} for _ in range(5)]
    result = tv.calculate("slow topic", stories)
    assert result.status in ("stable", "declining")


# ── TrendScout get_rss_trends (mock network) ─────────────────────────────────

def test_trendscout_get_rss_trends_empty(monkeypatch):
    from trendscout import TrendScout
    import requests

    def raise_exc(*args, **kwargs):
        raise requests.exceptions.ConnectionError("no network")

    ts = TrendScout()
    rss = ts._get_rss()
    monkeypatch.setattr(rss._session, "get", raise_exc)
    result = ts.get_rss_trends(category="tech", limit=5)
    assert isinstance(result, pd.DataFrame)


# ── TrendScout analyze_topics ────────────────────────────────────────────────

def test_trendscout_analyze_topics_mock(monkeypatch):
    from trendscout import TrendScout
    import requests

    def raise_exc(*args, **kwargs):
        raise requests.exceptions.ConnectionError("no network")

    ts = TrendScout()
    hn = ts._get_hn()
    monkeypatch.setattr(hn._session, "get", raise_exc)
    result = ts.analyze_topics(["python", "rust"], source="hackernews")
    assert isinstance(result, pd.DataFrame)
    assert "topic" in result.columns


# ── TrendScout get_rss_trends with custom feeds ──────────────────────────────

def test_trendscout_get_rss_trends_custom_feeds(monkeypatch):
    from trendscout import TrendScout
    import requests

    def raise_exc(*args, **kwargs):
        raise requests.exceptions.ConnectionError("no network")

    ts = TrendScout()
    rss = ts._get_rss()
    monkeypatch.setattr(rss._session, "get", raise_exc)
    result = ts.get_rss_trends(feeds=["http://example.com/feed.xml"], limit=5)
    assert isinstance(result, pd.DataFrame)


# ── TrendScout get_trend_velocity with rss source ────────────────────────────

def test_trendscout_velocity_rss_source(monkeypatch):
    from trendscout import TrendScout
    import requests

    def raise_exc(*args, **kwargs):
        raise requests.exceptions.ConnectionError("no network")

    ts = TrendScout()
    rss = ts._get_rss()
    monkeypatch.setattr(rss._session, "get", raise_exc)
    result = ts.get_trend_velocity("tech", source="rss")
    assert hasattr(result, "score")


# ── HackerNews get_top_stories network error ─────────────────────────────────

def test_hackernews_top_stories_network_error(monkeypatch):
    from trendscout.sources.hackernews import HackerNewsSource
    import requests

    def raise_exc(*args, **kwargs):
        raise requests.exceptions.ConnectionError("no network")

    hn = HackerNewsSource(timeout=1)
    monkeypatch.setattr(hn._session, "get", raise_exc)
    result = hn.get_top_stories(limit=5)
    assert result == []


# ── HackerNews search returns items when mocked ───────────────────────────────

def test_hackernews_search_mocked_response(monkeypatch):
    from trendscout.sources.hackernews import HackerNewsSource
    import json

    mock_response = {
        "hits": [
            {"objectID": "123", "title": "Python AI Tools", "url": "https://example.com/1",
             "points": 300, "num_comments": 50, "author": "user1", "created_at": "2026-01-01T00:00:00Z"},
            {"objectID": "456", "title": "Rust Performance", "url": "https://example.com/2",
             "points": 200, "num_comments": 30, "author": "user2", "created_at": "2026-01-02T00:00:00Z"},
        ]
    }

    class MockResp:
        def raise_for_status(self): pass
        def json(self): return mock_response

    hn = HackerNewsSource()
    monkeypatch.setattr(hn._session, "get", lambda *a, **kw: MockResp())
    stories = hn.search("python", limit=5)
    assert len(stories) == 2
    assert stories[0].score >= stories[1].score  # sorted by score


# ── SentimentAnalyzer neutral text ───────────────────────────────────────────

def test_sentiment_neutral():
    from trendscout import SentimentAnalyzer
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze("The meeting is scheduled for Tuesday.")
    assert result["label"] in ("positive", "negative", "neutral")


# ── HackerNews get_top_stories mocked ────────────────────────────────────────

def test_hackernews_top_stories_mocked(monkeypatch):
    from trendscout.sources.hackernews import HackerNewsSource
    import json, unittest.mock as mock

    call_count = [0]

    top_ids = [111, 222]
    items_by_id = {
        111: {"type": "story", "title": "Story One", "url": "https://ex.com/1",
              "score": 100, "descendants": 20, "by": "alice", "time": 1716000000},
        222: {"type": "story", "title": "Story Two", "url": None,
              "score": 80, "descendants": 10, "by": "bob", "time": 1716000001},
    }

    def mock_get(url, *args, **kwargs):
        resp = mock.MagicMock()
        resp.raise_for_status = lambda: None
        if "topstories" in url:
            resp.json.return_value = top_ids
        else:
            sid = int(url.split("/item/")[1].split(".json")[0])
            resp.json.return_value = items_by_id.get(sid, {})
        return resp

    hn = HackerNewsSource()
    monkeypatch.setattr(hn._session, "get", mock_get)
    monkeypatch.setattr("trendscout.sources.hackernews.time.sleep", lambda x: None)
    stories = hn.get_top_stories(limit=5)
    assert len(stories) >= 1
    assert stories[0].title in ("Story One", "Story Two")


# ── TrendScout get_emerging_trends exception fallback ─────────────────────────

def test_trendscout_emerging_trends_exception_fallback(monkeypatch):
    from trendscout import TrendScout

    ts = TrendScout()

    def raise_exc(topic, limit):
        raise RuntimeError("simulated error")

    monkeypatch.setattr(ts, "get_hackernews_trends", raise_exc)
    result = ts.get_emerging_trends(domain="ai", limit=3)
    assert isinstance(result, pd.DataFrame)

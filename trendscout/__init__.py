"""
TrendScout v1.2.0 — Real-time trend intelligence with HackerNews, RSS, GitHub Trending,
and multi-domain sentiment.
"""

__version__ = "1.2.0"

from typing import Optional

import pandas as pd

from .scraper import TrendScraper
from .sentiment import SentimentAnalyzer, SentimentResult
from .velocity import TrendVelocity, VelocityResult


class TrendScout:
    """
    Unified trend intelligence interface.

    Features:
    - HackerNews search via Algolia API (free, no key required)
    - RSS/Atom feed parsing with presets (tech, AI, business, python)
    - TextBlob sentiment + domain-aware lexicon boost (financial/tech)
    - Trend velocity and momentum scoring (emerging/peak/stable/declining)
    - Multi-topic comparison table
    - Backward-compatible with v0.3.0

    Example::

        from trendscout import TrendScout

        ts = TrendScout()

        # Real HackerNews trends
        df = ts.get_hackernews_trends("AI agents", limit=10)
        print(df[["title", "score"]].head())

        # Sentiment
        result = ts.analyze_sentiment("GPT-5 beats all benchmarks!", domain="tech")
        print(result)  # bullish / strong

        # Velocity score
        velocity = ts.get_trend_velocity("rust programming")
        print(velocity)

        # Compare multiple topics
        report = ts.analyze_topics(["AI", "blockchain", "quantum computing"])
        print(report)
    """

    def __init__(self):
        self._scraper = TrendScraper()
        self._sentiment = SentimentAnalyzer()
        self._velocity = TrendVelocity()
        self._hn = None
        self._rss = None

    def _get_hn(self):
        if self._hn is None:
            from .sources.hackernews import HackerNewsSource
            self._hn = HackerNewsSource()
        return self._hn

    def _get_rss(self):
        if self._rss is None:
            from .sources.rss import RSSFeedSource
            self._rss = RSSFeedSource()
        return self._rss

    def _get_github(self, token: str | None = None):
        from .sources.github_trending import GitHubTrendingSource
        return GitHubTrendingSource(token=token)

    # ── Trend fetching ─────────────────────────────────────────────────────────

    def get_hackernews_trends(self, topic: str, limit: int = 20) -> pd.DataFrame:
        """
        Fetch real trending stories from HackerNews for a topic.

        Uses HN Algolia API — free, no API key needed.

        Args:
            topic: Search keyword
            limit: Max stories to return

        Returns:
            DataFrame: title, url, score, num_comments, author, created_at, source
        """
        stories = self._get_hn().search(topic, limit=limit)
        if not stories:
            return pd.DataFrame(columns=["title", "url", "score", "num_comments", "author", "source"])
        return pd.DataFrame([s.to_dict() for s in stories])

    def get_rss_trends(
        self,
        category: str = "tech",
        feeds: Optional[list[str]] = None,
        limit: int = 20,
    ) -> pd.DataFrame:
        """
        Fetch trends from RSS/Atom feeds.

        Args:
            category: Preset — 'tech' | 'ai' | 'business' | 'python' | 'startup'
            feeds: Custom list of feed URLs (overrides category)
            limit: Max items to return

        Returns:
            DataFrame: title, url, description, published, feed_name, source
        """
        if feeds:
            items = self._get_rss().fetch_multiple(feeds, limit=limit)
        else:
            items = self._get_rss().fetch_preset(category, limit=limit)
        if not items:
            return pd.DataFrame(columns=["title", "url", "description", "published"])
        return pd.DataFrame([i.to_dict() for i in items])

    def get_github_trending(
        self,
        language: str | None = None,
        since: str = "daily",
        limit: int = 25,
        min_stars: int = 5,
        token: str | None = None,
    ) -> pd.DataFrame:
        """
        Fetch trending GitHub repositories created in the given time window.

        Uses GitHub Search API — no authentication required (60 req/hr).
        Optionally pass a ``token`` or set ``GITHUB_TOKEN`` env var for
        5,000 req/hr.

        Args:
            language: Filter by programming language (e.g. ``"python"``,
                      ``"typescript"``). ``None`` returns all languages.
            since: Time window — ``"daily"``, ``"weekly"``, or ``"monthly"``.
            limit: Max repositories to return (capped at 100 by the API).
            min_stars: Minimum star count filter.
            token: Optional GitHub personal access token.

        Returns:
            DataFrame with columns: name, full_name, description, url,
            stars, forks, language, created_at, topics, source.
        """
        repos = self._get_github(token=token).fetch(
            language=language, since=since, limit=limit, min_stars=min_stars
        )
        if not repos:
            return pd.DataFrame(
                columns=["name", "full_name", "description", "url", "stars",
                         "forks", "language", "created_at", "topics", "source"]
            )
        return pd.DataFrame([r.to_dict() for r in repos])

    def get_emerging_trends(self, domain: str = "general", limit: int = 5) -> pd.DataFrame:
        """
        Get trending topics (tries HackerNews, falls back to mock).

        Args:
            domain: Topic/keyword to search
            limit: Max results

        Returns:
            DataFrame with trend data
        """
        try:
            df = self.get_hackernews_trends(domain, limit=limit)
            if not df.empty:
                return df
        except Exception:
            pass
        return self._scraper.get_trends(topic=domain, limit=limit)

    # ── Sentiment ──────────────────────────────────────────────────────────────

    def analyze_sentiment(self, text: str, domain: str = "general") -> SentimentResult:
        """
        Analyze text sentiment with domain-aware scoring.

        Args:
            text: Input text to analyze
            domain: 'general' | 'financial' | 'tech' | 'social'

        Returns:
            SentimentResult with label, intensity, market_signal, polarity, confidence
        """
        return self._sentiment.analyze_rich(text, domain=domain)

    def analyze_dataframe(
        self,
        df: pd.DataFrame,
        text_col: str,
        domain: str = "general",
    ) -> pd.DataFrame:
        """
        Batch sentiment analysis on a DataFrame text column.

        Adds: polarity, subjectivity, sentiment_label, sentiment_intensity, market_signal
        """
        return self._sentiment.analyze_dataframe(df, text_col, domain=domain)

    # ── Velocity ───────────────────────────────────────────────────────────────

    def get_trend_velocity(self, keyword: str, source: str = "hackernews") -> VelocityResult:
        """
        Measure trend momentum for a keyword.

        Args:
            keyword: Keyword to measure
            source: 'hackernews' | 'rss'

        Returns:
            VelocityResult with score (0–1), status (emerging/peak/stable/declining)
        """
        if source == "hackernews":
            df = self.get_hackernews_trends(keyword, limit=30)
            stories = df.to_dict("records") if not df.empty else []
        else:
            df = self.get_rss_trends(category=keyword, limit=30)
            stories = [{"score": 10, "num_comments": 0} for _ in range(len(df))]
        return self._velocity.calculate(keyword, stories)

    def analyze_topics(
        self,
        topics: list[str],
        source: str = "hackernews",
    ) -> pd.DataFrame:
        """
        Compare velocity and sentiment across multiple topics.

        Args:
            topics: List of keywords to analyze
            source: 'hackernews' | 'rss'

        Returns:
            DataFrame sorted by velocity_score descending with status and recommendation
        """
        rows = []
        for topic in topics:
            v = self.get_trend_velocity(topic, source=source)
            rows.append({
                "topic": topic,
                "velocity_score": v.score,
                "status": v.status,
                "article_count": v.article_count,
                "avg_engagement": v.avg_score,
                "recommendation": v.recommendation,
            })
        df = pd.DataFrame(rows)
        return df.sort_values("velocity_score", ascending=False).reset_index(drop=True)

    # ── Backward compatibility ─────────────────────────────────────────────────

    def get_trend_volatility(self, keyword: str) -> dict:
        """Backward compat: returns velocity as volatility dict."""
        v = self.get_trend_velocity(keyword)
        return {"keyword": keyword, "volatility": v.score, "status": v.status}


__all__ = [
    "TrendScout",
    "TrendScraper",
    "SentimentAnalyzer",
    "SentimentResult",
    "TrendVelocity",
    "VelocityResult",
]

from .sources.github_trending import GitHubRepo, GitHubTrendingSource  # noqa: E402

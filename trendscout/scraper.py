"""TrendScout — Offline mock scraper (fallback when network unavailable)."""
from __future__ import annotations

import random

import pandas as pd


class TrendScraper:
    """
    Mock trend scraper — used as fallback when network sources are unavailable.
    For real data use TrendScout.get_hackernews_trends() or get_rss_trends().
    """

    def __init__(self, use_mock: bool = True):
        self.use_mock = use_mock

    def get_trends(self, topic: str = "technology", limit: int = 5) -> pd.DataFrame:
        """
        Return mock trend data for a topic (offline fallback).

        Args:
            topic: Keyword to simulate
            limit: Number of mock results

        Returns:
            DataFrame with title, source, url, score, timestamp
        """
        titles = [
            f"Why {topic} is booming in 2026",
            f"Top 10 {topic} trends to watch this year",
            f"The future of {topic}: what experts say",
            f"How {topic} is reshaping the industry",
            f"{topic}: key insights for decision-makers",
            f"Investors are paying attention to {topic}",
            f"{topic} momentum continues to accelerate",
        ]
        sources = ["TechCrunch", "Bloomberg", "Reuters", "The Verge", "Wired", "Ars Technica"]
        data = []
        for t in random.sample(titles, min(limit, len(titles))):
            data.append({
                "title": t,
                "source": random.choice(sources),
                "url": f"https://example.com/{random.randint(10000, 99999)}",
                "score": random.randint(20, 500),
                "num_comments": random.randint(5, 200),
                "timestamp": pd.Timestamp.now(),
            })
        return pd.DataFrame(data)

    def get_volatility(self, keyword: str) -> dict:
        """Mock volatility estimate (offline fallback)."""
        score = round(random.uniform(0.1, 0.9), 3)
        status = "emerging" if score > 0.7 else ("peak" if score > 0.4 else "stable")
        return {"keyword": keyword, "volatility": score, "status": status}

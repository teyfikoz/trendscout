import random

import pandas as pd


class TrendScraper:
    """
    Scrapes trending topics from various sources.
    """

    def __init__(self, use_mock: bool = True):
        self.use_mock = use_mock

    def get_trends(self, topic: str = "technology") -> pd.DataFrame:
        """
        Get trending articles/posts about a topic.

        Args:
            topic: Keyword to search

        Returns:
            DataFrame with 'title', 'source', 'url', 'timestamp'
        """
        if self.use_mock:
            return self._mock_trends(topic)

        # TODO: Implement real scraping logic here
        # For now, fallback to mock
        return self._mock_trends(topic)

    def _mock_trends(self, topic: str) -> pd.DataFrame:
        """Generate dummy trend data."""
        titles = [
            f"Why {topic} is booming in 2026",
            f"Top 10 {topic} trends to watch",
            f"The future of {topic} explained",
            f"Investors are flocking to {topic}",
            f"{topic} crash imminent? Experts warn.",
        ]

        sources = ["TechCrunch", "Bloomberg", "Reuters", "The Verge", "Wired"]

        data = []
        for t in titles:
            data.append({
                "title": t,
                "source": random.choice(sources),
                "url": f"https://example.com/{random.randint(1000,9999)}",
                "timestamp": pd.Timestamp.now()
            })

        return pd.DataFrame(data)

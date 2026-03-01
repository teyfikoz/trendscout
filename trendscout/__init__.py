"""
TrendScout - AI-Powered Market Trend Analysis
"""

__version__ = "0.3.0"

from .scraper import TrendScraper
from .sentiment import SentimentAnalyzer


class SentimentResult:
    """Wrapper for sentiment analysis result."""
    def __init__(self, data: dict):
        self.polarity = data.get('polarity', 0.0)
        self.subjectivity = data.get('subjectivity', 0.0)
        self.label = "bullish" if self.polarity > 0.1 else ("bearish" if self.polarity < -0.1 else "neutral")
        self.confidence = 0.95 if abs(self.polarity) > 0.5 else 0.85
        self.entities = []

class TrendScout:
    """
    Central facade for TrendScout library.
    Provides unified access to trend scraping and sentiment analysis.
    """
    def __init__(self):
        self.scraper = TrendScraper()
        self.analyzer = SentimentAnalyzer()

    def analyze_sentiment(self, text: str, domain: str = "general") -> SentimentResult:
        """Analyzes sentiment of text within a specific domain."""
        # Note: domain is ignored in v0.2.2 as underlying analyzer is generic
        data = self.analyzer.analyze(text)
        return SentimentResult(data)

    def get_emerging_trends(self, domain: str = "general", limit: int = 5):
        """Identifies emerging trends for a domain."""
        return self.scraper.get_trends(domain=domain, limit=limit)

    def get_trend_volatility(self, keyword: str):
        """Measures stability of a trend."""
        return self.scraper.get_volatility(keyword)

__all__ = ["TrendScout", "TrendScraper", "SentimentAnalyzer"]

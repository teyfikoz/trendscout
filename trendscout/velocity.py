"""TrendScout — Trend velocity and momentum scoring."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VelocityResult:
    """Trend momentum result."""
    keyword: str
    score: float       # 0.0–1.0: higher = faster growth
    status: str        # emerging | peak | stable | declining | unknown
    article_count: int
    avg_score: float
    recommendation: str

    def __str__(self) -> str:
        filled = int(self.score * 20)
        bar = "█" * filled + "░" * (20 - filled)
        return (
            f"Trend   : {self.keyword}\n"
            f"Velocity: [{bar}] {self.score:.2f}\n"
            f"Status  : {self.status.upper()}\n"
            f"Articles: {self.article_count}  |  Avg engagement: {self.avg_score:.0f}\n"
            f"→ {self.recommendation}"
        )


_RECOMMENDATIONS = {
    "emerging": "Fast-growing — great time to publish content or invest attention.",
    "peak": "Trending now — maximise exposure before it plateaus.",
    "stable": "Steady interest — good for evergreen content strategy.",
    "declining": "Losing momentum — consider pivoting to related keywords.",
    "unknown": "Insufficient data — try a broader keyword.",
}


class TrendVelocity:
    """
    Compute trend momentum from a list of story/article dicts.

    Each dict should contain at least: 'score' (int) and optionally 'num_comments' (int).
    """

    def calculate(self, keyword: str, stories: list[dict]) -> VelocityResult:
        """
        Calculate velocity score and classify trend stage.

        Args:
            keyword: The searched keyword
            stories: List of story dicts (from HN or RSS)

        Returns:
            VelocityResult with score (0–1), status, and recommendation
        """
        if not stories:
            return VelocityResult(
                keyword=keyword, score=0.0, status="unknown",
                article_count=0, avg_score=0.0,
                recommendation=_RECOMMENDATIONS["unknown"],
            )

        scores = [float(s.get("score") or 0) for s in stories]
        article_count = len(stories)
        avg_score = sum(scores) / article_count

        count_signal = min(1.0, article_count / 20.0)
        engagement_signal = min(1.0, avg_score / 200.0)
        velocity = round(0.5 * count_signal + 0.5 * engagement_signal, 3)

        if velocity >= 0.7:
            status = "emerging"
        elif velocity >= 0.4:
            status = "peak"
        elif velocity >= 0.15:
            status = "stable"
        else:
            status = "declining"

        return VelocityResult(
            keyword=keyword,
            score=velocity,
            status=status,
            article_count=article_count,
            avg_score=round(avg_score, 1),
            recommendation=_RECOMMENDATIONS[status],
        )

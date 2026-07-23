"""TrendScout — GitHub Trending source via Search API (free, 60 req/hr unauthenticated)."""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field

import requests

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"
_SINCE_DAYS = {"daily": 1, "weekly": 7, "monthly": 30}


@dataclass
class GitHubRepo:
    """A trending GitHub repository."""

    name: str
    full_name: str
    description: str
    url: str
    stars: int
    forks: int
    language: str | None
    created_at: str
    topics: list[str] = field(default_factory=list)
    source: str = "github_trending"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "full_name": self.full_name,
            "description": self.description,
            "url": self.url,
            "stars": self.stars,
            "forks": self.forks,
            "language": self.language,
            "created_at": self.created_at,
            "topics": self.topics,
            "source": self.source,
        }


class GitHubTrendingSource:
    """
    Fetch trending GitHub repositories using the GitHub Search API.

    No authentication required (60 req/hr). Pass a personal access token
    for 5,000 req/hr via the ``token`` parameter or ``GITHUB_TOKEN`` env var.

    Example::

        from trendscout.sources.github_trending import GitHubTrendingSource

        source = GitHubTrendingSource()
        repos = source.fetch(language="python", since="daily", limit=10)
        for r in repos:
            print(r.full_name, r.stars)
    """

    def __init__(self, token: str | None = None):
        import os
        self._headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "trendscout/1.2.0",
        }
        tok = token or os.environ.get("GITHUB_TOKEN")
        if tok:
            self._headers["Authorization"] = f"token {tok}"

    def fetch(
        self,
        language: str | None = None,
        since: str = "daily",
        limit: int = 25,
        min_stars: int = 5,
    ) -> list[GitHubRepo]:
        """
        Fetch trending repositories created within the given time window.

        Args:
            language: Filter by language (e.g. ``"python"``, ``"typescript"``).
                      ``None`` returns all languages.
            since: Time window — ``"daily"``, ``"weekly"``, or ``"monthly"``.
            limit: Max repositories to return (capped at 100 by the API).
            min_stars: Minimum star count filter.

        Returns:
            List of :class:`GitHubRepo` sorted by stars descending.
        """
        delta = _SINCE_DAYS.get(since, 1)
        since_date = (datetime.date.today() - datetime.timedelta(days=delta)).isoformat()
        query = f"created:>{since_date} stars:>={min_stars}"
        if language:
            query += f" language:{language}"

        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": min(limit, 100),
        }
        try:
            resp = requests.get(
                GITHUB_SEARCH_URL, headers=self._headers, params=params, timeout=10
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])
        except Exception:
            return []

        return [
            GitHubRepo(
                name=item.get("name", ""),
                full_name=item.get("full_name", ""),
                description=item.get("description") or "",
                url=item.get("html_url", ""),
                stars=item.get("stargazers_count", 0),
                forks=item.get("forks_count", 0),
                language=item.get("language"),
                created_at=item.get("created_at", ""),
                topics=item.get("topics", []),
            )
            for item in items
        ]

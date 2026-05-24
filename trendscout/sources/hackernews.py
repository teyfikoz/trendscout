"""TrendScout — HackerNews integration via Algolia API (free, no API key required)."""
from __future__ import annotations

import time
from dataclasses import dataclass

import requests

ALGOLIA_URL = "https://hn.algolia.com/api/v1/search"
HN_TOP_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"


@dataclass
class HNStory:
    """A HackerNews story."""
    id: int
    title: str
    url: str
    score: int
    num_comments: int
    author: str
    created_at: str
    source: str = "hackernews"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "score": self.score,
            "num_comments": self.num_comments,
            "author": self.author,
            "created_at": self.created_at,
            "source": self.source,
        }


class HackerNewsSource:
    """
    Fetch real stories from HackerNews via Algolia search API.
    No API key required. Respects HN's rate limits.

    Example::

        from trendscout.sources.hackernews import HackerNewsSource

        hn = HackerNewsSource()
        stories = hn.search("AI agents", limit=10)
        for s in stories:
            print(s.score, s.title)
    """

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers["User-Agent"] = "TrendScout/1.0.0 (+https://pypi.org/project/trendscout/)"

    def search(self, query: str, limit: int = 20, tags: str = "story") -> list[HNStory]:
        """
        Search HackerNews stories via Algolia API.

        Args:
            query: Search keyword(s)
            limit: Max results to return (max 50 per call)
            tags: HN item type filter ('story', 'ask_hn', 'show_hn')

        Returns:
            List of HNStory sorted by score descending
        """
        params = {"query": query, "tags": tags, "hitsPerPage": min(limit, 50)}
        try:
            resp = self._session.get(ALGOLIA_URL, params=params, timeout=self.timeout)
            resp.raise_for_status()
            hits = resp.json().get("hits", [])
            stories = [
                HNStory(
                    id=int(hit.get("objectID", 0)),
                    title=hit.get("title", ""),
                    url=hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                    score=int(hit.get("points") or 0),
                    num_comments=int(hit.get("num_comments") or 0),
                    author=hit.get("author", ""),
                    created_at=hit.get("created_at", ""),
                )
                for hit in hits
                if hit.get("title")
            ]
            return sorted(stories, key=lambda s: s.score, reverse=True)
        except Exception:
            return []

    def get_top_stories(self, limit: int = 20) -> list[HNStory]:
        """Fetch current top stories (slower — requires per-item API calls)."""
        try:
            resp = self._session.get(HN_TOP_URL, timeout=self.timeout)
            resp.raise_for_status()
            ids = resp.json()[: min(limit * 3, 60)]
            stories: list[HNStory] = []
            for sid in ids:
                try:
                    r = self._session.get(HN_ITEM_URL.format(sid), timeout=self.timeout)
                    item = r.json()
                    if item and item.get("type") == "story" and item.get("title"):
                        stories.append(HNStory(
                            id=sid,
                            title=item.get("title", ""),
                            url=item.get("url") or f"https://news.ycombinator.com/item?id={sid}",
                            score=int(item.get("score") or 0),
                            num_comments=int(item.get("descendants") or 0),
                            author=item.get("by", ""),
                            created_at=str(item.get("time", "")),
                        ))
                    time.sleep(0.3)
                    if len(stories) >= limit:
                        break
                except Exception:
                    continue
            return stories
        except Exception:
            return []

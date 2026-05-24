"""TrendScout — RSS/Atom feed parser (no API key required)."""
from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass

import requests

PRESET_FEEDS: dict[str, list[str]] = {
    "tech": [
        "https://feeds.hnrss.org/newest?points=50",
        "https://www.wired.com/feed/rss",
    ],
    "ai": [
        "https://feeds.hnrss.org/newest?q=AI+machine+learning&points=30",
        "https://huggingface.co/blog/feed.xml",
    ],
    "business": [
        "https://feeds.reuters.com/reuters/businessNews",
    ],
    "python": [
        "https://feeds.hnrss.org/newest?q=python&points=20",
        "https://planetpython.org/rss20.xml",
    ],
    "startup": [
        "https://feeds.hnrss.org/newest?q=startup+saas&points=20",
    ],
}


@dataclass
class RSSItem:
    """A parsed RSS / Atom feed item."""
    title: str
    url: str
    description: str
    published: str
    feed_name: str = ""
    source: str = "rss"

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "description": self.description,
            "published": self.published,
            "feed_name": self.feed_name,
            "source": self.source,
        }


class RSSFeedSource:
    """
    Parse RSS and Atom feeds for trend signals.

    Example::

        from trendscout.sources.rss import RSSFeedSource

        rss = RSSFeedSource()
        items = rss.fetch_preset("tech", limit=10)
        for item in items:
            print(item.title)

        # Custom feeds
        items = rss.fetch("https://feeds.hnrss.org/newest?points=50", limit=5)
    """

    def __init__(self, timeout: int = 8):
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers["User-Agent"] = "TrendScout/1.0.0"

    def fetch(self, feed_url: str, limit: int = 20, feed_name: str = "") -> list[RSSItem]:
        """Fetch and parse a single RSS/Atom feed URL."""
        try:
            resp = self._session.get(feed_url, timeout=self.timeout)
            resp.raise_for_status()
            return self._parse(resp.text, feed_name or feed_url, limit)
        except Exception:
            return []

    def fetch_preset(self, category: str, limit: int = 20) -> list[RSSItem]:
        """
        Fetch from a preset feed category.

        Args:
            category: 'tech' | 'ai' | 'business' | 'python' | 'startup'
            limit: Total items to return (split across feeds)
        """
        feeds = PRESET_FEEDS.get(category, PRESET_FEEDS["tech"])
        per_feed = max(1, limit // len(feeds))
        seen: set[str] = set()
        results: list[RSSItem] = []
        for url in feeds:
            for item in self.fetch(url, limit=per_feed, feed_name=category):
                if item.title not in seen:
                    results.append(item)
                    seen.add(item.title)
        return results[:limit]

    def fetch_multiple(self, feed_urls: list[str], limit: int = 20) -> list[RSSItem]:
        """Fetch and merge multiple feed URLs."""
        per_feed = max(1, limit // len(feed_urls))
        seen: set[str] = set()
        results: list[RSSItem] = []
        for url in feed_urls:
            for item in self.fetch(url, limit=per_feed):
                if item.url not in seen:
                    results.append(item)
                    seen.add(item.url)
        return results[:limit]

    def _parse(self, xml_text: str, feed_name: str, limit: int) -> list[RSSItem]:
        """Parse RSS 2.0 or Atom XML."""
        items: list[RSSItem] = []
        try:
            root = ET.fromstring(xml_text)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            tag = root.tag.lower()
            if "feed" in tag:
                # Atom feed
                for entry in root.findall("atom:entry", ns)[:limit]:
                    title_el = entry.find("atom:title", ns)
                    link_el = entry.find("atom:link", ns)
                    summary_el = entry.find("atom:summary", ns)
                    updated_el = entry.find("atom:updated", ns)
                    items.append(RSSItem(
                        title=(title_el.text or "").strip() if title_el is not None else "",
                        url=link_el.attrib.get("href", "") if link_el is not None else "",
                        description=((summary_el.text or "").strip()[:200]) if summary_el is not None else "",
                        published=(updated_el.text or "") if updated_el is not None else "",
                        feed_name=feed_name,
                    ))
            else:
                # RSS 2.0
                channel = root.find("channel") or root
                for item_el in channel.findall("item")[:limit]:
                    t = item_el.find("title")
                    lnk = item_el.find("link")
                    d = item_el.find("description")
                    p = item_el.find("pubDate")
                    items.append(RSSItem(
                        title=(t.text or "").strip() if t is not None else "",
                        url=(lnk.text or "").strip() if lnk is not None else "",
                        description=((d.text or "").strip()[:200]) if d is not None else "",
                        published=(p.text or "") if p is not None else "",
                        feed_name=feed_name,
                    ))
        except ET.ParseError:
            pass
        return [i for i in items if i.title]

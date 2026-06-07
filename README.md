# TrendScout

**Real-time trend intelligence** — HackerNews search, RSS feed parsing, trend velocity scoring, and multi-domain sentiment analysis. No API key required.

[![PyPI version](https://badge.fury.io/py/trendscout.svg)](https://pypi.org/project/trendscout/)
[![Build](https://github.com/teyfikoz/trendscout/actions/workflows/publish.yml/badge.svg)](https://github.com/teyfikoz/trendscout/actions/workflows/publish.yml)
[![CI](https://github.com/teyfikoz/trendscout/actions/workflows/ci.yml/badge.svg)](https://github.com/teyfikoz/trendscout/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
pip install trendscout
```

## Quick Start

```python
from trendscout import TrendScout

ts = TrendScout()

# Real HackerNews data — no API key needed
df = ts.get_hackernews_trends("AI agents", limit=10)
print(df[['title', 'score', 'num_comments']].head())

# Sentiment with market signal
result = ts.analyze_sentiment("GPT-5 crushes every benchmark!", domain="tech")
print(result)

# Trend velocity
velocity = ts.get_trend_velocity("rust programming language")
print(velocity)
```

---

## Features at a Glance

| Feature | Description |
|---------|-------------|
| **HackerNews API** | Real stories via Algolia — free, no key, always fresh |
| **RSS/Atom Feeds** | Tech, AI, business, Python presets + custom URLs |
| **Trend Velocity** | Momentum score 0–1 with status: emerging/peak/stable/declining |
| **Sentiment Analysis** | TextBlob + domain-aware lexicons (financial, tech, social) |
| **Multi-topic Analysis** | Compare topics side-by-side in a ranked DataFrame |
| **DataFrame Batch** | Bulk sentiment analysis on any text DataFrame |

---

## HackerNews Trends (Real Data)

```python
from trendscout import TrendScout

ts = TrendScout()

# Search by keyword — uses HN Algolia API
df = ts.get_hackernews_trends("large language models", limit=20)
print(df[['title', 'score', 'num_comments', 'author']].head(5))
#                                               title  score  num_comments  author
# 0    LLMs are now good enough for production use    847            312   pg
# 1    Show HN: Open-source LLM benchmark suite      412            189   teyfikoz
# ...

# Top stories right now
from trendscout.sources.hackernews import HackerNewsSource
hn = HackerNewsSource()
top = hn.get_top_stories(limit=10)
for story in top:
    print(f"[{story.score:4d}] {story.title[:70]}")
```

---

## RSS / Atom Feed Parsing

```python
ts = TrendScout()

# Preset categories: tech | ai | business | python | startup
tech_news = ts.get_rss_trends(category="tech", limit=15)
ai_news   = ts.get_rss_trends(category="ai", limit=10)

print(tech_news[['title', 'published', 'feed_name']].head())

# Custom feed URLs
custom = ts.get_rss_trends(
    feeds=[
        "https://feeds.hnrss.org/newest?points=100",
        "https://planetpython.org/rss20.xml",
    ],
    limit=20,
)
```

---

## Trend Velocity Scoring

```python
velocity = ts.get_trend_velocity("quantum computing")
print(velocity)
# Trend   : quantum computing
# Velocity: [████████░░░░░░░░░░░░] 0.42
# Status  : PEAK
# Articles: 12  |  Avg engagement: 156
# → Trending now — maximise exposure before it plateaus

# Status meanings:
# emerging  (0.70–1.00) — fast-growing, act now
# peak      (0.40–0.70) — trending, maximise reach
# stable    (0.15–0.40) — evergreen, good for long-form
# declining (0.00–0.15) — losing momentum, pivot keywords
```

---

## Multi-Topic Comparison

```python
report = ts.analyze_topics(
    ["AI agents", "blockchain", "quantum computing", "WebAssembly", "Rust"],
    source="hackernews",
)
print(report.to_string(index=False))
#              topic  velocity_score   status  article_count  avg_engagement
#          AI agents           0.87 emerging             24           312.4
#               Rust           0.64     peak             18           198.2
# quantum computing           0.42     peak             12           156.1
#        blockchain           0.21   stable              8            89.3
#     WebAssembly            0.09 declining              4            42.0
```

---

## Sentiment Analysis

```python
# General sentiment
result = ts.analyze_sentiment("The product launch exceeded all expectations.")
print(result.label)       # positive
print(result.intensity)   # strong
print(result.polarity)    # 0.625

# Financial domain (detects bullish/bearish signals)
fin = ts.analyze_sentiment("Revenue surged 40% beating analyst estimates.", domain="financial")
print(fin.market_signal)  # bullish
print(fin.confidence)     # 0.92

# Tech news domain
tech = ts.analyze_sentiment("Critical vulnerability found in popular library.", domain="tech")
print(tech.market_signal)  # bearish
print(tech.label)          # negative
```

### Batch DataFrame Analysis

```python
import pandas as pd

headlines = pd.DataFrame({
    'headline': [
        "OpenAI releases new model beating GPT-4",
        "Tech stocks plunge amid regulatory fears",
        "Startup raises $50M Series B for AI platform",
        "Security breach affects millions of users",
    ]
})

result = ts.analyze_dataframe(headlines, text_col="headline", domain="financial")
print(result[['headline', 'sentiment_label', 'market_signal', 'polarity']])
```

---

## Direct Source Access

```python
from trendscout.sources.hackernews import HackerNewsSource
from trendscout.sources.rss import RSSFeedSource

# HackerNews
hn = HackerNewsSource()
stories = hn.search("python async", limit=5)
for s in stories:
    print(f"[{s.score}] {s.title}")

# RSS
rss = RSSFeedSource()
items = rss.fetch("https://feeds.hnrss.org/newest?points=100", limit=5)
for item in items:
    print(item.title)
```

---

## Full Intelligence Pipeline

```python
from trendscout import TrendScout

ts = TrendScout()
topics = ["AI agents", "edge computing", "Web3", "open source LLMs"]

# 1. Velocity comparison
report = ts.analyze_topics(topics)

# 2. Fetch real articles for the top trend
top_topic = report.iloc[0]['topic']
articles = ts.get_hackernews_trends(top_topic, limit=20)

# 3. Batch sentiment on the articles
enriched = ts.analyze_dataframe(articles, text_col="title", domain="tech")

# 4. Summary
bullish_count = (enriched['market_signal'] == 'bullish').sum()
print(f"Top trend: {top_topic}")
print(f"Velocity: {report.iloc[0]['velocity_score']:.2f} ({report.iloc[0]['status']})")
print(f"Positive articles: {bullish_count}/{len(enriched)}")
```

---

## License

MIT — [Teyfik Öz](https://github.com/teyfikoz)

# TrendScout

AI-Powered Market Trend Analysis & Sentiment.

[![PyPI version](https://badge.fury.io/py/trendscout.svg)](https://pypi.org/project/trendscout/)
[![CI](https://github.com/teyfikoz/trendscout/actions/workflows/ci.yml/badge.svg)](https://github.com/teyfikoz/trendscout/actions/workflows/ci.yml)

## Installation

```bash
pip install trendscout
```

## Quick Start

```python
from trendscout import TrendScout

ts = TrendScout()

# Analyze sentiment
result = ts.analyze_sentiment("The market is looking very strong today!")
print(result.label)       # "bullish"
print(result.polarity)    # 0.xx
print(result.confidence)  # 0.xx

# Get trending topics (mock data in current version)
trends = ts.get_emerging_trends(domain="technology", limit=5)
print(trends)
```

## Features

- **Sentiment Analysis** - TextBlob-based polarity and subjectivity scoring
- **Trend Scraping** - Mock data with extensible scraping framework
- **DataFrame Analysis** - Batch sentiment analysis on pandas DataFrames

## License

MIT

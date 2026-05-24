"""TrendScout — Multi-domain sentiment analysis (TextBlob + domain lexicons)."""
from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd
from textblob import TextBlob

# Domain-specific lexicons for financial/tech signal boosting
_BULLISH = {
    "surge", "soar", "rally", "boom", "outperform", "beat", "strong", "record",
    "profit", "gain", "breakout", "momentum", "accelerate", "growth", "bullish",
}
_BEARISH = {
    "crash", "fall", "plunge", "drop", "slump", "loss", "weak", "miss", "decline",
    "risk", "concern", "warning", "bearish", "correction", "layoffs", "downturn",
}


@dataclass
class SentimentResult:
    """Rich sentiment analysis result."""
    text: str
    polarity: float       # −1 to +1
    subjectivity: float   # 0 to 1
    label: str            # positive | negative | neutral
    intensity: str        # strong | moderate | weak
    market_signal: str    # bullish | bearish | neutral
    confidence: float     # 0 to 1

    def __str__(self) -> str:
        return (
            f"Sentiment : {self.label.upper()} ({self.intensity})\n"
            f"Signal    : {self.market_signal}\n"
            f"Polarity  : {self.polarity:+.3f}  |  Subjectivity: {self.subjectivity:.3f}\n"
            f"Confidence: {self.confidence:.1%}"
        )


class SentimentAnalyzer:
    """
    TextBlob-based sentiment analyzer with domain-aware lexicon boosting.

    Domains: 'general', 'financial', 'tech', 'social'
    """

    def analyze(self, text: str, domain: str = "general") -> dict:
        """
        Analyze sentiment and return a plain dict.

        Args:
            text: Input text
            domain: Context domain for lexicon boost

        Returns:
            Dict with polarity, subjectivity, label, intensity, market_signal, confidence
        """
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity

        if domain in ("financial", "tech"):
            polarity = self._boost(text, polarity)

        label = "positive" if polarity > 0.05 else ("negative" if polarity < -0.05 else "neutral")
        abs_p = abs(polarity)
        intensity = "strong" if abs_p >= 0.5 else ("moderate" if abs_p >= 0.2 else "weak")
        market_signal = "bullish" if polarity > 0.1 else ("bearish" if polarity < -0.1 else "neutral")
        confidence = round(min(1.0, 0.6 + abs_p * 0.4), 4)

        return {
            "polarity": round(polarity, 4),
            "subjectivity": round(subjectivity, 4),
            "label": label,
            "intensity": intensity,
            "market_signal": market_signal,
            "confidence": confidence,
        }

    def analyze_rich(self, text: str, domain: str = "general") -> SentimentResult:
        """Analyze and return a SentimentResult dataclass."""
        d = self.analyze(text, domain)
        return SentimentResult(
            text=text[:120] + ("…" if len(text) > 120 else ""),
            **d,
        )

    def analyze_dataframe(
        self,
        df: pd.DataFrame,
        text_col: str,
        domain: str = "general",
    ) -> pd.DataFrame:
        """
        Add sentiment columns to a DataFrame.

        Returns DataFrame with added columns:
        polarity, subjectivity, sentiment_label, sentiment_intensity, market_signal
        """
        df = df.copy()
        results = df[text_col].fillna("").apply(lambda t: self.analyze(str(t), domain))
        df["polarity"] = results.apply(lambda r: r["polarity"])
        df["subjectivity"] = results.apply(lambda r: r["subjectivity"])
        df["sentiment_label"] = results.apply(lambda r: r["label"])
        df["sentiment_intensity"] = results.apply(lambda r: r["intensity"])
        df["market_signal"] = results.apply(lambda r: r["market_signal"])
        return df

    def _boost(self, text: str, base: float) -> float:
        words = set(re.findall(r"\b\w+\b", text.lower()))
        boost = (len(words & _BULLISH) - len(words & _BEARISH)) * 0.08
        return max(-1.0, min(1.0, base + boost))

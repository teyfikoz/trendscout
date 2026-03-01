import pandas as pd
from textblob import TextBlob


class SentimentAnalyzer:
    """
    Analyzes sentiment of text data.
    """

    @staticmethod
    def analyze(text: str) -> dict:
        """Get sentiment score."""
        blob = TextBlob(text)
        return {
            "polarity": blob.sentiment.polarity,         # -1 to 1
            "subjectivity": blob.sentiment.subjectivity  # 0 to 1
        }

    def analyze_dataframe(self, df: pd.DataFrame, text_col: str) -> pd.DataFrame:
        """Add sentiment columns to dataframe."""
        df = df.copy()
        df['sentiment'] = df[text_col].apply(lambda x: self.analyze(x)['polarity'])
        df['subjectivity'] = df[text_col].apply(lambda x: self.analyze(x)['subjectivity'])

        # Classify
        def classify(score):
            if score > 0.1:
                return "Positive"
            if score < -0.1:
                return "Negative"
            return "Neutral"

        df['sentiment_label'] = df['sentiment'].apply(classify)
        return df

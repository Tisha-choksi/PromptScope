from dataclasses import dataclass
from enum import Enum
from typing import Optional

from app.services.extraction.entity_extractor import MentionCandidate


class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


@dataclass
class AnalyzedMention:
    text: str
    brand_id: int
    position: int
    rank: Optional[int]
    context: str
    sentiment: SentimentLabel
    confidence: float


class MentionAnalyzer:
    POSITIVE_WORDS = {
        "best", "great", "excellent", "top", "leading", "recommended",
        "popular", "trusted", "reliable", "outstanding", "superior",
        "innovative", "award", "preferred", "#1", "first", "winner",
    }
    NEGATIVE_WORDS = {
        "worst", "bad", "poor", "avoid", "unreliable", "expensive",
        "outdated", "failing", "controversial", "issues", "problems",
        "complaints", "negative", "inferior", "lacking",
    }

    def analyze_sentiment(self, context: str) -> tuple[SentimentLabel, float]:
        lower = context.lower()
        words = set(lower.split())

        positive_hits = len(words & self.POSITIVE_WORDS)
        negative_hits = len(words & self.NEGATIVE_WORDS)
        total_hits = positive_hits + negative_hits

        if total_hits == 0:
            return SentimentLabel.NEUTRAL, 0.5

        net = positive_hits - negative_hits
        # Confidence scales with the ratio of the dominant polarity
        dominant = max(positive_hits, negative_hits)
        confidence = min(1.0, dominant / max(total_hits, 1) * (1 + 0.1 * dominant))
        confidence = round(min(confidence, 1.0), 4)

        if net > 0:
            return SentimentLabel.POSITIVE, confidence
        if net < 0:
            return SentimentLabel.NEGATIVE, confidence
        return SentimentLabel.NEUTRAL, 0.5

    def analyze_mentions(
        self, candidates: list[MentionCandidate]
    ) -> list[AnalyzedMention]:
        analyzed: list[AnalyzedMention] = []
        for candidate in candidates:
            sentiment, confidence = self.analyze_sentiment(candidate.context)
            analyzed.append(
                AnalyzedMention(
                    text=candidate.text,
                    brand_id=candidate.brand_id,
                    position=candidate.position,
                    rank=candidate.rank,
                    context=candidate.context,
                    sentiment=sentiment,
                    confidence=confidence,
                )
            )
        return analyzed

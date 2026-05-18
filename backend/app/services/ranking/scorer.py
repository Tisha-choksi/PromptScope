from dataclasses import dataclass, field
from typing import Optional

from app.services.extraction.mention_analyzer import AnalyzedMention, SentimentLabel
from app.services.llm.base import LLMResponse


@dataclass
class BrandScore:
    brand_id: int
    brand_name: str
    mention_count: int
    avg_rank: Optional[float]
    first_rank: Optional[int]
    positive_mentions: int
    neutral_mentions: int
    negative_mentions: int
    visibility_score: float  # 0-100
    providers_mentioned_in: list[str] = field(default_factory=list)


class VisibilityScorer:
    MENTION_WEIGHT = 30.0
    RANK_WEIGHT = 40.0
    SENTIMENT_WEIGHT = 20.0
    COVERAGE_WEIGHT = 10.0

    def compute_score(
        self,
        mentions: list[AnalyzedMention],
        provider_responses: list[LLMResponse],
        brand_id: int,
        brand_name: str,
    ) -> BrandScore:
        brand_mentions = [m for m in mentions if m.brand_id == brand_id]

        mention_count = len(brand_mentions)
        positive_mentions = sum(
            1 for m in brand_mentions if m.sentiment == SentimentLabel.POSITIVE
        )
        neutral_mentions = sum(
            1 for m in brand_mentions if m.sentiment == SentimentLabel.NEUTRAL
        )
        negative_mentions = sum(
            1 for m in brand_mentions if m.sentiment == SentimentLabel.NEGATIVE
        )

        ranked_mentions = [m for m in brand_mentions if m.rank is not None]
        avg_rank: Optional[float] = None
        first_rank: Optional[int] = None
        if ranked_mentions:
            ranks = [m.rank for m in ranked_mentions]  # type: ignore[misc]
            avg_rank = sum(ranks) / len(ranks)
            first_rank = min(ranks)

        # Determine which providers mentioned this brand
        # Map provider responses by a positional index; we need to correlate
        # mentions back to providers. Because MentionCandidate/AnalyzedMention
        # doesn't carry a provider field directly, we re-extract per provider.
        providers_mentioned_in: list[str] = []
        for response in provider_responses:
            if response.success and response.response_text:
                text_lower = response.response_text.lower()
                if brand_name.lower() in text_lower:
                    providers_mentioned_in.append(response.provider)
        providers_mentioned_in = list(dict.fromkeys(providers_mentioned_in))  # deduplicate, preserve order

        total_providers = len([r for r in provider_responses if r.success])

        # --- Score components ---
        # Mention score: max 30 points
        mention_score = min(mention_count * 10, 30.0)

        # Rank score: max 40 points (rank 1 = 40, drops by 8 per rank position)
        rank_score = 0.0
        if avg_rank is not None:
            rank_score = max(0.0, self.RANK_WEIGHT - (avg_rank - 1) * 8)

        # Sentiment score: -20 to +20
        sentiment_score = 0.0
        if mention_count > 0:
            sentiment_score = (positive_mentions - negative_mentions) / mention_count * self.SENTIMENT_WEIGHT

        # Coverage score: max 10 points
        coverage_score = 0.0
        if total_providers > 0:
            coverage_score = (len(providers_mentioned_in) / total_providers) * self.COVERAGE_WEIGHT

        raw_score = mention_score + rank_score + sentiment_score + coverage_score
        visibility_score = round(max(0.0, min(100.0, raw_score)), 4)

        return BrandScore(
            brand_id=brand_id,
            brand_name=brand_name,
            mention_count=mention_count,
            avg_rank=avg_rank,
            first_rank=first_rank,
            positive_mentions=positive_mentions,
            neutral_mentions=neutral_mentions,
            negative_mentions=negative_mentions,
            visibility_score=visibility_score,
            providers_mentioned_in=providers_mentioned_in,
        )

    def rank_brands(self, brand_scores: list[BrandScore]) -> list[BrandScore]:
        return sorted(brand_scores, key=lambda b: b.visibility_score, reverse=True)

    def compute_all_brands(
        self,
        mentions: list[AnalyzedMention],
        responses: list[LLMResponse],
        brands: list[dict],
    ) -> list[BrandScore]:
        scores: list[BrandScore] = []
        for brand in brands:
            score = self.compute_score(
                mentions=mentions,
                provider_responses=responses,
                brand_id=brand["id"],
                brand_name=brand["name"],
            )
            scores.append(score)
        return self.rank_brands(scores)

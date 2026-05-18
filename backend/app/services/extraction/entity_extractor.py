import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class MentionCandidate:
    text: str
    brand_id: int
    brand_name: str
    position: int
    context: str  # surrounding 200 chars
    rank: Optional[int]  # extracted from numbered lists


# Patterns that indicate a rank immediately before a brand mention.
# Matches: "1.", "1)", "#1", "First:", "first" (up to 20 for sanity)
_RANK_WORD_MAP = {
    "first": 1,
    "second": 2,
    "third": 3,
    "fourth": 4,
    "fifth": 5,
    "sixth": 6,
    "seventh": 7,
    "eighth": 8,
    "ninth": 9,
    "tenth": 10,
}

_NUMERIC_RANK_RE = re.compile(r"(?:#\s*|(?:^|\n)\s*)(\d{1,2})[\.\)]\s*$", re.MULTILINE)
_HASH_RANK_RE = re.compile(r"#(\d{1,2})\s*$")
_WORD_RANK_RE = re.compile(
    r"\b(" + "|".join(_RANK_WORD_MAP.keys()) + r")[:\s]*$",
    re.IGNORECASE,
)


class EntityExtractor:
    def __init__(self, brands: list[dict]):
        # brands: list of {"id": int, "name": str, "aliases": list[str]}
        self.brands = brands
        self.patterns: dict[int, tuple[str, re.Pattern]] = {}
        self._build_pattern_map()

    def _build_pattern_map(self) -> None:
        for brand in self.brands:
            brand_id: int = brand["id"]
            brand_name: str = brand["name"]
            aliases: list[str] = brand.get("aliases") or []
            terms = [brand_name] + aliases
            # Sort longest first to avoid partial-match shadowing
            terms_sorted = sorted(terms, key=len, reverse=True)
            escaped = [re.escape(t) for t in terms_sorted]
            pattern_str = r"\b(?:" + "|".join(escaped) + r")\b"
            compiled = re.compile(pattern_str, re.IGNORECASE)
            self.patterns[brand_id] = (brand_name, compiled)

    def extract_mentions(self, text: str) -> list[MentionCandidate]:
        candidates: list[MentionCandidate] = []
        seen_spans: list[tuple[int, int]] = []

        for brand_id, (brand_name, pattern) in self.patterns.items():
            for match in pattern.finditer(text):
                start, end = match.start(), match.end()
                # Deduplicate overlapping matches
                if any(s <= start < e or s < end <= e for s, e in seen_spans):
                    continue
                seen_spans.append((start, end))
                context = self._get_context(text, start)
                rank = self._extract_rank_from_context(text, start)
                candidates.append(
                    MentionCandidate(
                        text=match.group(),
                        brand_id=brand_id,
                        brand_name=brand_name,
                        position=start,
                        context=context,
                        rank=rank,
                    )
                )

        candidates.sort(key=lambda c: c.position)
        return candidates

    def _extract_rank_from_context(self, text: str, position: int) -> Optional[int]:
        look_back = 50
        start = max(0, position - look_back)
        preceding = text[start:position]

        # Try numeric patterns: "1.", "1)", "#1"
        m = _NUMERIC_RANK_RE.search(preceding)
        if m:
            return int(m.group(1))

        m = _HASH_RANK_RE.search(preceding)
        if m:
            return int(m.group(1))

        # Try word ordinals
        m = _WORD_RANK_RE.search(preceding)
        if m:
            return _RANK_WORD_MAP.get(m.group(1).lower())

        return None

    def _get_context(self, text: str, position: int, window: int = 200) -> str:
        half = window // 2
        start = max(0, position - half)
        end = min(len(text), position + half)
        return text[start:end]

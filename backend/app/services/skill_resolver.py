"""Resolve free-text skill names to canonical names using the skill_aliases table.

This is the database-backed alias tier from the skills matching design. It uses
the same normalization rule as SkillMatcherService.normalize_skill, so results
match the current dictionary exactly (verified in tests/test_skill_resolver.py).
"""
from typing import Callable, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import SkillAlias
from app.services.skill_matcher_service import SKILL_NORMALIZATION


def normalize_text(skill: str) -> str:
    """Lowercase and trim, as the matcher has always done."""
    return skill.lower().strip()


def load_alias_map(db: Session) -> Dict[str, str]:
    """Load every alias once; resolve many skills against the returned map."""
    rows = db.query(SkillAlias.alias, SkillAlias.canonical_name).all()
    return {alias: canonical for alias, canonical in rows}


def resolve_skill(skill: str, alias_map: Dict[str, str]) -> str:
    """Return the canonical name for a free-text skill, or the normalized text if unknown."""
    key = normalize_text(skill)
    return alias_map.get(key, key)


# A semantic lookup takes a normalized skill name and returns the nearest canonical
# skill and its cosine similarity, or None if there is no candidate.
SemanticLookup = Callable[[str], Optional[Tuple[str, float]]]


def resolve_semantic(
    skill: str,
    alias_map: Dict[str, str],
    lookup: Optional[SemanticLookup],
    *,
    enabled: bool,
    accept: float,
    review: float,
) -> Optional[Tuple[str, str]]:
    """Semantic tier (design section 3). Returns (canonical_name, "accept" | "review") or None.

    Never overrides an alias or exact match: if the alias tier already resolves
    the skill, this returns None. Does nothing unless the feature flag is on.
    """
    if not enabled or lookup is None:
        return None
    key = normalize_text(skill)
    if key in alias_map:
        return None
    hit = lookup(key)
    if hit is None:
        return None
    canonical, similarity = hit
    if similarity >= accept:
        return canonical, "accept"
    if similarity >= review:
        return canonical, "review"
    return None


def seed_aliases(db: Session) -> int:
    """Insert the current SKILL_NORMALIZATION entries that are not yet in the table.

    Idempotent: existing aliases are left unchanged. Returns the number inserted.
    """
    existing = {row[0] for row in db.query(SkillAlias.alias).all()}
    inserted = 0
    for alias, canonical in SKILL_NORMALIZATION.items():
        if alias in existing:
            continue
        db.add(SkillAlias(alias=alias, canonical_name=canonical, source="seed"))
        inserted += 1
    db.flush()
    return inserted

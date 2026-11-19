"""Semantic tier rules: off by default, thresholds respected, aliases never overridden."""
from app.config import Settings
from app.services.skill_resolver import resolve_semantic


def _lookup(canonical, similarity):
    return lambda key: (canonical, similarity)


def test_semantic_matching_is_disabled_by_default():
    assert Settings().SKILL_SEMANTIC_MATCHING_ENABLED is False
    assert Settings().SKILL_SEMANTIC_ACCEPT == 0.60
    assert Settings().SKILL_SEMANTIC_REVIEW == 0.50


def test_disabled_flag_ignores_semantic_hits():
    result = resolve_semantic(
        "terraformer",
        {},
        _lookup("terraform", 0.99),
        enabled=False,
        accept=0.60,
        review=0.50,
    )
    assert result is None


def test_enabled_accepts_at_or_above_accept_threshold():
    result = resolve_semantic(
        "terraformer",
        {},
        _lookup("terraform", 0.60),
        enabled=True,
        accept=0.60,
        review=0.50,
    )
    assert result == ("terraform", "accept")


def test_enabled_marks_review_band():
    result = resolve_semantic(
        "terraformer",
        {},
        _lookup("terraform", 0.55),
        enabled=True,
        accept=0.60,
        review=0.50,
    )
    assert result == ("terraform", "review")


def test_enabled_rejects_below_review_threshold():
    result = resolve_semantic(
        "terraformer",
        {},
        _lookup("terraform", 0.49),
        enabled=True,
        accept=0.60,
        review=0.50,
    )
    assert result is None


def test_alias_match_is_never_overridden_by_semantic_tier():
    alias_map = {"k8s": "kubernetes"}
    result = resolve_semantic(
        "k8s",
        alias_map,
        _lookup("docker", 0.95),
        enabled=True,
        accept=0.60,
        review=0.50,
    )
    assert result is None


def test_no_lookup_returns_none():
    assert (
        resolve_semantic(
            "anything",
            {},
            None,
            enabled=True,
            accept=0.60,
            review=0.50,
        )
        is None
    )

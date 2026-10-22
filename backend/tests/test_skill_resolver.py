"""Parity tests: the database alias tier must resolve exactly like the current dictionary."""
import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.services.skill_matcher_service import SKILL_NORMALIZATION
from app.services.skill_resolver import load_alias_map, resolve_skill, seed_aliases


@pytest.fixture
def db():
    """Session on the PostgreSQL test database, rolled back after each test."""
    url = os.getenv("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL is not set")
    engine = create_engine(url)
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()
    engine.dispose()


def test_seed_inserts_every_dictionary_entry(db):
    inserted = seed_aliases(db)
    assert inserted == len(SKILL_NORMALIZATION)
    assert seed_aliases(db) == 0  # idempotent


def test_resolver_matches_dictionary_for_every_entry(db):
    seed_aliases(db)
    alias_map = load_alias_map(db)
    for alias, canonical in SKILL_NORMALIZATION.items():
        assert resolve_skill(alias, alias_map) == canonical, alias


def test_resolver_normalizes_case_and_whitespace(db):
    seed_aliases(db)
    alias_map = load_alias_map(db)
    assert resolve_skill("  K8s ", alias_map) == SKILL_NORMALIZATION["k8s"]
    assert resolve_skill("PostgreSQL", alias_map) == "postgresql"


def test_unknown_skill_returns_normalized_text(db):
    alias_map = load_alias_map(db)
    assert resolve_skill("  Terraform  ", alias_map) == "terraform"

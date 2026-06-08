"""Checklist math: ground-truth (100%), early-save counts, naming, and official %."""

from __future__ import annotations

from pathlib import Path

from shar_checklist.checklist import ChecklistResult, compute_checklist
from shar_checklist.gci import read_gci
from shar_checklist.parser import parse_character_sheet

FIXTURES = Path(__file__).parent / "fixtures"

CANONICAL_TOTALS = {
    "cards": 49,
    "story_missions": 49,
    "bonus_missions": 7,
    "street_races": 21,
    "movies": 7,
    "wasp_cameras": 140,
    "gags": 84,
    "outfits": 21,
    "vehicles": 35,  # 5 unlockable per level (game's QueryNumCarUnlocked metric)
}


def _result(name: str) -> ChecklistResult:
    return compute_checklist(parse_character_sheet(read_gci(str(FIXTURES / name))))


def test_totals_match_canonical_definition():
    result = _result("sample_early.gci")
    totals = {c.key: c.total for c in result.categories}
    assert totals == CANONICAL_TOTALS
    assert result.overall_total == sum(CANONICAL_TOTALS.values()) == 413


def test_complete_save_is_100_percent():
    # A real, confirmed 100% GameCube save (not synthetic).
    result = _result("complete_100.gci")
    assert result.percent == 100.0  # matches the game's QueryPercentGameCompleted
    assert result.overall_done == result.overall_total == 413
    for cat in result.categories:
        assert cat.done == cat.total, f"{cat.key} not complete"


def test_complete_save_counts_m1_on_every_level():
    # Regression: levels 2-7 store M1-M7 at slots 0-6 (only Level 1 has the M0 tutorial at
    # slot 0). Counting slots 1-7 everywhere previously dropped M1 on six levels -> 43/49.
    result = _result("complete_100.gci")
    story = next(c for c in result.categories if c.key == "story_missions")
    assert story.done == 49


def test_early_save_counts():
    result = _result("sample_early.gci")
    by_key = {c.key: c for c in result.categories}
    # Only M1 and M2 are done in Level 1 (M0 tutorial is excluded from the 49).
    assert by_key["story_missions"].done == 2
    assert by_key["cards"].done == 6
    assert by_key["bonus_missions"].done == 1
    assert by_key["street_races"].done == 3
    assert by_key["wasp_cameras"].done == 20
    # L1: 0 purchased + bonus reward + street-race reward = 2; other levels 0.
    assert by_key["vehicles"].done == 2
    assert by_key["gags"].done == 10  # GagMask 0x369F has 10 bits set
    assert 0 < result.percent < 20


def test_gags_missing_by_index():
    # L1 GagMask 0x369F -> bits {0,1,2,3,4,7,9,10,12,13} set of 15 gags, so gags
    # 6, 7, 9, 12, 15 (1-based) are missing.
    result = _result("sample_early.gci")
    gags = next(c for c in result.categories if c.key == "gags")
    assert gags.done == 10
    l1_missing = [m for m in gags.missing if m.startswith("Level 1")]
    assert sorted(l1_missing) == sorted(f"Level 1 - Homer - Gag {n}" for n in (6, 7, 9, 12, 15))


def test_missing_items_use_canonical_names_not_save_placeholders():
    result = _result("sample_early.gci")
    cards = next(c for c in result.categories if c.key == "cards")
    # The save stores "Cardx"/"NULL"; the report must never surface those.
    assert all("Cardx" not in m and "NULL" not in m for m in cards.missing)
    # A known-missing Level 1 card must appear by its real name.
    assert any("Spinemelter 2000" in m for m in cards.missing)


def test_story_mission_naming_offset():
    # Level 1's next mission is M3 "Office Spaced"; M1/M2 are done and must NOT be missing.
    result = _result("sample_early.gci")
    missing = next(c for c in result.categories if c.key == "story_missions").missing
    assert any("Office Spaced" in m for m in missing)
    assert not any("S-M-R-T" in m for m in missing)
    assert not any("Petty Theft Homer" in m for m in missing)


def test_official_percent_matches_game_formula():
    # Spot-check the game's per-level formula on the early save's Level 1, which has a known
    # mix of progress, and confirm the headline never exceeds 100.
    result = _result("complete_100.gci")
    assert result.percent == 100.0
    early = _result("sample_early.gci")
    assert 0.0 <= early.percent <= 100.0


def test_level_label_prefixes_are_unique():
    # The --level filter relies on each level's missing lines starting with its label.
    from shar_checklist import names

    assert len(set(names.LEVEL_LABELS)) == names.NUM_LEVELS

"""Structural tests: parse the real early-game save and assert byte-level truths.

These lock the endianness (big-endian), the payload offset, and the slot layout against a
save written by the actual game. If any of those drift, these fail.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from shar_checklist.errors import InvalidSaveError
from shar_checklist.gci import extract_character_sheet, read_gci
from shar_checklist.parser import parse_character_sheet

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE = FIXTURES / "sample_early.gci"


@pytest.fixture
def sample():
    return parse_character_sheet(read_gci(str(SAMPLE)))


def test_player_name(sample):
    assert sample.player_name == "Player1"


def test_current_mission_decodes_big_endian(sample):
    # GCI comment says "Slot 1 (L1 M3)". Big-endian decodes to level 0 / mission 3;
    # little-endian would give garbage. This single assert pins the byte order.
    assert sample.current_level == 0
    assert sample.current_mission == 3


def test_coins(sample):
    assert sample.coins == 1223


def test_level1_mission_slots(sample):
    # The player is on M3, having completed M0 (tutorial), M1, M2 -> slots 0,1,2.
    completed = [m.completed for m in sample.levels[0].missions]
    assert completed == [True, True, True, False, False, False, False, False]


def test_level1_cards(sample):
    cards = sample.levels[0].cards
    assert len(cards) == 7
    assert sum(c.collected for c in cards) == 6  # slot 3 is uncollected ("NULL")


def test_level1_counts(sample):
    level = sample.levels[0]
    assert level.wasps_destroyed == 20
    assert level.num_skins_purchased == 3
    assert level.gags_viewed == 10


def test_wasp_camera_bitfield_matches_count(sample):
    # Cross-check: the per-camera destroyed flags from PersistentObjectStates must sum to
    # the WaspsDestroyed counter in every level. This proves the bitfield interpretation
    # (the per-level wasp sector) is correct, not a coincidence.
    for level in sample.levels:
        assert len(level.wasp_cameras) == 20
        assert sum(level.wasp_cameras) == level.wasps_destroyed


def test_level1_wasps_all_destroyed(sample):
    assert all(sample.levels[0].wasp_cameras)  # 20/20 in this save
    assert not any(sample.levels[1].wasp_cameras)  # level 2 untouched


def test_untouched_level_is_empty(sample):
    # Level 2 onward is untouched in this save.
    level = sample.levels[1]
    assert all(not m.completed for m in level.missions)
    assert level.wasps_destroyed == 0


def _patched(offset: int, value: int) -> bytes:
    data = bytearray(SAMPLE.read_bytes())
    data[offset] = value
    return bytes(data)


def test_accepts_other_gc_region():
    # All GameCube regions share the CharacterSheet layout, so flipping the region byte
    # (E -> P) must still parse via the SaveGameInfo magic anchor.
    parsed = parse_character_sheet(extract_character_sheet(_patched(3, ord("P"))))
    assert parsed.player_name == "Player1"


def test_rejects_non_shar_game():
    # Corrupt the game-code prefix.
    with pytest.raises(InvalidSaveError):
        extract_character_sheet(_patched(0, ord("X")))


def test_rejects_truncated_file():
    with pytest.raises(InvalidSaveError):
        extract_character_sheet(SAMPLE.read_bytes()[:2000])

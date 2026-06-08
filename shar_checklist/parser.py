"""Parse a flat CharacterSheet blob into the typed :mod:`model`.

This is a near-literal port of SHARMemory's sequential ``FromBytes`` readers
(``CharacterSheet.cs``, ``LevelRecord.cs``, ``MissionRecord.cs``, ``Record.cs``), reading
big-endian instead of little-endian. Field order and sizes are taken verbatim from those
structs, so no offset is hand-computed: we read a field and the cursor advances.

Layout reference (per level, 620 bytes):
    cards: 7 x 17-byte Record         (119)   + 1 padding byte
    missions: 8 x 32-byte MissionRecord (256)
    street races: 3 x 32-byte          (96)
    bonus mission: 32, gamble race: 32
    FMVUnlocked: bool read then +4 (4-byte aligned)
    NumCarsPurchased, NumSkinsPurchased, WaspsDestroyed: int32 each
    CurrentSkin: 16-byte string
    GagsViewed: int32, GagMask: uint32
    Gags: 32 bools, PurchasedRewards: 12 bools
"""

from __future__ import annotations

from .gci import LEVEL_RECORD_SIZE, MAX_LEVELS
from .model import Card, Level, Mission, SaveData
from .structs import Reader

MAX_CARDS = 7
MAX_MISSIONS = 8
MAX_STREET_RACES = 3
MAX_LEVEL_GAGS = 32
MAX_PURCHASED_ITEMS = 12

# Globals that follow the level array in the CharacterSheet.
CAR_INVENTORY_SIZE = 60 * 24 + 4  # 60 cars * 24 bytes + int32 counter
PERSISTENT_OBJECT_STATES_SIZE = 1312  # 82 sectors * 16 bytes (128 bits each)

# PersistentObjectStates sector layout. The first 75 sectors are per-room/zone breakables
# (crates and scenery, not individually labelled); the last 7 are the wasp cameras, one
# sector per level, 20 cameras each. A bit value of 0 means that object is destroyed.
WASP_SECTOR_BASE = 75  # index of the "Level1" sector
WASPS_PER_LEVEL = 20
SECTOR_SIZE = 16


def _wasp_cameras(persistent_states: bytes, level_index: int) -> list[bool]:
    """Return the 20 wasp-camera destroyed flags for a level (True == destroyed)."""
    sector = (WASP_SECTOR_BASE + level_index) * SECTOR_SIZE
    cameras = []
    for i in range(WASPS_PER_LEVEL):
        byte = persistent_states[sector + i // 8]
        destroyed = (byte & (1 << (i % 8))) == 0
        cameras.append(destroyed)
    return cameras


def _read_mission(reader: Reader) -> Mission:
    name = reader.string(16)
    completed = reader.bool8()  # offset +16
    bonus_objective = reader.bool8()  # +17
    reader.skip(2)  # remainder of the 4-byte block holding the two bools
    num_attempts = reader.u32()  # +20
    skipped = reader.bool8()  # +24
    reader.skip(3)
    best_time = reader.i32()  # +28
    return Mission(
        name=name,
        completed=completed,
        bonus_objective=bonus_objective,
        num_attempts=num_attempts,
        skipped=skipped,
        best_time=best_time,
    )


def _read_card(reader: Reader) -> Card:
    name = reader.string(16)
    collected = reader.bool8()
    return Card(name=name, collected=collected)


def _read_level(reader: Reader) -> Level:
    start = reader.offset
    cards = [_read_card(reader) for _ in range(MAX_CARDS)]
    reader.skip(1)  # padding byte after the card list

    missions = [_read_mission(reader) for _ in range(MAX_MISSIONS)]
    street_races = [_read_mission(reader) for _ in range(MAX_STREET_RACES)]
    bonus_mission = _read_mission(reader)
    gamble_race = _read_mission(reader)

    fmv_unlocked = reader.bool8()
    reader.skip(3)  # FMVUnlocked is a bool stored in a 4-byte slot
    num_cars_purchased = reader.i32()
    num_skins_purchased = reader.i32()
    wasps_destroyed = reader.i32()
    current_skin = reader.string(16)
    gags_viewed = reader.i32()
    gag_mask = reader.u32()
    gags = [reader.bool8() for _ in range(MAX_LEVEL_GAGS)]
    purchased_rewards = [reader.bool8() for _ in range(MAX_PURCHASED_ITEMS)]

    consumed = reader.offset - start
    assert consumed == LEVEL_RECORD_SIZE, (
        f"level record consumed {consumed} bytes, expected {LEVEL_RECORD_SIZE} "
        "(struct layout drift)"
    )

    return Level(
        cards=cards,
        missions=missions,
        street_races=street_races,
        bonus_mission=bonus_mission,
        gamble_race=gamble_race,
        fmv_unlocked=fmv_unlocked,
        num_cars_purchased=num_cars_purchased,
        num_skins_purchased=num_skins_purchased,
        wasps_destroyed=wasps_destroyed,
        current_skin=current_skin,
        gags_viewed=gags_viewed,
        gag_mask=gag_mask,
        gags=gags,
        purchased_rewards=purchased_rewards,
    )


def parse_character_sheet(blob: bytes) -> SaveData:
    """Parse the flat CharacterSheet bytes (from :func:`gci.extract_character_sheet`)."""
    reader = Reader(blob)
    player_name = reader.string(16)
    levels = [_read_level(reader) for _ in range(MAX_LEVELS)]

    current_level = reader.i32()
    current_mission = reader.i32()
    highest_level = reader.i32()
    highest_mission = reader.i32()
    nav_system_enabled = reader.bool8()
    reader.skip(3)
    coins = reader.i32()

    # Skip the CarInventory (60 cars + counter), then read the PersistentObjectStates
    # bitfield, which holds per-object "destroyed" state for every breakable in the world
    # (this is what makes them not respawn on load). The last 7 sectors hold the wasp
    # cameras, 20 per level.
    reader.skip(CAR_INVENTORY_SIZE)
    persistent_states = reader.bytes(PERSISTENT_OBJECT_STATES_SIZE)
    for level_index, level in enumerate(levels):
        level.wasp_cameras = _wasp_cameras(persistent_states, level_index)

    return SaveData(
        player_name=player_name,
        levels=levels,
        current_level=current_level,
        current_mission=current_mission,
        highest_level=highest_level,
        highest_mission=highest_mission,
        nav_system_enabled=nav_system_enabled,
        coins=coins,
    )

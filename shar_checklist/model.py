"""Typed data model for a parsed SHAR save.

These dataclasses are the seam between byte parsing and everything downstream: the
checklist and report never touch raw bytes, and a future PC-save reader only needs to
produce a :class:`SaveData`.

Indexing convention: levels and mission/card slots are stored **0-indexed** internally
(level 0 == "Level 1", per SHARMemory's ``LevelEnum``). Display code adds 1.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Mission:
    """A story mission, street race, bonus mission, or gamble race (32-byte record)."""

    name: str
    completed: bool
    bonus_objective: bool
    num_attempts: int
    skipped: bool
    best_time: int  # milliseconds, or -1 (0xFFFFFFFF) when never completed


@dataclass
class Card:
    """A collector card slot (17-byte record)."""

    name: str
    collected: bool


@dataclass
class Level:
    """One level's progress (a 620-byte LevelRecord)."""

    cards: list[Card]
    missions: list[Mission]  # 8 slots; slot i == mission Mi (slot 0 = M0 tutorial)
    street_races: list[Mission]  # 3
    bonus_mission: Mission
    gamble_race: Mission
    fmv_unlocked: bool
    num_cars_purchased: int
    num_skins_purchased: int  # outfits/costumes
    wasps_destroyed: int  # wasp cameras
    current_skin: str
    gags_viewed: int  # number of gags collected in this level
    gag_mask: int
    gags: list[bool] = field(default_factory=list)  # 32-slot bool array
    purchased_rewards: list[bool] = field(default_factory=list)  # 12-slot bool array
    # Per-wasp-camera destroyed state (True == destroyed/collected), 20 per level.
    # Sourced from the CharacterSheet's PersistentObjectStates bitfield, not the LevelRecord.
    wasp_cameras: list[bool] = field(default_factory=list)


@dataclass
class SaveData:
    """A full parsed CharacterSheet."""

    player_name: str
    levels: list[Level]
    current_level: int
    current_mission: int
    highest_level: int
    highest_mission: int
    nav_system_enabled: bool
    coins: int

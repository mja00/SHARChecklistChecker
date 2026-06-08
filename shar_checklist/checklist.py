"""Compute 100%-completion progress from a parsed :class:`SaveData`.

Each category yields a done/total count. "Named" categories (cards, story missions,
bonus missions, street races, movies) also list the specific remaining items; "count"
categories (wasp cameras, gags, outfits, vehicles) list per-level remaining counts since
the save does not expose reliable per-item names for them.

The gamble/wager race is intentionally excluded — it is not part of the in-game 100%.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from . import names
from .model import Level, SaveData


@dataclass
class CategoryResult:
    key: str
    label: str
    done: int
    total: int
    named: bool  # True if `missing` holds item names; False if per-level count lines
    missing: list[str] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return self.done >= self.total


@dataclass
class ChecklistResult:
    player_name: str
    current_level: int  # 1-indexed for display
    current_mission: int
    coins: int
    categories: list[CategoryResult]
    # The game's own completion percentage (see _game_percent), so this matches the value
    # shown on the in-game stats screen rather than a naive item ratio.
    percent: float

    @property
    def overall_done(self) -> int:
        return sum(c.done for c in self.categories)

    @property
    def overall_total(self) -> int:
        return sum(c.total for c in self.categories)

    def to_dict(self) -> dict:
        return {
            "player_name": self.player_name,
            "current_level": self.current_level,
            "current_mission": self.current_mission,
            "coins": self.coins,
            "percent": round(self.percent, 2),
            "items_done": self.overall_done,
            "items_total": self.overall_total,
            "categories": [asdict(c) for c in self.categories],
        }


def _named_per_slot(
    key: str,
    label: str,
    levels: list[Level],
    is_done,
    name_for,
) -> CategoryResult:
    """Build a category whose items are named per (level, slot).

    ``is_done`` is called as ``is_done(level, slot, lvl)`` so callbacks can vary their
    slot mapping by level (the story-missions category needs this).
    """
    done = 0
    total = 0
    missing: list[str] = []
    for lvl, level in enumerate(levels):
        for slot, item_name in enumerate(name_for(lvl)):
            total += 1
            if is_done(level, slot, lvl):
                done += 1
            else:
                missing.append(f"{names.LEVEL_LABELS[lvl]} - {item_name}")
    return CategoryResult(key=key, label=label, done=done, total=total, named=True, missing=missing)


def _count_category(
    key: str,
    label: str,
    levels: list[Level],
    per_level_total: list[int],
    value_for,
) -> CategoryResult:
    """Build a count-only category (no per-item names), clamped per level."""
    done = 0
    total = 0
    missing: list[str] = []
    for lvl, level in enumerate(levels):
        cap = per_level_total[lvl]
        got = min(max(value_for(level), 0), cap)
        total += cap
        done += got
        if got < cap:
            missing.append(f"{names.LEVEL_LABELS[lvl]} - {cap - got} of {cap} remaining")
    return CategoryResult(
        key=key, label=label, done=done, total=total, named=False, missing=missing
    )


def _all_street_races_done(level: Level) -> bool:
    return all(r.completed for r in level.street_races)


def _cars_unlocked(level: Level) -> int:
    """Vehicles unlocked for a level, per the game's QueryNumCarUnlocked: purchased cars
    plus the bonus-mission reward car plus the street-race reward car (5 max)."""
    return (
        level.num_cars_purchased
        + (1 if level.bonus_mission.completed else 0)
        + (1 if _all_street_races_done(level) else 0)
    )


def _story_missions_done(level: Level, lvl: int) -> int:
    """Completed story missions (M1-M7). Only Level 1 has the M0 tutorial at slot 0."""
    offset = 1 if lvl == 0 else 0
    return sum(level.missions[offset + i].completed for i in range(names.STORY_MISSIONS_PER_LEVEL))


def _game_percent(save: SaveData) -> float:
    """Replicate the game's QueryPercentGameCompleted exactly.

    Per level, eight categories each contribute an equal 1/8 share: missions/7, bonus,
    street-races/3, skins/3, cars/5, cards/7, wasps/total, gags/total. The game percentage
    is the average of the seven level percentages scaled to 99%, plus 1% for the Level 3
    bonus movie. (Source: charactersheetmanager.cpp.)
    """
    level_pcts = []
    for lvl, level in enumerate(save.levels):
        missions = _story_missions_done(level, lvl) / names.STORY_MISSIONS_PER_LEVEL
        bonus = 1.0 if level.bonus_mission.completed else 0.0
        races = sum(r.completed for r in level.street_races) / names.STREET_RACES_PER_LEVEL
        skins = (
            min(level.num_skins_purchased, names.OUTFITS_PER_LEVEL[lvl])
            / names.OUTFITS_PER_LEVEL[lvl]
        )
        cars = min(_cars_unlocked(level), names.CARS_PER_LEVEL) / names.CARS_PER_LEVEL
        cards = sum(c.collected for c in level.cards) / names.CARDS_PER_LEVEL
        wasps = level.wasps_destroyed / names.WASPS_PER_LEVEL[lvl]
        gags = level.gags_viewed / names.GAGS_PER_LEVEL[lvl]
        level_pcts.append((missions + bonus + races + skins + cars + cards + wasps + gags) / 8)

    average = sum(level_pcts) / names.NUM_LEVELS
    fmv_bonus = 1.0 if save.levels[2].fmv_unlocked else 0.0  # Level 3 bonus movie = 1%
    return min(100.0, average * 100.0 * 0.99 + fmv_bonus)


def compute_checklist(save: SaveData) -> ChecklistResult:
    levels = save.levels
    categories = [
        _named_per_slot(
            "cards",
            "Collector Cards",
            levels,
            is_done=lambda level, slot, lvl: level.cards[slot].collected,
            name_for=lambda lvl: names.CARD_NAMES[lvl],
        ),
        _named_per_slot(
            "story_missions",
            "Story Missions",
            levels,
            # The 7 counted story missions are M1-M7. Only Level 1 has the M0 tutorial
            # (The Cola Caper) at slot 0, pushing its M1-M7 to slots 1-7; levels 2-7 have
            # no tutorial, so their M1-M7 sit at slots 0-6 (slot 7 is unused).
            is_done=lambda level, slot, lvl: (
                level.missions[slot + (1 if lvl == 0 else 0)].completed
            ),
            name_for=lambda lvl: names.MISSION_NAMES[lvl],
        ),
        _named_per_slot(
            "bonus_missions",
            "Bonus Missions",
            levels,
            is_done=lambda level, slot, lvl: level.bonus_mission.completed,
            name_for=lambda lvl: [names.BONUS_MISSION_NAMES[lvl]],
        ),
        _named_per_slot(
            "street_races",
            "Street Races",
            levels,
            is_done=lambda level, slot, lvl: level.street_races[slot].completed,
            name_for=lambda lvl: [
                f"Street Race {i + 1}" for i in range(names.STREET_RACES_PER_LEVEL)
            ],
        ),
        _named_per_slot(
            "movies",
            "Movies",
            levels,
            is_done=lambda level, slot, lvl: level.fmv_unlocked,
            name_for=lambda lvl: ["Movie"],
        ),
        _named_per_slot(
            "wasp_cameras",
            "Wasp Cameras",
            levels,
            # Per-camera destroyed state from PersistentObjectStates. No in-game names, so
            # label by 1-based index within the level.
            is_done=lambda level, slot, lvl: level.wasp_cameras[slot],
            name_for=lambda lvl: [
                f"Wasp Camera {i + 1}" for i in range(names.WASPS_PER_LEVEL[lvl])
            ],
        ),
        _named_per_slot(
            "gags",
            "Gags",
            levels,
            # GagMask is a per-gag bitmask: bit i == gag i collected. The save has no gag
            # display names, so we label by 1-based index (matches the in-game gag order).
            is_done=lambda level, slot, lvl: bool(level.gag_mask & (1 << slot)),
            name_for=lambda lvl: [f"Gag {i + 1}" for i in range(names.GAGS_PER_LEVEL[lvl])],
        ),
        _count_category(
            "outfits",
            "Outfits",
            levels,
            names.OUTFITS_PER_LEVEL,
            value_for=lambda level: level.num_skins_purchased,
        ),
        _count_category(
            "vehicles",
            "Vehicles",
            levels,
            [names.CARS_PER_LEVEL] * names.NUM_LEVELS,
            value_for=_cars_unlocked,
        ),
    ]
    return ChecklistResult(
        player_name=save.player_name,
        current_level=save.current_level + 1,
        current_mission=save.current_mission,
        coins=save.coins,
        categories=categories,
        percent=_game_percent(save),
    )

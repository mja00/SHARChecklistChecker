# SHAR Checklist Checker

Read a *The Simpsons: Hit & Run* (SHAR) **GameCube** save and report which 100%-completion
checklist items are done and which remain — per category, with a named breakdown of the
specific cards, missions, and races still to do, and an overall completion percentage.

The well-known [SHARChecklist](https://github.com/Hampo/SHARChecklist) tool reads the
running game's live memory (Windows only). This tool instead parses a static save file, so
you can drop in a Dolphin `.gci` and see what's left without launching the game.

## Install

```sh
uv sync
```

## Usage

```sh
# Full report (summary + remaining items)
uv run shar-checklist path/to/save.gci

# Machine-readable output
uv run shar-checklist path/to/save.gci --json

# Just the summary table
uv run shar-checklist path/to/save.gci --no-missing

# Only one level's remaining items, or only some categories
uv run shar-checklist path/to/save.gci --level 3
uv run shar-checklist path/to/save.gci --category cards,gags

# Also runnable as a module
python -m shar_checklist path/to/save.gci
```

Category keys: `cards`, `story_missions`, `bonus_missions`, `street_races`, `movies`,
`wasp_cameras`, `gags`, `outfits`, `vehicles`.

## What it tracks

| Category | Total | Per-item names? |
|---|---|---|
| Collector cards | 49 | yes |
| Story missions | 49 | yes |
| Bonus missions | 7 | yes |
| Street races | 21 | by slot |
| Movies (FMVs) | 7 | by level |
| Wasp cameras | 140 | by index |
| Gags | 84 | by name |
| Outfits | 21 | by name |
| Vehicles | 35 | by name |

The headline completion percentage replicates the game's own `QueryPercentGameCompleted`
(each level is 8 equally-weighted categories; levels are 99% of the total and the Level 3
bonus movie is the last 1%), so it matches the number shown on the in-game stats screen.

The gamble/wager race (1 per level) is parsed but excluded, matching the in-game
completion definition.

## Scope and notes

- **GameCube `.gci` only.** All GameCube regions (`GHQE` NTSC-U, `GHQP` PAL, `GHQJ` NTSC-J)
  share the same save layout, so any GameCube SHAR save is accepted; the payload is located
  by the `SaveGameInfo` magic header, which absorbs region-specific banner/icon sizes. PAL/JP
  support is based on the game source but has only been tested against NTSC-U saves.
- The save stores only generic placeholder names (`Cardx`, `m0`, …), so display names come
  from canonical tables in `shar_checklist/names.py` — edit that file to fix a name or
  adjust a total.
- Every category is reported **per item**. Cards, missions, bonus missions, and movies come
  from curated tables (verified against the game's `cards.h` / text bible / mission scripts).
  Gags use the `GagMask` bitmask, named from each level's `level.mfk` (gag bit `N` = the
  `N`-th persistent gag in the script). Vehicles and outfits use the `PurchasedRewards` bits
  (`[0..2]` = the 3 purchasable cars, `[3..5]` = the 3 skins) plus the bonus/street-race
  reward cars, named from `rewards.mfk` + the car `.con` scripts. Wasp cameras use the
  `PersistentObjectStates` destruction bits, labelled by 1-based index (no script names).
- Vehicles use the game's own per-level completion metric (3 purchasable + bonus reward +
  street-race reward = 5 per level, 35 total), not the raw global car inventory.
- **Cola crates / vending machines are not tracked.** They are generic "object breakables"
  recorded in `PersistentObjectStates` by *load order* (the game's `PersistentWorldManager`
  stores no object type or ID — its own code resorts to sniffing the break sound to guess
  whether something is a crate). Unlike wasp cameras they have no dedicated counter, and
  they sit anonymously among ~170 other destructibles per level. Identifying them would
  require parsing each level's Pure3D files and replaying the exact load order — out of
  scope, and not derivable from the save alone.

## Format reference

The GameCube save is a flat, big-endian dump of the in-memory `CharacterSheet`. Layout is
ported from [Hampo/SHARMemory](https://github.com/Hampo/SHARMemory) (C# struct definitions)
and cross-referenced with [occanowey/share](https://github.com/occanowey/share). Names and
totals are compiled from the Simpsons Wiki and community completion guides.

Test fixtures: `tests/fixtures/sample_early.gci` is an early-game save (player `Player1`)
for structural tests; `tests/fixtures/complete_100.gci` is a real, confirmed 100% save used
as the ground-truth for the done-counting math.

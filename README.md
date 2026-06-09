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
| Outfits | 21 | count only |
| Vehicles | 35 | count only |

The headline completion percentage replicates the game's own `QueryPercentGameCompleted`
(each level is 8 equally-weighted categories; levels are 99% of the total and the Level 3
bonus movie is the last 1%), so it matches the number shown on the in-game stats screen.

The gamble/wager race (1 per level) is parsed but excluded, matching the in-game
completion definition.

## Scope and notes

- **GameCube `.gci` (NTSC-U / `GHQE`) only** for v1. PAL/JP saves are rejected with a clear
  message; the parser core is format-agnostic so other platforms can be added later.
- The save stores only generic placeholder names (`Cardx`, `m0`, …), so display names come
  from a canonical table in `shar_checklist/names.py` — edit that file to fix a name or
  adjust a total.
- Cards, missions, races, movies, **gags**, and **wasp cameras** are reported per item.
  Gags use the save's `GagMask` bitmask, named from each level's `level.mfk` script (the
  game assigns gag bit `N` to the `N`-th persistent gag defined in the script). Wasp cameras
  use the per-object destruction state in `PersistentObjectStates` (the same data that stops
  them respawning on load), labelled by 1-based index since they have no script names.
- Outfits are count-only per level (`NumSkinsPurchased`). Vehicles use the game's own
  per-level metric — purchased cars + the bonus-mission reward + the street-race reward,
  5 per level (35 total) — not the raw global car inventory.
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

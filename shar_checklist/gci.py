"""Locate the CharacterSheet payload inside a Dolphin GameCube ``.gci`` save.

A ``.gci`` is a 64-byte DEntry header followed by the raw memory-card save data
(comment block, banner/icon images, then the game's save payload). SHAR's payload is a
*flat* dump of the in-memory ``CharacterSheet`` (verified empirically: integers decode
sanely at flat offsets with no interspersed CRC chunks — unlike the PC save container).

The CharacterSheet begins after the fixed-size banner/icon image data, which is constant
for a given game version, so a single offset works in practice. We still validate the
located offset with a sentinel and fall back to scanning, so we never silently parse
misaligned data.
"""

from __future__ import annotations

from .errors import InvalidSaveError

# SHAR GameCube game codes: "GHQ" + region byte.
SHAR_GAME_PREFIX = b"GHQ"
REGION_NAMES = {ord("E"): "NTSC-U (USA)", ord("P"): "PAL (Europe)", ord("J"): "NTSC-J (Japan)"}

# Sizes of the flat CharacterSheet, derived from SHARMemory's struct definitions.
PLAYER_NAME_SIZE = 16
LEVEL_RECORD_SIZE = 620
MAX_LEVELS = 7
CHARACTER_SHEET_SIZE = 7137  # name(16) + 7*620 + globals; see parser for the field walk.

# The CharacterSheet is preceded by a 16-byte SaveGameInfo header whose first two bytes are
# a magic number (game source: savegameinfo.cpp). It's a distinctive anchor for locating
# the payload regardless of the preceding banner/icon size (which varies by region).
SAVE_INFO_SIZE = 16
SAVE_INFO_MAGIC = b"\xba\x07"

# Observed payload offset for single-slot NTSC-U saves. Used as the primary guess; the
# real location is always confirmed by sentinel validation below.
PRIMARY_OFFSET = 0x2095


def _player_name_looks_valid(window: bytes) -> bool:
    name = window[:PLAYER_NAME_SIZE]
    # Up to the first NUL, bytes should be printable ASCII; the remainder NUL padding.
    head, _, tail = name.partition(b"\x00")
    if not head:
        return False  # empty player name is implausible for a real save
    if any(b < 0x20 or b > 0x7E for b in head):
        return False
    return all(b == 0 for b in tail)


def _sentinel_ok(data: bytes, offset: int) -> bool:
    """A located CharacterSheet must be anchored by the SaveGameInfo magic and have a sane
    player name + current mission."""
    if offset < SAVE_INFO_SIZE or offset + CHARACTER_SHEET_SIZE > len(data):
        return False
    if data[offset - SAVE_INFO_SIZE : offset - SAVE_INFO_SIZE + 2] != SAVE_INFO_MAGIC:
        return False
    if not _player_name_looks_valid(data[offset : offset + PLAYER_NAME_SIZE]):
        return False
    # CurrentMissionInfo sits right after the 7 level records (big-endian level + mission).
    cmi = offset + PLAYER_NAME_SIZE + LEVEL_RECORD_SIZE * MAX_LEVELS
    level = int.from_bytes(data[cmi : cmi + 4], "big")
    mission = int.from_bytes(data[cmi + 4 : cmi + 8], "big")
    return 0 <= level < MAX_LEVELS and 0 <= mission <= 9


def validate_region(data: bytes) -> None:
    """Raise if this isn't a SHAR GameCube save. All GC regions (GHQE/GHQP/GHQJ) share the
    same CharacterSheet layout (game source), so any GHQ* save is accepted; the payload is
    located by the SaveGameInfo magic, which absorbs the region-specific banner/icon size."""
    if len(data) < 64:
        raise InvalidSaveError("file is too small to be a GameCube .gci save")
    code = data[0:4]
    if code[0:3] != SHAR_GAME_PREFIX:
        raise InvalidSaveError(
            f"not a Simpsons: Hit & Run save (game code {code!r}, expected GHQ*)"
        )


def extract_character_sheet(data: bytes) -> bytes:
    """Return the flat CharacterSheet bytes from a ``.gci`` file's contents.

    Validates region first, then locates the payload (primary offset, else a scan),
    confirming with a sentinel so misaligned reads fail loudly.
    """
    validate_region(data)

    candidates = [PRIMARY_OFFSET]
    # Fallback: scan 4-byte-aligned offsets. Cheap (a few thousand) and only reached if
    # the primary guess is wrong (e.g. a save laid out differently than the sample).
    candidates += range(0, len(data) - CHARACTER_SHEET_SIZE + 1, 4)

    for offset in candidates:
        if _sentinel_ok(data, offset):
            return data[offset : offset + CHARACTER_SHEET_SIZE]

    raise InvalidSaveError(
        "could not locate a valid CharacterSheet in this save; it may be corrupt, "
        "from an unsupported game version, or a format this tool does not understand"
    )


def read_gci(path: str) -> bytes:
    """Read a ``.gci`` file and return its flat CharacterSheet bytes."""
    with open(path, "rb") as handle:
        data = handle.read()
    return extract_character_sheet(data)

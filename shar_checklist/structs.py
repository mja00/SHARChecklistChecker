"""Bounds-checked big-endian readers for the GameCube save records.

The GameCube is big-endian PowerPC, so every multi-byte integer/float in the save is
stored big-endian. SHARMemory (the C# reference) uses ``BitConverter`` and is therefore
little-endian, because it reads the *PC* game's memory — the byte layout (field order and
sizes) is identical, only the endianness differs.

Every read is bounds-checked: an out-of-range access raises :class:`InvalidSaveError`
with offset context rather than a raw ``IndexError``/``struct.error``, so truncated or
corrupt files fail with a clear message.
"""

from __future__ import annotations

import struct

from .errors import InvalidSaveError


class Reader:
    """A cursor over a bytes buffer with sequential, bounds-checked big-endian reads.

    Mirrors the sequential ``FromBytes`` style of SHARMemory's struct readers so the
    parser can be a near-literal port: read a field, the cursor advances.
    """

    def __init__(self, data: bytes, offset: int = 0) -> None:
        self._data = data
        self.offset = offset

    def _check(self, size: int) -> None:
        if self.offset < 0 or self.offset + size > len(self._data):
            raise InvalidSaveError(
                f"read of {size} byte(s) at offset {self.offset} (0x{self.offset:X}) "
                f"is out of bounds (buffer is {len(self._data)} bytes); "
                "the save is truncated or misaligned"
            )

    def skip(self, size: int) -> None:
        self._check(size)
        self.offset += size

    def bytes(self, size: int) -> bytes:
        self._check(size)
        raw = self._data[self.offset : self.offset + size]
        self.offset += size
        return raw

    def string(self, length: int = 16) -> str:
        """Read a fixed-length, NUL-terminated ASCII/UTF-8 string field."""
        self._check(length)
        raw = self._data[self.offset : self.offset + length]
        self.offset += length
        return raw.split(b"\x00", 1)[0].decode("utf-8", errors="replace")

    def u8(self) -> int:
        self._check(1)
        value = self._data[self.offset]
        self.offset += 1
        return value

    def bool8(self) -> bool:
        return self.u8() != 0

    def u32(self) -> int:
        self._check(4)
        (value,) = struct.unpack_from(">I", self._data, self.offset)
        self.offset += 4
        return value

    def i32(self) -> int:
        self._check(4)
        (value,) = struct.unpack_from(">i", self._data, self.offset)
        self.offset += 4
        return value

    def f32(self) -> float:
        self._check(4)
        (value,) = struct.unpack_from(">f", self._data, self.offset)
        self.offset += 4
        return value

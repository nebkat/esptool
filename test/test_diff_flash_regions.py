# SPDX-FileCopyrightText: 2026 Espressif Systems (Shanghai) CO LTD
# SPDX-License-Identifier: GPL-2.0-or-later

"""Host-level unit tests for write-flash helpers (no hardware required)."""

import pytest

SECTOR = 0x1000


def _changed(sectors, total=16):
    """An old and a new image of `total` sectors differing in `sectors`."""
    old = bytearray(b"\xaa" * total * SECTOR)
    new = bytearray(old)
    for s in sectors:
        new[s * SECTOR] ^= 0xFF
    return bytes(old), bytes(new)


@pytest.mark.host_test
class TestDiffFlashRegions:
    def _ranges(self, sectors, bridge):
        from esptool.cmds import _diff_flash_regions

        old, new = _changed(sectors)
        regions = _diff_flash_regions(old, new, 0x10000, bridge_sectors=bridge)
        return [
            ((addr - 0x10000) // SECTOR, len(data) // SECTOR) for addr, data in regions
        ]

    def test_gaps_up_to_the_bridge_are_merged(self):
        # Gap of 2 between 1 and 4, gap of 3 between 4 and 8.
        assert self._ranges([1, 4, 8], bridge=2) == [(1, 4), (8, 1)]

    def test_bridge_zero_keeps_only_consecutive_sectors_together(self):
        assert self._ranges([1, 2, 4], bridge=0) == [(1, 2), (4, 1)]

    def test_bridged_sectors_hold_the_new_image(self):
        from esptool.cmds import _diff_flash_regions

        old, new = _changed([1, 3])
        [(addr, data)] = _diff_flash_regions(old, new, 0x10000, bridge_sectors=2)
        assert addr == 0x10000 + SECTOR
        assert data == new[SECTOR : 4 * SECTOR]

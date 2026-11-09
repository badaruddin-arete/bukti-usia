"""Peran pemegang (warga): menyimpan klaim sendiri dan memilih yang paling sedikit membuka diri."""

from __future__ import annotations

from .penerbit import KlaimBertandaTangan


class Dompet:
    def __init__(self) -> None:
        self._klaim: list[KlaimBertandaTangan] = []

    def simpan(self, klaim: KlaimBertandaTangan) -> None:
        self._klaim.append(klaim)

    def pilih(self, ambang_dibutuhkan: int) -> KlaimBertandaTangan | None:
        """Klaim dengan ambang terkecil yang masih memenuhi kebutuhan.

        Contoh: platform meminta usia >= 13 dan pemegang punya klaim 13, 16, 18;
        yang diserahkan klaim 13, bukan 18, supaya tidak membuka lebih dari perlu.
        """
        cocok = [k for k in self._klaim if k.klaim.ambang >= ambang_dibutuhkan]
        if not cocok:
            return None
        return min(cocok, key=lambda k: k.klaim.ambang)

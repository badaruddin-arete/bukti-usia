"""Model klaim usia dan serialisasi kanonik untuk ditandatangani.

Prinsip minimisasi: klaim hanya memuat pernyataan "usia >= ambang". Tanggal lahir
tidak pernah menjadi bagian klaim, sehingga pemverifikasi tidak bisa menerimanya.
"""

from __future__ import annotations

import json
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

# Ambang yang didukung. Pasal 20 ayat (2) PP 17/2025 membagi rentang usia menjadi 3-5,
# 6-9, 10-12, 13-15, dan 16 hingga di bawah 18 tahun. Prototipe sengaja hanya memakai
# batas 13, 16, dan 18 (dewasa) agar tetap kecil; batas lain mudah ditambahkan.
AMBANG_DIDUKUNG: tuple[int, ...] = (13, 16, 18)

VERSI_KLAIM = 1


class Klaim(BaseModel):
    """Pernyataan bertanda tangan: pemegang berusia sedikitnya `ambang` tahun."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    versi: int = VERSI_KLAIM
    id_klaim: str = Field(min_length=8)
    penerbit: str = Field(min_length=1)
    ambang: int
    diterbitkan: date
    berlaku_hingga: date


def serialisasi_kanonik(klaim: Klaim) -> bytes:
    """Bentuk byte yang stabil dan sama di mana pun, agar tanda tangan dapat diperiksa."""
    isi = klaim.model_dump(mode="json")
    return json.dumps(isi, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

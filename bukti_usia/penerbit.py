"""Peran penerbit (misalnya kelurahan atau kampus): satu-satunya pihak yang melihat tanggal lahir."""

from __future__ import annotations

import base64
import secrets
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from .klaim import AMBANG_DIDUKUNG, Klaim, serialisasi_kanonik


class PenerbitError(ValueError):
    """Penerbit menolak menerbitkan klaim."""


@dataclass(frozen=True)
class KlaimBertandaTangan:
    klaim: Klaim
    tanda_tangan: str  # base64


def usia_penuh(tanggal_lahir: date, hari_ini: date) -> int:
    tahun = hari_ini.year - tanggal_lahir.year
    belum_ulang_tahun = (hari_ini.month, hari_ini.day) < (tanggal_lahir.month, tanggal_lahir.day)
    return tahun - 1 if belum_ulang_tahun else tahun


class Penerbit:
    def __init__(self, nama: str, kunci: Ed25519PrivateKey | None = None) -> None:
        self.nama = nama
        self._kunci = kunci or Ed25519PrivateKey.generate()
        # Id klaim yang dicabut oleh penerbit ini. Pemverifikasi dapat memakai himpunan yang sama.
        self.daftar_cabut: set[str] = set()

    @property
    def kunci_publik(self) -> bytes:
        return self._kunci.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)

    def terbitkan(
        self,
        tanggal_lahir: date,
        ambang: int,
        hari_ini: date,
        masa_berlaku_hari: int = 30,
    ) -> KlaimBertandaTangan:
        """Menandatangani klaim 'usia >= ambang'. Tanggal lahir dipakai lalu dibuang."""
        if ambang not in AMBANG_DIDUKUNG:
            raise PenerbitError(f"ambang {ambang} tidak didukung; pilih salah satu dari {AMBANG_DIDUKUNG}")
        if tanggal_lahir > hari_ini:
            raise PenerbitError("tanggal lahir berada di masa depan")
        if usia_penuh(tanggal_lahir, hari_ini) < ambang:
            raise PenerbitError("pemohon belum memenuhi ambang usia; klaim tidak benar tidak diterbitkan")
        if masa_berlaku_hari <= 0:
            raise PenerbitError("masa berlaku harus positif")

        klaim = Klaim(
            id_klaim=secrets.token_hex(8),
            penerbit=self.nama,
            ambang=ambang,
            diterbitkan=hari_ini,
            berlaku_hingga=hari_ini + timedelta(days=masa_berlaku_hari),
        )
        tanda_tangan = self._kunci.sign(serialisasi_kanonik(klaim))
        return KlaimBertandaTangan(klaim=klaim, tanda_tangan=base64.b64encode(tanda_tangan).decode("ascii"))

    def terbitkan_semua(
        self, tanggal_lahir: date, hari_ini: date, masa_berlaku_hari: int = 30
    ) -> list[KlaimBertandaTangan]:
        """Satu klaim per ambang yang dipenuhi, agar pemegang bisa menyerahkan yang paling kecil."""
        hasil: list[KlaimBertandaTangan] = []
        for ambang in AMBANG_DIDUKUNG:
            if usia_penuh(tanggal_lahir, hari_ini) >= ambang:
                hasil.append(self.terbitkan(tanggal_lahir, ambang, hari_ini, masa_berlaku_hari))
        return hasil

    def koreksi(
        self,
        id_klaim_lama: Iterable[str],
        tanggal_lahir_benar: date,
        hari_ini: date,
        masa_berlaku_hari: int = 30,
    ) -> list[KlaimBertandaTangan]:
        """Jalur keberatan: mencabut klaim lama lalu menerbitkan ulang dari data yang benar.

        PP 17/2025 Pasal 22 ayat (3) huruf g meminta mekanisme keberatan atau koreksi bila
        usia yang teridentifikasi tidak sesuai usia sebenarnya.
        """
        self.daftar_cabut.update(id_klaim_lama)
        return self.terbitkan_semua(tanggal_lahir_benar, hari_ini, masa_berlaku_hari)

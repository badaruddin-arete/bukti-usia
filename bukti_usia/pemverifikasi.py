"""Peran pemverifikasi (platform): memeriksa tanda tangan, lalu tidak menyimpan apa pun."""

from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from datetime import date
from enum import IntEnum

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .klaim import serialisasi_kanonik
from .penerbit import KlaimBertandaTangan


class TingkatKepastian(IntEnum):
    """Seberapa kuat pemverifikasi mempercayai pernyataan sebuah penerbit.

    Tingkat ini ditetapkan oleh pemverifikasi, bukan oleh penerbit: penerbit tidak boleh
    menaikkan kepercayaan dirinya sendiri. PP 17/2025 Pasal 22 ayat (2) meminta tingkat
    kepastian verifikasi disesuaikan dengan risiko terhadap hak anak.
    """

    RENDAH = 1  # misalnya pernyataan orang tua atau diri sendiri
    SEDANG = 2  # misalnya sekolah atau kampus
    TINGGI = 3  # misalnya instansi pencatat kependudukan


@dataclass(frozen=True)
class PenerbitTepercaya:
    kunci_publik: bytes
    kepastian: TingkatKepastian


@dataclass(frozen=True)
class Hasil:
    sah: bool
    alasan: str


class Pemverifikasi:
    def __init__(
        self,
        penerbit_tepercaya: dict[str, PenerbitTepercaya],
        daftar_cabut: set[str] | None = None,
    ) -> None:
        """penerbit_tepercaya: nama penerbit -> kunci publik dan tingkat kepastiannya.

        daftar_cabut: id klaim yang dicabut, misalnya setelah keberatan atas data usia yang keliru.
        """
        self._penerbit = dict(penerbit_tepercaya)
        self._cabut = daftar_cabut if daftar_cabut is not None else set()

    def periksa(
        self,
        bukti: KlaimBertandaTangan,
        ambang_dibutuhkan: int,
        hari_ini: date,
        kepastian_minimum: TingkatKepastian = TingkatKepastian.RENDAH,
    ) -> Hasil:
        """Layanan berisiko tinggi sebaiknya meminta kepastian_minimum yang lebih tinggi."""
        klaim = bukti.klaim

        penerbit = self._penerbit.get(klaim.penerbit)
        if penerbit is None:
            return Hasil(False, "penerbit tidak dikenal")
        kunci_mentah = penerbit.kunci_publik

        try:
            tanda_tangan = base64.b64decode(bukti.tanda_tangan, validate=True)
            Ed25519PublicKey.from_public_bytes(kunci_mentah).verify(tanda_tangan, serialisasi_kanonik(klaim))
        except (InvalidSignature, binascii.Error, ValueError):
            return Hasil(False, "tanda tangan tidak sah")

        if klaim.id_klaim in self._cabut:
            return Hasil(False, "klaim telah dicabut")
        if hari_ini > klaim.berlaku_hingga:
            return Hasil(False, "klaim kedaluwarsa")
        if hari_ini < klaim.diterbitkan:
            return Hasil(False, "klaim belum berlaku")
        if penerbit.kepastian < kepastian_minimum:
            return Hasil(
                False,
                f"tingkat kepastian penerbit ({penerbit.kepastian.name.lower()}) "
                f"lebih rendah dari yang dibutuhkan ({kepastian_minimum.name.lower()})",
            )
        if klaim.ambang < ambang_dibutuhkan:
            return Hasil(False, f"ambang klaim ({klaim.ambang}) lebih rendah dari yang dibutuhkan ({ambang_dibutuhkan})")

        # Sengaja tidak ada penyimpanan: hasil dikembalikan, klaim dilepas.
        return Hasil(True, "klaim sah")

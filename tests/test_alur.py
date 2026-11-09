from dataclasses import replace
from datetime import date, timedelta

import pytest

from bukti_usia import (
    Dompet,
    Pemverifikasi,
    Penerbit,
    PenerbitError,
    PenerbitTepercaya,
    TingkatKepastian,
    usia_penuh,
)
from bukti_usia.klaim import Klaim

HARI_INI = date(2026, 11, 9)
LAHIR_20 = date(2006, 1, 1)  # 20 tahun
LAHIR_14 = date(2012, 5, 5)  # 14 tahun
LAHIR_10 = date(2016, 3, 3)  # 10 tahun


@pytest.fixture
def penerbit() -> Penerbit:
    return Penerbit("Kelurahan Contoh")


@pytest.fixture
def verifikator(penerbit: Penerbit) -> Pemverifikasi:
    return Pemverifikasi({penerbit.nama: PenerbitTepercaya(penerbit.kunci_publik, TingkatKepastian.TINGGI)})


# --- usia dan penerbitan -------------------------------------------------


def test_usia_penuh_tepat_di_hari_ulang_tahun():
    assert usia_penuh(date(2008, 11, 9), HARI_INI) == 18
    assert usia_penuh(date(2008, 11, 10), HARI_INI) == 17


def test_penerbit_menolak_klaim_yang_tidak_benar(penerbit):
    with pytest.raises(PenerbitError):
        penerbit.terbitkan(LAHIR_14, 18, HARI_INI)


def test_penerbit_menolak_ambang_tidak_didukung(penerbit):
    with pytest.raises(PenerbitError):
        penerbit.terbitkan(LAHIR_20, 21, HARI_INI)


def test_penerbit_menolak_tanggal_lahir_masa_depan(penerbit):
    with pytest.raises(PenerbitError):
        penerbit.terbitkan(HARI_INI + timedelta(days=1), 13, HARI_INI)


def test_terbitkan_semua_hanya_ambang_yang_dipenuhi(penerbit):
    assert [k.klaim.ambang for k in penerbit.terbitkan_semua(LAHIR_14, HARI_INI)] == [13]
    assert [k.klaim.ambang for k in penerbit.terbitkan_semua(LAHIR_20, HARI_INI)] == [13, 16, 18]
    assert penerbit.terbitkan_semua(LAHIR_10, HARI_INI) == []


# --- minimisasi ----------------------------------------------------------


def test_klaim_tidak_memuat_tanggal_lahir(penerbit):
    bukti = penerbit.terbitkan(LAHIR_20, 18, HARI_INI)
    assert set(bukti.klaim.model_dump()) == {"versi", "id_klaim", "penerbit", "ambang", "diterbitkan", "berlaku_hingga"}


def test_klaim_menolak_bidang_tambahan():
    with pytest.raises(ValueError):
        Klaim(
            id_klaim="abcdefgh",
            penerbit="X",
            ambang=18,
            diterbitkan=HARI_INI,
            berlaku_hingga=HARI_INI,
            tanggal_lahir="2006-01-01",
        )


def test_dompet_menyerahkan_klaim_terkecil_yang_cukup(penerbit):
    dompet = Dompet()
    for k in penerbit.terbitkan_semua(LAHIR_20, HARI_INI):
        dompet.simpan(k)
    assert dompet.pilih(13).klaim.ambang == 13
    assert dompet.pilih(16).klaim.ambang == 16
    assert dompet.pilih(18).klaim.ambang == 18


def test_dompet_mengembalikan_none_bila_tidak_ada_yang_cukup(penerbit):
    dompet = Dompet()
    for k in penerbit.terbitkan_semua(LAHIR_14, HARI_INI):
        dompet.simpan(k)
    assert dompet.pilih(18) is None


def test_pemverifikasi_tidak_menyimpan_klaim(penerbit, verifikator):
    bukti = penerbit.terbitkan(LAHIR_20, 18, HARI_INI)
    verifikator.periksa(bukti, 18, HARI_INI)
    assert bukti.klaim.id_klaim not in repr(vars(verifikator))


# --- verifikasi ----------------------------------------------------------


def test_klaim_sah_diterima(penerbit, verifikator):
    bukti = penerbit.terbitkan(LAHIR_20, 18, HARI_INI)
    assert verifikator.periksa(bukti, 18, HARI_INI).sah


def test_klaim_lebih_tinggi_memenuhi_kebutuhan_lebih_rendah(penerbit, verifikator):
    bukti = penerbit.terbitkan(LAHIR_20, 18, HARI_INI)
    assert verifikator.periksa(bukti, 13, HARI_INI).sah


def test_klaim_lebih_rendah_ditolak(penerbit, verifikator):
    bukti = penerbit.terbitkan(LAHIR_14, 13, HARI_INI)
    hasil = verifikator.periksa(bukti, 18, HARI_INI)
    assert not hasil.sah and "lebih rendah" in hasil.alasan


def test_klaim_dipalsukan_ditolak(penerbit, verifikator):
    bukti = penerbit.terbitkan(LAHIR_14, 13, HARI_INI)
    palsu = replace(bukti, klaim=bukti.klaim.model_copy(update={"ambang": 18}))
    hasil = verifikator.periksa(palsu, 18, HARI_INI)
    assert not hasil.sah and "tanda tangan" in hasil.alasan


def test_tanda_tangan_rusak_ditolak(penerbit, verifikator):
    bukti = penerbit.terbitkan(LAHIR_20, 18, HARI_INI)
    rusak = replace(bukti, tanda_tangan="bukan-base64!!")
    assert not verifikator.periksa(rusak, 18, HARI_INI).sah


def test_penerbit_tidak_dikenal_ditolak(verifikator):
    asing = Penerbit("Penerbit Asing")
    bukti = asing.terbitkan(LAHIR_20, 18, HARI_INI)
    hasil = verifikator.periksa(bukti, 18, HARI_INI)
    assert not hasil.sah and "tidak dikenal" in hasil.alasan


def test_penerbit_menyamar_dengan_kunci_lain_ditolak(penerbit, verifikator):
    penyamar = Penerbit(penerbit.nama)  # nama sama, kunci berbeda
    bukti = penyamar.terbitkan(LAHIR_20, 18, HARI_INI)
    assert not verifikator.periksa(bukti, 18, HARI_INI).sah


def test_klaim_kedaluwarsa_ditolak(penerbit, verifikator):
    bukti = penerbit.terbitkan(LAHIR_20, 18, HARI_INI, masa_berlaku_hari=30)
    assert verifikator.periksa(bukti, 18, HARI_INI + timedelta(days=30)).sah
    hasil = verifikator.periksa(bukti, 18, HARI_INI + timedelta(days=31))
    assert not hasil.sah and "kedaluwarsa" in hasil.alasan


def test_klaim_dicabut_ditolak_setelah_keberatan(penerbit):
    bukti = penerbit.terbitkan(LAHIR_20, 18, HARI_INI)
    verifikator = Pemverifikasi({penerbit.nama: PenerbitTepercaya(penerbit.kunci_publik, TingkatKepastian.TINGGI)}, daftar_cabut={bukti.klaim.id_klaim})
    hasil = verifikator.periksa(bukti, 18, HARI_INI)
    assert not hasil.sah and "dicabut" in hasil.alasan


# --- keterbatasan yang sengaja didokumentasikan ---------------------------


def test_keterbatasan_klaim_yang_sama_dapat_dikaitkan_antarplatform(penerbit):
    """Dua platform yang menerima klaim sama melihat id_klaim yang sama.

    Ini bukan bug yang disembunyikan: inilah batas pendekatan tanda tangan saja,
    dan alasan studi menunjuk ZKP atau klaim sekali pakai sebagai langkah berikutnya.
    """
    bukti = penerbit.terbitkan(LAHIR_20, 18, HARI_INI)
    dilihat_platform_a = bukti.klaim.id_klaim
    dilihat_platform_b = bukti.klaim.id_klaim
    assert dilihat_platform_a == dilihat_platform_b


# --- tingkat kepastian ----------------------------------------------------


def _verifikator(penerbit: Penerbit, kepastian: TingkatKepastian, **kwargs) -> Pemverifikasi:
    return Pemverifikasi({penerbit.nama: PenerbitTepercaya(penerbit.kunci_publik, kepastian)}, **kwargs)


def test_penerbit_kepastian_rendah_ditolak_untuk_layanan_berisiko_tinggi(penerbit):
    bukti = penerbit.terbitkan(LAHIR_20, 18, HARI_INI)
    verifikator = _verifikator(penerbit, TingkatKepastian.RENDAH)
    hasil = verifikator.periksa(bukti, 18, HARI_INI, kepastian_minimum=TingkatKepastian.TINGGI)
    assert not hasil.sah and "tingkat kepastian" in hasil.alasan


def test_penerbit_kepastian_rendah_diterima_untuk_layanan_berisiko_rendah(penerbit):
    bukti = penerbit.terbitkan(LAHIR_20, 18, HARI_INI)
    verifikator = _verifikator(penerbit, TingkatKepastian.RENDAH)
    assert verifikator.periksa(bukti, 18, HARI_INI, kepastian_minimum=TingkatKepastian.RENDAH).sah


def test_penerbit_kepastian_tinggi_memenuhi_semua_kebutuhan(penerbit):
    bukti = penerbit.terbitkan(LAHIR_20, 18, HARI_INI)
    verifikator = _verifikator(penerbit, TingkatKepastian.TINGGI)
    for minimum in TingkatKepastian:
        assert verifikator.periksa(bukti, 18, HARI_INI, kepastian_minimum=minimum).sah


def test_tingkat_kepastian_ditentukan_pemverifikasi_bukan_penerbit(penerbit):
    """Penerbit yang sama dipercaya berbeda oleh dua platform; klaimnya tidak membawa tingkat apa pun."""
    bukti = penerbit.terbitkan(LAHIR_20, 18, HARI_INI)
    assert "kepastian" not in bukti.klaim.model_dump()
    longgar = _verifikator(penerbit, TingkatKepastian.TINGGI)
    ketat = _verifikator(penerbit, TingkatKepastian.RENDAH)
    assert longgar.periksa(bukti, 18, HARI_INI, TingkatKepastian.TINGGI).sah
    assert not ketat.periksa(bukti, 18, HARI_INI, TingkatKepastian.TINGGI).sah


# --- keberatan dan koreksi ------------------------------------------------


def test_koreksi_mencabut_klaim_lama_dan_menerbitkan_yang_baru(penerbit):
    lama = penerbit.terbitkan(LAHIR_20, 18, HARI_INI)
    verifikator = _verifikator(penerbit, TingkatKepastian.TINGGI, daftar_cabut=penerbit.daftar_cabut)
    assert verifikator.periksa(lama, 18, HARI_INI).sah

    baru = penerbit.koreksi([lama.klaim.id_klaim], LAHIR_20, HARI_INI)

    hasil_lama = verifikator.periksa(lama, 18, HARI_INI)
    assert not hasil_lama.sah and "dicabut" in hasil_lama.alasan
    assert all(verifikator.periksa(k, k.klaim.ambang, HARI_INI).sah for k in baru)


def test_koreksi_dengan_tanggal_lahir_benar_yang_lebih_muda_tidak_menghasilkan_klaim_18(penerbit):
    salah = penerbit.terbitkan(LAHIR_20, 18, HARI_INI)
    verifikator = _verifikator(penerbit, TingkatKepastian.TINGGI, daftar_cabut=penerbit.daftar_cabut)

    baru = penerbit.koreksi([salah.klaim.id_klaim], LAHIR_14, HARI_INI)

    assert [k.klaim.ambang for k in baru] == [13]
    assert not verifikator.periksa(salah, 18, HARI_INI).sah
    assert not any(verifikator.periksa(k, 18, HARI_INI).sah for k in baru)

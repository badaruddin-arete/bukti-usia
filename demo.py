"""Demo alur tiga peran. Jalankan: python demo.py"""

from datetime import date

from bukti_usia import Dompet, Pemverifikasi, Penerbit, PenerbitTepercaya, TingkatKepastian

HARI_INI = date(2026, 11, 9)


def main() -> None:
    kelurahan = Penerbit("Kelurahan Contoh")
    platform = Pemverifikasi({kelurahan.nama: PenerbitTepercaya(kelurahan.kunci_publik, TingkatKepastian.TINGGI)})

    # Penerbit melihat tanggal lahir satu kali, lalu menerbitkan klaim tanpa tanggal itu.
    dompet = Dompet()
    for klaim in kelurahan.terbitkan_semua(date(2012, 5, 5), HARI_INI):
        dompet.simpan(klaim)

    # Platform meminta usia >= 13; pemegang menyerahkan klaim yang paling kecil yang cukup.
    for kebutuhan in (13, 18):
        bukti = dompet.pilih(kebutuhan)
        if bukti is None:
            print(f"Usia >= {kebutuhan}: pemegang tidak punya klaim yang cukup, tidak ada data yang dibuka.")
            continue
        hasil = platform.periksa(bukti, kebutuhan, HARI_INI)
        print(f"Usia >= {kebutuhan}: {'DITERIMA' if hasil.sah else 'DITOLAK'} ({hasil.alasan})")


if __name__ == "__main__":
    main()

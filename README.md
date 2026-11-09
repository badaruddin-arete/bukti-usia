# Bukti Usia: prototipe kedaulatan data dengan tanda tangan digital

Karya 3 dari rangkaian empat karya filsafat teknologi. Studi *Value Sensitive Design* tentang pertanyaan: bagaimana sebuah platform memenuhi kewajiban memverifikasi usia pengguna tanpa mengumpulkan lebih dari yang perlu?

Prototipe ini sengaja kecil. Ia memakai **tanda tangan digital saja**, bukan *zero-knowledge proof* (ZKP), dan keterbatasannya dijelaskan terang di bawah.

## Gagasan

Tiga peran:

| Peran | Contoh | Melihat apa |
|---|---|---|
| Penerbit | kelurahan, kampus | tanggal lahir, satu kali, saat menerbitkan |
| Pemegang | warga | klaim miliknya sendiri |
| Pemverifikasi | platform | hanya klaim "usia ≥ ambang" dan tanda tangannya |

Penerbit menandatangani pernyataan seperti "pemegang berusia sedikitnya 13 tahun". Tanggal lahir tidak ikut dalam klaim, jadi pemverifikasi tidak dapat menerimanya. Pemegang membawa beberapa klaim (13, 16, 18) dan menyerahkan **yang terkecil yang masih cukup**, supaya tidak membuka lebih dari yang diminta.

## Keputusan desain

| Keputusan | Alasan |
|---|---|
| Klaim hanya memuat ambang, bukan tanggal lahir | Minimisasi data: platform tidak perlu tahu kapan seseorang lahir. |
| Skema klaim menolak bidang tambahan | Tanggal lahir tidak bisa diselundupkan ke dalam klaim. |
| Penerbit menolak menerbitkan klaim yang tidak benar | Klaim bertanda tangan harus jujur pada saat diterbitkan. |
| Pemegang memilih klaim terkecil yang cukup | Menyerahkan "≥ 18" untuk kebutuhan "≥ 13" membuka lebih dari perlu. |
| Klaim berumur pendek (bawaan 30 hari) | Membatasi kerugian bila klaim bocor. |
| Daftar pencabutan | Menyediakan jalur koreksi bila data usia ternyata keliru. |
| Pemverifikasi tidak menyimpan klaim | Selaras dengan ketentuan bahwa data verifikasi dipakai untuk verifikasi saja. |

## Dasar hukum yang dirujuk

Rujukan berikut berasal dari ringkasan sumber sekunder dan **perlu dicocokkan dengan teks resmi** sebelum dipakai sungguhan.

- UU 27/2022 tentang Pelindungan Data Pribadi: pengumpulan data yang terbatas dan spesifik, pemrosesan sesuai tujuan, dan persetujuan orang tua untuk data anak.
- PP 17/2025 (PP Tunas): kewajiban verifikasi usia bagi penyelenggara sistem elektronik, dengan data verifikasi hanya untuk verifikasi, dihapus setelahnya, dan tersedianya jalur keberatan.

## Keterbatasan

Bagian ini sama pentingnya dengan kodenya.

- **Dapat dikaitkan antarplatform.** Klaim yang sama membawa `id_klaim` yang sama. Dua platform yang menerimanya dapat mencocokkan pengguna. Pendekatan tanda tangan saja tidak mengatasi ini; klaim sekali pakai atau ZKP bisa.
- **Penerbit tetap tahu.** Penerbit melihat tanggal lahir, dan dalam rancangan ini bisa mencatat siapa meminta klaim kapan.
- **Tidak ada pengikatan ke perangkat atau orang.** Klaim bisa dipinjamkan. Prototipe tidak membuktikan bahwa penyaji klaim adalah pemilik klaim.
- **Seluruh klaim terbuka.** Tanda tangan membuktikan keaslian, bukan pengungkapan selektif.
- Penerbit, daftar pencabutan, dan penyimpanan kunci hanya disimulasikan di memori. Ini bukan sistem produksi dan tidak boleh dipakai untuk keputusan tentang orang sungguhan.

Karena itu karya ini berhenti di tanda tangan dan menjadikan ZKP sebagai arah lanjutan, bukan klaim yang sudah dikerjakan.

## Menjalankan

```bash
pip install -r requirements.txt
python demo.py
python -m pytest
```

20 uji otomatis mencakup penerbitan, penolakan klaim palsu, kedaluwarsa, pencabutan, penerbit tak dikenal, penyamaran dengan kunci lain, dan minimisasi.

## Transparansi

Rancangan, kode, dan pengujian disusun dengan bantuan AI (Claude). Pilihan kasus, keputusan desain, dan peninjauan dilakukan oleh saya.

## Lisensi

All rights reserved. Kode ini ditampilkan sebagai portofolio dan tidak boleh disalin atau dipakai ulang tanpa izin tertulis.

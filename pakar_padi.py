"""
Sistem Pakar Identifikasi Hama dan Penyakit Tanaman Padi
Metode: Forward Chaining
Penulis: [Nama dan NIM Anda]

Mesin inferensi ditulis sendiri (tanpa library AI/expert-system).
"""

import json
import sys
import os


def muat_knowledge_base(path):
    """Memuat knowledge base dari file JSON."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def kumpulkan_fakta_dasar(aturan_list):
    """
    Mengumpulkan semua fakta dasar, yaitu fakta yang TIDAK pernah
    menjadi hasil (maka) dari aturan manapun.
    Fakta-fakta inilah yang akan ditanyakan ke user.
    """
    semua_maka = set()
    for r in aturan_list:
        semua_maka.add(r["maka"])

    fakta_dasar = []
    sudah = set()
    for r in aturan_list:
        for syarat in r["jika"]:
            if syarat not in semua_maka and syarat not in sudah:
                fakta_dasar.append(syarat)
                sudah.add(syarat)

    return fakta_dasar


def tanya_fakta(fakta_dasar):
    """Menanyakan setiap fakta dasar ke user, mengembalikan set fakta yang 'ya'."""
    print("\nJawab y/t (ya/tidak) untuk setiap pertanyaan berikut:\n")
    memori = set()
    for i, fakta in enumerate(fakta_dasar, 1):
        while True:
            jawaban = input(f"  {i}. Apakah {fakta}? (y/t) > ").strip().lower()
            if jawaban in ("y", "t"):
                break
            print("     Masukkan 'y' atau 't'.")
        if jawaban == "y":
            memori.add(fakta)
    return memori


def syarat_terpenuhi(aturan, memori):
    """
    Mengecek apakah syarat aturan terpenuhi berdasarkan isi memori.
    mode 'dan': semua syarat harus ada di memori.
    mode 'atau': minimal satu syarat ada di memori.
    """
    if aturan["mode"] == "dan":
        return all(s in memori for s in aturan["jika"])
    elif aturan["mode"] == "atau":
        return any(s in memori for s in aturan["jika"])
    return False


def forward_chaining(aturan_list, memori):
    """
    Menjalankan forward chaining:
    - Mulai dari fakta di memori.
    - Ulangi: cari aturan yang syaratnya terpenuhi dan hasilnya belum ada.
    - Tambahkan hasil ke memori, catat jejak alasan.
    - Berhenti jika tidak ada aturan baru yang bisa dijalankan.

    Mengembalikan: (memori_akhir, jejak_siklus, alasan_dict)
    """
    alasan = {}  # maka -> (id_aturan, list_syarat_yang_terpenuhi)
    jejak = []   # list of (siklus_ke, id_aturan, maka)
    siklus = 0

    while True:
        ada_baru = False
        for r in aturan_list:
            if r["maka"] not in memori and syarat_terpenuhi(r, memori):
                siklus += 1
                memori.add(r["maka"])
                # Catat syarat mana yang terpenuhi
                syarat_cocok = [s for s in r["jika"] if s in memori]
                alasan[r["maka"]] = (r["id"], syarat_cocok)
                jejak.append((siklus, r["id"], r["maka"]))
                ada_baru = True
        if not ada_baru:
            siklus += 1
            jejak.append((siklus, None, None))  # siklus terakhir, tidak ada aturan baru
            break

    return memori, jejak, alasan


def cetak_alasan_rekursif(maka, alasan, indent=2):
    """Mencetak alasan secara rekursif (rantai aturan)."""
    if maka in alasan:
        id_aturan, syarat_list = alasan[maka]
        spasi = " " * indent
        syarat_str = ", ".join(syarat_list)
        print(f"{spasi}{maka}  <- {id_aturan} ({syarat_str})")
        for s in syarat_list:
            if s in alasan:
                cetak_alasan_rekursif(s, alasan, indent + 4)


def main():
    # Tentukan path knowledge base
    script_dir = os.path.dirname(os.path.abspath(__file__))
    kb_path = os.path.join(script_dir, "kb_padi.json")

    if not os.path.exists(kb_path):
        print(f"Error: File knowledge base tidak ditemukan: {kb_path}")
        sys.exit(1)

    # Muat knowledge base
    kb = muat_knowledge_base(kb_path)

    print("=" * 60)
    print(f"  {kb['judul']}")
    print("=" * 60)

    # Kumpulkan dan tanyakan fakta dasar
    fakta_dasar = kumpulkan_fakta_dasar(kb["aturan"])
    memori = tanya_fakta(fakta_dasar)

    if not memori:
        print("\nTidak ada fakta yang diberikan. Tidak ada kesimpulan.")
        print(f"\nCatatan: {kb['batas']}")
        return

    # Tampilkan fakta awal
    print(f"\nFakta awal: {', '.join(sorted(memori))}")

    # Jalankan forward chaining
    memori_akhir, jejak, alasan = forward_chaining(kb["aturan"], memori)

    # Tampilkan proses siklus
    print()
    for siklus_ke, id_aturan, maka in jejak:
        if id_aturan is not None:
            print(f"Siklus {siklus_ke}: {id_aturan} -> {maka}")
        else:
            print(f"Siklus {siklus_ke}: tidak ada aturan baru, berhenti")

    # Tentukan kesimpulan (hasil akhir = fakta yang ada di 'maka' aturan
    # tetapi TIDAK menjadi syarat aturan lain yang hasilnya juga terpenuhi)
    semua_maka = {r["maka"] for r in kb["aturan"]}
    kesimpulan_list = []
    for maka in sorted(memori_akhir):
        if maka in semua_maka and maka in alasan:
            # Cek apakah maka ini digunakan sebagai syarat di aturan lain yang hasilnya juga ada
            dipakai_lebih_lanjut = False
            for r in kb["aturan"]:
                if maka in r["jika"] and r["maka"] in memori_akhir:
                    dipakai_lebih_lanjut = True
                    break
            if not dipakai_lebih_lanjut:
                kesimpulan_list.append(maka)

    # Tampilkan kesimpulan
    if kesimpulan_list:
        print(f"\nKesimpulan: {', '.join(kesimpulan_list)}")
        print("\nAlasan:")
        for k in kesimpulan_list:
            cetak_alasan_rekursif(k, alasan)
    else:
        print("\nKesimpulan: tidak ada kesimpulan yang dapat ditarik dari fakta yang diberikan.")

    # Tampilkan batas keberlakuan
    print(f"\nCatatan: {kb['batas']}")


if __name__ == "__main__":
    main()


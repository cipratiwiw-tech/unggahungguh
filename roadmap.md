ROADMAP UPGRADE UNGGAHUNGGUH

Dari “Uploader” → “Command Center Multi-Channel (Ringan)”

TUJUAN AKHIR (JANGAN BERUBAH)

Aplikasi desktop yang:

Mengelola banyak channel YouTube

Upload batch video

Maksimal 5 video / hari / channel

Fokus ke kecepatan & kenyamanan kerja

Tetap sederhana & stabil

PRINSIP DASAR (DIKUNCI)

❌ Tidak bikin backend ribet

❌ Tidak wajib database berat

❌ Tidak jadi analytics tool

✅ UI jadi pusat kendali (Command Center)

✅ Batch workflow (Draft → Edit → Upload)

FASE 1 — UI FOUNDATION (Upgrade Tampilan Dasar)

Target: Tampilan lebih rapi & scalable
Scope: UI saja, logic lama tetap jalan

1. Sidebar = Navigasi Utama

Upgrade sidebar.py

Isi Sidebar:

Dashboard (ringkasan global)

Channels (daftar channel, bukan tab)

Asset Library (placeholder dulu)

Global Queue (placeholder dulu)

✅ Hapus konsep banyak tab di atas
✅ Channel dipilih lewat sidebar

2. Workspace Area (Tengah – Dinamis)

Ganti QTabWidget → 1 container dinamis

Klik menu sidebar → workspace berubah

Channel dipilih → tampil Channel Workspace

3. Status Bar Global (Bawah)

Tambahkan QStatusBar

Isi:

Upload status: Uploading 2 files…

Daily limit indicator: Channel A: 3/5

(Opsional) spinner kecil

FASE 2 — CHANNEL WORKSPACE (Inti Aplikasi)

Target: Workflow batch yang nyaman
Scope: Upgrade channel_tab.py + video_table.py

Mode 1: Spreadsheet View (DEFAULT)

Tetap pakai VideoDropTable (aset utama repo)

Upgrade kecil:

Toolbar di atas tabel:

Apply Preset (dummy dulu / JSON)

Bulk Schedule (pakai logic lama)

Status warna:

Abu-abu → Draft

Biru → Ready

Kuning → Uploading

Hijau → Done

Merah → Error

Mode 2: Focus View (Detail Editor)

Trigger:

Double-click satu row

Tampilan:

Popup / side panel

Preview video (QMediaPlayer)

Edit:

Judul

Deskripsi

Tags

Playlist

⚠️ Tidak perlu fancy, cukup fungsional

FASE 3 — USER FLOW RESMI (Draft → Polish → Sync)

Target: Alur kerja jelas & konsisten

Tahap 1: Ingest & Draft (Offline)

Drag & drop banyak video

Auto-fill dari nama file:

2024-01-20_Minecraft_Part1.mp4
→ Minecraft Part 1


Status: Draft (Abu-abu)

Tidak ada upload di sini.

Tahap 2: Polish & Optimization

Apply template metadata

Drag thumbnail

Set jadwal (chain schedule)

User klik Mark as Ready

Status berubah:

Draft → Ready (Biru)

Tahap 3: Sync & Execution

Tombol besar: START UPLOAD SEQUENCE

Sebelum upload:

Validasi judul

Validasi file thumbnail

Cek limit 5 video / hari

Upload berjalan di background:

UI tetap bisa dipakai

Bisa minimize ke tray

Status:

Uploading → Done / Error

FASE 4 — GLOBAL QUEUE (Sederhana tapi Berguna)

Target: Kontrol upload lintas channel

Isi:

List upload aktif

Channel mana

Progress bar

Tombol:

Pause (opsional)

Cancel (opsional)

Tidak perlu kompleks.

FASE 5 — ASSET LIBRARY (VERSI RINGAN)

Target: Hemat waktu, bukan sistem CMS

Isi:

Preset JSON:

Template deskripsi

Tag list

UI simpel:

Pilih preset

Apply ke selected rows

Tidak ada editor canggih.

RINGKASAN ROADMAP (1 HALAMAN)
Fase	Fokus	Hasil
1	Layout & Sidebar	UI scalable
2	Channel Workspace	Batch edit nyaman
3	Workflow	Draft → Upload jelas
4	Global Queue	Kontrol upload
5	Asset Preset	Kerja lebih cepat
YANG SENGAJA TIDAK MASUK

Supaya tidak pusing:

❌ Analytics berat

❌ Database besar

❌ Multi-user

❌ Cloud sync

❌ AI generator

KESIMPULAN PALING PENTING

UnggahUngguh tidak diganti, hanya ditingkatkan

UI jadi Command Center, bukan sekadar uploader

Semua upgrade inkremental & masuk akal

Bisa berhenti di fase mana pun, tetap usable
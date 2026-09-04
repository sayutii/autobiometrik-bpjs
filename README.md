# AutoBiometrik BPJS

Service HTTP lokal berbasis Python yang menjadi jembatan antara sistem antrean rumah sakit (berbasis web) dengan dua aplikasi desktop biometrik BPJS Kesehatan:
- **FRISTA** (Verifikasi Wajah)
- **Aplikasi Sidik Jari** (`After.exe`)

Dengan service ini, operator pendaftaran tidak perlu lagi membuka aplikasi secara manual dan mengetikkan nomor BPJS pasien.

---

## 🚀 Cara Kerja

```
┌─────────────────┐  HTTP GET /start_frista?no_peserta=0001xxxx ┌──────────────────────┐
│  Web Antrean    │ ─────────────────────────────────────────► │  AutoBiometrik BPJS  │
│  (Browser)      │                                            │  (Service Python)    │
└─────────────────┘                                            └──────────┬───────────┘
                                                                          │ Otomatisasi Jendela
                                                                          ▼
                                                       FRISTA.exe / After.exe (Biometrik BPJS)
```

1. Aplikasi web antrean mengirim request `GET` ke endpoint AutoBiometrik BPJS.
2. Service membuka aplikasi desktop biometrik BPJS yang sesuai (jika belum jalan) dan mengisi login secara otomatis.
3. Service memasukkan nomor BPJS/NIK pasien ke kolom yang sesuai di aplikasi.
4. Operator tinggal menekan tombol aksi (misal: "Ambil Foto" di FRISTA).

---

## 📌 Endpoint API

Semua endpoint menggunakan method `GET` dan mengembalikan respon berformat JSON. CORS diaktifkan terbuka (`*`), sehingga halaman web antrean dari origin mana pun dapat mengaksesnya.

| Endpoint | Query Parameter | Fungsi |
| :--- | :--- | :--- |
| `/start_frista` | `no_peserta` | Jika FRISTA belum jalan: buka dan login. Lalu ketikkan nomor BPJS ke kolom No. BPJS Kesehatan/NIK. Tombol Ambil Foto tetap ditekan operator |
| `/start_finger` | `no_peserta` | Jika aplikasi sidik jari belum jalan: buka, login, lalu ketikkan nomor BPJS. Jika sudah jalan: gunakan jendela yang ada dan ketikkan nomornya |
| `/stop_frista` | — | Menutup aplikasi FRISTA |
| `/stop_finger` | — | Menutup aplikasi sidik jari (`After.exe`) |
| `/health` | — | Memeriksa status service, ketersediaan AutoItX, serta status kredensial |

### Contoh Penggunaan

```bash
# Menjalankan verifikasi wajah FRISTA
curl "http://127.0.0.1:5000/start_frista?no_peserta=0001234567890"
# Respon: {"status":"running","target":"frista","no_peserta":"0001234567890"}

# Cek kesehatan service
curl "http://127.0.0.1:5000/health"
# Respon: {"status":"ok","service":"autobiometrik-bpjs","version":"1.0.1","autoit":true,"has_credentials":true,"has_finger_credentials":true,"scheme":"http"}
```

---

## ⚙️ Konfigurasi (`config.json`)

Salin `config.example.json` menjadi `config.json` pada folder yang sama dengan program:

```json
{
  "frista_path": "C:\\frista\\frista.exe",
  "finger_path": "C:\\Program Files (x86)\\BPJS Kesehatan\\Aplikasi Sidik Jari BPJS Kesehatan\\After.exe",
  "frista_username": "username_frista",
  "frista_password": "password_frista",
  "finger_username": "username_finger",
  "finger_password": "password_finger",
  "host": "127.0.0.1",
  "port": 5000,
  "tls_cert": "",
  "tls_key": "",
  "frista_api": "https://frista.bpjs-kesehatan.go.id/frista-api",
  "camera_id": 0
}
```

- **`frista_path`**: Lokasi executable FRISTA (`frista.exe`).
- **`finger_path`**: Lokasi executable Aplikasi Sidik Jari (`After.exe`).
- **`frista_username` / `frista_password`**: Kredensial login aplikasi FRISTA.
- **`finger_username` / `finger_password`**: Kredensial login aplikasi Sidik Jari. Jika dikosongkan, langkah login di-skip.
- **`host` / `port`**: Alamat & port listener HTTP server (default `127.0.0.1:5000`).
- **`tls_cert` / `tls_key`**: Path file sertifikat TLS/SSL jika ingin menggunakan HTTPS.

---

## 💻 Menjalankan & Menguji (Sebelum Build Windows)

### 1. Persiapan Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Menyiapkan Config
```bash
cp config.example.json config.json
```

### 3. Menjalankan Service Server
```bash
python3 -m autobiometrik
```

Server akan berjalan pada `http://127.0.0.1:5000`.

### 4. Menguji Endpoint (di Terminal / Browser lain)
Buka terminal baru untuk mengetes endpoint:

- **Cek Status Service**:
  ```bash
  curl "http://127.0.0.1:5000/health"
  ```
- **Tes Start FRISTA**:
  ```bash
  curl "http://127.0.0.1:5000/start_frista?no_peserta=0001234567890"
  ```
- **Tes Start Fingerprint**:
  ```bash
  curl "http://127.0.0.1:5000/start_finger?no_peserta=0001234567890"
  ```
- **Tes Stop FRISTA**:
  ```bash
  curl "http://127.0.0.1:5000/stop_frista"
  ```
- **Tes Stop Fingerprint**:
  ```bash
  curl "http://127.0.0.1:5000/stop_finger"
  ```

*(Catatan: Di macOS/Linux sebelum di-build ke Windows, service akan tetap berjalan normal dan merespon API JSON, sementara aksi AutoIt window akan di-mock/skip secara otomatis).*

---

## 🧪 Jalankan Unit Tests

```bash
PYTHONPATH=. .venv/bin/pytest
```

---

## 📦 Build Standalone Executable (.exe) di Windows

### Cara A: Manual di PC Windows
Gunakan `PyInstaller` untuk mem-build aplikasi menjadi file standalone `.exe` tanpa membutuhkan instalasi Python di PC Windows target:

```bash
pip install pyinstaller PyAutoIt
pyinstaller autobiometrik-bpjs.spec
```

Hasil `.exe` akan berada di folder `dist/autobiometrik-bpjs.exe`. Cukup letakkan `config.json` di sebelahnya dan jalankan.

### 📄 File Logging (`autobiometrik.log`)
Aplikasi secara otomatis mencatat seluruh log aktivitas server dan error traceback ke dalam file **`autobiometrik.log`** di folder tempat file `.exe` / program berada.
- Jika terjadi error saat dijalankan di Windows, buka file **`autobiometrik.log`** untuk melihat pesan error secara lengkap.

---

## 📜 Lisensi

MIT License

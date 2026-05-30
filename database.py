import sqlite3
import pandas as pd
import hashlib

DB_NAME = "kebun_strawberry.db"

# 1. FUNGSI HASH PASSWORD (Harus ditaruh di atas agar dikenali fungsi lain)
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 2. INISIASI DATABASE & TABEL
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Tabel Master CoA & Jurnal
    cursor.execute('''CREATE TABLE IF NOT EXISTS accounts (code TEXT PRIMARY KEY, name TEXT NOT NULL, type TEXT NOT NULL, normal_balance TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS journal_headers (id INTEGER PRIMARY KEY AUTOINCREMENT, date DATE NOT NULL, description TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS journal_entries (id INTEGER PRIMARY KEY AUTOINCREMENT, header_id INTEGER, account_code TEXT, debit REAL DEFAULT 0, credit REAL DEFAULT 0, FOREIGN KEY(header_id) REFERENCES journal_headers(id), FOREIGN KEY(account_code) REFERENCES accounts(code))''')

    # Tabel Users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')

    # --- TABEL BARU: DAFTAR BARANG (INVENTORY) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            item_code TEXT PRIMARY KEY,
            item_name TEXT NOT NULL,
            category TEXT NOT NULL,
            unit TEXT NOT NULL,
            purchase_price REAL DEFAULT 0,
            selling_price REAL DEFAULT 0,
            stock REAL DEFAULT 0
        )
    ''')

    # --- TABEL BARU: ASET TETAP (FIXED ASSETS) ---
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fixed_assets (
            asset_code TEXT PRIMARY KEY,
            asset_name TEXT NOT NULL,
            acquisition_date DATE NOT NULL,
            acquisition_value REAL NOT NULL,
            useful_life_years INTEGER NOT NULL
        )
    ''')

    # Insert Default Users
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        users_data = [
            ("imam_admin", hash_password("admin123"), "Mas Imam", "Admin"),
            ("operator_kebun", hash_password("kebun123"), "Keluarga/Pekerja", "Operator")
        ]
        cursor.executemany("INSERT INTO users (username, password, name, role) VALUES (?, ?, ?, ?)", users_data)

    # Insert Data CoA Agribisnis (tetap pertahankan CoA yang ada)
    cursor.execute("SELECT COUNT(*) FROM accounts")
    if cursor.fetchone()[0] == 0:
        coa_data = [
            ("1110", "Kas & Bank", "Aset", "Debit"),
            ("1120", "Piutang Usaha", "Aset", "Debit"),
            ("1131", "Persediaan Barang Jadi (Strawberry)", "Aset", "Debit"),
            ("1132", "Persediaan Bahan Baku (Pupuk & Obat)", "Aset", "Debit"),
            ("1133", "Persediaan Perlengkapan (Mika, Polybag)", "Aset", "Debit"),
            ("1210", "Aset Tetap (Lahan & Bangunan)", "Aset", "Debit"),
            ("1220", "Peralatan Pertanian", "Aset", "Debit"),
            ("1230", "Akumulasi Penyusutan Peralatan", "Aset", "Kredit"),
            ("1240", "Aset Biologis (Tanaman Menghasilkan)", "Aset", "Debit"),
            ("2110", "Utang Usaha (Supplier)", "Kewajiban", "Kredit"),
            ("2120", "Utang Bagi Hasil", "Kewajiban", "Kredit"),
            ("3110", "Modal Mas Imam", "Ekuitas", "Kredit"),
            ("3120", "Prive Mas Imam", "Ekuitas", "Debit"),
            ("4110", "Penjualan Strawberry (Pasar/Pengepul)", "Pendapatan", "Kredit"),
            ("4120", "Pendapatan Wisata Petik", "Pendapatan", "Kredit"),
            ("4130", "Penjualan Bibit", "Pendapatan", "Kredit"),
            ("5110", "Harga Pokok Penjualan (HPP)", "Beban", "Debit"),
            ("5120", "Beban Kerusakan Panen (Afkir)", "Beban", "Debit"),
            ("6110", "Beban Pemakaian Pupuk & Obat", "Beban", "Debit"),
            ("6120", "Beban Perlengkapan Packing", "Beban", "Debit"),
            ("6130", "Beban Pemeliharaan & Renovasi", "Beban", "Debit"),
            ("6140", "Beban Penyusutan Peralatan", "Beban", "Debit"),
            ("6190", "Beban Lain-lain", "Beban", "Debit"),
        ]
        cursor.executemany("INSERT INTO accounts (code, name, type, normal_balance) VALUES (?, ?, ?, ?)", coa_data)

    # Insert Data Master Barang Default (Diperbarui)
    cursor.execute("SELECT COUNT(*) FROM items")
    if cursor.fetchone()[0] == 0:
        items_data = [
            ("BRG-001", "Strawberry Segar", "Barang Jadi", "Kg", 5000, 60000, 0), # Disatukan jadi satu entitas "Kg"
            ("BRG-003", "Pupuk NPK", "Bahan Baku", "Kg", 15000, 0, 0),
            ("BRG-004", "Fungisida Daponil", "Bahan Baku", "Botol", 75000, 0, 0),
            ("BRG-005", "Mika Packing", "Perlengkapan", "Pack", 25000, 0, 0),
            ("BRG-006", "Polybag", "Perlengkapan", "Pack", 10000, 0, 0),
            ("BRG-007", "Bibit Strawberry", "Barang Jadi", "Pcs", 2000, 5000, 0)
        ]
        cursor.executemany("INSERT INTO items (item_code, item_name, category, unit, purchase_price, selling_price, stock) VALUES (?, ?, ?, ?, ?, ?, ?)", items_data)

    conn.commit()
    conn.close()

# 3. FUNGSI AUTENTIKASI LOGIN
def verify_login(username, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    hashed_pw = hash_password(password) # Error garis merahmu tadi akan hilang karena fungsinya sudah ada di atas
    
    cursor.execute("SELECT name, role FROM users WHERE username = ? AND password = ?", (username, hashed_pw))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return {"status": True, "name": user[0], "role": user[1]}
    else:
        return {"status": False}

# 4. FUNGSI JURNAL & BUKU BESAR
def insert_journal(tanggal, deskripsi, akun_debit, nominal_debit, akun_kredit, nominal_kredit):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO journal_headers (date, description) VALUES (?, ?)", (tanggal, deskripsi))
        header_id = cursor.lastrowid
        cursor.execute("INSERT INTO journal_entries (header_id, account_code, debit, credit) VALUES (?, ?, ?, ?)", (header_id, akun_debit, nominal_debit, 0))
        cursor.execute("INSERT INTO journal_entries (header_id, account_code, debit, credit) VALUES (?, ?, ?, ?)", (header_id, akun_kredit, 0, nominal_kredit))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error Database: {e}")
        return False
    finally:
        conn.close()

def get_jurnal_umum():
    conn = sqlite3.connect(DB_NAME)
    # PERBAIKAN: Menambahkan h.id AS 'No. Bukti' untuk memisahkan setiap transaksi
    query = '''
        SELECT h.id AS 'No. Bukti', h.date AS 'Tanggal', h.description AS 'Keterangan', 
               e.account_code AS 'Kode', a.name AS 'Nama Akun', e.debit AS 'Debit', e.credit AS 'Kredit'
        FROM journal_headers h 
        JOIN journal_entries e ON h.id = e.header_id 
        JOIN accounts a ON e.account_code = a.code
        ORDER BY h.id DESC, e.id ASC
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_buku_besar(account_code):
    conn = sqlite3.connect(DB_NAME)
    query = f'''
        SELECT h.date AS 'Tanggal', h.description AS 'Keterangan', e.debit AS 'Debit', e.credit AS 'Kredit'
        FROM journal_headers h JOIN journal_entries e ON h.id = e.header_id
        WHERE e.account_code = '{account_code}' ORDER BY h.date ASC
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_laba_rugi_data():
    conn = sqlite3.connect(DB_NAME)
    query = '''
        SELECT a.type AS Kategori, a.code AS Kode, a.name AS 'Nama Akun', IFNULL(SUM(e.debit), 0) AS total_debit, IFNULL(SUM(e.credit), 0) AS total_kredit
        FROM accounts a LEFT JOIN journal_entries e ON a.code = e.account_code
        WHERE a.type IN ('Pendapatan', 'Beban') GROUP BY a.code, a.name, a.type
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    def hitung_saldo(row):
        if row['Kategori'] == 'Pendapatan': return row['total_kredit'] - row['total_debit']
        elif row['Kategori'] == 'Beban': return row['total_debit'] - row['total_kredit']
        return 0

    df['Saldo'] = df.apply(hitung_saldo, axis=1)
    return df[df['Saldo'] > 0].copy()

def get_neraca_saldo():
    conn = sqlite3.connect(DB_NAME)
    query = '''
        SELECT 
            a.code AS 'Kode Akun',
            a.name AS 'Nama Akun',
            a.normal_balance AS 'Saldo Normal',
            IFNULL(SUM(e.debit), 0) AS total_debit,
            IFNULL(SUM(e.credit), 0) AS total_kredit
        FROM accounts a
        LEFT JOIN journal_entries e ON a.code = e.account_code
        GROUP BY a.code, a.name, a.normal_balance
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Logika Akuntansi: Menghitung saldo akhir berdasarkan saldo normal
    def hitung_saldo_debit(row):
        if row['Saldo Normal'] == 'Debit':
            saldo = row['total_debit'] - row['total_kredit']
            # Jika saldo negatif (abnormal), kita tampilkan 0 di debit, sisanya akan ditangani kredit
            return saldo if saldo > 0 else 0
        elif row['Saldo Normal'] == 'Kredit':
            saldo = row['total_kredit'] - row['total_debit']
            return abs(saldo) if saldo < 0 else 0
        return 0

    def hitung_saldo_kredit(row):
        if row['Saldo Normal'] == 'Kredit':
            saldo = row['total_kredit'] - row['total_debit']
            return saldo if saldo > 0 else 0
        elif row['Saldo Normal'] == 'Debit':
            saldo = row['total_debit'] - row['total_kredit']
            return abs(saldo) if saldo < 0 else 0
        return 0

    df['Debit'] = df.apply(hitung_saldo_debit, axis=1)
    df['Kredit'] = df.apply(hitung_saldo_kredit, axis=1)

    # Filter akun yang ada saldonya saja agar tabel tidak kepanjangan
    df = df[(df['Debit'] > 0) | (df['Kredit'] > 0)].copy()
    
    return df[['Kode Akun', 'Nama Akun', 'Debit', 'Kredit']]

def eksekusi_tutup_buku(tanggal_tutup):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        # 1. Ambil saldo akun Pendapatan (Normal Kredit)
        cursor.execute('''
            SELECT a.code, IFNULL(SUM(e.credit) - SUM(e.debit), 0) as saldo
            FROM accounts a
            LEFT JOIN journal_entries e ON a.code = e.account_code
            WHERE a.type = 'Pendapatan'
            GROUP BY a.code
            HAVING saldo <> 0
        ''')
        pendapatan = cursor.fetchall()
        
        # 2. Ambil saldo akun Beban (Normal Debit)
        cursor.execute('''
            SELECT a.code, IFNULL(SUM(e.debit) - SUM(e.credit), 0) as saldo
            FROM accounts a
            LEFT JOIN journal_entries e ON a.code = e.account_code
            WHERE a.type = 'Beban'
            GROUP BY a.code
            HAVING saldo <> 0
        ''')
        beban = cursor.fetchall()
        
        # 3. Ambil saldo Prive (3120 - Normal Debit)
        cursor.execute('''
            SELECT IFNULL(SUM(e.debit) - SUM(e.credit), 0) as saldo
            FROM journal_entries e
            WHERE e.account_code = '3120'
        ''')
        prive_row = cursor.fetchone()
        saldo_prive = prive_row[0] if prive_row[0] else 0
        
        # Cek apakah ada yang perlu ditutup
        if not pendapatan and not beban and saldo_prive == 0:
            return {"status": False, "pesan": "Tidak ada saldo Pendapatan, Beban, atau Prive yang perlu ditutup."}
        
        # Hitung Laba/Rugi
        total_pendapatan = sum([p[1] for p in pendapatan])
        total_beban = sum([b[1] for b in beban])
        laba_bersih = total_pendapatan - total_beban
        
        # ==========================================
        # JURNAL 1: MENUTUP PENDAPATAN & BEBAN
        # ==========================================
        cursor.execute("INSERT INTO journal_headers (date, description) VALUES (?, ?)", (tanggal_tutup, "Jurnal Penutup Akhir Periode"))
        header_id = cursor.lastrowid
        
        # Debit-kan semua akun Pendapatan agar saldonya nol
        for p in pendapatan:
            cursor.execute("INSERT INTO journal_entries (header_id, account_code, debit, credit) VALUES (?, ?, ?, ?)", (header_id, p[0], p[1], 0))
        
        # Kredit-kan semua akun Beban agar saldonya nol
        for b in beban:
            cursor.execute("INSERT INTO journal_entries (header_id, account_code, debit, credit) VALUES (?, ?, ?, ?)", (header_id, b[0], 0, b[1]))
        
        # Distribusi Laba Bersih
        if laba_bersih > 0:
            hak_pemilik = laba_bersih * 0.50
            hak_lainnya = laba_bersih - hak_pemilik # 50% gabungan untuk Pengelola & Operasional
            
            # Kredit ke Modal & Utang Bagi Hasil
            cursor.execute("INSERT INTO journal_entries (header_id, account_code, debit, credit) VALUES (?, ?, ?, ?)", (header_id, '3110', 0, hak_pemilik))
            cursor.execute("INSERT INTO journal_entries (header_id, account_code, debit, credit) VALUES (?, ?, ?, ?)", (header_id, '2120', 0, hak_lainnya))
        elif laba_bersih < 0:
            # Jika rugi, sepenuhnya memotong Modal Pemilik (Debit)
            cursor.execute("INSERT INTO journal_entries (header_id, account_code, debit, credit) VALUES (?, ?, ?, ?)", (header_id, '3110', abs(laba_bersih), 0))
            
        # ==========================================
        # JURNAL 2: MENUTUP PRIVE (Jika Ada)
        # ==========================================
        if saldo_prive > 0:
            cursor.execute("INSERT INTO journal_headers (date, description) VALUES (?, ?)", (tanggal_tutup, "Jurnal Penutup Prive"))
            header_prive_id = cursor.lastrowid
            
            # Debit Modal (3110), Kredit Prive (3120)
            cursor.execute("INSERT INTO journal_entries (header_id, account_code, debit, credit) VALUES (?, ?, ?, ?)", (header_prive_id, '3110', saldo_prive, 0))
            cursor.execute("INSERT INTO journal_entries (header_id, account_code, debit, credit) VALUES (?, ?, ?, ?)", (header_prive_id, '3120', 0, saldo_prive))
        
        conn.commit()
        return {"status": True, "pesan": "Tutup buku berhasil! Saldo nominal telah dinolkan dan laba didistribusikan ke Modal & Utang Bagi Hasil."}
        
    except Exception as e:
        conn.rollback()
        return {"status": False, "pesan": f"Terjadi kesalahan database: {str(e)}"}
    finally:
        conn.close()

def get_items():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM items", conn)
    conn.close()
    return df

def get_fixed_assets():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM fixed_assets", conn)
    conn.close()
    return df

# ==========================================
# FUNGSI MANAJEMEN STOK & OPERASIONAL
# ==========================================

def update_stok_barang(item_code, qty_change):
    """Menambah atau mengurangi stok fisik di tabel items"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE items SET stock = stock + ? WHERE item_code = ?", (qty_change, item_code))
    conn.commit()
    conn.close()

def simpan_panen(tanggal, qty_bagus, qty_busuk, estimasi_hpp_per_kg):
    """Mencatat panen: menambah stok barang jadi dan menjurnal ke persediaan"""
    # 1. Update stok fisik (Asumsi: masuk ke stok BRG-001 Strawberry Pengepul sbg standar gudang)
    update_stok_barang('BRG-001', qty_bagus)
    
    # 2. Jurnal Pengakuan Persediaan Hasil Panen (Kapitalisasi biaya ke aset)
    total_nilai_bagus = qty_bagus * estimasi_hpp_per_kg
    total_nilai_busuk = qty_busuk * estimasi_hpp_per_kg
    total_kredit = total_nilai_bagus + total_nilai_busuk
    
    if total_kredit > 0:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO journal_headers (date, description) VALUES (?, ?)", (tanggal, f"Hasil Panen: {qty_bagus}kg Bagus, {qty_busuk}kg Busuk"))
        header_id = cursor.lastrowid
        
        # (D) Persediaan Barang Jadi
        if total_nilai_bagus > 0:
            cursor.execute("INSERT INTO journal_entries (header_id, account_code, debit, credit) VALUES (?, ?, ?, ?)", (header_id, '1131', total_nilai_bagus, 0))
        # (D) Beban Kerusakan / Afkir
        if total_nilai_busuk > 0:
            cursor.execute("INSERT INTO journal_entries (header_id, account_code, debit, credit) VALUES (?, ?, ?, ?)", (header_id, '5120', total_nilai_busuk, 0))
        # (K) HPP / Ikhtisar Biaya Produksi (Memindahkan biaya yang sudah keluar jadi nilai aset)
        if total_kredit > 0:
            cursor.execute("INSERT INTO journal_entries (header_id, account_code, debit, credit) VALUES (?, ?, ?, ?)", (header_id, '5110', 0, total_kredit))
        
        conn.commit()
        conn.close()
    return True

def simpan_pembelian_barang(tanggal, item_code, qty, total_harga, metode_bayar):
    """Mencatat pembelian: menambah stok dan menjurnal pembelian"""
    # 1. Tambah stok fisik
    update_stok_barang(item_code, qty)
    
    # 2. Tentukan akun debit berdasarkan kategori barang di master data
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT category, item_name FROM items WHERE item_code = ?", (item_code,))
    row = cursor.fetchone()
    conn.close()
    
    kategori = row[0]
    nama_barang = row[1]
    
    akun_debit = '1132' # Default: Persediaan Bahan Baku
    if kategori == 'Perlengkapan':
        akun_debit = '1133' # Persediaan Perlengkapan
        
    akun_kredit = '1110' if metode_bayar == 'Tunai' else '2110' # Kas atau Utang
    
    # 3. Catat Jurnal
    return insert_journal(tanggal, f"Beli {qty} {nama_barang}", akun_debit, total_harga, akun_kredit, total_harga)

def insert_penjualan_perpetual(tanggal, desc_sales, akun_db_sales, akun_kr_sales, nominal_sales, desc_hpp, akun_db_hpp, akun_kr_hpp, nominal_hpp):
    """Mencatat 4 baris jurnal (Penjualan dan HPP) dalam 1 ID Transaksi (No. Bukti) yang sama."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # 1. Buat SATU Header untuk seluruh rangkaian transaksi penjualan ini
        cursor.execute("INSERT INTO journal_headers (date, description) VALUES (?, ?)", (tanggal, desc_sales))
        header_id = cursor.lastrowid
        
        # 2. Baris 1: Debit (Kas/Piutang)
        cursor.execute("INSERT INTO journal_entries (header_id, account_code, debit, credit) VALUES (?, ?, ?, ?)", (header_id, akun_db_sales, nominal_sales, 0))
        # 3. Baris 2: Kredit (Pendapatan Penjualan)
        cursor.execute("INSERT INTO journal_entries (header_id, account_code, debit, credit) VALUES (?, ?, ?, ?)", (header_id, akun_kr_sales, 0, nominal_sales))
        
        # 4. Baris 3: Debit (HPP)
        cursor.execute("INSERT INTO journal_entries (header_id, account_code, debit, credit) VALUES (?, ?, ?, ?)", (header_id, akun_db_hpp, nominal_hpp, 0))
        # 5. Baris 4: Kredit (Persediaan Barang Jadi)
        cursor.execute("INSERT INTO journal_entries (header_id, account_code, debit, credit) VALUES (?, ?, ?, ?)", (header_id, akun_kr_hpp, 0, nominal_hpp))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error Database: {e}")
        return False
    finally:
        conn.close()

def get_arus_kas():
    """Mengambil riwayat mutasi khusus untuk akun Kas & Bank (1110)"""
    conn = sqlite3.connect(DB_NAME)
    query = '''
        SELECT h.date AS Tanggal, h.description AS Keterangan, 
               e.debit AS Masuk, e.credit AS Keluar
        FROM journal_headers h
        JOIN journal_entries e ON h.id = e.header_id
        WHERE e.account_code = '1110'
        ORDER BY h.date ASC, h.id ASC
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def insert_fixed_asset(asset_code, asset_name, acquisition_date, acquisition_value, useful_life_years):
    """Menyimpan data aset tetap baru ke dalam database master."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO fixed_assets (asset_code, asset_name, acquisition_date, acquisition_value, useful_life_years) 
            VALUES (?, ?, ?, ?, ?)
        ''', (asset_code, asset_name, acquisition_date, acquisition_value, useful_life_years))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Menangkap error jika kode aset sudah pernah ada
        return False
    except Exception as e:
        print(f"Error Database Aset: {e}")
        return False
    finally:
        conn.close()

def get_riwayat_penjualan():
    """Mengambil riwayat penjualan dari jurnal untuk analitik dashboard"""
    conn = sqlite3.connect(DB_NAME)
    query = '''
        SELECT h.date AS Tanggal, h.description AS Keterangan, 
               a.name AS Jalur_Penjualan, e.credit AS Pendapatan
        FROM journal_headers h
        JOIN journal_entries e ON h.id = e.header_id
        JOIN accounts a ON e.account_code = a.code
        WHERE e.account_code IN ('4110', '4120') AND e.credit > 0
        ORDER BY h.date ASC, h.id ASC
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_coa_data():
    """Mengambil data Chart of Accounts dari database"""
    conn = sqlite3.connect(DB_NAME)
    query = "SELECT code AS 'Kode Akun', name AS 'Nama Akun', type AS 'Kategori', normal_balance AS 'Saldo Normal' FROM accounts"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def reset_database():
    """Mengosongkan seluruh isi tabel dan mereset sistem ke kondisi awal (Factory Reset)"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Nonaktifkan perlindungan foreign keys sementara
        cursor.execute("PRAGMA foreign_keys = OFF;")
        
        # Ambil daftar semua tabel yang ada di dalam database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        # Eksekusi penghapusan (DROP) untuk setiap tabel, KECUALI tabel sistem (sqlite_sequence)
        for table_name in tables:
            nama_tabel = table_name[0]
            # Lewati tabel internal bawaan SQLite
            if not nama_tabel.startswith('sqlite_'):
                cursor.execute(f"DROP TABLE IF EXISTS {nama_tabel};")
            else:
                # Untuk sqlite_sequence, kita cukup kosongkan isinya, jangan di-drop
                cursor.execute(f"DELETE FROM {nama_tabel};")
                
        conn.commit()
        conn.close()
        
        # Panggil fungsi inisialisasi untuk membuat ulang kerangka tabel & memasukkan data default (CoA/Katalog)
        init_db()
        
        return {"status": True, "pesan": "Berhasil! Seluruh data telah di-reset ke kondisi awal (Factory Reset)."}
    except Exception as e:
        return {"status": False, "pesan": f"Gagal mereset database: {e}"}

# Eksekusi inisiasi saat file dijalankan langsung
if __name__ == "__main__":
    init_db()
    print("Database berhasil diperbarui dengan seluruh fungsionalitas ERP!")
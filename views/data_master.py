import streamlit as st
import pandas as pd
import database

def render():
    st.title("Pusat Data Master")
    st.markdown("Katalog utama untuk mengelola daftar barang, harga, dan pengaturan inti perusahaan.")
    
    # KITA TAMBAHKAN 1 TAB BARU: "Pengaturan Sistem"
    tab_barang, tab_aset, tab_coa, tab_pengaturan = st.tabs([
        "Katalog Barang", 
        "Daftar Aset Tetap", 
        "Master Data Akun (CoA)",
        "Pengaturan Sistem"
    ])
    
    with tab_barang:
        st.subheader("Daftar Item & Persediaan")
        df_items = database.get_items()
        if not df_items.empty:
            df_items.columns = ['Kode Barang', 'Nama Barang', 'Kategori', 'Satuan', 'Harga Beli (Rp)', 'Harga Jual (Rp)', 'Stok Tersedia']
            st.dataframe(df_items.style.format({"Harga Beli (Rp)": "{:,.0f}", "Harga Jual (Rp)": "{:,.0f}", "Stok Tersedia": "{:,.2f}"}), use_container_width=True, hide_index=True)
        else:
            st.info("Katalog barang masih kosong.")
            
    with tab_aset:
        st.subheader("Registrasi & Pembelian Aset Tetap")
        st.markdown("Catat pembelian aset jangka panjang (seperti lahan, mesin, peralatan pertanian) agar tercatat di inventaris sekaligus di dalam Jurnal Buku Besar.")
        
        with st.form("form_tambah_aset"):
            col1, col2 = st.columns(2)
            with col1:
                kode_aset = st.text_input("Kode Aset", placeholder="Misal: AST-001")
                nama_aset = st.text_input("Nama Aset", placeholder="Misal: Pompa Air Shimizu")
                kategori_aset = st.selectbox("Kategori Aset (Akun Debit)", [
                    "1210 - Aset Tetap (Lahan & Bangunan)", 
                    "1220 - Peralatan Pertanian"
                ])
            with col2:
                tgl_perolehan = st.date_input("Tanggal Perolehan")
                nilai_perolehan = st.number_input("Nilai Perolehan (Rp)", min_value=0, step=100000)
                umur_ekonomis = st.number_input("Umur Ekonomis (Tahun)", min_value=1, step=1, help="Digunakan sebagai dasar perhitungan jurnal penyusutan.")
            
            metode_bayar = st.radio("Sistem Pembayaran", ["Tunai (Kas)", "Kredit (Utang Usaha)"])
            
            if st.form_submit_button("Simpan & Jurnal Aset", use_container_width=True):
                if not kode_aset or not nama_aset:
                    st.warning("⚠️ Harap lengkapi Kode dan Nama Aset.")
                elif nilai_perolehan <= 0:
                    st.warning("⚠️ Nilai perolehan tidak boleh nol.")
                else:
                    sukses_master = database.insert_fixed_asset(kode_aset, nama_aset, tgl_perolehan, nilai_perolehan, umur_ekonomis)
                    
                    if sukses_master:
                        kode_akun_debit = kategori_aset.split(" - ")[0]
                        kode_akun_kredit = "1110" if "Tunai" in metode_bayar else "2110"
                        desc_jurnal = f"Pembelian Aset: {kode_aset} - {nama_aset}"
                        
                        database.insert_journal(tgl_perolehan, desc_jurnal, kode_akun_debit, nilai_perolehan, kode_akun_kredit, nilai_perolehan)
                        
                        st.success(f"✅ Aset {nama_aset} berhasil diregistrasi ke katalog dan sukses dijurnal ke Buku Besar.")
                        st.rerun()
                    else:
                        st.error("❌ Gagal menyimpan aset! Kemungkinan Kode Aset tersebut sudah dipakai, silakan gunakan kode lain.")
                        
        st.markdown("---")
        st.subheader("Daftar Inventaris Aset")
        df_assets = database.get_fixed_assets()
        if not df_assets.empty:
            df_assets.columns = ['Kode Aset', 'Nama Aset', 'Tgl Perolehan', 'Nilai Perolehan (Rp)', 'Umur Ekonomis (Thn)']
            st.dataframe(df_assets.style.format({"Nilai Perolehan (Rp)": "{:,.0f}"}), use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada aset tetap yang diregistrasi di kebun.")

    with tab_coa:
        st.subheader("Daftar Chart of Accounts")
        st.dataframe(database.get_coa_data(), use_container_width=True, hide_index=True)

    # =======================================================
    # MODUL BARU: PENGATURAN SISTEM & FACTORY RESET
    # =======================================================
    with tab_pengaturan:
        st.subheader("⚙️ Pemeliharaan Sistem")
        st.markdown("Fitur kendali tingkat lanjut (*Advanced Control*) untuk administrator.")
        st.markdown("---")
        st.warning("Tindakan di bawah ini bersifat **permanen** dan tidak dapat dibatalkan. Pastikan Anda telah mengunduh (backup) Laporan Jurnal ke Excel sebelum mengeksekusi fitur ini.")
        
        with st.container(border=True):
            st.markdown("##### Factory Reset (Hapus Semua Data)")
            st.write("Fungsi ini akan memusnahkan **SELURUH TRANSAKSI**, riwayat panen, penjualan, jurnal, saldo, dan aset. Sistem akan dikembalikan dalam keadaan kosong seperti baru pertama kali diinstal.")
            
            # Mekanisme konfirmasi ganda agar tidak sengaja terpencet
            konfirmasi = st.text_input("Ketik kata 'RESET' (dengan huruf kapital) untuk membuka kunci pengaman:", placeholder="Ketik RESET disini...")
            
            if st.button("Hapus Seluruh Database", type="primary", use_container_width=True):
                if konfirmasi == "RESET":
                    hasil = database.reset_database()
                    if hasil['status']:
                        st.success(hasil['pesan'])
                        st.balloons() # Beri animasi balon sebagai penanda sukses
                        st.rerun()    # Segarkan tampilan
                    else:
                        st.error(hasil['pesan'])
                else:
                    st.error("❌ Validasi gagal! Anda harus mengetik kata 'RESET' secara tepat untuk mengeksekusi proses ini.")
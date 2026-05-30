import streamlit as st
import pandas as pd
import database

def render():
    st.title("Modul Operasional (Terintegrasi)")
    st.markdown("Seluruh form di sini akan secara otomatis memperbarui **Stok Fisik di Data Master** dan mencatat **Jurnal Double-Entry**.")

    df_items = database.get_items()
    
    opsi_barang_mentah = df_items[df_items['category'].isin(['Bahan Baku', 'Perlengkapan'])]['item_code'] + " - " + df_items[df_items['category'].isin(['Bahan Baku', 'Perlengkapan'])]['item_name']
    opsi_barang_jadi = df_items[df_items['category'] == 'Barang Jadi']['item_code'] + " - " + df_items[df_items['category'] == 'Barang Jadi']['item_name']

    tab_panen, tab_pembelian, tab_pemakaian, tab_penjualan, tab_beban = st.tabs([
        "1. Input Panen", "2. Beli Barang", "3. Pakai Bahan", "4. Penjualan", "5. Input Beban"
    ])

    with tab_panen:
        with st.form("form_panen"):
            st.subheader("Catat Hasil Panen (Masuk Gudang)")
            tanggal_panen = st.date_input("Tanggal Panen")
            
            col1, col2 = st.columns(2)
            with col1:
                total_panen = st.number_input("Total Panen Kotor (Kg)", min_value=0.0, value=25.0, step=0.5)
            with col2:
                persen_busuk = st.number_input("Estimasi Buah Busuk (%)", min_value=0.0, max_value=100.0, value=3.0, step=0.5)
            
            estimasi_hpp = st.number_input("Estimasi Biaya Modal / HPP per Kg (Rp)", min_value=0, value=5000, step=1000, help="Nilai ini digunakan untuk menjurnal barang jadi ke dalam aset.")

            buah_busuk_kg = total_panen * (persen_busuk / 100)
            buah_bagus_kg = total_panen - buah_busuk_kg

            st.info(f"**Kalkulasi:** {buah_bagus_kg:.2f} Kg akan ditambahkan ke Stok Persediaan. {buah_busuk_kg:.2f} Kg masuk Beban Afkir.")
            
            if st.form_submit_button("Simpan & Kapitalisasi Persediaan", use_container_width=True):
                sukses = database.simpan_panen(tanggal_panen, buah_bagus_kg, buah_busuk_kg, estimasi_hpp)
                if sukses:
                    st.success(f"✅ Panen direkam! Stok bertambah dan nilai Rp {buah_bagus_kg * estimasi_hpp:,.0f} diposting ke Aset Persediaan.")

    with tab_pembelian:
        with st.form("form_pembelian"):
            st.subheader("Pembelian Inventaris (Restock)")
            tanggal_beli = st.date_input("Tanggal Pembelian")
            
            barang_dibeli = st.selectbox("Pilih Barang", opsi_barang_mentah.tolist())
            
            col1, col2 = st.columns(2)
            with col1:
                qty_beli = st.number_input("Jumlah Beli", min_value=1.0, step=1.0)
            with col2:
                total_harga = st.number_input("Total Harga Beli (Rp)", min_value=0, step=10000)
            
            metode_bayar = st.radio("Metode Pembayaran", ["Tunai", "Kredit (Utang)"])

            if st.form_submit_button("Catat Pembelian & Tambah Stok", use_container_width=True):
                kode_barang = barang_dibeli.split(" - ")[0]
                if total_harga <= 0:
                    st.warning("Total harga tidak boleh nol.")
                else:
                    sukses = database.simpan_pembelian_barang(tanggal_beli, kode_barang, qty_beli, total_harga, metode_bayar)
                    if sukses:
                        st.success(f"✅ Pembelian berhasil! Stok {kode_barang} bertambah dan jurnal dicatat.")

    with tab_pemakaian:
        with st.form("form_pemakaian"):
            st.subheader("Pemakaian Bahan ke Kebun")
            tanggal_pakai = st.date_input("Tanggal Pemakaian")
            
            barang_dipakai = st.selectbox("Pilih Barang yang Dipakai", opsi_barang_mentah.tolist())
            
            col1, col2 = st.columns(2)
            with col1:
                qty_pakai = st.number_input("Jumlah Dipakai", min_value=1.0, step=1.0)
            with col2:
                nilai_pemakaian = st.number_input("Estimasi Nilai Pemakaian (Rp)", min_value=0, step=5000)

            if st.form_submit_button("Catat Pemakaian & Kurangi Stok", use_container_width=True):
                kode_barang = barang_dipakai.split(" - ")[0]
                if nilai_pemakaian <= 0:
                    st.warning("Nilai pemakaian harus diisi untuk jurnal akuntansi.")
                else:
                    database.update_stok_barang(kode_barang, -qty_pakai)
                    
                    kategori = df_items[df_items['item_code'] == kode_barang]['category'].values[0]
                    akun_debit = "6110" if kategori == 'Bahan Baku' else "6120"
                    akun_kredit = "1132" if kategori == 'Bahan Baku' else "1133"
                    
                    database.insert_journal(tanggal_pakai, f"Pemakaian {qty_pakai} {kode_barang}", akun_debit, nilai_pemakaian, akun_kredit, nilai_pemakaian)
                    st.success(f"✅ Pemakaian dicatat! Stok {kode_barang} berkurang {qty_pakai} dan Beban diakui.")

    with tab_penjualan:
        with st.form("form_penjualan"):
            st.subheader("Penjualan Barang Jadi & Pengendalian Stok")
            tanggal_jual = st.date_input("Tanggal Penjualan")
            
            barang_dijual = st.selectbox("Produk Terjual", opsi_barang_jadi.tolist())
            
            kode_jual = barang_dijual.split(" - ")[0]
            stok_saat_ini = df_items[df_items['item_code'] == kode_jual]['stock'].values[0]
            satuan_jual = df_items[df_items['item_code'] == kode_jual]['unit'].values[0]
            
            if stok_saat_ini <= 0:
                st.error(f"🚨 **Stok Habis!** Saat ini stok tersedia: 0 {satuan_jual}. Sistem akan mengunci penjualan.")
            elif stok_saat_ini < 5:
                st.warning(f"⚠️ **Stok Tipis!** Stok tersedia: {stok_saat_ini:.2f} {satuan_jual}")
            else:
                st.success(f"📦 **Stok Aman:** Tersedia {stok_saat_ini:.2f} {satuan_jual}")
            st.markdown("---")
            
            col_jalur, col_bayar = st.columns(2)
            with col_jalur:
                jenis_penjualan = st.radio("Jalur Penjualan", ["Penjualan Pengepul", "Wisata Petik"])
            with col_bayar:
                metode_bayar_jual = st.radio("Metode Pembayaran", ["Tunai", "Kredit (Piutang)"])
            
            qty_jual = st.number_input("Jumlah Terjual (Kg)", min_value=0.0, value=0.0, step=0.5, help="Masukkan dalam satuan Kilogram agar sinkron dengan hasil panen.")
            
            if "Pengepul" in jenis_penjualan:
                harga_per_kg = 24000
                st.caption("ℹ️ Estimasi Pengepul: Rp 24.000 / Kg (Setara ~4 Pack)")
            else:
                harga_per_kg = 100000
                st.caption("ℹ️ Estimasi Wisata Petik: Rp 100.000 / Kg (Setara Rp 10.000 / Ons)")
            
            harga_beli_satuan = df_items[df_items['item_code'] == kode_jual]['purchase_price'].values[0]
            if harga_beli_satuan == 0: harga_beli_satuan = 5000 
            
            total_pendapatan = st.number_input("Total Pendapatan Aktual (Rp)", min_value=0, value=int(qty_jual * harga_per_kg), step=5000)
            total_hpp = int(qty_jual * harga_beli_satuan)

            st.info(f"**Kalkulasi Akuntansi (Perpetual):**\n"
                    f"* **Nilai Penjualan:** Rp {total_pendapatan:,}\n"
                    f"* **Beban HPP (Harga Pokok):** Rp {total_hpp:,}")

            if st.form_submit_button("Catat Penjualan & Jurnal", use_container_width=True):
                if qty_jual <= 0:
                    st.warning("⚠️ Jumlah terjual tidak boleh nol.")
                elif qty_jual > stok_saat_ini:
                    st.error(f"❌ **Transaksi Ditolak!** Jumlah {qty_jual} {satuan_jual} melebihi stok gudang ({stok_saat_ini:.2f} {satuan_jual}).")
                elif total_pendapatan <= 0:
                    st.warning("⚠️ Total pendapatan tidak valid.")
                else:
                    database.update_stok_barang(kode_jual, -qty_jual)
                    
                    akun_debit_sales = "1110" if metode_bayar_jual == "Tunai" else "1120" 
                    akun_kredit_sales = "4110" if "Pengepul" in jenis_penjualan else "4120" 
                    desc_sales = f"Penjualan {qty_jual} Kg ({jenis_penjualan} - {metode_bayar_jual})"
                    
                    desc_hpp = f"HPP atas Penjualan {qty_jual} Kg"
                    akun_debit_hpp = "5110"
                    akun_kredit_hpp = "1131"
                    
                    sukses = database.insert_penjualan_perpetual(
                        tanggal_jual, desc_sales, 
                        akun_debit_sales, akun_kredit_sales, total_pendapatan,
                        desc_hpp, akun_debit_hpp, akun_kredit_hpp, total_hpp
                    )
                    
                    if sukses:
                        st.success(f"✅ Penjualan {qty_jual} Kg sukses dicatat dengan rapi dalam 1 No. Bukti!")
                        st.rerun()

    with tab_beban:
        with st.form("form_beban"):
            st.subheader("Catat Pengeluaran & Beban Harian")
            tanggal_beban = st.date_input("Tanggal Pengeluaran")
            
            df_coa = database.get_coa_data()
            df_beban = df_coa[(df_coa['Kategori'] == 'Beban') & (~df_coa['Nama Akun'].str.contains('Penyusutan|HPP', case=False, na=False))]
            opsi_beban = df_beban['Kode Akun'] + " - " + df_beban['Nama Akun']
            
            akun_beban_pilihan = st.selectbox("Pilih Kategori Beban", opsi_beban.tolist())
            
            deskripsi_beban = st.text_input("Keterangan Detail (Untuk Nota/Kuitansi)", placeholder="Misal: Beli bensin genset 5 liter / Konsumsi pekerja / Listrik")
            
            col_nom, col_bayar = st.columns(2)
            with col_nom:
                nominal_beban = st.number_input("Nominal Pengeluaran (Rp)", min_value=0, step=5000)
            with col_bayar:
                metode_bayar_beban = st.radio("Sumber Dana", ["Tunai (Kas Laci)", "Belum Dibayar (Utang Usaha)"])

            if st.form_submit_button("Catat Pengeluaran & Jurnal", use_container_width=True):
                if nominal_beban <= 0:
                    st.warning("⚠️ Nominal pengeluaran tidak boleh kosong.")
                elif not deskripsi_beban:
                    st.warning("⚠️ Keterangan detail harus diisi sebagai bukti.")
                else:
                    kode_debit_beban = akun_beban_pilihan.split(" - ")[0]
                    kode_kredit_beban = "1110" if "Tunai" in metode_bayar_beban else "2110"
                    
                    sukses = database.insert_journal(tanggal_beban, f"Beban: {deskripsi_beban}", kode_debit_beban, nominal_beban, kode_kredit_beban, nominal_beban)
                    if sukses:
                        st.success(f"✅ Pengeluaran senilai Rp {nominal_beban:,.0f} berhasil dicatat ke dalam Buku Besar!")
                        st.rerun()
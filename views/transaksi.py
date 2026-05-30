import streamlit as st
import pandas as pd
import database

def render():
    # Header 
    st.markdown("<h2 style='color: #111827; font-weight: 800; margin-bottom: 0;'>Financial Ledger</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #6B7280; font-size: 14px;'>Modul pencatatan transaksi dan koreksi jurnal berbasis Audit Trail.</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # 4 Tabs (Menambahkan Tab Koreksi Jurnal)
    tab_jurnal_umum, tab_penyesuaian, tab_koreksi, tab_tutup_buku = st.tabs([
        "Jurnal Umum (Harian)", 
        "Jurnal Penyesuaian", 
        "Koreksi (Audit Trail)", 
        "Tutup Buku"
    ])
    
    df_coa = database.get_coa_data()
    daftar_akun = []
    if not df_coa.empty:
        daftar_akun = df_coa['Kode Akun'] + " - " + df_coa['Nama Akun']

    # =========================================================================
    # TAB 1: JURNAL UMUM 
    # =========================================================================
    with tab_jurnal_umum:
        st.markdown("Input transaksi manual yang tidak ter-*cover* di modul operasional.")
        with st.container(border=True):
            with st.form("form_jurnal"):
                col_tanggal, col_deskripsi = st.columns([1, 2])
                with col_tanggal:
                    tanggal_transaksi = st.date_input("Tanggal Transaksi")
                with col_deskripsi:
                    deskripsi = st.text_input("Keterangan", placeholder="Misal: Pembayaran utang supplier")

                st.markdown("<hr style='margin: 10px 0; border-color: #E5E7EB;'>", unsafe_allow_html=True)
                st.markdown("<p style='color:#E11D48; font-weight:bold; font-size: 14px; margin-bottom:5px;'>SISI DEBIT</p>", unsafe_allow_html=True)
                col_akun_db, col_nominal_db = st.columns([2, 1])
                with col_akun_db:
                    akun_debit = st.selectbox("Akun Debit", daftar_akun, key="db_ju")
                with col_nominal_db:
                    nominal_debit = st.number_input("Nominal Debit (Rp)", min_value=0, step=10000, key="nom_db_ju")

                st.markdown("<p style='color:#E11D48; font-weight:bold; font-size: 14px; margin-bottom:5px; margin-top:15px;'>SISI KREDIT</p>", unsafe_allow_html=True)
                col_akun_kr, col_nominal_kr = st.columns([2, 1])
                with col_akun_kr:
                    akun_kredit = st.selectbox("Akun Kredit", daftar_akun, key="kr_ju")
                with col_nominal_kr:
                    nominal_kredit = st.number_input("Nominal Kredit (Rp)", min_value=0, step=10000, key="nom_kr_ju")

                st.write("")
                if nominal_debit > 0 or nominal_kredit > 0:
                    if nominal_debit == nominal_kredit:
                        st.success("Status: Balance ✓")
                    else:
                        st.error(f"Status: Tidak Balance (Selisih Rp {abs(nominal_debit - nominal_kredit):,})")

                if st.form_submit_button("Posting Jurnal Harian", type="primary", use_container_width=True):
                    kode_debit = akun_debit.split(" - ")[0]
                    kode_kredit = akun_kredit.split(" - ")[0]
                    if nominal_debit != nominal_kredit or nominal_debit <= 0:
                        st.warning("⚠️ Transaksi tidak valid / tidak balance!")
                    else:
                        sukses = database.insert_journal(tanggal_transaksi, deskripsi, kode_debit, nominal_debit, kode_kredit, nominal_kredit)
                        if sukses: st.success("✅ Jurnal berhasil diposting!")
    
    # =========================================================================
    # TAB 2: JURNAL PENYESUAIAN 
    # =========================================================================
    with tab_penyesuaian:
        st.markdown("Digunakan pada akhir periode (bulan/tahun) untuk mengakui beban penyusutan alat atau koreksi nilai persediaan.")
        with st.container(border=True):
            with st.form("form_ajp"):
                col_tanggal_ajp, col_deskripsi_ajp = st.columns([1, 2])
                with col_tanggal_ajp:
                    tanggal_ajp = st.date_input("Tanggal AJP")
                with col_deskripsi_ajp:
                    deskripsi_ajp = st.selectbox("Jenis Penyesuaian", [
                        "AJP: Penyusutan Peralatan Pertanian",
                        "AJP: Penyesuaian Fisik Persediaan Pupuk/Obat",
                        "AJP: Alokasi Beban Dibayar Dimuka"
                    ])

                st.markdown("<p style='color:#E11D48; font-weight:bold; font-size: 14px; margin-bottom:5px; margin-top:10px;'>DEBIT (Beban/Biaya)</p>", unsafe_allow_html=True)
                col_akun_db_ajp, col_nominal_db_ajp = st.columns([2, 1])
                with col_akun_db_ajp:
                    akun_debit_ajp = st.selectbox("Akun Debit", daftar_akun, key="db_ajp")
                with col_nominal_db_ajp:
                    nominal_debit_ajp = st.number_input("Nominal (Rp)", min_value=0, step=10000, key="nom_db_ajp")

                st.markdown("<p style='color:#E11D48; font-weight:bold; font-size: 14px; margin-bottom:5px; margin-top:15px;'>KREDIT (Akumulasi/Aset)</p>", unsafe_allow_html=True)
                col_akun_kr_ajp, col_nominal_kr_ajp = st.columns([2, 1])
                with col_akun_kr_ajp:
                    akun_kredit_ajp = st.selectbox("Akun Kredit", daftar_akun, key="kr_ajp")
                with col_nominal_kr_ajp:
                    nominal_kredit_ajp = st.number_input("Nominal (Rp)", min_value=0, step=10000, key="nom_kr_ajp")

                st.write("")
                if st.form_submit_button("Posting Jurnal Penyesuaian", type="primary", use_container_width=True):
                    kode_debit_ajp = akun_debit_ajp.split(" - ")[0]
                    kode_kredit_ajp = akun_kredit_ajp.split(" - ")[0]
                    if nominal_debit_ajp != nominal_kredit_ajp or nominal_debit_ajp <= 0:
                        st.warning("⚠️ AJP tidak valid / tidak balance!")
                    else:
                        sukses = database.insert_journal(tanggal_ajp, deskripsi_ajp, kode_debit_ajp, nominal_debit_ajp, kode_kredit_ajp, nominal_kredit_ajp)
                        if sukses: st.success("✅ Jurnal Penyesuaian berhasil direkam!")

    # =========================================================================
    # TAB 3: KOREKSI JURNAL & AUDIT TRAIL 
    # =========================================================================
    with tab_koreksi:
        st.markdown("""
            <div style='background-color: #FFF1F2; padding: 15px; border-radius: 8px; border-left: 4px solid #E11D48; margin-bottom: 20px;'>
                <h4 style='color: #E11D48; margin-top: 0; font-size: 16px;'>Sistem Jejak Audit (Audit Trail) Aktif</h4>
                <p style='color: #4B5563; font-size: 13px; margin-bottom: 0;'>
                Sesuai standar akuntansi (SAK EMKM), transaksi yang salah <b>dilarang dihapus</b>. 
                Fitur ini akan otomatis memposting <b>Jurnal Pembalik (Reversing)</b> untuk menetralkan nominal lama, 
                lalu memposting jurnal baru hasil revisi Anda.
                </p>
            </div>
        """, unsafe_allow_html=True)

        df_all = database.get_jurnal_umum()
        
        if df_all.empty:
            st.info("Belum ada transaksi yang bisa dikoreksi.")
        else:
            # Mengambil daftar No Bukti yang Unik & Bukan hasil batal
            df_unik = df_all.drop_duplicates(subset=['No. Bukti'])
            # Filter jurnal yang tidak mengandung kata [BATAL] atau [REVISI] agar bersih
            df_valid = df_unik[~df_unik['Keterangan'].str.contains(r'\[BATAL\]|\[REVISI\]', na=False, regex=True)]

            if df_valid.empty:
                st.info("Semua transaksi saat ini sudah dikoreksi atau dibatalkan.")
            else:
                with st.container(border=True):
                    st.markdown("#### 1. Pilih Transaksi yang Salah")
                    opsi_bukti = df_valid['No. Bukti'].astype(str) + " | " + df_valid['Tanggal'].astype(str) + " | " + df_valid['Keterangan'].astype(str)
                    pilihan = st.selectbox("Cari Jurnal yang Ingin Direvisi:", opsi_bukti.tolist())
                    
                    target_no_bukti = pilihan.split(" | ")[0]
                    
                    # Tampilkan rincian jurnal lama (Memaksa perbandingan format String)
                    df_lama = df_all[df_all['No. Bukti'].astype(str) == str(target_no_bukti)]
                    st.write("Rincian Jurnal Lama:")
                    st.dataframe(df_lama.style.format({"Debit": "Rp {:,.0f}", "Kredit": "Rp {:,.0f}"}), use_container_width=True, hide_index=True)

                    st.markdown("<hr style='margin: 20px 0; border-color: #E5E7EB;'>", unsafe_allow_html=True)
                    st.markdown("#### 2. Masukkan Data yang Benar (Revisi)")

                    with st.form("form_koreksi"):
                        tgl_koreksi = st.date_input("Tanggal Koreksi", pd.to_datetime(df_lama['Tanggal'].iloc[0]).date())
                        ket_koreksi = st.text_input("Keterangan Benar", value=df_lama['Keterangan'].iloc[0])

                        st.markdown("<p style='color:#E11D48; font-weight:bold; font-size: 14px; margin-bottom:5px; margin-top:10px;'>REVISI SISI DEBIT</p>", unsafe_allow_html=True)
                        rc1, rc2 = st.columns([2, 1])
                        rev_akun_debit = rc1.selectbox("Akun Debit Benar", daftar_akun, key="r_db_akun")
                        rev_nom_debit = rc2.number_input("Nominal Debit Benar (Rp)", min_value=0, step=10000, value=int(df_lama['Debit'].max()), key="r_db_nom")

                        st.markdown("<p style='color:#E11D48; font-weight:bold; font-size: 14px; margin-bottom:5px; margin-top:15px;'>REVISI SISI KREDIT</p>", unsafe_allow_html=True)
                        rc3, rc4 = st.columns([2, 1])
                        rev_akun_kredit = rc3.selectbox("Akun Kredit Benar", daftar_akun, key="r_kr_akun")
                        rev_nom_kredit = rc4.number_input("Nominal Kredit Benar (Rp)", min_value=0, step=10000, value=int(df_lama['Kredit'].max()), key="r_kr_nom")

                        st.write("")
                        submit_koreksi = st.form_submit_button("Simpan Koreksi & Buat Jejak Audit", type="primary", use_container_width=True)

                        if submit_koreksi:
                            if rev_nom_debit != rev_nom_kredit or rev_nom_debit <= 0:
                                st.error("Gagal: Total Debit dan Kredit revisi harus BALANCE dan > 0!")
                            else:
                                # 1. EKSTRAK DATA LAMA (Sistem Anti-Salah Kolom)
                                old_ket = df_lama['Keterangan'].iloc[0]
                                old_nom = int(df_lama['Debit'].max())
                                
                                # Tarik daftar kode valid dari master untuk dicocokkan
                                valid_codes = database.get_coa_data()['Kode Akun'].astype(str).tolist()
                                
                                # Fungsi menyisir baris mencari kode angka akuntansi yang valid
                                def get_valid_code(row):
                                    for val in row.values:
                                        k = str(val).split(" - ")[0].strip()
                                        if k in valid_codes: return k
                                    return None

                                # BERSIH DARI TYPO: Menarik data dengan variabel df_lama yang benar
                                old_kode_debit = get_valid_code(df_lama[df_lama['Debit'] > 0].iloc[0])
                                old_kode_kredit = get_valid_code(df_lama[df_lama['Kredit'] > 0].iloc[0])

                                if not old_kode_debit or not old_kode_kredit:
                                    st.error("Gagal: Sistem tidak menemukan format Kode Akun yang valid di data lama.")
                                else:
                                    # 2. EKSEKUSI JURNAL PEMBALIK (Tukar posisi Debit & Kredit lama)
                                    ket_batal = f"[BATAL] {old_ket}"
                                    
                                    # PENTING: old_kode_kredit ditaruh di posisi debit, dan sebaliknya
                                    sukses_batal = database.insert_journal(tgl_koreksi, ket_batal, old_kode_kredit, old_nom, old_kode_debit, old_nom)

                                    if not sukses_batal:
                                        st.error(f"⚠️ Gagal membuat Jurnal Pembalik untuk kode {old_kode_kredit} & {old_kode_debit}. Ditolak oleh Database!")
                                    else:
                                        # 3. EKSEKUSI JURNAL REVISI BARU
                                        new_kode_debit = rev_akun_debit.split(" - ")[0]
                                        new_kode_kredit = rev_akun_kredit.split(" - ")[0]
                                        ket_revisi = f"[REVISI] {ket_koreksi}"
                                        
                                        sukses_revisi = database.insert_journal(tgl_koreksi, ket_revisi, new_kode_debit, rev_nom_debit, new_kode_kredit, rev_nom_kredit)
                                        
                                        if sukses_revisi:
                                            st.success("✅ Jejak Audit Sempurna! Jurnal lama telah dibalik [BATAL], dan jurnal baru diposting [REVISI].")
                                            st.rerun()
                                        else:
                                            st.error("⚠️ Jurnal Batal berhasil, namun Jurnal Revisi gagal disimpan!")

    # =========================================================================
    # TAB 4: TUTUP BUKU 
    # =========================================================================
    with tab_tutup_buku:
        st.markdown("### ⚠️ PERINGATAN: Eksekusi Tutup Buku")
        st.markdown("Proses ini akan menihilkan semua saldo Pendapatan, Beban, dan Prive, lalu memindahkannya secara otomatis ke **Modal Mas Imam** dan **Utang Bagi Hasil** sesuai proporsi dokumen (50-20-30). Lakukan ini hanya pada akhir periode akuntansi (akhir bulan/tahun).")
        
        with st.container(border=True):
            with st.form("form_tutup_buku"):
                tanggal_tutup = st.date_input("Tanggal Tutup Buku")
                
                st.warning("Pastikan semua Jurnal Harian dan Jurnal Penyesuaian (AJP) bulan ini sudah terinput sebelum mengeksekusi proses ini.")
                
                submit_tutup = st.form_submit_button("🔒 Eksekusi Tutup Buku Sekarang", type="primary", use_container_width=True)
                
                if submit_tutup:
                    hasil = database.eksekusi_tutup_buku(tanggal_tutup)
                    if hasil["status"]:
                        st.success(hasil["pesan"])
                    else:
                        st.error(hasil["pesan"])
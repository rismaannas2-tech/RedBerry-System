import streamlit as st
import pandas as pd
import database
import io

def render():
    st.title("Laporan Keuangan Komprehensif")
    st.markdown("Menyajikan siklus pelaporan penuh: Laba Rugi, Perubahan Modal, Neraca, dan Arus Kas secara *real-time*.")

    # 1. Menarik SATU SUMBER KEBENARAN: Neraca Saldo
    df_neraca = database.get_neraca_saldo()
    df_coa = database.get_coa_data()

    if not df_neraca.empty:
        df_gabungan = pd.merge(df_neraca, df_coa[['Kode Akun', 'Kategori']], on='Kode Akun', how='left')
    else:
        df_gabungan = pd.DataFrame(columns=['Kode Akun', 'Nama Akun', 'Debit', 'Kredit', 'Kategori'])

    # --- LOGIKA KUNCI: KALKULASI DARI SATU SUMBER AGAR 100% BALANCE ---
    df_pendapatan = df_gabungan[df_gabungan['Kategori'] == 'Pendapatan'].copy()
    df_pendapatan['Saldo'] = df_pendapatan['Kredit'] - df_pendapatan['Debit']
    tot_pendapatan = df_pendapatan['Saldo'].sum() if not df_pendapatan.empty else 0

    df_beban_all = df_gabungan[df_gabungan['Kategori'] == 'Beban'].copy()
    df_beban_all['Saldo'] = df_beban_all['Debit'] - df_beban_all['Kredit']
    tot_beban_all = df_beban_all['Saldo'].sum() if not df_beban_all.empty else 0

    laba_bersih = tot_pendapatan - tot_beban_all

    modal_awal = 0
    prive = 0
    if not df_gabungan.empty:
        modal_row = df_gabungan[df_gabungan['Kode Akun'] == '3110']
        if not modal_row.empty: 
            modal_awal = modal_row['Kredit'].values[0] - modal_row['Debit'].values[0]
        
        prive_row = df_gabungan[df_gabungan['Kode Akun'] == '3120']
        if not prive_row.empty: 
            prive = prive_row['Debit'].values[0] - prive_row['Kredit'].values[0]

    modal_akhir = modal_awal + laba_bersih - prive

    df_hpp = df_beban_all[df_beban_all['Kode Akun'].astype(str).str.startswith('5')]
    tot_hpp = df_hpp['Saldo'].sum() if not df_hpp.empty else 0
    
    df_beban_op = df_beban_all[df_beban_all['Kode Akun'].astype(str).str.startswith('6')]
    tot_beban_op = df_beban_op['Saldo'].sum() if not df_beban_op.empty else 0
    
    laba_kotor = tot_pendapatan - tot_hpp
    laba_operasional = laba_kotor - tot_beban_op

    # TABS LAPORAN TERPADU
    tab_jurnal, tab_buku_besar, tab_trial_balance, tab_lajur, tab_lr, tab_pm, tab_neraca, tab_ak = st.tabs([
        "Jurnal Umum", 
        "Buku Besar", 
        "Neraca Saldo", 
        "Neraca Lajur",
        "Laba Rugi", 
        "Perubahan Modal", 
        "Neraca (Balance Sheet)", 
        "Arus Kas"
    ])

    with tab_jurnal:
        st.subheader("Ringkasan Jurnal Umum")
        st.markdown("Setiap aktivitas operasional dikelompokkan ke dalam blok berdasarkan **No. Bukti** transaksi.")
        
        df_jurnal = database.get_jurnal_umum()
        
        if not df_jurnal.empty:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_jurnal.to_excel(writer, index=False, sheet_name='Jurnal Umum')
            st.download_button(label="📥 Download Jurnal (Excel)", data=buffer.getvalue(), file_name="Jurnal_Umum_Kebun.xlsx", mime="application/vnd.ms-excel", type="primary")
            
            baris_baru = []
            for no_bukti, group in df_jurnal.groupby('No. Bukti', sort=False):
                baris_baru.append(group)
                baris_kosong = pd.DataFrame([[None] * len(df_jurnal.columns)], columns=df_jurnal.columns)
                baris_baru.append(baris_kosong)
            
            df_display = pd.concat(baris_baru, ignore_index=True).iloc[:-1]
            df_display = df_display.fillna("")

            def format_rupiah(val):
                if val == "": return ""
                return f"{val:,.0f}"

            st.dataframe(
                df_display.style.format({
                    "No. Bukti": lambda x: f"TRX-{int(x):04d}" if x != "" else "",
                    "Debit": format_rupiah, 
                    "Kredit": format_rupiah
                }), 
                use_container_width=True, 
                hide_index=True
            )
        else:
            st.info("Belum ada transaksi yang tercatat.")

    with tab_buku_besar:
        st.subheader("Filter Buku Besar")
        opsi_akun = df_coa['Kode Akun'] + " - " + df_coa['Nama Akun']
        pilihan_akun = st.selectbox("Pilih Akun", opsi_akun)
        code_akun = pilihan_akun.split(" - ")[0]
        df_bb = database.get_buku_besar(code_akun)
        
        if not df_bb.empty:
            tipe_akun = df_coa[df_coa['Kode Akun'] == code_akun]['Saldo Normal'].values[0]
            if tipe_akun == "Debit":
                df_bb['Saldo'] = df_bb['Debit'].cumsum() - df_bb['Kredit'].cumsum()
            else:
                df_bb['Saldo'] = df_bb['Kredit'].cumsum() - df_bb['Debit'].cumsum()
            st.dataframe(df_bb.style.format({"Debit": "{:,.0f}", "Kredit": "{:,.0f}", "Saldo": "{:,.0f}"}), use_container_width=True, hide_index=True)
        else:
            st.info(f"Tidak ada aktivitas untuk akun {pilihan_akun}.")
            
    with tab_trial_balance:
        st.subheader("Neraca Saldo (Trial Balance)")
        st.markdown("Rekapitulasi saldo akhir semua akun untuk pengecekan keseimbangan debit dan kredit.")
        if not df_neraca.empty:
            total_db = df_neraca['Debit'].sum()
            total_kr = df_neraca['Kredit'].sum()
            
            col1, col2 = st.columns(2)
            col1.metric("Total Debit", f"Rp {total_db:,.0f}")
            col2.metric("Total Kredit", f"Rp {total_kr:,.0f}")
            
            if total_db == total_kr:
                st.success("✅ NERACA SALDO SEIMBANG (BALANCE)")
            else:
                st.error(f"❌ TIDAK SEIMBANG! Terdapat selisih Rp {abs(total_db - total_kr):,.0f}")
            
            st.dataframe(df_neraca.style.format({"Debit": "{:,.0f}", "Kredit": "{:,.0f}"}), use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada saldo akun yang tercatat.")

    with tab_lajur:
        st.subheader("Neraca Lajur (10 Kolom)")
        st.markdown("Kertas kerja (*worksheet*) standar akuntansi untuk mempermudah penyusunan laporan keuangan.")

        df_ns = database.get_neraca_saldo()
        df_coa = database.get_coa_data()

        if not df_ns.empty:
            df_lajur = pd.merge(df_ns, df_coa[['Kode Akun', 'Kategori']], on='Kode Akun', how='left').fillna(0)

            df_lajur['NS_D'] = df_lajur['Debit']
            df_lajur['NS_K'] = df_lajur['Kredit']
            df_lajur['AJP_D'] = 0
            df_lajur['AJP_K'] = 0
            df_lajur['NSD_D'] = df_lajur['NS_D'] + df_lajur['AJP_D']
            df_lajur['NSD_K'] = df_lajur['NS_K'] + df_lajur['AJP_K']

            df_lajur['LR_D'] = df_lajur.apply(lambda x: x['NSD_D'] if x['Kategori'] == 'Beban' else 0, axis=1)
            df_lajur['LR_K'] = df_lajur.apply(lambda x: x['NSD_K'] if x['Kategori'] == 'Pendapatan' else 0, axis=1)

            df_lajur['N_D'] = df_lajur.apply(lambda x: x['NSD_D'] if x['Kategori'] in ['Aset', 'Ekuitas'] and x['NSD_D'] > 0 else 0, axis=1)
            df_lajur['N_K'] = df_lajur.apply(lambda x: x['NSD_K'] if x['Kategori'] in ['Kewajiban', 'Ekuitas'] and x['NSD_K'] > 0 else 0, axis=1)

            df_lajur['Total_Baris'] = df_lajur['NS_D'] + df_lajur['NS_K'] + df_lajur['AJP_D'] + df_lajur['AJP_K']
            df_lajur = df_lajur[df_lajur['Total_Baris'] > 0].copy()

            totals = {
                'Kode Akun': '', 'Nama Akun': 'Jumlah',
                'NS_D': df_lajur['NS_D'].sum(), 'NS_K': df_lajur['NS_K'].sum(),
                'AJP_D': df_lajur['AJP_D'].sum(), 'AJP_K': df_lajur['AJP_K'].sum(),
                'NSD_D': df_lajur['NSD_D'].sum(), 'NSD_K': df_lajur['NSD_K'].sum(),
                'LR_D': df_lajur['LR_D'].sum(), 'LR_K': df_lajur['LR_K'].sum(),
                'N_D': df_lajur['N_D'].sum(), 'N_K': df_lajur['N_K'].sum()
            }
            df_lajur = pd.concat([df_lajur, pd.DataFrame([totals])], ignore_index=True)

            laba_bersih_lajur = totals['LR_K'] - totals['LR_D']
            if laba_bersih_lajur >= 0:
                laba_row = {
                    'Kode Akun': '', 'Nama Akun': 'Laba Bersih',
                    'NS_D': 0, 'NS_K': 0, 'AJP_D': 0, 'AJP_K': 0, 'NSD_D': 0, 'NSD_K': 0,
                    'LR_D': laba_bersih_lajur, 'LR_K': 0, 'N_D': 0, 'N_K': laba_bersih_lajur
                }
            else:
                laba_row = {
                    'Kode Akun': '', 'Nama Akun': 'Rugi Bersih',
                    'NS_D': 0, 'NS_K': 0, 'AJP_D': 0, 'AJP_K': 0, 'NSD_D': 0, 'NSD_K': 0,
                    'LR_D': 0, 'LR_K': abs(laba_bersih_lajur), 'N_D': abs(laba_bersih_lajur), 'N_K': 0
                }
            df_lajur = pd.concat([df_lajur, pd.DataFrame([laba_row])], ignore_index=True)

            gtotal = {
                'Kode Akun': '', 'Nama Akun': 'Total Keseluruhan',
                'NS_D': 0, 'NS_K': 0, 'AJP_D': 0, 'AJP_K': 0, 'NSD_D': 0, 'NSD_K': 0,
                'LR_D': totals['LR_D'] + laba_row['LR_D'], 'LR_K': totals['LR_K'] + laba_row['LR_K'],
                'N_D': totals['N_D'] + laba_row['N_D'], 'N_K': totals['N_K'] + laba_row['N_K']
            }
            df_lajur = pd.concat([df_lajur, pd.DataFrame([gtotal])], ignore_index=True)

            numeric_cols = ['NS_D', 'NS_K', 'AJP_D', 'AJP_K', 'NSD_D', 'NSD_K', 'LR_D', 'LR_K', 'N_D', 'N_K']
            for col in numeric_cols:
                df_lajur[col] = df_lajur[col].replace(0, None)

            columns_hierarki = [
                ('', 'No'),
                ('', 'Nama Akun'),
                ('Neraca Saldo', 'Debit'), ('Neraca Saldo', 'Kredit'),
                ('Jurnal Penyesuaian', 'Debit'), ('Jurnal Penyesuaian', 'Kredit'),
                ('Neraca Saldo Disesuaikan', 'Debit'), ('Neraca Saldo Disesuaikan', 'Kredit'),
                ('Laba Rugi', 'Debit'), ('Laba Rugi', 'Kredit'),
                ('Neraca', 'Debit'), ('Neraca', 'Kredit')
            ]
            
            df_display = df_lajur[['Kode Akun', 'Nama Akun', 'NS_D', 'NS_K', 'AJP_D', 'AJP_K', 'NSD_D', 'NSD_K', 'LR_D', 'LR_K', 'N_D', 'N_K']]
            df_display.columns = pd.MultiIndex.from_tuples(columns_hierarki)

            def highlight_lajur(row):
                nama_akun = str(row[('', 'Nama Akun')])
                if nama_akun == 'Jumlah':
                    return ['background-color: #F9FAFB; font-weight: bold; color: #111827; border-top: 1px solid #E5E7EB;'] * len(row)
                elif 'Bersih' in nama_akun:
                    return ['background-color: #FFF1F2; font-weight: bold; color: #E11D48;'] * len(row)
                elif nama_akun == 'Total Keseluruhan':
                    return ['background-color: #F3F4F6; font-weight: bold; color: #E11D48; border-top: 2px solid #E11D48; border-bottom: 4px double #E11D48;'] * len(row)
                return [''] * len(row)

            styler_lajur = df_display.style.apply(highlight_lajur, axis=1)
            styler_lajur = styler_lajur.format(
                lambda x: f"{x:,.0f}" if pd.notnull(x) and isinstance(x, (int, float)) else "", 
                subset=pd.IndexSlice[:, df_display.columns.get_level_values(1).isin(['Debit', 'Kredit'])]
            )

            with st.container(border=True):
                st.dataframe(styler_lajur, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada data untuk ditampilkan di Neraca Lajur.")

    with tab_lr:
        st.subheader("Laporan Laba Rugi")
        col_kotor, col_ops, col_bersih = st.columns(3)
        with col_kotor:
            with st.container(border=True):
                st.caption("Total Laba Kotor")
                st.subheader(f"Rp {laba_kotor:,.0f}")
        with col_ops:
            with st.container(border=True):
                st.caption("Total Laba Operasional")
                st.subheader(f"Rp {laba_operasional:,.0f}")
        with col_bersih:
            with st.container(border=True):
                st.caption("Total Laba Bersih")
                st.subheader(f"Rp {laba_bersih:,.0f}")
        
        st.divider()

        baris_laporan = []
        def tambah_bagian(df_bagian, nama_bagian, total_bagian):
            baris_laporan.append({"DESKRIPSI": f"🔸 {nama_bagian}", "SALDO": None, "Tipe": "Header"})
            if df_bagian.empty:
                baris_laporan.append({"DESKRIPSI": "   (Tidak ada transaksi)", "SALDO": 0, "Tipe": "Detail"})
            else:
                for _, row in df_bagian.iterrows():
                    baris_laporan.append({
                        "DESKRIPSI": f"   ({row['Kode Akun']}) {row['Nama Akun']}", 
                        "SALDO": row['Saldo'], 
                        "Tipe": "Detail"
                    })
            baris_laporan.append({"DESKRIPSI": f"Total {nama_bagian}", "SALDO": total_bagian, "Tipe": "Subtotal"})
            baris_laporan.append({"DESKRIPSI": "", "SALDO": None, "Tipe": "Spacer"})

        tambah_bagian(df_pendapatan, "Pendapatan", tot_pendapatan)
        tambah_bagian(df_hpp, "Harga Pokok Penjualan", tot_hpp)
        
        baris_laporan.append({"DESKRIPSI": "LABA (RUGI) KOTOR", "SALDO": laba_kotor, "Tipe": "LabaKotor"})
        baris_laporan.append({"DESKRIPSI": "", "SALDO": None, "Tipe": "Spacer"})
        
        tambah_bagian(df_beban_op, "Beban Operasional", tot_beban_op)
        
        baris_laporan.append({"DESKRIPSI": "LABA (RUGI) BERSIH", "SALDO": laba_bersih, "Tipe": "LabaBersih"})

        df_tampilan = pd.DataFrame(baris_laporan)

        def gaya_laporan(row):
            tipe_baris = df_tampilan.loc[row.name, 'Tipe']
            if tipe_baris == 'Header':
                return ['font-weight: bold; background-color: #F9FAFB; color: #E11D48;'] * 2
            elif tipe_baris == 'Subtotal':
                return ['font-weight: bold; color: #E11D48;'] * 2
            elif tipe_baris == 'LabaKotor':
                return ['font-weight: bold; background-color: #F3F4F6; color: #111827; font-size: 14px;'] * 2
            elif tipe_baris == 'LabaBersih':
                return ['font-weight: bold; background-color: #FFF1F2; color: #E11D48; font-size: 15px;'] * 2
            elif tipe_baris == 'Spacer':
                return ['background-color: #FFFFFF; color: #FFFFFF; border: none;'] * 2
            else: 
                return ['color: #4B5563;'] * 2

        styler = df_tampilan[['DESKRIPSI', 'SALDO']].style.apply(gaya_laporan, axis=1)
        styler = styler.format({"SALDO": lambda x: f"Rp {x:,.0f}" if pd.notnull(x) else ""})
        st.dataframe(styler, use_container_width=True, hide_index=True)

    with tab_pm:
        st.subheader("Laporan Perubahan Modal")
        st.markdown("Melacak pergerakan nilai ekuitas selama periode berjalan.")
        
        df_pm = pd.DataFrame([
            {"KETERANGAN": "Modal Awal", "SALDO": modal_awal, "Tipe": "Normal"},
            {"KETERANGAN": "Laba Bersih Periode Berjalan", "SALDO": laba_bersih, "Tipe": "Laba"},
            {"KETERANGAN": "Prive (Penarikan Pribadi)", "SALDO": -prive, "Tipe": "Prive"},
            {"KETERANGAN": "Modal Akhir", "SALDO": modal_akhir, "Tipe": "Total"}
        ])
        
        def gaya_pm(row):
            tipe = df_pm.loc[row.name, 'Tipe']
            if tipe == 'Total':
                return ['font-weight: bold; background-color: #F3F4F6; color: #E11D48; font-size: 14px;'] * 2
            elif tipe == 'Laba':
                return ['font-weight: bold; color: #E11D48;'] * 2
            elif tipe == 'Prive':
                return ['font-weight: bold; color: #EF4444;'] * 2
            return ['color: #4B5563;'] * 2

        styler_pm = df_pm[['KETERANGAN', 'SALDO']].style.apply(gaya_pm, axis=1)
        styler_pm = styler_pm.format({"SALDO": lambda x: f"(Rp {abs(x):,.0f})" if x < 0 else f"Rp {x:,.0f}"})
        
        with st.container(border=True):
            st.dataframe(styler_pm, use_container_width=True, hide_index=True)

    with tab_neraca:
        st.subheader("Neraca (Balance Sheet)")
        if df_gabungan.empty:
            st.info("Belum ada data posisi keuangan yang dapat disajikan.")
        else:
            df_aset = df_gabungan[df_gabungan['Kategori'] == 'Aset'].copy()
            df_kewajiban = df_gabungan[df_gabungan['Kategori'] == 'Kewajiban'].copy()

            df_aset['Nilai Buku'] = df_aset['Debit'] - df_aset['Kredit']
            total_aset = df_aset['Nilai Buku'].sum()

            df_kewajiban['Saldo'] = df_kewajiban['Kredit'] - df_kewajiban['Debit']
            total_kewajiban = df_kewajiban['Saldo'].sum()
            
            total_pasiva = total_kewajiban + modal_akhir

            # 1. INDIKATOR KESEIMBANGAN
            if total_aset == total_pasiva:
                st.success(f"**NERACA SEIMBANG (BALANCE):** Aktiva dan Pasiva terkunci sempurna pada nominal **Rp {total_aset:,.0f}**")
            else:
                st.error(f"⚠️ **NERACA TIDAK SEIMBANG:** Terdapat selisih sebesar **Rp {abs(total_aset - total_pasiva):,.0f}** antara posisi Aktiva dan Pasiva.")

            col_aktiva, col_pasiva = st.columns(2)
            
            with col_aktiva:
                with st.container(border=True):
                    st.markdown("##### AKTIVA (Aset)")
                    
                    baris_aktiva = []
                    df_aset_bersih = df_aset[df_aset['Nilai Buku'] != 0]
                    if df_aset_bersih.empty:
                        baris_aktiva.append({"AKUN / DESKRIPSI": "(Tidak ada saldo aset aktif)", "NILAI BUKU": None, "Tipe": "Detail"})
                    else:
                        for _, row in df_aset_bersih.iterrows():
                            baris_aktiva.append({
                                "AKUN / DESKRIPSI": f"({row['Kode Akun']}) {row['Nama Akun']}",
                                "NILAI BUKU": row['Nilai Buku'],
                                "Tipe": "Detail"
                            })
                    
                    baris_aktiva.append({"AKUN / DESKRIPSI": "TOTAL AKTIVA", "NILAI BUKU": total_aset, "Tipe": "Total"})
                    df_aktiva_tampilan = pd.DataFrame(baris_aktiva)

                    def gaya_aktiva(row):
                        tipe_baris = df_aktiva_tampilan.loc[row.name, 'Tipe']
                        if tipe_baris == 'Total':
                            return ['font-weight: bold; background-color: #F3F4F6; color: #E11D48; font-size: 14px;'] * 2
                        return ['color: #4B5563;'] * 2

                    styler_aktiva = df_aktiva_tampilan[['AKUN / DESKRIPSI', 'NILAI BUKU']].style.apply(gaya_aktiva, axis=1)
                    styler_aktiva = styler_aktiva.format({"NILAI BUKU": lambda x: f"Rp {x:,.0f}" if pd.notnull(x) else ""})
                    st.dataframe(styler_aktiva, use_container_width=True, hide_index=True)

            with col_pasiva:
                with st.container(border=True):
                    st.markdown("##### PASIVA (Kewajiban & Ekuitas)")
                    
                    baris_pasiva = []
                    baris_pasiva.append({"AKUN / DESKRIPSI": "🔸 KEWAJIBAN", "SALDO": None, "Tipe": "Header"})
                    df_kew_bersih = df_kewajiban[df_kewajiban['Saldo'] != 0]
                    if df_kew_bersih.empty:
                        baris_pasiva.append({"AKUN / DESKRIPSI": "   (Tidak ada saldo kewajiban)", "SALDO": 0, "Tipe": "Detail"})
                    else:
                        for _, row in df_kew_bersih.iterrows():
                            baris_pasiva.append({
                                "AKUN / DESKRIPSI": f"   ({row['Kode Akun']}) {row['Nama Akun']}",
                                "SALDO": row['Saldo'],
                                "Tipe": "Detail"
                            })
                    baris_pasiva.append({"AKUN / DESKRIPSI": "Total Kewajiban", "SALDO": total_kewajiban, "Tipe": "Subtotal"})
                    baris_pasiva.append({"AKUN / DESKRIPSI": "", "SALDO": None, "Tipe": "Spacer"})
                    
                    baris_pasiva.append({"AKUN / DESKRIPSI": "🔸 EKUITAS", "SALDO": None, "Tipe": "Header"})
                    baris_pasiva.append({"AKUN / DESKRIPSI": "   (3110) Modal Mas Imam (Akhir)", "SALDO": modal_akhir, "Tipe": "Detail"})
                    baris_pasiva.append({"AKUN / DESKRIPSI": "", "SALDO": None, "Tipe": "Spacer"})
                    
                    baris_pasiva.append({"AKUN / DESKRIPSI": "TOTAL PASIVA", "SALDO": total_pasiva, "Tipe": "Total"})
                    df_pasiva_tampilan = pd.DataFrame(baris_pasiva)

                    def gaya_pasiva(row):
                        tipe_baris = df_pasiva_tampilan.loc[row.name, 'Tipe']
                        if tipe_baris == 'Header':
                            return ['font-weight: bold; background-color: #F9FAFB; color: #E11D48;'] * 2
                        elif tipe_baris == 'Subtotal':
                            return ['font-weight: bold; color: #E11D48;'] * 2
                        elif tipe_baris == 'Total':
                            return ['font-weight: bold; background-color: #F3F4F6; color: #E11D48; font-size: 14px;'] * 2
                        elif tipe_baris == 'Spacer':
                            return ['background-color: #FFFFFF; color: #FFFFFF; border: none;'] * 2
                        return ['color: #4B5563;'] * 2

                    styler_pasiva = df_pasiva_tampilan[['AKUN / DESKRIPSI', 'SALDO']].style.apply(gaya_pasiva, axis=1)
                    styler_pasiva = styler_pasiva.format({"SALDO": lambda x: f"Rp {x:,.0f}" if pd.notnull(x) else ""})
                    st.dataframe(styler_pasiva, use_container_width=True, hide_index=True)

    with tab_ak:
        st.subheader("Laporan Arus Kas (Standar Akuntansi)")
        st.markdown("Melacak arus kas yang diklasifikasikan ke dalam aktivitas **Operasional, Investasi, dan Pendanaan**.")
        
        df_ak = database.get_arus_kas()
        if not df_ak.empty:
            # 1. Normalisasi Data
            df_ak['Masuk'] = df_ak['Masuk'].fillna(0)
            df_ak['Keluar'] = df_ak['Keluar'].fillna(0)
            df_ak['Net'] = df_ak['Masuk'] - df_ak['Keluar']

            # 2. Logika Pythonic untuk Kategorisasi Arus Kas
            def categorize_cf(desc):
                desc = desc.lower()
                if 'aset' in desc or 'inventaris' in desc:
                    return 'Investasi', 'Perolehan/Penjualan aset'
                elif 'modal' in desc or 'prive' in desc or 'utang' in desc:
                    return 'Pendanaan', 'Ekuitas/Modal/Pinjaman'
                elif 'penjualan' in desc:
                    return 'Operasional', 'Penerimaan dari pelanggan'
                elif 'beban' in desc:
                    return 'Operasional', 'Pengeluaran operasional'
                elif 'pemasok' in desc or 'pembelian' in desc or 'restock' in desc:
                    return 'Operasional', 'Pembayaran ke pemasok'
                else:
                    return 'Operasional', 'Penerimaan/Pengeluaran lainnya'

            # Menerapkan kategori ke data
            df_ak['Kategori_Utama'], df_ak['Sub_Kategori'] = zip(*df_ak['Keterangan'].apply(categorize_cf))
            
            # Mengelompokkan nominal berdasarkan sub-kategori
            cf_summary = df_ak.groupby(['Kategori_Utama', 'Sub_Kategori'])['Net'].sum().reset_index()

            # 3. Membangun Struktur Baris Laporan
            baris_cf = []
            
            def tambah_grup_cf(nama_kategori, label_header, label_total):
                baris_cf.append({"Akun & Kategori": label_header, "Periode Berjalan": None, "Tipe": "Header"})
                df_grup = cf_summary[cf_summary['Kategori_Utama'] == nama_kategori]
                tot = 0
                if df_grup.empty:
                    baris_cf.append({"Akun & Kategori": "   (Tidak ada aktivitas)", "Periode Berjalan": 0, "Tipe": "Detail"})
                else:
                    for _, r in df_grup.iterrows():
                        baris_cf.append({"Akun & Kategori": f"   {r['Sub_Kategori']}", "Periode Berjalan": r['Net'], "Tipe": "Detail"})
                        tot += r['Net']
                baris_cf.append({"Akun & Kategori": label_total, "Periode Berjalan": tot, "Tipe": "Subtotal"})
                baris_cf.append({"Akun & Kategori": "", "Periode Berjalan": None, "Tipe": "Spacer"})
                return tot

            # Menyusun 3 Pilar Arus Kas
            tot_op = tambah_grup_cf("Operasional", "Arus Kas dari Aktivitas Operasional", "Kas Bersih dari Aktivitas Operasional")
            tot_inv = tambah_grup_cf("Investasi", "Arus Kas dari Aktivitas Investasi", "Kas Bersih dari Aktivitas Investasi")
            tot_fin = tambah_grup_cf("Pendanaan", "Arus Kas dari Aktivitas Pendanaan", "Kas Bersih dari Aktivitas Pendanaan")

            # Kalkulasi Summary Bawah
            net_kas = tot_op + tot_inv + tot_fin
            saldo_awal = 0 
            saldo_akhir = saldo_awal + net_kas

            baris_cf.append({"Akun & Kategori": "Kenaikan (penurunan) kas", "Periode Berjalan": net_kas, "Tipe": "Summary"})
            baris_cf.append({"Akun & Kategori": "Total revaluasi bank", "Periode Berjalan": 0, "Tipe": "Summary"})
            baris_cf.append({"Akun & Kategori": "Saldo kas awal", "Periode Berjalan": saldo_awal, "Tipe": "Summary"})
            baris_cf.append({"Akun & Kategori": "Saldo kas akhir", "Periode Berjalan": saldo_akhir, "Tipe": "GrandTotal"})

            df_cf_tampilan = pd.DataFrame(baris_cf)

            # 4. PANDAS STYLER: Mewarnai & Memformat Kurung untuk Angka Negatif
            def gaya_cf(row):
                tipe = df_cf_tampilan.loc[row.name, 'Tipe']
                if tipe == 'Header':
                    return ['font-weight: bold; background-color: #FFF1F2; color: #E11D48;'] * 2 
                elif tipe == 'Subtotal':
                    return ['font-weight: bold; color: #E11D48;'] * 2
                elif tipe == 'Spacer':
                    return ['background-color: #FFFFFF; color: #FFFFFF; border: none;'] * 2
                elif tipe == 'Summary':
                    return ['color: #4B5563; background-color: #F9FAFB;'] * 2
                elif tipe == 'GrandTotal':
                    return ['font-weight: bold; color: #FFFFFF; background-color: #E11D48;'] * 2
                return ['color: #4B5563;'] * 2

            def format_akuntansi(val):
                if pd.isnull(val): return ""
                if val < 0: return f"({abs(val):,.0f})"
                return f"{val:,.0f}"

            styler_cf = df_cf_tampilan[['Akun & Kategori', 'Periode Berjalan']].style.apply(gaya_cf, axis=1)
            styler_cf = styler_cf.format({"Periode Berjalan": format_akuntansi})

            with st.container(border=True):
                st.dataframe(styler_cf, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada mutasi Kas & Bank yang tercatat.")
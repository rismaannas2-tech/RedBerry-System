import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import database
import re
from datetime import datetime, timedelta

def render():
    col_title, col_filter = st.columns([2, 1])
    with col_title:
        st.markdown("<h2 style='color: #393A3D; font-weight: 800; margin-bottom: 0;'>Business Overview</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #6B6C72; font-size: 14px;'>Intelijen Bisnis & Analisis Rasio Keuangan Komprehensif.</p>", unsafe_allow_html=True)
    
    with col_filter:
        st.write("")
        periode = st.selectbox("Pilih Periode Analitik", ["Semua Waktu", "Bulan Ini", "Bulan Lalu", "Kuartal Ini", "Tahun Ini"])

    # --- LOGIKA TANGGAL ---
    now = datetime.now()
    if periode == "Bulan Ini":
        start_date = now.replace(day=1).date()
        end_date = now.date()
    elif periode == "Bulan Lalu":
        first_day_this_month = now.replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        start_date = last_day_last_month.replace(day=1).date()
        end_date = last_day_last_month.date()
    elif periode == "Kuartal Ini":
        current_quarter = (now.month - 1) // 3 + 1
        start_month = 3 * current_quarter - 2
        start_date = now.replace(month=start_month, day=1).date()
        end_date = now.date()
    elif periode == "Tahun Ini":
        start_date = now.replace(month=1, day=1).date()
        end_date = now.date()
    else:
        start_date = pd.to_datetime('2000-01-01').date()
        end_date = pd.to_datetime('2099-12-31').date()

    # --- DATA EXTRACTION & ENGINE ---
    df_jurnal = database.get_jurnal_umum()
    df_coa = database.get_coa_data()
    df_sales = database.get_riwayat_penjualan()
    df_ns = database.get_neraca_saldo() 

    name_to_code = {}
    if not df_coa.empty:
        for _, row in df_coa.iterrows():
            k = str(row.get('Kode Akun', '')).strip()
            n = str(row.get('Nama Akun', '')).strip()
            if k:
                name_to_code[k.lower()] = k
                name_to_code[n.lower()] = k
                name_to_code[f"{k} - {n}".lower()] = k
                name_to_code[f"{k}-{n}".lower()] = k

    def smart_extract_code(val):
        v = str(val).strip().lower()
        if v in name_to_code: return name_to_code[v]
        m = re.search(r'\b(\d{4})\b', v)
        if m: return m.group(1)
        for key, code in name_to_code.items():
            if v != '' and len(v) > 3 and (v in key or key in v): return code
        return ""

    pendapatan, hpp, beban_op = 0, 0, 0
    df_jurnal_f = pd.DataFrame()

    if not df_jurnal.empty:
        df_jurnal['Tanggal'] = pd.to_datetime(df_jurnal['Tanggal']).dt.date
        df_jurnal_f = df_jurnal[(df_jurnal['Tanggal'] >= start_date) & (df_jurnal['Tanggal'] <= end_date)].copy()
        
        if not df_jurnal_f.empty:
            akun_col = next((col for col in df_jurnal_f.columns if 'akun' in col.lower() or 'account' in col.lower()), None)
            debit_col = next((col for col in df_jurnal_f.columns if 'debit' in col.lower()), 'Debit')
            kredit_col = next((col for col in df_jurnal_f.columns if 'kredit' in col.lower() or 'credit' in col.lower()), 'Kredit')
            
            if akun_col:
                df_jurnal_f['KODE_AKURAT'] = df_jurnal_f[akun_col].apply(smart_extract_code)
                df_jurnal_f['Val_Debit'] = pd.to_numeric(df_jurnal_f[debit_col], errors='coerce').fillna(0)
                df_jurnal_f['Val_Kredit'] = pd.to_numeric(df_jurnal_f[kredit_col], errors='coerce').fillna(0)
                
                pendapatan = df_jurnal_f[df_jurnal_f['KODE_AKURAT'].str.startswith('4', na=False)]['Val_Kredit'].sum() - df_jurnal_f[df_jurnal_f['KODE_AKURAT'].str.startswith('4', na=False)]['Val_Debit'].sum()
                hpp = df_jurnal_f[df_jurnal_f['KODE_AKURAT'].str.startswith('5', na=False)]['Val_Debit'].sum() - df_jurnal_f[df_jurnal_f['KODE_AKURAT'].str.startswith('5', na=False)]['Val_Kredit'].sum()
                beban_op = df_jurnal_f[df_jurnal_f['KODE_AKURAT'].str.startswith('6', na=False)]['Val_Debit'].sum() - df_jurnal_f[df_jurnal_f['KODE_AKURAT'].str.startswith('6', na=False)]['Val_Kredit'].sum()

    if pendapatan == 0 and not df_sales.empty:
        df_sales_f = df_sales[(pd.to_datetime(df_sales['Tanggal']).dt.date >= start_date) & (pd.to_datetime(df_sales['Tanggal']).dt.date <= end_date)]
        pendapatan = df_sales_f['Pendapatan'].sum() if not df_sales_f.empty else 0

    laba_kotor = pendapatan - hpp
    laba_bersih = laba_kotor - beban_op
    
    gross_margin = (laba_kotor / pendapatan * 100) if pendapatan > 0 else 0
    net_margin = (laba_bersih / pendapatan * 100) if pendapatan > 0 else 0

    tot_aset_lancar, tot_kewajiban_lancar = 0, 0
    if not df_ns.empty:
        akun_col_ns = next((col for col in df_ns.columns if 'akun' in col.lower() or 'account' in col.lower()), 'Kode Akun')
        debit_col_ns = next((col for col in df_ns.columns if 'debit' in col.lower()), 'Debit')
        kredit_col_ns = next((col for col in df_ns.columns if 'kredit' in col.lower() or 'credit' in col.lower()), 'Kredit')
        
        df_ns['KODE_AKURAT'] = df_ns[akun_col_ns].apply(smart_extract_code)
        df_ns['Val_Debit'] = pd.to_numeric(df_ns[debit_col_ns], errors='coerce').fillna(0)
        df_ns['Val_Kredit'] = pd.to_numeric(df_ns[kredit_col_ns], errors='coerce').fillna(0)
        
        tot_aset_lancar = df_ns[df_ns['KODE_AKURAT'].str.startswith('11', na=False)]['Val_Debit'].sum() - df_ns[df_ns['KODE_AKURAT'].str.startswith('11', na=False)]['Val_Kredit'].sum()
        tot_kewajiban_lancar = df_ns[df_ns['KODE_AKURAT'].str.startswith('21', na=False)]['Val_Kredit'].sum() - df_ns[df_ns['KODE_AKURAT'].str.startswith('21', na=False)]['Val_Debit'].sum()
        
    current_ratio = (tot_aset_lancar / tot_kewajiban_lancar) if tot_kewajiban_lancar > 0 else 0

    # =========================================================================
    # ROW 1: EXECUTIVE FINANCIAL RATIOS (LIGHT THEME)
    # =========================================================================
    st.markdown("""
        <style>
        .metric-box { background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 8px; padding: 20px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        .metric-title { color: #6B6C72; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
        .metric-val { color: #393A3D; font-size: 26px; font-weight: 800; margin: 5px 0; }
        .metric-sub { font-size: 12px; font-weight: 600; }
        </style>
    """, unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
            <div class='metric-box' style='border-top: 4px solid #2CA01C;'>
                <div class='metric-title'>Total Revenue</div>
                <div class='metric-val'>Rp {pendapatan:,.0f}</div>
                <div class='metric-sub' style='color: #2CA01C;'>Top Line Sales</div>
            </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
            <div class='metric-box'>
                <div class='metric-title'>Gross Profit</div>
                <div class='metric-val'>Rp {laba_kotor:,.0f}</div>
                <div class='metric-sub' style='color: #2CA01C;'>{gross_margin:.1f}% Margin</div>
            </div>
        """, unsafe_allow_html=True)
    with m3:
        color_net = "#2CA01C" if net_margin >= 0 else "#D93A30"
        st.markdown(f"""
            <div class='metric-box'>
                <div class='metric-title'>Net Income</div>
                <div class='metric-val'>Rp {laba_bersih:,.0f}</div>
                <div class='metric-sub' style='color: {color_net};'>{net_margin:.1f}% Margin</div>
            </div>
        """, unsafe_allow_html=True)
    with m4:
        if tot_kewajiban_lancar == 0 and tot_aset_lancar > 0:
            cr_display, cr_status, cr_color = "Aman", "Tidak Ada Utang", "#2CA01C"
        elif tot_kewajiban_lancar == 0 and tot_aset_lancar == 0:
            cr_display, cr_status, cr_color = "0.00x", "Belum Ada Data", "#6B6C72"
        else:
            cr_display = f"{current_ratio:.2f}x"
            cr_status = "Sangat Sehat" if current_ratio >= 1.5 else ("Aman" if current_ratio >= 1 else "Risiko Likuiditas")
            cr_color = "#2CA01C" if current_ratio >= 1 else "#D93A30"
            
        st.markdown(f"""
            <div class='metric-box'>
                <div class='metric-title'>Current Ratio</div>
                <div class='metric-val'>{cr_display}</div>
                <div class='metric-sub' style='color: {cr_color};'>{cr_status}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # =========================================================================
    # ROW 2: ADVANCED ANALYTICS (TREND & OPEX)
    # =========================================================================
    c1, c2 = st.columns([2, 1])
    
    with c1:
        with st.container(border=True):
            st.markdown("<div style='color:#393A3D; font-weight:700; font-size:14px; margin-bottom:15px;'>SALES TREND</div>", unsafe_allow_html=True)
            
            if not df_sales.empty:
                df_sales['Tanggal'] = pd.to_datetime(df_sales['Tanggal']).dt.date
                df_sales_f = df_sales[(df_sales['Tanggal'] >= start_date) & (df_sales['Tanggal'] <= end_date)]
                
                if not df_sales_f.empty:
                    trend_harian = df_sales_f.groupby('Tanggal')['Pendapatan'].sum().reset_index()
                    
                    fig_trend = go.Figure()
                    fig_trend.add_trace(go.Scatter(
                        x=trend_harian['Tanggal'], 
                        y=trend_harian['Pendapatan'],
                        mode='lines+markers',
                        name='Revenue',
                        line=dict(color='#2CA01C', width=3, shape='spline'), 
                        marker=dict(size=8, color='#FFFFFF', line=dict(width=2, color='#2CA01C')),
                        fill='tozeroy',
                        fillcolor='rgba(44, 160, 28, 0.1)',
                        hovertemplate='<b>%{x}</b><br>Omzet: Rp %{y:,.0f}<extra></extra>'
                    ))
                    
                    fig_trend.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=0, r=0, t=0, b=0), height=300,
                        hovermode="x unified"
                    )
                    fig_trend.update_xaxes(showgrid=False, tickfont=dict(color='#6B6C72'))
                    fig_trend.update_yaxes(showgrid=True, gridcolor='#E5E7EB', tickfont=dict(color='#6B6C72'))
                    
                    st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info("Tidak ada data transaksi pada periode ini.")
            else:
                st.info("Belum ada riwayat penjualan operasional yang tercatat.")

    with c2:
        with st.container(border=True):
            st.markdown("<div style='color:#393A3D; font-weight:700; font-size:14px; margin-bottom:15px;'>EXPENSES DISTRIBUTION</div>", unsafe_allow_html=True)
            
            if not df_jurnal_f.empty and beban_op > 0:
                df_bop = df_jurnal_f[df_jurnal_f['KODE_AKURAT'].str.startswith('6', na=False)]
                
                if not df_bop.empty:
                    akun_col_jurnal = next((col for col in df_jurnal_f.columns if 'akun' in col.lower() or 'account' in col.lower()), 'KODE_AKURAT')
                    bop_group = df_bop.groupby(akun_col_jurnal)['Val_Debit'].sum().reset_index().sort_values(by='Val_Debit', ascending=False)
                    
                    fig_pie = go.Figure(data=[go.Pie(
                        labels=bop_group[akun_col_jurnal], 
                        values=bop_group['Val_Debit'],
                        hole=0.65,
                        marker=dict(colors=['#0077C5', '#2CA01C', '#F4B223', '#6B6C72']),
                        textposition='none',
                        hovertemplate='<b>%{label}</b><br>Rp %{value:,.0f} (%{percent})<extra></extra>'
                    )])
                    
                    fig_pie.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=0, r=0, t=0, b=0), height=300,
                        showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, font=dict(color='#6B6C72', size=10))
                    )
                    
                    total_beban_teks = f"{beban_op/1000000:.1f}M" if beban_op >= 1000000 else f"{beban_op/1000:,.0f}K"
                    fig_pie.add_annotation(text=f"<b>Total OPEX</b><br>Rp {total_beban_teks}", x=0.5, y=0.5, font=dict(size=14, color='#393A3D'), showarrow=False)
                    
                    st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
                else:
                    st.info("Beban operasional belum dirinci.")
            else:
                st.info("Belum ada pengeluaran operasional.")

    # =========================================================================
    # ROW 3: DETAILED BREAKDOWN
    # =========================================================================
    with st.container(border=True):
        st.markdown("<div style='color:#393A3D; font-weight:700; font-size:14px; margin-bottom:15px;'>INVOICES & REVENUE CHANNEL</div>", unsafe_allow_html=True)
        if not df_sales.empty:
            df_sales_f = df_sales[(pd.to_datetime(df_sales['Tanggal']).dt.date >= start_date) & (pd.to_datetime(df_sales['Tanggal']).dt.date <= end_date)]
            if not df_sales_f.empty:
                df_sales_f['Volume (Kg)'] = df_sales_f['Keterangan'].str.extract(r'([\d\.]+)\s*[Kk]g').astype(float).fillna(0)
                
                channel_group = df_sales_f.groupby('Jalur_Penjualan').agg({'Pendapatan': 'sum', 'Volume (Kg)': 'sum'}).reset_index()
                channel_group['Harga Rata-rata / Kg'] = channel_group['Pendapatan'] / channel_group['Volume (Kg)']
                channel_group['Harga Rata-rata / Kg'] = channel_group['Harga Rata-rata / Kg'].fillna(0)
                
                st.dataframe(
                    channel_group,
                    column_config={
                        "Jalur_Penjualan": st.column_config.TextColumn("Kanal Distribusi"),
                        "Volume (Kg)": st.column_config.NumberColumn("Volume (Kg)", format="%.1f Kg"),
                        "Pendapatan": st.column_config.ProgressColumn("Total Omzet", format="Rp %f", min_value=0, max_value=float(channel_group['Pendapatan'].max())),
                        "Harga Rata-rata / Kg": st.column_config.NumberColumn("Avg. Price", format="Rp %.0f")
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.info("Data saluran penjualan kosong pada periode ini.")
        else:
            st.info("Tidak ada riwayat penjualan.")
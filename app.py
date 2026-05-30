import streamlit as st
from streamlit_option_menu import option_menu
import database

# Import semua modul dari folder views
from views import dashboard, data_master, operasional, transaksi, laporan

# 1. KONFIGURASI HALAMAN
st.set_page_config(
    page_title="AgriSys.io | Enterprise ERP", 
    page_icon="🍓", 
    layout="wide",
    initial_sidebar_state="expanded"
)

database.init_db()

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['name'] = ''
    st.session_state['role'] = ''

# ==========================
# KONDISI 1: GERBANG LOGIN 
# ==========================
if not st.session_state['logged_in']:
    
    # CSS LOGIN: Memaksa Background Mesh Gradient Apple-Style & UI Kaca
    st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap');

header[data-testid="stHeader"], [data-testid="stSidebar"] { display: none !important; }

.stApp {
    background-color: #ffffff !important;
    background-image: 
        radial-gradient(at 40% 20%, hsla(350,100%,88%,0.4) 0px, transparent 50%),
        radial-gradient(at 80% 0%, hsla(350,100%,92%,0.5) 0px, transparent 50%),
        radial-gradient(at 0% 50%, hsla(350,100%,88%,0.4) 0px, transparent 50%),
        radial-gradient(at 80% 50%, hsla(340,100%,76%,0.15) 0px, transparent 50%),
        radial-gradient(at 0% 100%, hsla(22,100%,77%,0.15) 0px, transparent 50%),
        radial-gradient(at 0% 0%, hsla(343,100%,76%,0.1) 0px, transparent 50%) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background-attachment: fixed !important;
}

.block-container {
    padding-top: 8vh !important;
    max-width: 1200px !important;
}

div[data-testid="stForm"] {
    background: rgba(255, 255, 255, 0.85) !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border: 1px solid rgba(255, 255, 255, 0.6) !important;
    border-radius: 28px !important;
    padding: 45px !important;
    box-shadow: 0 30px 60px -15px rgba(225, 29, 72, 0.15), 0 0 20px rgba(0,0,0,0.02) !important;
}

div[data-testid="stTextInput"] > div > div > input {
    background: #F8FAFC !important;
    border: 2px solid #F1F5F9 !important;
    border-radius: 14px !important;
    padding: 16px 20px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    color: #0F172A !important;
    transition: all 0.3s ease !important;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.02) !important;
}
div[data-testid="stTextInput"] > div > div > input:focus {
    border-color: #E11D48 !important;
    background: #FFFFFF !important;
    box-shadow: 0 0 0 4px rgba(225, 29, 72, 0.15) !important;
}
div[data-testid="stTextInput"] > div > div > input::placeholder {
    color: #94A3B8 !important; font-weight: 500; font-size: 13px;
}

.stButton>button[kind="primary"] {
    background: linear-gradient(135deg, #E11D48 0%, #BE123C 100%) !important;
    color: #FFFFFF !important;
    border-radius: 14px !important;
    height: 58px !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 800 !important;
    font-size: 16px !important;
    letter-spacing: 1px !important;
    margin-top: 20px !important;
    border: none !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 10px 25px -5px rgba(225, 29, 72, 0.4) !important;
}
.stButton>button[kind="primary"]:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 20px 35px -5px rgba(225, 29, 72, 0.5) !important;
}
</style>""", unsafe_allow_html=True)
    
    col_left, col_spacing, col_right = st.columns([1.3, 0.1, 1.1])
    
    with col_left:
        hero_html = (
            "<div style='font-family: \"Plus Jakarta Sans\", sans-serif; margin-top: 30px;'>"
            "<div style='display: inline-flex; align-items: center; gap: 10px; background: rgba(225, 29, 72, 0.08); padding: 8px 18px; border-radius: 50px; margin-bottom: 30px; border: 1px solid rgba(225, 29, 72, 0.15);'>"
            "<span style='font-size: 16px;'>🍓</span>"
            "<span style='color: #E11D48; font-weight: 800; font-size: 12px; letter-spacing: 2px;'>AGRISYS.IO ENTERPRISE</span>"
            "</div>"
            "<h1 style='font-size: 4.8rem; font-weight: 900; color: #0F172A; line-height: 1.05; margin-bottom: 25px; letter-spacing: -2.5px;'>"
            "Smart <span style='color: #E11D48; position: relative;'>Farming.<svg style='position: absolute; bottom: -5px; left: 0; width: 100%; height: 12px;' viewBox='0 0 100 10' preserveAspectRatio='none'><path d='M0 5 Q 50 15 100 5' stroke=\"rgba(225, 29, 72, 0.2)\" stroke-width=\"6\" fill=\"transparent\"/></svg></span><br>"
            "Better Future."
            "</h1>"
            "<p style='font-size: 1.15rem; color: #475569; line-height: 1.7; max-width: 90%; margin-bottom: 35px; font-weight: 500;'>"
            "Sistem mini ERP untuk agribisnis Mas Imam. Otomatisasi rantai pasok dan penyusunan laporan keuangan yang lengkap."
            "</p>"
            "<div style='display: flex; gap: 12px; align-items: center; flex-wrap: wrap; margin-bottom: 20px;'>"
            "<div style='display: flex; align-items: center; gap: 8px; background: rgba(255, 255, 255, 0.6); backdrop-filter: blur(5px); padding: 10px 16px; border-radius: 12px; border: 1px solid rgba(225, 29, 72, 0.15); color: #0F172A; font-weight: 700; font-size: 13px;'>"
            "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='#E11D48' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><path d='M22 11.08V12a10 10 0 1 1-5.93-9.14'/><polyline points='22 4 12 14.01 9 11.01'/></svg>"
            "SAK EMKM"
            "</div>"
            "<div style='display: flex; align-items: center; gap: 8px; background: rgba(255, 255, 255, 0.6); backdrop-filter: blur(5px); padding: 10px 16px; border-radius: 12px; border: 1px solid rgba(225, 29, 72, 0.15); color: #0F172A; font-weight: 700; font-size: 13px;'>"
            "<svg width='18' height='18' viewBox='0 0 24 24' fill='none' stroke='#E11D48' stroke-width='2.5' stroke-linejoin='round'><rect x='2' y='3' width='20' height='14' rx='2' ry='2'/><line x1='8' y1='21' x2='16' y2='21'/><line x1='12' y1='17' x2='12' y2='21'/></svg>"
            "Real-time Dashboard"
            "</div>"
            "</div>"
            "<div style='margin-top: 55px; display: flex; align-items: center; gap: 15px;'>"
            "<div style='display: flex; margin-left: 10px;'>"
            "<div style='width: 35px; height: 35px; border-radius: 50%; background: #E11D48; border: 2px solid white; display: flex; align-items: center; justify-content: center; color: white; font-size: 10px; font-weight: bold; z-index: 3; margin-left: -10px;'>G9</div>"
            "<div style='width: 35px; height: 35px; border-radius: 50%; background: #BE123C; border: 2px solid white; margin-left: -10px; z-index: 2;'></div>"
            "<div style='width: 35px; height: 35px; border-radius: 50%; background: #9F1239; border: 2px solid white; margin-left: -10px; z-index: 1;'></div>"
            "</div>"
            "<div style='font-size: 13px; color: #64748B; font-weight: 600; margin-left: 5px;'>Developed by <span style='color: #0F172A;'>Group 9</span></div>"
            "</div>"
            "</div>"
        )
        st.markdown(hero_html, unsafe_allow_html=True)
        
    with col_right:
        st.write("")
        st.write("")
        with st.form("login_form"):
            form_header_html = (
                "<div style='text-align: center; margin-bottom: 35px;'>"
                "<div style='width: 55px; height: 55px; background: linear-gradient(135deg, #E11D48 0%, #BE123C 100%); border-radius: 16px; display: inline-flex; align-items: center; justify-content: center; margin-bottom: 20px; box-shadow: 0 15px 30px -5px rgba(225, 29, 72, 0.4);'>"
                "<svg width='28' height='28' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2.5' stroke-linecap='round' stroke-linejoin='round'><path d='M12 2L2 7l10 5 10-5-10-5z'/><path d='M2 17l10 5 10-5M2 12l10 5 10-5'/></svg>"
                "</div>"
                "<h2 style='font-family: \"Plus Jakarta Sans\", sans-serif; font-size: 26px; font-weight: 800; color: #0F172A; margin: 0; letter-spacing: -0.5px;'>Welcome Back</h2>"
                "<p style='color: #64748B; font-size: 14px; margin-top: 8px; font-weight: 500;'>Enter your credentials to access the system</p>"
                "</div>"
            )
            st.markdown(form_header_html, unsafe_allow_html=True)
            
            username = st.text_input("Username", placeholder="Masukkan ID Pengguna", label_visibility="collapsed")
            st.write("")
            password = st.text_input("Password", type="password", placeholder="••••••••••••", label_visibility="collapsed")
            
            submit_login = st.form_submit_button("Sign In to AgriSys", type="primary", use_container_width=True)
            
            if submit_login:
                auth = database.verify_login(username, password)
                if auth['status']:
                    st.session_state['logged_in'] = True
                    st.session_state['name'] = auth['name']
                    st.session_state['role'] = auth['role']
                    st.rerun() 
                else:
                    st.error("Autentikasi gagal. Periksa kembali kredensial Anda.")

# ===================================
# KONDISI 2: HALAMAN DASHBOARD UTAMA 
# ===================================
else:
    st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

/* MEMBUAT HEADER BAWAAN MENJADI TRANSPARAN AGAR MOTIF TIDAK TERTUTUP */
header[data-testid="stHeader"] {
    background: transparent !important;
}

/* MEMAKSA CONTAINER BAWAAN TRANSPARAN AGAR BACKGROUND MUNCUL */
[data-testid="stAppViewContainer"] {
    background: transparent !important;
}

/* ====================================
   BACKGROUND DENGAN MOTIF "DOT MATRIX"
   ==================================== */
.stApp {
    background-color: #F4F7F9 !important; 
    background-image: 
        radial-gradient(circle at 85% 10%, rgba(225, 29, 72, 0.12) 0%, transparent 45%),
        radial-gradient(circle at 15% 90%, rgba(190, 18, 60, 0.08) 0%, transparent 45%),
        radial-gradient(rgba(15, 23, 42, 0.1) 1.5px, transparent 1.5px) !important;
    background-size: 100% 100%, 100% 100%, 26px 26px !important;
    background-attachment: fixed !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

h1, h2, h3, h4, h5, h6 { color: #0F172A !important; font-weight: 800; letter-spacing: -0.5px; }

/* SIDEBAR: Efek Kaca (Glassmorphism) */
[data-testid="stSidebar"] { 
    background: rgba(255, 255, 255, 0.6) !important; 
    backdrop-filter: blur(24px) !important;
    -webkit-backdrop-filter: blur(24px) !important;
    border-right: 1px solid rgba(225, 29, 72, 0.15) !important; 
}

/* METRIC CARDS: Kaca Premium dengan Bayangan Halus */
div[data-testid="metric-container"] {
    background: rgba(255, 255, 255, 0.8) !important;
    backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255, 255, 255, 0.9) !important;
    border-radius: 20px;
    padding: 25px;
    box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.05), inset 0 0 0 1px rgba(255, 255, 255, 0.6);
    transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
div[data-testid="metric-container"]:hover {
    border-color: rgba(225, 29, 72, 0.3) !important;
    box-shadow: 0 20px 35px -10px rgba(225, 29, 72, 0.15);
    transform: translateY(-4px);
    background: rgba(255, 255, 255, 0.95) !important;
}
div[data-testid="metric-container"] label { color: #64748B !important; font-weight: 700; font-size: 13px; letter-spacing: 0.5px; }
div[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #0F172A !important; font-weight: 900; font-size: 36px; }

/* INPUT & SELECT BOX */
.stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
    background: rgba(255, 255, 255, 0.9) !important;
    border: 2px solid rgba(226, 232, 240, 0.9) !important;
    color: #0F172A !important;
    border-radius: 12px !important;
    font-weight: 600;
    transition: all 0.3s ease;
}
.stTextInput>div>div>input:focus, .stSelectbox>div>div>div:focus { 
    border-color: #E11D48 !important; 
    box-shadow: 0 0 0 4px rgba(225, 29, 72, 0.1) !important; 
    background: #FFFFFF !important;
}

/* TOMBOL UTAMA */
.stButton>button[kind="primary"] {
    background: linear-gradient(135deg, #E11D48 0%, #BE123C 100%) !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 12px !important;
    transition: all 0.3s ease;
    box-shadow: 0 4px 10px rgba(225, 29, 72, 0.2);
}
.stButton>button[kind="primary"]:hover { 
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(225, 29, 72, 0.35); 
}

/* DATAFRAME / TABEL - Semi transparan agar motif background tembus */
.stDataFrame { 
    border: 1px solid rgba(226, 232, 240, 0.9); 
    border-radius: 16px; 
    background: rgba(255, 255, 255, 0.85); 
    backdrop-filter: blur(10px);
    padding: 10px;
    box-shadow: 0 10px 30px -10px rgba(0,0,0,0.05);
}
</style>""", unsafe_allow_html=True)

    with st.sidebar:
        user_initial = st.session_state['name'][0].upper() if st.session_state.get('name') else 'U'
        user_name = st.session_state['name']
        user_role = st.session_state['role']
        
        sidebar_html = (
            f"<div style='padding: 20px 0px; text-align: center;'>"
            f"<h2 style='font-weight: 900; letter-spacing: -1px; color: #0F172A; margin:0;'>AgriSys<span style='color: #E11D48;'>.</span>io</h2>"
            f"<div style='color: #E11D48; font-size: 10px; font-weight: 800; letter-spacing: 1.5px; margin-top: 5px; text-transform: uppercase;'>By Group 9</div>"
            f"<div style='display: flex; align-items: center; justify-content: center; gap: 15px; margin-top: 25px; padding: 12px; background: rgba(255, 255, 255, 0.7); border-radius: 16px; border: 1px solid rgba(255,255,255,0.9); box-shadow: 0 4px 15px rgba(0,0,0,0.03);'>"
            f"<div style='width: 45px; height: 45px; border-radius: 12px; background: linear-gradient(135deg, #E11D48 0%, #BE123C 100%); display: flex; align-items: center; justify-content: center; color: #FFFFFF; font-weight: 800; font-size: 20px; box-shadow: 0 4px 10px rgba(225,29,72,0.3);'>"
            f"{user_initial}"
            f"</div>"
            f"<div style='text-align: left;'>"
            f"<div style='color: #0F172A; font-weight: 800; font-size: 14px;'>{user_name}</div>"
            f"<div style='color: #64748B; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;'>{user_role}</div>"
            f"</div>"
            f"</div>"
            f"</div>"
            f"<hr style='border-color: rgba(226, 232, 240, 0.8); margin: 10px 0 20px 0;'>"
        )
        st.markdown(sidebar_html, unsafe_allow_html=True)
        
        if st.session_state['role'] == "Admin":
            menu_options = ["Platform Overview", "Master Registry", "Field Operations", "Financial Ledger", "Executive Reports"]
            menu_icons = ["grid-1x2", "database-fill", "basket3-fill", "bank2", "file-earmark-bar-graph-fill"]
        else:
            menu_options = ["Platform Overview", "Field Operations"]
            menu_icons = ["grid-1x2", "basket3-fill"]

        selected = option_menu(
            menu_title=None,
            options=menu_options,
            icons=menu_icons,
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#64748B", "font-size": "16px"}, 
                "nav-link": {"font-size": "14px", "font-weight": "700", "text-align": "left", "margin":"5px 0px", "color": "#475569", "border-radius": "12px", "padding": "12px 15px"},
                "nav-link-selected": {
                    "background": "linear-gradient(90deg, rgba(225,29,72,0.1) 0%, rgba(255,255,255,0) 100%)", 
                    "color": "#E11D48", 
                    "font-weight": "800", 
                    "border-left": "4px solid #E11D48",
                    "border-radius": "0 12px 12px 0"
                },
            }
        )
        
        st.write("")
        if st.button("Sign Out", use_container_width=True, type="secondary"):
            st.session_state['logged_in'] = False
            st.session_state['name'] = ''
            st.session_state['role'] = ''
            st.rerun()

    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    
    if selected == "Platform Overview":
        dashboard.render()
    elif selected == "Master Registry":
        data_master.render()
    elif selected == "Field Operations":
        operasional.render()
    elif selected == "Financial Ledger":
        transaksi.render()
    elif selected == "Executive Reports":
        laporan.render()
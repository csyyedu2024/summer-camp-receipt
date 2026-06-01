import streamlit as st
import pandas as pd
import json
import gspread

# ==========================
# 1. 網頁基本設定與自訂樣式 (CSS)
# ==========================
st.set_page_config(
    page_title="創思優語 | 營隊課程明細查詢",
    page_icon="🎓",
    layout="centered"
)

st.markdown(
    """
    <style>
    div[data-testid="stTextInput"] label p {
        font-size: 20px !important;
        font-weight: bold !important;
        color: #485C6E !important;
    }
    div[data-testid="stTextInput"] input {
        font-size: 22px !important;
        padding: 15px !important;
    }
    div[data-testid="stButton"] button {
        height: auto !important;
        padding: 10px 24px !important;
    }
    div[data-testid="stButton"] button p {
        font-size: 20px !important;
        font-weight: bold !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🎓 創思優語 - 營隊明細與繳費回報")
st.write("請輸入家長聯絡電話並按下 Enter，系統將為您整併明細。")
st.markdown("---")

# ==========================
# 2. 連線 Google Sheet 與讀取資料
# ==========================
# ⚠️ 【重要】請將下方替換成您總表「真實的網址」(帶有 /edit 的那串)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1d1H1ofnf2NS0EJf5eaDH6XrmPT0k9tvk_7jwKjlPUtE/edit?resourcekey=&gid=56127787#gid=56127787"

@st.cache_resource
def get_gspread_client():
    creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
    return gspread.service_account_from_dict(creds_dict)

@st.cache_data(ttl=30)
def load_data():
    try:
        gc = get_gspread_client()
        sh = gc.open_by_url(SHEET_URL)
        # 這裡如果您有用方法二改過分頁名稱，請記得改回來，例如 ws = sh.worksheet("您的分頁名稱")
        ws = sh.sheet1
        data = ws.get_all_values()
        
        if not data:
            return pd.DataFrame()
            
        headers = data[0]
        df = pd.DataFrame(data[1:], columns=headers)
        
        df.columns = df.columns.astype(str).str.strip()
        df['真實列數'] = range(2, len(df) + 2)
        
        if '家長聯絡電話' in df.columns:
            df['家長聯絡電話'] = df['家長聯絡電話'].astype(str).str.

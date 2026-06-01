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
        ws = sh.sheet1
        data = ws.get_all_values()
        
        if not data:
            return pd.DataFrame()
            
        headers = data[0]
        df = pd.DataFrame(data[1:], columns=headers)
        
        # 【新增防護罩】徹底清除所有標題欄位可能隱藏的空白鍵
        df.columns = df.columns.astype(str).str.strip()
        
        # 紀錄每筆資料在 Google 表單中的「真實列數」(以便稍後寫入後五碼)
        df['真實列數'] = range(2, len(df) + 2)
        
        # 資料清理
        if '家長聯絡電話' in df.columns:
            df['家長聯絡電話'] = df['家長聯絡電話'].astype(str).str.replace("'", "").str.strip()
            
        # 確保金額可以計算 (移除可能包含的逗號)
        if '應繳金額' in df.columns:
            df['應繳金額'] = pd.to_numeric(df['應繳金額'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        if '實繳金額' in df.columns:
            df['實繳金額'] = pd.to_numeric(df['實繳金額'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        
        # 處理空值與符號防護
        df = df.replace(["", "nan", "NaN", "None"], "無")
        for col in df.columns:
            if df[col].dtype == 'object' and col != '真實列數':
                df[col] = df[col].astype(str).str.replace('$', '＄')
                
        return df
    except Exception as e:
        st.error(f"資料讀取失敗，請確認網址是否正確。詳細錯誤：{e}")
        return pd.DataFrame()

df = load_data()

# ==========================
# 3. 查詢介面與合併邏輯
# ==========================
if not df.empty:
    search_phone = st.text_input("🔍 請輸入家長聯絡電話 (例如：0912345678)：", max_chars=15)
    
    if search_phone:
        # 在篩選前，確認總表真的有這個欄位
        if '家長聯絡電話' not in df.columns:
            st.error("⚠️ 總表格式錯誤：找不到『家長聯絡電話』這個欄位，請確認總表第一列的標題是否有打錯字！")
        else:
            user_data = df[df['家長聯絡電話'] == search_phone.strip()]
            
            if user_data.empty:
                st.warning("找不到此電話的報名紀錄，請確認號碼是否輸入正確，或聯繫行政人員。")
            else:
                parent_name = user_data['家長姓名'].iloc[0]
                student_names = "、".join(user_data['學生姓名'].astype(str).unique())
                total_amount = int(user_data['實繳金額'].sum())
                
                display_df = user_data[['學生姓名', '營隊名稱', '應繳金額', '優惠內容', '實繳金額', '繳費狀態']]
                
                table_html = "<table style='width:100%; border-collapse: collapse; text-align: left; font-size: 14px; margin-top: 15px;'>"
                table_html += "<tr style='background-color: #EAEFF3; color: #485C6E; border-bottom: 2px solid #7B90A7;'>"
                table_html += "<th style='padding: 10px; white-space: nowrap;'>學生姓名</th>"
                table_html += "<th style='padding: 10px;'>營隊名稱</th>"
                table_html += "<th style='padding: 10px; white-space: nowrap; text-align: center;'>應繳<br>金額</th>"
                table_html += "<th style='padding: 10px;'>優惠內容</th>"
                table_html += "<th style='padding: 10px; white-space: nowrap; text-align: center;'>實繳<br>金額</th>"
                table_html += "<th style='padding: 10px; white-space: nowrap; text-align: center;'>繳費<br>狀態</th>"
                table_html += "</tr>"
                
                for index, row in display_df.iterrows():
                    table_html += "<tr style='border-bottom: 1px solid #EEEEEE; color: #444444;'>"
                    table_html += f"<td style='padding: 10px; white-space: nowrap;'>{row['學生姓名']}</td>"
                    table_html += f"<td style='padding: 10px;'>{row['營隊名稱']}</td>"
                    table_html += f"<td style='padding: 10px; text-align: center;'>{int(row['應繳金額']):,}</td>"
                    table_html += f"<td style='padding: 10px;'>{row['優惠內容']}</td>"
                    table_html += f"<td style='padding: 10px; text-align: center;'>{int(

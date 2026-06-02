import streamlit as st
import pandas as pd
import json
import gspread
from datetime import datetime, timedelta

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
        
        df.columns = df.columns.astype(str).str.strip()
        df['真實列數'] = range(2, len(df) + 2)
        
        if '家長聯絡電話' in df.columns:
            df['家長聯絡電話'] = df['家長聯絡電話'].astype(str).str.replace("'", "").str.strip()
            
        if '應繳金額' in df.columns:
            df['應繳金額'] = pd.to_numeric(df['應繳金額'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        if '實繳金額' in df.columns:
            df['實繳金額'] = pd.to_numeric(df['實繳金額'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        
        # 處理空值，並把繳費狀態的「無」變成「待繳費」
        df = df.replace(["", "nan", "NaN", "None"], "無")
        if '繳費狀態' in df.columns:
            df['繳費狀態'] = df['繳費狀態'].replace("無", "待繳費")
            
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
                    table_html += f"<td style='padding: 10px; text-align: center;'>{int(row['實繳金額']):,}</td>"
                    
                    # 【新增】顏色標籤邏輯判斷
                    status = str(row['繳費狀態'])
                    if "待繳費" in status:
                        # 紅色系標籤
                        status_html = f"<span style='color: #D32F2F; font-weight: bold; background-color: #FDECEA; padding: 6px 10px; border-radius: 6px; display: inline-block;'>{status}</span>"
                    elif "待確認" in status:
                        # 橘黃色系標籤
                        status_html = f"<span style='color: #E68A00; font-weight: bold; background-color: #FFF4E5; padding: 6px 10px; border-radius: 6px; display: inline-block;'>{status}</span>"
                    elif "已繳費" in status:
                        # 綠色系標籤
                        status_html = f"<span style='color: #2E7D32; font-weight: bold; background-color: #E8F5E9; padding: 6px 10px; border-radius: 6px; display: inline-block;'>{status}</span>"
                    else:
                        status_html = status
                        
                    table_html += f"<td style='padding: 10px; text-align: center; white-space: nowrap;'>{status_html}</td>"
                    table_html += "</tr>"
                table_html += "</table>"
                
                receipt_html = f"""
<div style="max-width: 800px; margin: auto; border: 1px solid #7B90A7; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); background-color: #FFFFFF; overflow: hidden; margin-bottom: 20px;">
    <div style="background-color: #F3F6F8; padding: 25px; border-bottom: 2px dashed #7B90A7; text-align: center;">
        <h2 style="margin: 0; color: #485C6E; letter-spacing: 2px; font-weight: bold;">🎓 創思優語 營隊課程明細</h2>
        <p style="margin: 5px 0 0 0; color: #6B8296; font-size: 14px;">用心陪伴，啟發無限可能</p>
    </div>
    <div style="padding: 25px;">
        <div style="display: flex; justify-content: space-between; flex-wrap: wrap; margin-bottom: 20px; font-size: 16px; color: #333;">
            <div>
                <p style="margin: 5px 0;"><strong>👨‍👩‍👧‍👦 家長姓名：</strong> {parent_name}</p>
                <p style="margin: 5px 0;"><strong>📞 聯絡電話：</strong> {search_phone}</p>
            </div>
            <div style="text-align: right;">
                <p style="margin: 5px 0;"><strong>🎓 學生姓名：</strong> {student_names}</p>
            </div>
        </div>
        <h4 style="color: #485C6E; border-left: 4px solid #7B90A7; padding-left: 10px; margin-bottom: 10px;">📋 報名明細</h4>
        {table_html}
        <div style="margin-top: 25px; padding-top: 15px; border-top: 2px solid #7B90A7; text-align: right;">
            <span style="font-size: 16px; color: #555;">總計實繳金額：</span>
            <span style="font-size: 26px; font-weight: bold; color: #D32F2F;">{total_amount:,} 元</span>
        </div>
    </div>
    <div style="background-color: #F8F9FA; padding: 20px 25px; border-top: 2px dashed #7B90A7;">
        <h4 style="color: #485C6E; margin-top: 0; margin-bottom: 15px;">🏦 匯款資訊</h4>
        <div style="font-size: 16px; color: #444; line-height: 1.6;">
            <p style="margin: 0;"><strong>銀行代碼：</strong>807 (永豐銀行) </p>
            <p style="margin: 0;"><strong>匯款帳號：</strong>007-018-0005798-6</p>
            <p style="margin: 0;"><strong>戶　　名：</strong>創思優語有限公司</p>
        </div>
    </div>
</div>
"""
                st.markdown(receipt_html, unsafe_allow_html=True)
                
                # ==========================
                # 4. 繳費回報表單 (寫入 Google Sheet)
                # ==========================
                st.markdown("### 💳 繳費回報")
                st.info("若您已完成匯款，請於下方輸入帳號後五碼，系統將自動為您登記。")
                
                with st.form("payment_form"):
                    five_digits = st.text_input("📝 請輸入匯款帳號【後五碼】", max_chars=5, placeholder="例如：12345")
                    submit_btn = st.form_submit_button("送出回報", type="primary")
                    
                    if submit_btn:
                        if len(five_digits.strip()) < 4:
                            st.error("⚠️ 請輸入完整的後五碼！")
                        else:
                            with st.spinner("系統正在將資料寫入總表，請稍候..."):
                                try:
                                    gc = get_gspread_client()
                                    sh = gc.open_by_url(SHEET_URL)
                                    ws = sh.sheet1
                                    
                                    sheet_headers = ws.row_values(1)
                                    clean_headers = [str(h).strip() for h in sheet_headers]
                                    
                                    # 檢查三個欄位是不是都準備好了
                                    if "匯款後五碼" not in clean_headers or "回報時間" not in clean_headers or "繳費狀態" not in clean_headers:
                                        st.error("⚠️ 寫入失敗！請確認總表第一列有「匯款後五碼」、「回報時間」及「繳費狀態」這三個標題。")
                                    else:
                                        col_idx_5digits = clean_headers.index("匯款後五碼") + 1
                                        col_idx_time = clean_headers.index("回報時間") + 1
                                        col_idx_status = clean_headers.index("繳費狀態") + 1 # 找到繳費狀態欄位
                                        
                                        rows_to_update = user_data['真實列數'].tolist()
                                        tw_time = (datetime.utcnow() + timedelta(hours=8)).strftime("%Y-%m-%d %H:%M:%S")
                                        
                                        # 依序寫入三個欄位 (後五碼、時間、把狀態改成待確認)
                                        for r in rows_to_update:
                                            ws.update_cell(r, col_idx_5digits, f"'{five_digits.strip()}")
                                            ws.update_cell(r, col_idx_time, tw_time)
                                            ws.update_cell(r, col_idx_status, "待確認")
                                            
                                        st.success("🎉 回報成功！已為您寫入系統，行政人員將會盡快為您對帳。")
                                        st.cache_data.clear()
                                except Exception as e:
                                    st.error(f"寫入失敗，請稍後再試或截圖聯繫行政。詳細錯誤：{e}")

import streamlit as st
import pandas as pd

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
    /* 放大輸入框上方的提示文字 */
    div[data-testid="stTextInput"] label p {
        font-size: 20px !important;
        font-weight: bold !important;
        color: #485C6E !important;
    }
    /* 放大輸入框本身與打字進去的文字 */
    div[data-testid="stTextInput"] input {
        font-size: 22px !important;
        padding: 15px !important;
    }
    /* 放大查詢按鈕與裡面的文字 */
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

st.title("🎓 創思優語 - 營隊明細查詢")
st.write("請輸入家長聯絡電話，系統將自動為您整併同戶手足的報名明細。")
st.markdown("---")

# ==========================
# 2. 讀取 Google Sheet 資料
# ==========================
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSuoeRKUfTRl-FFQrVLw42y3yD_kJfXutXDgRFQOGh7aSy_fs9iQGwy5Fz_eY4XSX7TINvBRJSLmkrv/pub?gid=56127787&single=true&output=csv"

@st.cache_data(ttl=30)
def load_data():
    try:
        df = pd.read_csv(SHEET_CSV_URL, dtype=str)
        df['家長聯絡電話'] = df['家長聯絡電話'].astype(str).str.replace("'", "").str.strip()
        df['應繳金額'] = pd.to_numeric(df['應繳金額'], errors='coerce').fillna(0)
        df['實繳金額'] = pd.to_numeric(df['實繳金額'], errors='coerce').fillna(0)
        
        # 填補空值，並徹底消滅 nan
        df = df.fillna("無")
        df = df.replace(["nan", "NaN", "None"], "無")
        
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.replace('$', '＄')
        return df
    except Exception as e:
        st.error(f"抓到蟲了，錯誤原因是：{e}")
        return pd.DataFrame()

df = load_data()

# ==========================
# 3. 查詢介面與合併邏輯
# ==========================
if not df.empty:
    search_phone = st.text_input("🔍 請輸入家長聯絡電話 (例如：0912345678)：", max_chars=15)
    
    if st.button("查詢明細", type="primary"):
        if search_phone:
            user_data = df[df['家長聯絡電話'] == search_phone.strip()]
            
            if user_data.empty:
                st.warning("找不到此電話的報名紀錄，請確認號碼是否輸入正確，或聯繫行政人員。")
            else:
                parent_name = user_data['家長姓名'].iloc[0]
                student_names = "、".join(user_data['學生姓名'].astype(str).unique())
                total_amount = int(user_data['實繳金額'].sum())
                
                st.success("查詢成功！以下是您的專屬明細：")
                
                # ==========================
                # 4. 渲染一體成型的高質感收據 (莫蘭迪藍 + 排版優化)
                # ==========================
                display_df = user_data[['學生姓名', '營隊名稱', '應繳金額', '優惠內容', '實繳金額', '繳費狀態']]
                
                table_html = "<table style='width:100%; border-collapse: collapse; text-align: left; font-size: 14px; margin-top: 15px;'>"
                table_html += "<tr style='background-color: #EAEFF3; color: #485C6E; border-bottom: 2px solid #7B90A7;'>"
                # 【排版優化】設定標題不換行、強制斷行與置中
                table_html += "<th style='padding: 10px; white-space: nowrap;'>學生姓名</th>"
                table_html += "<th style='padding: 10px;'>營隊名稱</th>"
                table_html += "<th style='padding: 10px; white-space: nowrap; text-align: center;'>應繳<br>金額</th>"
                table_html += "<th style='padding: 10px;'>優惠內容</th>"
                table_html += "<th style='padding: 10px; white-space: nowrap; text-align: center;'>實繳<br>金額</th>"
                table_html += "<th style='padding: 10px; white-space: nowrap; text-align: center;'>繳費<br>狀態</th>"
                table_html += "</tr>"
                
                for index, row in display_df.iterrows():
                    table_html += "<tr style='border-bottom: 1px solid #EEEEEE; color: #444444;'>"
                    # 【排版優化】學生姓名加上 white-space: nowrap 確保不斷行；數字與狀態置中對齊
                    table_html += f"<td style='padding: 10px; white-space: nowrap;'>{row['學生姓名']}</td>"
                    table_html += f"<td style='padding: 10px;'>{row['營隊名稱']}</td>"
                    table_html += f"<td style='padding: 10px; text-align: center;'>{int(row['應繳金額']):,}</td>"
                    table_html += f"<td style='padding: 10px;'>{row['優惠內容']}</td>"
                    table_html += f"<td style='padding: 10px; text-align: center;'>{int(row['實繳金額']):,}</td>"
                    table_html += f"<td style='padding: 10px; text-align: center;'>{row['繳費狀態']}</td>"
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
</div>
"""
                
                st.markdown(receipt_html, unsafe_allow_html=True)
                
                st.info("💡 感謝您的報名！若需紙本留存，可直接使用手機截圖，或電腦版瀏覽器的「列印」功能（Ctrl+P 或 Cmd+P）將本頁儲存為 PDF。")

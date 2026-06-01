import streamlit as st
import pandas as pd

# ==========================
# 1. 網頁基本設定
# ==========================
st.set_page_config(
    page_title="創思優語 | 營隊收據查詢系統",
    page_icon="🎓",
    layout="centered"
)

st.title("🎓 創思優語 - 營隊收據查詢")
st.write("請輸入家長聯絡電話，系統將自動為您整併同戶手足的報名明細。")
st.markdown("---")

# ==========================
# 2. 讀取 Google Sheet 資料
# ==========================
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSuoeRKUfTRl-FFQrVLw42y3yD_kJfXutXDgRFQOGh7aSy_fs9iQGwy5Fz_eY4XSX7TINvBRJSLmkrv/pub?gid=56127787&single=true&output=csv"

@st.cache_data(ttl=30) # 快取 30 秒，您更新總表後，網頁最慢 30 秒內會更新
def load_data():
    try:
        df = pd.read_csv(SHEET_CSV_URL)
        # 確保電話欄位是字串，避免 0912 變成 912
        df['家長聯絡電話'] = df['家長聯絡電話'].astype(str).str.strip()
        
        # 確保金額可以計算，轉為數值格式並將空白補 0
        df['應繳金額'] = pd.to_numeric(df['應繳金額'], errors='coerce').fillna(0)
        df['實繳金額'] = pd.to_numeric(df['實繳金額'], errors='coerce').fillna(0)
        
        # 針對文字欄位填補「無」，放過數字欄位避免報錯
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].fillna("無")
                
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
    
    if st.button("查詢收據", type="primary"):
        if search_phone:
            # 篩選符合電話的資料
            user_data = df[df['家長聯絡電話'] == search_phone.strip()]
            
            if user_data.empty:
                st.warning("找不到此電話的報名紀錄，請確認號碼是否輸入正確，或聯繫行政人員。")
            else:
                # 抓取基本資料 (取第一筆紀錄的家長姓名)
                parent_name = user_data['家長姓名'].iloc[0]
                # 收集所有出現過的學生姓名 (自動去重複，例如手足名字會變成「王大寶、王小寶」)
                student_names = "、".join(user_data['學生姓名'].astype(str).unique())
                # 計算總計實繳金額
                total_amount = int(user_data['實繳金額'].sum())
                
                st.success("查詢成功！以下是您的專屬收據：")
                
                # ==========================
                # 4. 渲染收據畫面 (HTML/CSS 增加品牌質感)
                # ==========================
                st.markdown(f"""
                <div style="border: 2px solid #E6B34A; border-radius: 10px; padding: 20px; background-color: #FFFCF7;">
                    <h2 style="text-align: center; color: #8C6A28; letter-spacing: 2px;">創思優語 課程收據</h2>
                    <hr style="border-top: 1px dashed #E6B34A;">
                    <p style="font-size: 16px;"><strong>👨‍👩‍👧‍👦 家長姓名：</strong> {parent_name}</p>
                    <p style="font-size: 16px;"><strong>🎓 學生姓名：</strong> {student_names}</p>
                    <p style="font-size: 16px;"><strong>📞 聯絡電話：</strong> {search_phone}</p>
                    <br>
                    <h4 style="color: #8C6A28;">📋 報名明細：</h4>
                </div>
                """, unsafe_allow_html=True)
                
                # 顯示明細表格 (只挑選家長核對需要的欄位，隱藏內部行政欄位)
               display_df = user_data[['學生姓名', '營隊名稱', '應繳金額', '優惠內容', '實繳金額', '繳費狀態']]

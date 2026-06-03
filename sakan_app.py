import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="نظام مصاريف السكن", page_icon="🏠", layout="wide")

# الروابط الخاصة بك
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1g0VfbnUVwNXjV0c2BFlmlX3RSh5eZnpzLUrzwLeqG2I/export?format=csv&gid=0"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxdbKpbajXkRUFsAhSJMuxlW7_etBpq05Kx8B_zWQ2I4C3VTxZVAMyM0mtAvFHighCU/exec"

SHABAB = ["أبو عمار على شهبور", "أبو أحمد تامر حيدر", "أبو فهد عبد الرحمن", "أبو بدر أحمد حسان", "أبو كريم", "أبو زين علاء الصاوي"]
MONTHS_AR = {"January": "يناير", "February": "فبراير", "March": "مارس", "April": "أبريل", "May": "مايو", "June": "يونيو", "July": "يوليو", "August": "أغسطس", "September": "سبتمبر", "October": "أكتوبر", "November": "نوفمبر", "December": "ديسمبر"}

st.title("🏠 نظام مصاريف السكن (إعداد أبو زين)")

def load_data():
    try:
        url = f"{SHEET_CSV_URL}&cachebust={datetime.now().timestamp()}"
        df = pd.read_csv(url)
        return df
    except:
        return pd.DataFrame(columns=["الشهر", "الاسم", "المبلغ", "البيان", "التاريخ", "الصورة"])

all_data = load_data()

# التحكم العلوي
col_top1, col_top2 = st.columns(2)
with col_top1:
    current_date = datetime.now()
    month_options_en = [datetime(2026, m, 1).strftime("%B %Y") for m in range(1, 13)]
    month_options_ar = [f"{MONTHS_AR[m.split()[0]]} {m.split()[1]}" for m in month_options_en]
    selected_month_ar = st.selectbox("📅 اختر الشهر:", month_options_ar, index=current_date.month - 1)

with col_top2:
    rent_val = st.number_input(f"💰 إيجار الفرد ({selected_month_ar}):", min_value=0.0, value=42.165, format="%.3f")

st.divider()

# الإدخال والحسابات
month_df = all_data[all_data["الشهر"] == selected_month_ar]
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("➕ إضافة مصروف")
    with st.form("add_form", clear_on_submit=True):
        name = st.selectbox("من دفع؟", SHABAB)
        amount = st.number_input("المبلغ:", min_value=0.0, step=0.1, format="%.3f")
        note = st.text_input("البيان:", placeholder="مثال: أنبوبة، منظفات")
        uploaded_img = st.file_uploader("📸 رفع صورة الفاتورة:", type=['png', 'jpg', 'jpeg'])
        submit = st.form_submit_button("تسجيل المصروف")
        
        if submit:
            if amount > 0:
                img_base64 = ""
                img_name = ""
                if uploaded_img is not None:
                    img_name = uploaded_img.name
                    # تحويل ملف الصورة لنص مشفر ليتم نقله لجوجل درايف
                    img_base64 = base64.b64encode(uploaded_img.read()).decode('utf-8')
                
                payload = {
                    "month": selected_month_ar, "name": name, "amount": amount,
                    "note": note, "date": datetime.now().strftime("%Y-%m-%d"),
                    "imgData": img_base64, "imgName": img_name
                }
                
                try:
                    # نستخدم POST لدعم الملفات الكبيرة
                    with st.spinner("جاري رفع الفاتورة وتسجيل المصروف..."):
                        response = requests.post(SCRIPT_URL, data=payload)
                    if "Success" in response.text:
                        st.success("✅ تم تسجيل المصروف ورفع الفاتورة بنجاح!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"استجاب السيرفر بـ: {response.text}")
                except:
                    st.error("فشل الاتصال بالخادم السحابي.")

with col2:
    st.subheader(f"📊 تصفية {selected_month_ar}")
    total_extra = pd.to_numeric(month_df["المبلغ"], errors='coerce').sum()
    fair_extra = total_extra / len(SHABAB) if total_extra > 0 else 0
    summary = []
    for person in SHABAB:
        paid = pd.to_numeric(month_df[month_df["الاسم"] == person]["المبلغ"], errors='coerce').sum()
        balance = paid - (fair_extra + rent_val)
        status = "🟢 له" if balance > 0 else "🔴 عليه"
        summary.append({"الاسم": person, "مدفوع": f"{paid:.3f}", "الوضع": status, "المبلغ": f"{abs(balance):.3f}"})
    st.table(summary)

# --- سجل المصروفات المطور لعرض الصور وروابطها ---
st.divider()
st.subheader(f"📜 سجل مصاريف {selected_month_ar}")
if not month_df.empty:
    for idx, row in month_df.iloc[::-1].iterrows():
        with st.expander(f"📌 {row['الاسم']} | {row['المبلغ']:.3f} | {row['البيان']}"):
            st.write(f"**التاريخ:** {row['التاريخ']}")
            img_link = str(row['الصورة']).strip()
            
            if img_link.startswith("http"):
                # عرض زر مباشر لفتح الصورة المحفوظة في جوجل درايف
                st.link_button("🔗 اضغط هنا لفتح وعرض صورة الفاتورة", img_link)
            else:
                st.warning("⚠️ لا توجد صورة مرفوعة لهذا المصروف.")
else:
    st.info("لا توجد مصاريف مسجلة.")

st.divider()
st.subheader("📱 تقرير الواتساب")
report = f"*تقرير مصاريف السكن - {selected_month_ar}*\n🏠 الإيجار: {rent_val:.3f}\n💰 النثريات: {total_extra:.3f}\n"
for item in summary:
    report += f"• {item['الاسم']}: {item['الوضع']} *{item['المبلغ']}*\n"
st.code(report)

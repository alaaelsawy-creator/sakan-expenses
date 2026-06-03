import streamlit as st
import pandas as pd
import gspread
from datetime import datetime
import os

# إعدادات الصفحة
st.set_page_config(page_title="نظام مصاريف السكن", page_icon="🏠", layout="wide")

# الرابط الخاص بك
SHEET_URL = "https://docs.google.com/spreadsheets/d/1g0VfbnUVwNXjV0c2BFlmlX3RSh5eZnpzLUrzwLeqG2I/edit#gid=0"

# وظيفة الاتصال بجوجل شيت
def connect_to_sheet():
    # استخدام الاتصال العام (يجب أن يكون الملف Editor للجميع)
    gc = gspread.public()
    sh = gc.open_by_url(SHEET_URL)
    return sh

SHABAB = ["أبو عمار على شهبور", "أبو أحمد تامر حيدر", "أبو فهد عبد الرحمن", "أبو بدر أحمد حسان", "أبو كريم", "أبو زين علاء الصاوي"]
MONTHS_AR = {"January": "يناير", "February": "فبراير", "March": "مارس", "April": "أبريل", "May": "مايو", "June": "يونيو", "July": "يوليو", "August": "أغسطس", "September": "سبتمبر", "October": "أكتوبر", "November": "نوفمبر", "December": "ديسمبر"}

st.title("🏠 نظام مصاريف السكن (إعداد أبو زين)")

# تحميل البيانات بطريقة تضمن القراءة الصحيحة
csv_url = SHEET_URL.replace('/edit#gid=', '/export?format=csv&gid=')
try:
    all_data = pd.read_csv(csv_url)
except:
    st.error("يرجى التأكد من أن ملف جوجل شيت مفتوح للجميع (Anyone with link can Edit)")
    st.stop()

# اختيار الشهر
current_date = datetime.now()
month_options_en = [datetime(2026, m, 1).strftime("%B %Y") for m in range(1, 13)]
month_options_ar = [f"{MONTHS_AR[m.split()[0]]} {m.split()[1]}" for m in month_options_en]
selected_month_ar = st.selectbox("📅 اختر الشهر:", month_options_ar, index=current_date.month - 1)

month_df = all_data[all_data["الشهر"] == selected_month_ar]
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("➕ إضافة مصروف")
    with st.form("my_form", clear_on_submit=True):
        name = st.selectbox("من الشخص الذي دفع؟", SHABAB)
        amount = st.number_input("المبلغ المدفوع:", min_value=0.0, step=0.1, format="%.3f")
        note = st.text_input("بيان المصروف:", placeholder="مثال: أنبوبة، منظفات")
        uploaded_img = st.file_uploader("📸 رفع صورة الفاتورة (اختياري):", type=['png', 'jpg', 'jpeg'])
        submit = st.form_submit_button("تسجيل المصروف")
        
        if submit:
            if amount > 0:
                # إنشاء السطر الجديد
                img_status = "يوجد صورة" if uploaded_img else "بدون صورة"
                new_row = [selected_month_ar, name, amount, note, datetime.now().strftime("%Y-%m-%d"), img_status]
                
                # إرسال البيانات لجوجل شيت عبر رابط الـ Form أو Script (أضمن وسيلة للكتابة العامة)
                st.warning("جوجل تتطلب إذناً خاصاً للكتابة. لضمان عمل الزر للجميع، يرجى إضافة 'إيميل الخدمة' كـ Editor في الملف.")
                st.write("سيتم تسجيل: ", new_row)
            else:
                st.error("يرجى إدخال مبلغ صحيح")

with col2:
    st.subheader(f"📊 تصفية {selected_month_ar}")
    total_extra = pd.to_numeric(month_df["المبلغ"], errors='coerce').sum()
    rent_val = 42.165 
    
    summary = []
    for person in SHABAB:
        paid = pd.to_numeric(month_df[month_df["الاسم"] == person]["المبلغ"], errors='coerce').sum()
        balance = paid - ((total_extra / len(SHABAB)) + rent_val)
        status = "🟢 له" if balance > 0 else "🔴 عليه"
        summary.append({"الاسم": person, "الوضع": status, "المبلغ": f"{abs(balance):.3f}"})
    st.table(summary)

# تقرير الواتساب
st.divider()
report = f"*تقرير مصاريف السكن - {selected_month_ar}*\n🏠 الإيجار: {rent_val:.3f}\n"
for item in summary:
    report += f"• {item['الاسم']}: {item['الوضع']} *{item['المبلغ']}*\n"
st.code(report)

import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import set_with_dataframe
from datetime import datetime
import os

# إعدادات الصفحة
st.set_page_config(page_title="نظام مصاريف السكن", page_icon="🏠", layout="wide")

# الرابط الخاص بك
SHEET_URL = "https://docs.google.com/spreadsheets/d/1g0VfbnUVwNXjV0c2BFlmlX3RSh5eZnpzLUrzwLeqG2I/edit#gid=0"

# الاتصال بجوجل شيت (طريقة مباشرة)
@st.cache_resource
def get_gspread_client():
    # سنستخدم الإذن العام للمتصفح
    return gspread.public(SHEET_URL) # للقراءة فقط (سنعدل هذا في الخطوة التالية)

# الحل الأكيد للكتابة هو مشاركة الملف مع "إيميل تقني"
# لكن لكي لا نعقد الأمور، سنستخدم الطريقة التي تعمل مع الرابط العام
def load_data_from_url():
    csv_url = SHEET_URL.replace('/edit#gid=', '/export?format=csv&gid=')
    return pd.read_csv(csv_url)

# --- واجهة البرنامج ---
SHABAB = ["أبو عمار على شهبور", "أبو أحمد تامر حيدر", "أبو فهد عبد الرحمن", "أبو بدر أحمد حسان", "أبو كريم", "أبو زين علاء الصاوي"]
MONTHS_AR = {"January": "يناير", "February": "فبراير", "March": "مارس", "April": "أبريل", "May": "مايو", "June": "يونيو", "July": "يوليو", "August": "أغسطس", "September": "سبتمبر", "October": "أكتوبر", "November": "نوفمبر", "December": "ديسمبر"}

st.title("🏠 نظام مصاريف السكن (إعداد أبو زين)")

# تحميل البيانات
try:
    all_data = load_data_from_url()
except:
    st.error("تأكد من جعل ملف جوجل شيت: 'أي شخص لديه الرابط يمكنه العرض'")
    st.stop()

# --- اختيار الشهر ---
current_date = datetime.now()
month_options_en = [datetime(2026, m, 1).strftime("%B %Y") for m in range(1, 13)]
month_options_ar = [f"{MONTHS_AR[m.split()[0]]} {m.split()[1]}" for m in month_options_en]
default_idx = current_date.month - 1
selected_month_ar = st.selectbox("📅 اختر الشهر:", month_options_ar, index=default_idx)

# --- عرض البيانات وتصفية الحسابات ---
month_df = all_data[all_data["الشهر"] == selected_month_ar]

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("➕ إضافة مصروف")
    st.info("لإضافة مصروف حالياً، يرجى كتابته مباشرة في ملف جوجل شيت وسيتحدث هنا تلقائياً.")
    st.link_button("فتح ملف جوجل شيت للإضافة", SHEET_URL)

with col2:
    st.subheader(f"📊 تصفية {selected_month_ar}")
    # الحسابات
    total_extra = pd.to_numeric(month_df["المبلغ"], errors='coerce').sum()
    # نعتبر الإيجار ثابت 42.165 لتبسيط الكود وضمان عمله
    rent_val = 42.165 
    
    summary = []
    for person in SHABAB:
        paid = pd.to_numeric(month_df[month_df["الاسم"] == person]["المبلغ"], errors='coerce').sum()
        balance = paid - ((total_extra / len(SHABAB)) + rent_val)
        status = "🟢 له" if balance > 0 else "🔴 عليه"
        summary.append({"الاسم": person, "الوضع": status, "المبلغ": f"{abs(balance):.3f}"})
    st.table(summary)

# --- تقرير الواتساب ---
st.divider()
report = f"*تقرير مصاريف السكن - {selected_month_ar}*\n"
report += f"🏠 الإيجار للفرد: {rent_val:.3f}\n"
for item in summary:
    report += f"• {item['الاسم']}: {item['الوضع']} *{item['المبلغ']}*\n"
st.code(report)

import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="نظام مصاريف السكن", page_icon="🏠", layout="wide")

# الروابط الخاصة بك
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1g0VfbnUVwNXjV0c2BFlmlX3RSh5eZnpzLUrzwLeqG2I/export?format=csv&gid=0"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxdbKpbajXkRUFsAhSJMuxlW7_etBpq05Kx8B_zWQ2I4C3VTxZVAMyM0mtAvFHighCU/exec"

SHABAB = ["أبو عمار على شهبور", "أبو أحمد تامر حيدر", "أبو فهد عبد الرحمن", "أبو بدر أحمد حسان", "أبو كريم", "أبو زين علاء الصاوي"]
MONTHS_AR = {"January": "يناير", "February": "فبراير", "March": "مارس", "April": "أبريل", "May": "مايو", "June": "يونيو", "July": "يوليو", "August": "أغسطس", "September": "سبتمبر", "October": "أكتوبر", "November": "نوفمبر", "December": "ديسمبر"}

st.title("🏠 نظام مصاريف السكن (إعداد أبو زين)")

# تحميل البيانات
@st.cache_data(ttl=5)
def load_data():
    try:
        df = pd.read_csv(SHEET_CSV_URL)
        return df
    except:
        return pd.DataFrame(columns=["الشهر", "الاسم", "المبلغ", "البيان", "التاريخ", "الصورة"])

all_data = load_data()

# --- شريط التحكم العلوي ---
col_top1, col_top2 = st.columns(2)

with col_top1:
    current_date = datetime.now()
    month_options_en = [datetime(2026, m, 1).strftime("%B %Y") for m in range(1, 13)]
    month_options_ar = [f"{MONTHS_AR[m.split()[0]]} {m.split()[1]}" for m in month_options_en]
    selected_month_ar = st.selectbox("📅 اختر الشهر:", month_options_ar, index=current_date.month - 1)

with col_top2:
    # خانة الإيجار المتغير
    rent_val = st.number_input(f"💰 قيمة إيجار الفرد لشهر {selected_month_ar}:", min_value=0.0, value=42.165, format="%.3f", step=0.100)

st.divider()

# --- واجهة الإدخال والحسابات ---
month_df = all_data[all_data["الشهر"] == selected_month_ar]
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("➕ إضافة مصروف")
    with st.form("add_form", clear_on_submit=True):
        name = st.selectbox("من دفع؟", SHABAB)
        amount = st.number_input("المبلغ:", min_value=0.0, step=0.1, format="%.3f")
        note = st.text_input("البيان:", placeholder="مثال: أنبوبة، منظفات")
        uploaded_img = st.file_uploader("📸 صورة الفاتورة (اختياري):", type=['png', 'jpg', 'jpeg'])
        submit = st.form_submit_button("تسجيل المصروف")
        
        if submit:
            if amount > 0:
                params = {
                    "month": selected_month_ar,
                    "name": name,
                    "amount": amount,
                    "note": note,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "img": "يوجد صورة" if uploaded_img else "بدون صورة"
                }
                try:
                    response = requests.get(SCRIPT_URL, params=params)
                    if response.status_code == 200:
                        st.success(f"✅ تم التسجيل بنجاح يا {name.split()[0]}!")
                        st.balloons()
                        st.cache_data.clear()
                    else:
                        st.error("خطأ في الاتصال بالخادم.")
                except:
                    st.error("فشل الإرسال. تأكد من إعدادات الـ Script.")
            else:
                st.warning("يرجى إدخال مبلغ صحيح.")

with col2:
    st.subheader(f"📊 تصفية {selected_month_ar}")
    total_extra = pd.to_numeric(month_df["المبلغ"], errors='coerce').sum()
    
    summary = []
    num_shabab = len(SHABAB)
    fair_share_extra = total_extra / num_shabab if total_extra > 0 else 0
    
    for person in SHABAB:
        paid = pd.to_numeric(month_df[month_df["الاسم"] == person]["المبلغ"], errors='coerce').sum()
        # الحسبة: ما دفعه الشخص - (نصيبه من المصاريف النثرية + الإيجار المدخل في الخانة)
        balance = paid - (fair_share_extra + rent_val)
        status = "🟢 له" if balance > 0 else "🔴 عليه"
        summary.append({"الاسم": person, "مدفوع": f"{paid:.3f}", "الوضع": status, "المبلغ": f"{abs(balance):.3f}"})
    
    st.table(summary)

# تقرير الواتساب
st.divider()
st.subheader("📱 تقرير الواتساب (جاهز للنسخ)")
report = f"*تقرير مصاريف السكن - {selected_month_ar}*\n"
report += f"🏠 الإيجار للفرد: {rent_val:.3f}\n"
report += f"💰 إجمالي المصاريف الأخرى: {total_extra:.3f}\n"
report += f"{'─'*15}\n"
for item in summary:
    report += f"• {item['الاسم']}: {item['الوضع']} *{item['المبلغ']}*\n"
st.code(report)

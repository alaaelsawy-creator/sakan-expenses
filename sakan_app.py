import streamlit as st
import pandas as pd
import os
from datetime import datetime
from PIL import Image

# إعدادات الصفحة
st.set_page_config(page_title="نظام مصاريف السكن", page_icon="🏠", layout="wide")

# مسارات الملفات
DB_FILE = "sakan_archive.csv"
RENT_FILE = "rent_settings.csv"
IMG_DIR = "uploaded_images"

# إنشاء مجلد الصور إذا لم يكن موجوداً
if not os.path.exists(IMG_DIR):
    os.makedirs(IMG_DIR)

SHABAB = ["أبو عمار على شهبور", "أبو أحمد تامر حيدر", "أبو فهد عبد الرحمن", "أبو بدر أحمد حسان", "أبو كريم", "أبو زين علاء الصاوي"]

MONTHS_AR = {
    "January": "يناير", "February": "فبراير", "March": "مارس", "April": "أبريل", 
    "May": "مايو", "June": "يونيو", "July": "يوليو", "August": "أغسطس", 
    "September": "سبتمبر", "October": "أكتوبر", "November": "نوفمبر", "December": "ديسمبر"
}

# --- وظائف البيانات ---
def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["الشهر", "الاسم", "المبلغ", "البيان", "التاريخ", "الصورة"])

def load_rent():
    if os.path.exists(RENT_FILE):
        return pd.read_csv(RENT_FILE)
    return pd.DataFrame(columns=["الشهر", "قيمة_الإيجار"])

def save_data(df, file):
    df.to_csv(file, index=False)

if 'all_data' not in st.session_state:
    st.session_state.all_data = load_data()
if 'rent_data' not in st.session_state:
    st.session_state.rent_data = load_rent()

# --- الشريط العلوي ---
st.title("🏠 نظام أرشيف مصاريف السكن المشترك")

col_a, col_b = st.columns(2)
with col_a:
    current_date = datetime.now()
    month_options_en = [datetime(2025, m, 1).strftime("%B %Y") for m in range(1, 13)] + \
                       [datetime(2026, m, 1).strftime("%B %Y") for m in range(1, 13)]
    month_options_ar = [f"{MONTHS_AR[m.split()[0]]} {m.split()[1]}" for m in month_options_en]
    default_idx = month_options_en.index(current_date.strftime("%B %Y"))
    selected_month_ar = st.selectbox("📅 اختر الشهر المراد عرضه أو إدارته:", month_options_ar, index=default_idx)

with col_b:
    current_rent_row = st.session_state.rent_data[st.session_state.rent_data["الشهر"] == selected_month_ar]
    default_rent = float(current_rent_row["قيمة_الإيجار"].values[0]) if not current_rent_row.empty else 42.165
    new_rent = st.number_input(f"💰 إيجار شهر {selected_month_ar} (للفرد):", min_value=0.0, value=default_rent, format="%.3f")
    if st.button("حفظ قيمة الإيجار لهذا الشهر"):
        if not current_rent_row.empty:
            st.session_state.rent_data.loc[st.session_state.rent_data["الشهر"] == selected_month_ar, "قيمة_الإيجار"] = new_rent
        else:
            new_row = pd.DataFrame([{"الشهر": selected_month_ar, "قيمة_الإيجار": new_rent}])
            st.session_state.rent_data = pd.concat([st.session_state.rent_data, new_row], ignore_index=True)
        save_data(st.session_state.rent_data, RENT_FILE)
        st.success(f"✅ تم حفظ إيجار شهر {selected_month_ar}.")

st.divider()

# --- واجهة الإدخال والحسابات ---
month_df = st.session_state.all_data[st.session_state.all_data["الشهر"] == selected_month_ar]
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader(f"➕ إضافة مصاريف لـ {selected_month_ar}")
    name = st.selectbox("من الشخص الذي دفع؟", SHABAB)
    amount = st.number_input("المبلغ المدفوع:", min_value=0.0, step=0.1, format="%.3f")
    note = st.text_input("بيان المصروف:", placeholder="مثال: أنبوبة، منظفات")
    
    # خيارات الصورة
    img_option = st.radio("إضافة صورة الفاتورة:", ("بدون صورة", "رفع من الجهاز", "فتح الكاميرا"))
    uploaded_img = None
    if img_option == "رفع من الجهاز":
        uploaded_img = st.file_uploader("اختر صورة من الاستوديو", type=['png', 'jpg', 'jpeg'])
    elif img_option == "فتح الكاميرا":
        uploaded_img = st.camera_input("التقط صورة الفاتورة")

    if st.button("تسجيل المصروف"):
        if amount > 0:
            img_path = "None"
            if uploaded_img is not None:
                img_path = os.path.join(IMG_DIR, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
                img = Image.open(uploaded_img)
                img.save(img_path)
            
            new_entry = {
                "الشهر": selected_month_ar, "الاسم": name, "المبلغ": amount, 
                "البيان": note, "التاريخ": datetime.now().strftime("%Y-%m-%d"),
                "الصورة": img_path
            }
            st.session_state.all_data = pd.concat([st.session_state.all_data, pd.DataFrame([new_entry])], ignore_index=True)
            save_data(st.session_state.all_data, DB_FILE)
            st.rerun()

with col2:
    st.subheader(f"📊 تصفية حسابات {selected_month_ar}")
    total_extra = month_df["المبلغ"].sum()
    fair_extra = total_extra / len(SHABAB) if total_extra > 0 else 0
    paid_series = month_df.groupby("الاسم")["المبلغ"].sum().reindex(SHABAB, fill_value=0)
    
    summary_data = []
    for person in SHABAB:
        paid = paid_series[person]
        balance = paid - (fair_extra + new_rent)
        status = "🟢 له" if balance > 0 else "🔴 عليه" if balance < 0 else "⚪ مخلص"
        summary_data.append({"الاسم": person, "مدفوعات": f"{paid:.3f}", "الوضع": status, "المبلغ": f"{abs(balance):.3f}"})
    st.table(summary_data)

st.divider()

# --- سجل المصاريف ---
st.subheader(f"📜 سجل مصاريف {selected_month_ar}")
if not month_df.empty:
    # عرض السجل مع الصور
    for index, row in month_df.iterrows():
        with st.expander(f"📌 {row['الاسم']} - {row['المبلغ']} - {row['البيان']}"):
            col_info, col_img = st.columns([2, 1])
            with col_info:
                st.write(f"**التاريخ:** {row['التاريخ']}")
                st.write(f"**البيان:** {row['البيان']}")
            with col_img:
                if row['الصورة'] != "None" and os.path.exists(row['الصورة']):
                    st.image(row['الصورة'], width=150)
                else:
                    st.warning("لم تتم إضافة صورة")
    
    if st.button("🗑️ حذف آخر مصروف مسجل"):
        last_idx = month_df.index[-1]
        st.session_state.all_data = st.session_state.all_data.drop(last_idx)
        save_data(st.session_state.all_data, DB_FILE)
        st.rerun()

# --- تقرير الواتساب ---
st.divider()
st.subheader("📱 تقرير الواتساب")
report = f"*تقرير مصاريف السكن - {selected_month_ar}*\n"
report += f"🏠 الإيجار للفرد: {new_rent:.3f}\n"
report += f"💰 إجمالي المصاريف الأخرى: {total_extra:.3f}\n"
report += f"{'─'*15}\n"
for item in summary_data:
    report += f"• {item['الاسم']}: {item['الوضع']} *{item['المبلغ']}*\n"
st.code(report)
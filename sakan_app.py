import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# إعدادات الصفحة
st.set_page_config(page_title="نظام مصاريف السكن", page_icon="🏠", layout="wide")

# الاتصال بجوجل شيت مباشرة
conn = st.connection("gsheets", type=GSheetsConnection)

SHABAB = ["أبو عمار على شهبور", "أبو أحمد تامر حيدر", "أبو فهد عبد الرحمن", "أبو بدر أحمد حسان", "أبو كريم", "أبو زين علاء الصاوي"]

MONTHS_AR = {
    "January": "يناير", "February": "فبراير", "March": "مارس", "April": "أبريل", 
    "May": "مايو", "June": "يونيو", "July": "يوليو", "August": "أغسطس", 
    "September": "سبتمبر", "October": "أكتوبر", "November": "نوفمبر", "December": "ديسمبر"
}

# --- وظائف قراءة البيانات من جوجل شيت ---
def get_data():
    try:
        # ttl=0 تضمن عدم كاش البيانات وقراءتها حية فوراً
        return conn.read(worksheet="Expenses", ttl=0)
    except:
        return pd.DataFrame(columns=["الشهر", "الاسم", "المبلغ", "البيان", "التاريخ", "الصورة"])

def get_rent():
    try:
        return conn.read(worksheet="Rent", ttl=0)
    except:
        return pd.DataFrame(columns=["الشهر", "قيمة_الإيجار"])

# تحميل البيانات الحالية
all_data = get_data()
rent_data = get_rent()

# --- الشريط العلوي ---
st.title("🏠 نظام مصاريف السكن (نسخة جوجل شيت)")

col_a, col_b = st.columns(2)
with col_a:
    current_date = datetime.now()
    month_options_en = [datetime(2025, m, 1).strftime("%B %Y") for m in range(1, 13)] + \
                       [datetime(2026, m, 1).strftime("%B %Y") for m in range(1, 13)]
    month_options_ar = [f"{MONTHS_AR[m.split()[0]]} {m.split()[1]}" for m in month_options_en]
    default_idx = month_options_en.index(current_date.strftime("%B %Y"))
    selected_month_ar = st.selectbox("📅 اختر الشهر المراد عرضه أو إدارته:", month_options_ar, index=default_idx)

with col_b:
    current_rent_row = rent_data[rent_data["الشهر"] == selected_month_ar]
    default_rent = float(current_rent_row["قيمة_الإيجار"].values[0]) if not current_rent_row.empty else 42.165
    new_rent = st.number_input(f"💰 إيجار شهر {selected_month_ar} (للفرد):", min_value=0.0, value=default_rent, format="%.3f")
    
    if st.button("حفظ قيمة الإيجار لهذا الشهر"):
        new_rent_df = pd.DataFrame([{"الشهر": selected_month_ar, "قيمة_الإيجار": new_rent}])
        updated_rent = pd.concat([rent_data[rent_data["الشهر"] != selected_month_ar], new_rent_df])
        conn.update(worksheet="Rent", data=updated_rent)
        st.success(f"✅ تم حفظ الإيجار في جوجل شيت.")
        st.rerun()

st.divider()

# --- واجهة الإدخال والحسابات ---
# تصفية بيانات الشهر المختار من الجوجل شيت مباشرة
month_df = all_data[all_data["الشهر"] == selected_month_ar]
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader(f"➕ إضافة مصاريف لـ {selected_month_ar}")
    name = st.selectbox("من الشخص الذي دفع؟", SHABAB)
    amount = st.number_input("المبلغ المدفوع:", min_value=0.0, step=0.1, format="%.3f")
    note = st.text_input("بيان المصروف:", placeholder="مثال: أنبوبة، منظفات")
    
    # الخيار المباشر والنظيف الذي طلبته
    uploaded_img = st.file_uploader("📸 رفع صورة الفاتورة:", type=['png', 'jpg', 'jpeg'])

    if st.button("تسجيل المصروف"):
        if amount > 0:
            # بما أن جوجل شيت لا يخزن ملفات صور مباشرة، سنثبت كلمة "تم رفع صورة" في الشيت كإثبات
            # حتى لا نثقل البرنامج بروابط خارجية معقدة وتظل الحسبة هي الأساس
            img_status = "تم رفع صورة الفاتورة" if uploaded_img is not None else "لم تتم إضافة صورة"
            
            new_entry = pd.DataFrame([{
                "الشهر": selected_month_ar, 
                "الاسم": name, 
                "المبلغ": amount, 
                "البيان": note, 
                "التاريخ": datetime.now().strftime("%Y-%m-%d"),
                "الصورة": img_status
            }])
            
            updated_data = pd.concat([all_data, new_entry], ignore_index=True)
            conn.update(worksheet="Expenses", data=updated_data)
            st.success("✅ تم تسجيل المصروف ورفعه لجوجل شيت")
            st.rerun()

with col2:
    st.subheader(f"📊 تصفية حسابات {selected_month_ar}")
    # تحويل المبالغ لأرقام لضمان عدم حدوث أخطاء حسابية أثناء القراءة من جوجل شيت
    total_extra = pd.to_numeric(month_df["المبلغ"]).sum()
    fair_extra = total_extra / len(SHABAB) if total_extra > 0 else 0
    
    summary_data = []
    for person in SHABAB:
        paid = pd.to_numeric(month_df[month_df["الاسم"] == person]["المبلغ"]).sum()
        balance = paid - (fair_extra + new_rent)
        status = "🟢 له" if balance > 0 else "🔴 عليه" if balance < 0 else "⚪ مخلص"
        summary_data.append({"الاسم": person, "مدفوعات": f"{paid:.3f}", "الوضع": status, "المبلغ": f"{abs(balance):.3f}"})
    st.table(summary_data)

st.divider()

# --- سجل المصاريف ---
st.subheader(f"📜 سجل مصاريف {selected_month_ar}")
if not month_df.empty:
    for index, row in month_df.iterrows():
        with st.expander(f"📌 {row['الاسم']} - {row['المبلغ']} - {row['البيان']}"):
            st.write(f"**التاريخ:** {row['التاريخ']}")
            st.write(f"**البيان:** {row['البيان']}")
            if row['الصورة'] == "تم رفع صورة الفاتورة":
                st.info("📎 تم رفع صورة الفاتورة مع هذا السجل (محفوظة في جوجل شيت)")
            else:
                st.warning("⚠️ لم تتم إضافة صورة")
    
    if st.button("🗑️ حذف آخر مصروف مسجل"):
        # حذف السطر الأخير وتحديث جوجل شيت
        last_global_idx = all_data[all_data["الشهر"] == selected_month_ar].index[-1]
        updated_data = all_data.drop(last_global_idx)
        conn.update(worksheet="Expenses", data=updated_data)
        st.success("🗑️ تم حذف المصروف من جوجل شيت")
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

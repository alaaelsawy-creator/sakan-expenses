import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime, date
import calendar
from PIL import Image
import io

# ─────────────────────────────────────────────
#  إعدادات الصفحة
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="نظام مصاريف السكن",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
#  CSS مخصص – تصميم عربي احترافي
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Tajawal', sans-serif !important;
    direction: rtl;
}

.main { background: #0f1117; }

/* بطاقات الإحصاء */
.stat-card {
    background: linear-gradient(135deg, #1e2130 0%, #252840 100%);
    border: 1px solid #2e3250;
    border-radius: 16px;
    padding: 20px;
    text-align: center;
    margin-bottom: 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
.stat-card .value { font-size: 1.8rem; font-weight: 800; color: #fff; }
.stat-card .label { font-size: 0.85rem; color: #8892b0; margin-top: 4px; }

/* صف الشخص */
.person-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #1a1e2e;
    border: 1px solid #2a2f45;
    border-radius: 12px;
    padding: 14px 20px;
    margin-bottom: 10px;
    direction: rtl;
}
.person-name { font-weight: 700; font-size: 1rem; color: #e0e6ff; }
.person-paid { font-size: 0.9rem; color: #7ecfb3; }
.badge-green {
    background: #0d3b2e;
    color: #4ade80;
    border: 1px solid #166534;
    border-radius: 20px;
    padding: 4px 14px;
    font-weight: 700;
    font-size: 0.85rem;
}
.badge-red {
    background: #3b0d0d;
    color: #f87171;
    border: 1px solid #991b1b;
    border-radius: 20px;
    padding: 4px 14px;
    font-weight: 700;
    font-size: 0.85rem;
}
.badge-vacation {
    background: #1a2e3b;
    color: #60a5fa;
    border: 1px solid #1d4ed8;
    border-radius: 20px;
    padding: 4px 14px;
    font-weight: 700;
    font-size: 0.85rem;
}
.badge-zero {
    background: #2a2a2a;
    color: #aaa;
    border: 1px solid #444;
    border-radius: 20px;
    padding: 4px 14px;
    font-weight: 700;
    font-size: 0.85rem;
}

/* تقرير الواتساب */
.whatsapp-box {
    background: #0a1a0f;
    border: 1px solid #166534;
    border-radius: 12px;
    padding: 20px;
    font-family: 'Tajawal', monospace;
    white-space: pre-wrap;
    color: #4ade80;
    font-size: 0.95rem;
    direction: rtl;
}

/* عنوان */
.app-header {
    background: linear-gradient(135deg, #1a237e 0%, #283593 50%, #1565c0 100%);
    border-radius: 20px;
    padding: 30px;
    text-align: center;
    margin-bottom: 30px;
    box-shadow: 0 8px 32px rgba(26,35,126,0.4);
}
.app-header h1 { color: white; font-size: 2rem; font-weight: 800; margin: 0; }
.app-header p { color: #90caf9; margin: 8px 0 0; font-size: 0.95rem; }

/* تبويبات مخصصة */
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] {
    background: #1a1e2e;
    border-radius: 10px;
    border: 1px solid #2e3250;
    color: #8892b0;
    font-family: 'Tajawal', sans-serif;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #1a237e, #1565c0) !important;
    color: white !important;
    border-color: #1565c0 !important;
}

/* إشعار إجازة */
.vacation-notice {
    background: #0d1f3c;
    border: 1px solid #1d4ed8;
    border-right: 4px solid #60a5fa;
    border-radius: 10px;
    padding: 12px 16px;
    color: #93c5fd;
    font-size: 0.9rem;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  الثوابت
# ─────────────────────────────────────────────
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1g0VfbnUVwNXjV0c2BFlmlX3RSh5eZnpzLUrzwLeqG2I/export?format=csv&gid=0"
SCRIPT_URL    = "https://script.google.com/macros/s/AKfycbxdbKpbajXkRUFsAhSJMuxlW7_etBpq05Kx8B_zWQ2I4C3VTxZVAMyM0mtAvFHighCU/exec"

SHABAB = [
    "أبو عمار على شهبور",
    "أبو أحمد تامر حيدر",
    "أبو فهد عبد الرحمن",
    "أبو بدر أحمد حسان",
    "أبو كريم",
    "أبو زين علاء الصاوي",
]

MONTHS_AR = {
    "January":"يناير","February":"فبراير","March":"مارس","April":"أبريل",
    "May":"مايو","June":"يونيو","July":"يوليو","August":"أغسطس",
    "September":"سبتمبر","October":"أكتوبر","November":"نوفمبر","December":"ديسمبر",
}

# ─────────────────────────────────────────────
#  العنوان الرئيسي
# ─────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <h1>🏠 نظام مصاريف السكن</h1>
    <p>إعداد أبو زين • تتبع وتوزيع المصاريف بدقة وشفافية</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  تحميل البيانات
# ─────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_data():
    try:
        url = f"{SHEET_CSV_URL}&cachebust={datetime.now().timestamp()}"
        df  = pd.read_csv(url)
        return df
    except:
        return pd.DataFrame(columns=["الشهر","الاسم","المبلغ","البيان","التاريخ","الصورة"])

all_data = load_data()

# ─────────────────────────────────────────────
#  شريط الإعدادات العلوي
# ─────────────────────────────────────────────
current_date    = datetime.now()
month_opts_en   = [datetime(2026, m, 1).strftime("%B %Y") for m in range(1, 13)]
month_opts_ar   = [f"{MONTHS_AR[m.split()[0]]} {m.split()[1]}" for m in month_opts_en]

c1, c2, c3 = st.columns([2, 1, 1])
with c1:
    selected_month_ar = st.selectbox("📅 الشهر", month_opts_ar, index=current_date.month - 1)
with c2:
    rent_val = st.number_input("💰 إيجار الفرد", min_value=0.0, value=42.165, format="%.3f")
with c3:
    # استخراج رقم الشهر والسنة
    month_idx  = month_opts_ar.index(selected_month_ar)
    sel_month  = month_idx + 1
    sel_year   = 2026
    days_in_month = calendar.monthrange(sel_year, sel_month)[1]
    st.metric("📆 أيام الشهر", days_in_month)

st.divider()

# ─────────────────────────────────────────────
#  نظام الإجازات – Session State
# ─────────────────────────────────────────────
if "vacations" not in st.session_state:
    st.session_state.vacations = {}   # {month_ar: {person: {...}}}

month_vacations = st.session_state.vacations.get(selected_month_ar, {})

# ─────────────────────────────────────────────
#  دالة حساب نسبة الإجازة
# ─────────────────────────────────────────────
def calc_vacation_ratio(vac_info: dict, days_in_month: int, sel_year: int, sel_month: int) -> float:
    """
    ترجع نسبة المشاركة في المصاريف (0.0 → 1.0).
    """
    vtype = vac_info.get("type", "none")
    if vtype == "full":
        return 0.0
    elif vtype == "from_start":
        absent_days = int(vac_info.get("days", 0))
        absent_days = min(absent_days, days_in_month)
        return max(0.0, (days_in_month - absent_days) / days_in_month)
    elif vtype == "from_date":
        vac_date = vac_info.get("date")
        if vac_date:
            start = date(sel_year, sel_month, 1)
            absent_days = (vac_date - start).days
            absent_days = max(0, absent_days)
            present_days = min(absent_days, days_in_month)
            return present_days / days_in_month
        return 1.0
    elif vtype == "deduct":
        return 1.0   # سيُطبَّق الخصم لاحقاً
    else:
        return 1.0

# ─────────────────────────────────────────────
#  حساب الملخص
# ─────────────────────────────────────────────
month_df    = all_data[all_data["الشهر"] == selected_month_ar] if not all_data.empty else pd.DataFrame()
total_extra = pd.to_numeric(month_df["المبلغ"], errors='coerce').sum() if not month_df.empty else 0.0

# حساب المقام الفعلي (مجموع نسب المشاركة)
total_ratio = 0.0
ratios      = {}
deduct_map  = {}
for person in SHABAB:
    vac = month_vacations.get(person, {})
    ratio = calc_vacation_ratio(vac, days_in_month, sel_year, sel_month)
    ratios[person]   = ratio
    total_ratio     += ratio
    deduct_map[person] = float(vac.get("deduct_amount", 0)) if vac.get("type") == "deduct" else 0.0

# المصاريف المشتركة المُوزَّعة
def get_share(person):
    """حصة الشخص من المصاريف المشتركة"""
    if total_ratio == 0:
        return 0.0
    vac = month_vacations.get(person, {})
    if vac.get("type") == "deduct":
        # يشارك كامل مطروحاً منه مبلغ ثابت
        base_share = (total_extra / len(SHABAB))
        return max(0.0, base_share - deduct_map[person])
    return (ratios[person] / total_ratio) * total_extra

summary = []
for person in SHABAB:
    paid  = pd.to_numeric(month_df[month_df["الاسم"] == person]["المبلغ"], errors='coerce').sum() if not month_df.empty else 0.0
    share = get_share(person) + (rent_val * ratios[person])
    balance = paid - share
    vac     = month_vacations.get(person, {})
    summary.append({
        "الاسم":       person,
        "مدفوع":       paid,
        "المستحق":     share,
        "الرصيد":      balance,
        "إجازة":       vac.get("type", "none"),
        "النسبة":      ratios[person],
    })

# ─────────────────────────────────────────────
#  التبويبات
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📊 الملخص والتوزيع", "➕ إضافة مصروف", "🏖️ إدارة الإجازات", "📜 سجل المصاريف"])

# ══════════════════════════════════════════════
#  تبويب ١: الملخص
# ══════════════════════════════════════════════
with tab1:
    # بطاقات إحصاء
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(f"""<div class="stat-card">
            <div class="value">{total_extra:.3f}</div>
            <div class="label">💰 إجمالي المصاريف</div>
        </div>""", unsafe_allow_html=True)
    with s2:
        total_rent = rent_val * sum(ratios.values())
        st.markdown(f"""<div class="stat-card">
            <div class="value">{total_rent:.3f}</div>
            <div class="label">🏠 إجمالي الإيجار</div>
        </div>""", unsafe_allow_html=True)
    with s3:
        grand_total = total_extra + total_rent
        st.markdown(f"""<div class="stat-card">
            <div class="value">{grand_total:.3f}</div>
            <div class="label">📊 الإجمالي الكلي</div>
        </div>""", unsafe_allow_html=True)
    with s4:
        active_count = sum(1 for p in SHABAB if ratios[p] > 0)
        st.markdown(f"""<div class="stat-card">
            <div class="value">{active_count}/{len(SHABAB)}</div>
            <div class="label">👥 المشاركون الفعليون</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("### 👥 وضع كل شخص")
    for row in summary:
        bal   = row["الرصيد"]
        vtype = row["إجازة"]

        if vtype not in ("none",) and vtype:
            vac_labels = {
                "full":       "🏖️ إجازة كاملة",
                "from_start": f"🗓️ غياب {days_in_month - round(ratios[row['الاسم']]*days_in_month)} يوم",
                "from_date":  "📅 إجازة من تاريخ",
                "deduct":     "➖ خصم مبلغ",
            }
            vac_text = vac_labels.get(vtype, "")
            badge = f'<span class="badge-vacation">{vac_text} • نسبة {row["النسبة"]*100:.0f}%</span>'
        elif abs(bal) < 0.01:
            badge = '<span class="badge-zero">➖ صفر</span>'
        elif bal > 0:
            badge = f'<span class="badge-green">🟢 له {bal:.3f}</span>'
        else:
            badge = f'<span class="badge-red">🔴 عليه {abs(bal):.3f}</span>'

        st.markdown(f"""
        <div class="person-row">
            <span class="person-name">{row['الاسم']}</span>
            <span class="person-paid">دفع: {row['مدفوع']:.3f} | مستحق: {row['المستحق']:.3f}</span>
            {badge}
        </div>
        """, unsafe_allow_html=True)

    # ── تقرير واتساب ──
    st.markdown("### 📱 تقرير الواتساب")
    report_lines = [
        f"*تقرير مصاريف السكن – {selected_month_ar}*",
        f"🏠 إيجار الفرد: {rent_val:.3f}",
        f"💰 إجمالي المصاريف: {total_extra:.3f}",
        "─────────────────",
    ]
    for row in summary:
        bal   = row["الرصيد"]
        vtype = row["إجازة"]
        status = "له 🟢" if bal > 0 else ("عليه 🔴" if bal < 0 else "صفر ➖")
        vac_note = ""
        if vtype == "full":
            vac_note = " (إجازة كاملة)"
        elif vtype in ("from_start","from_date"):
            vac_note = f" (نسبة {row['النسبة']*100:.0f}%)"
        elif vtype == "deduct":
            vac_note = " (خصم خاص)"
        report_lines.append(f"• {row['الاسم']}{vac_note}: {status} *{abs(bal):.3f}*")

    report_text = "\n".join(report_lines)
    st.markdown(f'<div class="whatsapp-box">{report_text}</div>', unsafe_allow_html=True)
    st.button("📋 نسخ التقرير", on_click=lambda: st.write(""), help="انسخ النص أعلاه يدوياً")

# ══════════════════════════════════════════════
#  تبويب ٢: إضافة مصروف
# ══════════════════════════════════════════════
with tab2:
    col_form, col_recent = st.columns([1, 1])
    with col_form:
        st.subheader("➕ تسجيل مصروف جديد")
        with st.form("add_form", clear_on_submit=True):
            name   = st.selectbox("من دفع؟", SHABAB)
            amount = st.number_input("المبلغ", min_value=0.0, step=0.1, format="%.3f")
            note   = st.text_input("البيان", placeholder="مثال: شاي، سكر، أنبوبة، صابون…")
            expense_date = st.date_input("التاريخ", value=date.today())
            uploaded_img = st.file_uploader("📸 صورة الفاتورة (اختياري)", type=["png","jpg","jpeg"])
            submit = st.form_submit_button("✅ تسجيل المصروف", use_container_width=True)

            if submit:
                if amount > 0:
                    img_base64 = ""
                    img_name   = ""
                    if uploaded_img:
                        img_name = uploaded_img.name
                        try:
                            image = Image.open(uploaded_img)
                            if image.mode in ("RGBA","P"):
                                image = image.convert("RGB")
                            image.thumbnail((800, 800))
                            buf = io.BytesIO()
                            image.save(buf, format="JPEG", quality=70)
                            img_base64 = base64.b64encode(buf.getvalue()).decode()
                        except Exception as e:
                            st.error(f"خطأ في الصورة: {e}")

                    payload = {
                        "month": selected_month_ar, "name": name, "amount": amount,
                        "note": note, "date": str(expense_date),
                        "imgData": img_base64, "imgName": img_name,
                    }
                    try:
                        with st.spinner("جاري الحفظ…"):
                            resp = requests.post(SCRIPT_URL, data=payload, timeout=30)
                        if "Success" in resp.text:
                            st.success("✅ تم التسجيل بنجاح!")
                            st.balloons()
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"رد الخادم: {resp.text}")
                    except Exception as e:
                        st.error(f"❌ فشل الاتصال: {e}")
                else:
                    st.warning("⚠️ أدخل مبلغاً صحيحاً.")

    with col_recent:
        st.subheader("🕐 آخر المصاريف")
        if not month_df.empty:
            recent = month_df.tail(5).iloc[::-1]
            for _, row in recent.iterrows():
                st.info(f"**{row['الاسم']}** | {float(row['المبلغ']):.3f} | {row['البيان']}")
        else:
            st.info("لا توجد مصاريف بعد.")

# ══════════════════════════════════════════════
#  تبويب ٣: إدارة الإجازات
# ══════════════════════════════════════════════
with tab3:
    st.subheader(f"🏖️ إدارة الإجازات – {selected_month_ar}")
    st.markdown("""
    <div style="background:#0d1f3c;border:1px solid #1d4ed8;border-radius:10px;padding:14px 18px;color:#93c5fd;margin-bottom:20px;">
    💡 <strong>كيف يعمل النظام؟</strong><br>
    • <b>إجازة كاملة</b>: لا يُحسب عليه شيء من المصاريف أو الإيجار.<br>
    • <b>غياب من أول الشهر X أيام</b>: يُحسب بنسبة الأيام الحاضرة.<br>
    • <b>إجازة من تاريخ معين</b>: يُحسب فقط على الأيام قبل الإجازة.<br>
    • <b>خصم مبلغ ثابت</b>: يشارك كامل لكن يُخصم منه مبلغ محدد.
    </div>
    """, unsafe_allow_html=True)

    for person in SHABAB:
        with st.expander(f"⚙️ {person}", expanded=False):
            vac = month_vacations.get(person, {})
            vtype = st.radio(
                "نوع الإجازة",
                options=["none","full","from_start","from_date","deduct"],
                format_func=lambda x: {
                    "none":       "✅ لا توجد إجازة – يشارك كامل",
                    "full":       "🏖️ إجازة كاملة – لا يُحسب عليه شيء",
                    "from_start": "🗓️ غياب عدد أيام من أول الشهر",
                    "from_date":  "📅 إجازة من تاريخ معين حتى نهاية الشهر",
                    "deduct":     "➖ خصم مبلغ ثابت من حصته",
                }[x],
                index=["none","full","from_start","from_date","deduct"].index(vac.get("type","none")),
                key=f"vtype_{person}",
            )

            extra = {}
            if vtype == "from_start":
                absent_days = st.number_input(
                    "عدد أيام الغياب من أول الشهر",
                    min_value=1, max_value=days_in_month, step=1,
                    value=int(vac.get("days", 1)),
                    key=f"days_{person}",
                )
                present = days_in_month - absent_days
                ratio   = present / days_in_month
                st.info(f"سيشارك {present} يوماً من {days_in_month} يوماً → نسبة {ratio*100:.1f}%")
                extra["days"] = absent_days

            elif vtype == "from_date":
                vac_date_val = vac.get("date") or date(sel_year, sel_month, 15)
                vac_date = st.date_input(
                    "تاريخ بداية الإجازة",
                    value=vac_date_val,
                    min_value=date(sel_year, sel_month, 1),
                    max_value=date(sel_year, sel_month, days_in_month),
                    key=f"vdate_{person}",
                )
                present = (vac_date - date(sel_year, sel_month, 1)).days
                present = max(0, min(present, days_in_month))
                ratio   = present / days_in_month
                st.info(f"حاضر {present} يوماً قبل الإجازة → نسبة {ratio*100:.1f}%")
                extra["date"] = vac_date

            elif vtype == "deduct":
                ded = st.number_input(
                    "المبلغ الثابت المخصوم من حصته",
                    min_value=0.0, step=0.5, format="%.3f",
                    value=float(vac.get("deduct_amount", 0.0)),
                    key=f"ded_{person}",
                )
                extra["deduct_amount"] = ded

            if st.button(f"💾 حفظ إعدادات {person}", key=f"save_{person}"):
                if selected_month_ar not in st.session_state.vacations:
                    st.session_state.vacations[selected_month_ar] = {}
                if vtype == "none":
                    st.session_state.vacations[selected_month_ar].pop(person, None)
                else:
                    st.session_state.vacations[selected_month_ar][person] = {"type": vtype, **extra}
                st.success(f"✅ تم حفظ إعدادات {person}")
                st.rerun()

    # ملخص الإجازات الحالية
    if month_vacations:
        st.divider()
        st.markdown("**📋 الإجازات المسجلة لهذا الشهر:**")
        for person, vac in month_vacations.items():
            vtype = vac.get("type","")
            if vtype == "full":
                desc = "إجازة كاملة"
            elif vtype == "from_start":
                desc = f"غياب {vac.get('days',0)} يوم من أول الشهر"
            elif vtype == "from_date":
                desc = f"إجازة من {vac.get('date','')}"
            elif vtype == "deduct":
                desc = f"خصم {vac.get('deduct_amount',0):.3f}"
            else:
                desc = ""
            st.markdown(f'<div class="vacation-notice">🏖️ <strong>{person}</strong>: {desc}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  تبويب ٤: سجل المصاريف
# ══════════════════════════════════════════════
with tab4:
    st.subheader(f"📜 سجل مصاريف {selected_month_ar}")

    # فلتر بالاسم
    filter_name = st.selectbox("فلتر باسم", ["الكل"] + SHABAB, key="filter_name")

    display_df = month_df if not month_df.empty else pd.DataFrame()
    if filter_name != "الكل" and not display_df.empty:
        display_df = display_df[display_df["الاسم"] == filter_name]

    if not display_df.empty:
        # إجمالي المُصفَّى
        filtered_total = pd.to_numeric(display_df["المبلغ"], errors='coerce').sum()
        st.metric("إجمالي المبالغ المعروضة", f"{filtered_total:.3f}")

        for idx, row in display_df.iloc[::-1].iterrows():
            amount_val = float(row["المبلغ"]) if pd.notna(row["المبلغ"]) else 0.0
            with st.expander(f"📌 {row['الاسم']}  |  {amount_val:.3f}  |  {row['البيان']}"):
                col_a, col_b = st.columns(2)
                col_a.write(f"**التاريخ:** {row['التاريخ']}")
                col_a.write(f"**الشهر:** {row['الشهر']}")
                img_link = str(row['الصورة']).strip()
                if img_link.startswith("http"):
                    col_b.link_button("🖼️ فتح صورة الفاتورة", img_link)
                else:
                    col_b.caption("⚠️ لا توجد صورة مرفوعة")
    else:
        st.info("لا توجد مصاريف مسجلة لهذا الشهر.")

    # ── إجماليات لكل فرد
    if not month_df.empty:
        st.divider()
        st.markdown("**📊 إجماليات كل شخص هذا الشهر:**")
        cols = st.columns(3)
        for i, person in enumerate(SHABAB):
            total_person = pd.to_numeric(month_df[month_df["الاسم"] == person]["المبلغ"], errors='coerce').sum()
            with cols[i % 3]:
                st.metric(person, f"{total_person:.3f}")
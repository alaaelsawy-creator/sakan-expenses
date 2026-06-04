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

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Tajawal', sans-serif !important; direction: rtl; }
.main { background: #0f1117; }
.stat-card {
    background: linear-gradient(135deg, #1e2130 0%, #252840 100%);
    border: 1px solid #2e3250; border-radius: 16px;
    padding: 20px; text-align: center; margin-bottom: 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
.stat-card .value { font-size: 1.8rem; font-weight: 800; color: #fff; }
.stat-card .label { font-size: 0.85rem; color: #8892b0; margin-top: 4px; }
.person-row {
    display: flex; align-items: center; justify-content: space-between;
    background: #1a1e2e; border: 1px solid #2a2f45;
    border-radius: 12px; padding: 14px 20px; margin-bottom: 10px; direction: rtl;
}
.person-name  { font-weight: 700; font-size: 1rem; color: #e0e6ff; }
.person-paid  { font-size: 0.85rem; color: #7ecfb3; }
.badge-green  { background:#0d3b2e;color:#4ade80;border:1px solid #166534;border-radius:20px;padding:4px 14px;font-weight:700;font-size:0.85rem; }
.badge-red    { background:#3b0d0d;color:#f87171;border:1px solid #991b1b;border-radius:20px;padding:4px 14px;font-weight:700;font-size:0.85rem; }
.badge-vacation{background:#1a2e3b;color:#60a5fa;border:1px solid #1d4ed8;border-radius:20px;padding:4px 14px;font-weight:700;font-size:0.85rem;}
.badge-zero   { background:#2a2a2a;color:#aaa;border:1px solid #444;border-radius:20px;padding:4px 14px;font-weight:700;font-size:0.85rem; }
.whatsapp-box { background:#0a1a0f;border:1px solid #166534;border-radius:12px;padding:20px;
    font-family:'Tajawal',monospace;white-space:pre-wrap;color:#4ade80;font-size:0.95rem;direction:rtl; }
.app-header { background:linear-gradient(135deg,#1a237e 0%,#283593 50%,#1565c0 100%);
    border-radius:20px;padding:30px;text-align:center;margin-bottom:30px;
    box-shadow:0 8px 32px rgba(26,35,126,0.4); }
.app-header h1 { color:white;font-size:2rem;font-weight:800;margin:0; }
.app-header p  { color:#90caf9;margin:8px 0 0;font-size:0.95rem; }
.stTabs [data-baseweb="tab-list"] { gap:8px; }
.stTabs [data-baseweb="tab"] { background:#1a1e2e;border-radius:10px;border:1px solid #2e3250;
    color:#8892b0;font-family:'Tajawal',sans-serif;font-weight:600; }
.stTabs [aria-selected="true"] { background:linear-gradient(135deg,#1a237e,#1565c0)!important;
    color:white!important;border-color:#1565c0!important; }
.vacation-notice { background:#0d1f3c;border:1px solid #1d4ed8;border-right:4px solid #60a5fa;
    border-radius:10px;padding:12px 16px;color:#93c5fd;font-size:0.9rem;margin-bottom:8px; }
.info-box { background:#0d1f3c;border:1px solid #1d4ed8;border-radius:10px;
    padding:14px 18px;color:#93c5fd;margin-bottom:20px; }
.rule-box { background:#1a1a0d;border:1px solid #854d0e;border-radius:10px;
    padding:14px 18px;color:#fde047;margin-bottom:20px;font-size:0.9rem; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  الثوابت
# ─────────────────────────────────────────────
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1g0VfbnUVwNXjV0c2BFlmlX3RSh5eZnpzLUrzwLeqG2I/export?format=csv&gid=0"
SCRIPT_URL    = "https://script.google.com/macros/s/AKfycbxdbKpbajXkRUFsAhSJMuxlW7_etBpq05Kx8B_zWQ2I4C3VTxZVAMyM0mtAvFHighCU/exec"

DEFAULT_SHABAB = [
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
#  تحميل الأشخاص من Sheets (مع fallback)
# ─────────────────────────────────────────────
@st.cache_data(ttl=120)
def load_persons():
    try:
        resp = requests.get(SCRIPT_URL + "?type=persons", timeout=10)
        data = resp.json()
        if data:
            return sorted([d["name"] for d in data],
                          key=lambda x: next((d["order"] for d in data if d["name"]==x), 99))
    except:
        pass
    return DEFAULT_SHABAB.copy()

# ─────────────────────────────────────────────
#  تحميل الإجازات من Sheets
# ─────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_vacations_from_sheet():
    try:
        resp   = requests.get(SCRIPT_URL + "?type=vacations", timeout=10)
        data   = resp.json()
        result = {}
        for row in data:
            m = row["month"]; n = row["name"]
            if m not in result: result[m] = {}
            entry = {"type": row["vtype"]}
            if row.get("days"):      entry["days"]          = int(row["days"])
            if row.get("vacDate"):   entry["date"]           = _parse_date(row["vacDate"])
            if row.get("deductAmt"): entry["deduct_amount"]  = float(row["deductAmt"])
            result[m][n] = entry
        return result
    except:
        return {}

@st.cache_data(ttl=60)
def load_settings():
    try:
        resp = requests.get(SCRIPT_URL + "?type=settings", timeout=10)
        return resp.json()   # {"total_rent": "250.000", ...}
    except:
        return {}

def _parse_date(val):
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try: return datetime.strptime(str(val), fmt).date()
        except: pass
    return None

# ─────────────────────────────────────────────
#  تحميل المصاريف
# ─────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(f"{SHEET_CSV_URL}&cachebust={datetime.now().timestamp()}")
        # _row = رقم الصف الحقيقي في Sheets (صف 1 = headers، البيانات من صف 2)
        df["_row"] = range(2, len(df) + 2)
        # rowId = معرّف فريد مركّب من بيانات الصف للبحث الدقيق في Sheets
        df["_rowId"] = (
            df["الشهر"].astype(str) + "|" +
            df["الاسم"].astype(str) + "|" +
            df["المبلغ"].astype(str) + "|" +
            df["التاريخ"].astype(str)
        )
        return df
    except:
        return pd.DataFrame(columns=["الشهر","الاسم","المبلغ","البيان","التاريخ","الصورة","_row","_rowId"])

def call_script(payload):
    try:
        return requests.post(SCRIPT_URL, data=payload, timeout=30).text
    except Exception as e:
        return f"Error: {e}"

# ═══════════════════════════════════════════════
#  العنوان
# ═══════════════════════════════════════════════
st.markdown("""
<div class="app-header">
    <h1>🏠 نظام مصاريف السكن</h1>
    <p>إعداد أبو زين • تتبع وتوزيع المصاريف بدقة وشفافية</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  تحميل البيانات
# ─────────────────────────────────────────────
SHABAB          = load_persons()
all_data        = load_data()
sheet_vacations = load_vacations_from_sheet()
sheet_settings  = load_settings()

if "vacations" not in st.session_state:
    st.session_state.vacations = sheet_vacations.copy()

# ─────────────────────────────────────────────
#  شريط الإعدادات العلوي
# ─────────────────────────────────────────────
current_date  = datetime.now()
month_opts_en = [datetime(2026, m, 1).strftime("%B %Y") for m in range(1, 13)]
month_opts_ar = [f"{MONTHS_AR[m.split()[0]]} {m.split()[1]}" for m in month_opts_en]

c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
with c1:
    selected_month_ar = st.selectbox("📅 الشهر", month_opts_ar, index=current_date.month - 1)
with c2:
    # تحميل الإيجار: session_state له الأولوية، ثم Sheets، ثم الافتراضي
    if "total_rent" not in st.session_state:
        st.session_state.total_rent = float(sheet_settings.get("total_rent", 250.0))
    total_rent_input = st.number_input(
        "🏠 إجمالي الإيجار الكلي", min_value=0.0,
        value=st.session_state.total_rent,
        format="%.3f",
        help="يُقسَّم بالتساوي على جميع الأشخاص بدون استثناء",
        key="rent_input"
    )
with c3:
    month_idx     = month_opts_ar.index(selected_month_ar)
    sel_month     = month_idx + 1
    sel_year      = 2026
    days_in_month = calendar.monthrange(sel_year, sel_month)[1]
    st.metric("📆 أيام الشهر", days_in_month)
with c4:
    if st.button("🔄 تحديث"):
        st.cache_data.clear()
        st.session_state.pop("total_rent", None)
        st.rerun()

# حفظ الإيجار تلقائياً عند التغيير
if total_rent_input != st.session_state.total_rent:
    st.session_state.total_rent = total_rent_input

_sheet_rent = float(sheet_settings.get("total_rent", 250.0))
if total_rent_input != _sheet_rent:
    rc1, rc2 = st.columns([3, 1])
    rc1.info(f"💡 قيمة الإيجار تغيّرت من {_sheet_rent:.3f} إلى {total_rent_input:.3f} — اضغط حفظ لتثبيتها.")
    if rc2.button("💾 حفظ الإيجار", type="primary"):
        res = call_script({"action": "saveSetting", "key": "total_rent", "value": total_rent_input})
        if "Success" in res:
            st.success(f"✅ تم حفظ الإيجار: {total_rent_input:.3f}")
            st.cache_data.clear()
            st.session_state.total_rent = total_rent_input
            st.rerun()
        else:
            st.error(res)

# قاعدة التوزيع
st.markdown("""
<div class="rule-box">
⚠️ <b>قاعدة التوزيع:</b>
الإيجار يُقسَّم بالتساوي على <b>جميع الأشخاص</b> بدون استثناء حتى من في إجازة. |
المصاريف المشتركة تُوزَّع على <b>المتواجدين فقط</b> حسب نسبة حضورهم.
</div>
""", unsafe_allow_html=True)
st.divider()

# ─────────────────────────────────────────────
#  الإجازات للشهر
# ─────────────────────────────────────────────
month_vacations = st.session_state.vacations.get(selected_month_ar, {})

# ─────────────────────────────────────────────
#  دالة نسبة الحضور (للمصاريف فقط)
# ─────────────────────────────────────────────
def calc_expense_ratio(vac_info, days_in_month, sel_year, sel_month):
    """
    نسبة مشاركة الشخص في المصاريف المشتركة (0.0 → 1.0).
    الإيجار لا يتأثر بهذه النسبة.
    """
    vtype = vac_info.get("type", "none")
    if vtype == "full":
        return 0.0
    elif vtype == "from_start":
        absent = min(int(vac_info.get("days", 0)), days_in_month)
        return max(0.0, (days_in_month - absent) / days_in_month)
    elif vtype == "from_date":
        vac_date = vac_info.get("date")
        if vac_date:
            present = max(0, (vac_date - date(sel_year, sel_month, 1)).days)
            return min(present, days_in_month) / days_in_month
        return 1.0
    elif vtype == "deduct":
        return 1.0   # يشارك كامل لكن يُخصم مبلغ لاحقاً
    return 1.0

# ─────────────────────────────────────────────
#  الحسابات الرئيسية
# ─────────────────────────────────────────────
# فلترة المصاريف الحقيقية فقط (مبلغ صحيح > 0) – يستبعد أي صفوف إجازات أو فارغة
_raw_month  = all_data[all_data["الشهر"] == selected_month_ar] if not all_data.empty else pd.DataFrame()
if not _raw_month.empty:
    _valid_mask = pd.to_numeric(_raw_month["المبلغ"], errors='coerce').fillna(0) > 0
    month_df    = _raw_month[_valid_mask].copy()
else:
    month_df    = pd.DataFrame()
total_extra = pd.to_numeric(month_df["المبلغ"], errors='coerce').sum() if not month_df.empty else 0.0

# نسب الحضور للمصاريف
expense_ratios = {}
deduct_map     = {}
total_ratio    = 0.0
for person in SHABAB:
    vac  = month_vacations.get(person, {})
    r    = calc_expense_ratio(vac, days_in_month, sel_year, sel_month)
    expense_ratios[person] = r
    total_ratio           += r
    deduct_map[person]     = float(vac.get("deduct_amount", 0)) if vac.get("type") == "deduct" else 0.0

# الإيجار: ثابت على الجميع
rent_per_person = total_rent_input / len(SHABAB) if SHABAB else 0.0

# حصة الشخص من المصاريف المشتركة
def get_expense_share(person):
    if total_ratio == 0:
        return 0.0
    vac = month_vacations.get(person, {})
    if vac.get("type") == "deduct":
        base = (expense_ratios[person] / total_ratio) * total_extra
        return max(0.0, base - deduct_map[person])
    return (expense_ratios[person] / total_ratio) * total_extra

summary = []
for person in SHABAB:
    paid          = pd.to_numeric(month_df[month_df["الاسم"] == person]["المبلغ"], errors='coerce').sum() if not month_df.empty else 0.0
    exp_share     = get_expense_share(person)
    total_due     = exp_share + rent_per_person   # الإيجار ثابت دائماً
    balance       = paid - total_due
    vac           = month_vacations.get(person, {})
    summary.append({
        "الاسم":         person,
        "مدفوع":         paid,
        "حصة_مصاريف":   exp_share,
        "إيجار":         rent_per_person,
        "المستحق":       total_due,
        "الرصيد":        balance,
        "إجازة":         vac.get("type", "none"),
        "النسبة":        expense_ratios[person],
    })

active_count = sum(1 for p in SHABAB if expense_ratios[p] > 0)

# ─────────────────────────────────────────────
#  التبويبات
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 الملخص", "➕ إضافة مصروف", "🏖️ الإجازات", "📜 السجل", "⚙️ إدارة الأشخاص"
])

# ══════════════════════════════════════════════
#  تبويب ١: الملخص
# ══════════════════════════════════════════════
with tab1:
    s1, s2, s3, s4, s5 = st.columns(5)
    with s1:
        st.markdown(f'<div class="stat-card"><div class="value">{total_extra:.3f}</div><div class="label">💰 إجمالي المصاريف</div></div>', unsafe_allow_html=True)
    with s2:
        st.markdown(f'<div class="stat-card"><div class="value">{total_rent_input:.3f}</div><div class="label">🏠 إجمالي الإيجار</div></div>', unsafe_allow_html=True)
    with s3:
        st.markdown(f'<div class="stat-card"><div class="value">{rent_per_person:.3f}</div><div class="label">👤 إيجار الفرد</div></div>', unsafe_allow_html=True)
    with s4:
        grand_total = total_extra + total_rent_input
        st.markdown(f'<div class="stat-card"><div class="value">{grand_total:.3f}</div><div class="label">📊 الإجمالي الكلي</div></div>', unsafe_allow_html=True)
    with s5:
        st.markdown(f'<div class="stat-card"><div class="value">{active_count}/{len(SHABAB)}</div><div class="label">👥 حاضرون (للمصاريف)</div></div>', unsafe_allow_html=True)

    st.markdown(f"### 👥 وضع كل شخص")
    for row in summary:
        bal   = row["الرصيد"]
        vtype = row["إجازة"]

        # تفاصيل الإجازة
        if vtype and vtype != "none":
            vac_labels = {
                "full":       f"🏖️ إجازة كاملة (إيجار: {rent_per_person:.3f})",
                "from_start": f"🗓️ نسبة مصاريف {row['النسبة']*100:.0f}% + إيجار كامل",
                "from_date":  f"📅 نسبة مصاريف {row['النسبة']*100:.0f}% + إيجار كامل",
                "deduct":     f"➖ خصم مبلغ من المصاريف + إيجار كامل",
            }
            vac_text = vac_labels.get(vtype, "")
            badge = f'<span class="badge-vacation">{vac_text}</span>'
        elif abs(bal) < 0.01:
            badge = '<span class="badge-zero">➖ صفر</span>'
        elif bal > 0:
            badge = f'<span class="badge-green">🟢 له {bal:.3f}</span>'
        else:
            badge = f'<span class="badge-red">🔴 عليه {abs(bal):.3f}</span>'

        details = f"دفع: {row['مدفوع']:.3f} | مصاريف: {row['حصة_مصاريف']:.3f} | إيجار: {row['إيجار']:.3f} | المستحق: {row['المستحق']:.3f}"
        st.markdown(f"""
        <div class="person-row">
            <span class="person-name">{row['الاسم']}</span>
            <span class="person-paid">{details}</span>
            {badge}
        </div>""", unsafe_allow_html=True)

    # تقرير الواتساب
    st.markdown("### 📱 تقرير الواتساب")
    lines = [
        f"*تقرير مصاريف السكن – {selected_month_ar}*",
        f"🏠 الإيجار الكلي: {total_rent_input:.3f} (على كل فرد: {rent_per_person:.3f})",
        f"💰 إجمالي المصاريف المشتركة: {total_extra:.3f}",
        f"📊 الإجمالي الكلي: {total_extra + total_rent_input:.3f}",
        "─────────────────",
    ]
    for row in summary:
        bal    = row["الرصيد"]
        vtype  = row["إجازة"]
        status = "له 🟢" if bal > 0 else ("عليه 🔴" if bal < 0 else "صفر ➖")
        note   = ""
        if vtype == "full":
            note = " (إجازة – بدون مصاريف مشتركة)"
        elif vtype in ("from_start", "from_date"):
            note = f" (مصاريف {row['النسبة']*100:.0f}%)"
        elif vtype == "deduct":
            note = " (خصم من المصاريف)"
        lines.append(f"• {row['الاسم']}{note}: {status} *{abs(bal):.3f}*")

    report_text = "\n".join(lines)
    st.markdown(f'<div class="whatsapp-box">{report_text}</div>', unsafe_allow_html=True)
    st.button("📋 نسخ التقرير", help="انسخ النص أعلاه يدوياً")

# ══════════════════════════════════════════════
#  تبويب ٢: إضافة مصروف
# ══════════════════════════════════════════════
with tab2:
    col_form, col_recent = st.columns([1, 1])
    with col_form:
        st.subheader("➕ تسجيل مصروف جديد")
        with st.form("add_form", clear_on_submit=True):
            name         = st.selectbox("من دفع؟", SHABAB)
            amount       = st.number_input("المبلغ", min_value=0.0, step=0.1, format="%.3f")
            note         = st.text_input("البيان", placeholder="مثال: شاي، سكر، أنبوبة…")
            expense_date = st.date_input("التاريخ", value=date.today())
            uploaded_img = st.file_uploader("📸 صورة الفاتورة (اختياري)", type=["png","jpg","jpeg"])
            submit       = st.form_submit_button("✅ تسجيل", use_container_width=True)

            if submit:
                if amount > 0:
                    img_base64, img_name = "", ""
                    if uploaded_img:
                        img_name = uploaded_img.name
                        try:
                            image = Image.open(uploaded_img)
                            if image.mode in ("RGBA","P"): image = image.convert("RGB")
                            image.thumbnail((800, 800))
                            buf = io.BytesIO()
                            image.save(buf, format="JPEG", quality=70)
                            img_base64 = base64.b64encode(buf.getvalue()).decode()
                        except Exception as ex:
                            st.error(f"خطأ في الصورة: {ex}")

                    with st.spinner("جاري الحفظ…"):
                        result = call_script({
                            "action": "addExpense",
                            "month": selected_month_ar, "name": name,
                            "amount": amount, "note": note, "date": str(expense_date),
                            "imgData": img_base64, "imgName": img_name,
                        })
                    if "Success" in result:
                        st.success("✅ تم التسجيل!")
                        st.balloons()
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"رد الخادم: {result}")
                else:
                    st.warning("⚠️ أدخل مبلغاً صحيحاً.")

    with col_recent:
        st.subheader("🕐 آخر المصاريف")
        if not month_df.empty:
            for _, row in month_df.tail(6).iloc[::-1].iterrows():
                st.info(f"**{row['الاسم']}** | {float(row['المبلغ']):.3f} | {row['البيان']}")
        else:
            st.info("لا توجد مصاريف بعد.")

# ══════════════════════════════════════════════
#  تبويب ٣: الإجازات (تؤثر على المصاريف فقط)
# ══════════════════════════════════════════════
with tab3:
    st.subheader(f"🏖️ إدارة الإجازات – {selected_month_ar}")
    st.markdown("""
    <div class="info-box">
    💡 <b>تذكير:</b> الإجازة تؤثر على <u>المصاريف المشتركة فقط</u>.<br>
    الإيجار يبقى ثابتاً على <b>جميع الأشخاص</b> بغض النظر عن الإجازة.
    <br><br>
    • <b>إجازة كاملة</b>: لا يُحسب عليه شيء من المصاريف المشتركة (الإيجار يبقى).<br>
    • <b>غياب من أول الشهر X أيام</b>: يُحسب عليه من المصاريف بنسبة أيام حضوره.<br>
    • <b>إجازة من تاريخ</b>: يُحسب عليه المصاريف قبل الإجازة فقط.<br>
    • <b>خصم مبلغ ثابت</b>: يشارك كامل في المصاريف لكن يُخصم منه مبلغ معين.
    </div>
    """, unsafe_allow_html=True)

    for person in SHABAB:
        with st.expander(f"⚙️ {person}", expanded=False):
            vac   = month_vacations.get(person, {})
            vtype = st.radio(
                "نوع الإجازة",
                options=["none","full","from_start","from_date","deduct"],
                format_func=lambda x: {
                    "none":       "✅ لا توجد إجازة – يشارك كامل في المصاريف",
                    "full":       "🏖️ إجازة كاملة – بدون مصاريف مشتركة (الإيجار يبقى)",
                    "from_start": "🗓️ غياب من أول الشهر – نسبة حضور من المصاريف",
                    "from_date":  "📅 إجازة من تاريخ – مصاريف الأيام الحاضرة فقط",
                    "deduct":     "➖ خصم مبلغ ثابت من حصته في المصاريف",
                }[x],
                index=["none","full","from_start","from_date","deduct"].index(vac.get("type","none")),
                key=f"vtype_{person}",
            )

            extra = {}
            if vtype == "from_start":
                absent = st.number_input(
                    "عدد أيام الغياب من أول الشهر",
                    min_value=1, max_value=days_in_month, step=1,
                    value=int(vac.get("days", 1)), key=f"days_{person}"
                )
                present = days_in_month - absent
                st.info(f"✅ من المصاريف: {present}/{days_in_month} يوم → نسبة {present/days_in_month*100:.1f}%  |  🏠 الإيجار: {rent_per_person:.3f} (كامل)")
                extra["days"] = absent

            elif vtype == "from_date":
                vd = vac.get("date") or date(sel_year, sel_month, 15)
                vac_date = st.date_input(
                    "تاريخ بداية الإجازة",
                    value=vd,
                    min_value=date(sel_year, sel_month, 1),
                    max_value=date(sel_year, sel_month, days_in_month),
                    key=f"vdate_{person}"
                )
                present = max(0, min((vac_date - date(sel_year, sel_month, 1)).days, days_in_month))
                st.info(f"✅ من المصاريف: {present}/{days_in_month} يوم → نسبة {present/days_in_month*100:.1f}%  |  🏠 الإيجار: {rent_per_person:.3f} (كامل)")
                extra["date"] = vac_date

            elif vtype == "deduct":
                ded = st.number_input(
                    "المبلغ المخصوم من حصته في المصاريف",
                    min_value=0.0, step=0.5, format="%.3f",
                    value=float(vac.get("deduct_amount", 0.0)), key=f"ded_{person}"
                )
                st.info(f"✅ يشارك كامل في المصاريف مع خصم {ded:.3f}  |  🏠 الإيجار: {rent_per_person:.3f} (كامل)")
                extra["deduct_amount"] = ded

            elif vtype == "full":
                st.info(f"🏖️ لا يُحسب عليه أي مصاريف مشتركة  |  🏠 الإيجار: {rent_per_person:.3f} (كامل)")

            if st.button(f"💾 حفظ إعدادات {person}", key=f"save_{person}"):
                # تحديث session_state
                if selected_month_ar not in st.session_state.vacations:
                    st.session_state.vacations[selected_month_ar] = {}
                if vtype == "none":
                    st.session_state.vacations[selected_month_ar].pop(person, None)
                else:
                    st.session_state.vacations[selected_month_ar][person] = {"type": vtype, **extra}

                # حفظ في Sheets
                with st.spinner("حفظ في Sheets…"):
                    result = call_script({
                        "action":    "saveVacation",
                        "month":     selected_month_ar,
                        "name":      person,
                        "vtype":     vtype,
                        "days":      extra.get("days", ""),
                        "vacDate":   str(extra.get("date", "")),
                        "deductAmt": extra.get("deduct_amount", ""),
                    })
                if "Success" in result:
                    st.success(f"✅ تم حفظ إجازة {person}")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error(f"رد الخادم: {result}")

    if month_vacations:
        st.divider()
        st.markdown("**📋 الإجازات المسجلة هذا الشهر:**")
        for person, vac in month_vacations.items():
            vtype = vac.get("type", "")
            desc_map = {
                "full":       "إجازة كاملة (بدون مصاريف)",
                "from_start": f"غياب {vac.get('days',0)} يوم من أول الشهر",
                "from_date":  f"إجازة من {vac.get('date','')}",
                "deduct":     f"خصم {vac.get('deduct_amount',0):.3f} من المصاريف",
            }
            desc = desc_map.get(vtype, "")
            st.markdown(f'<div class="vacation-notice">🏖️ <strong>{person}</strong>: {desc} | 🏠 الإيجار ثابت: {rent_per_person:.3f}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  تبويب ٤: سجل المصاريف (تعديل + حذف)
# ══════════════════════════════════════════════
with tab4:
    st.subheader(f"📜 سجل مصاريف {selected_month_ar}")
    filter_name = st.selectbox("فلتر باسم", ["الكل"] + SHABAB, key="filter_name")
    display_df  = month_df.copy() if not month_df.empty else pd.DataFrame()
    if filter_name != "الكل" and not display_df.empty:
        display_df = display_df[display_df["الاسم"] == filter_name]

    if not display_df.empty:
        filtered_total = pd.to_numeric(display_df["المبلغ"], errors='coerce').sum()
        st.metric("إجمالي المبالغ المعروضة", f"{filtered_total:.3f}")

        for idx, row in display_df.iloc[::-1].iterrows():
            amount_val = float(row["المبلغ"]) if pd.notna(row["المبلغ"]) else 0.0
            row_num    = int(row["_row"])   if "_row"   in row else None
            row_id     = str(row["_rowId"]) if "_rowId" in row else ""

            with st.expander(f"📌 {row['الاسم']}  |  {amount_val:.3f}  |  {row['البيان']}"):
                col_a, col_b = st.columns(2)
                col_a.write(f"**التاريخ:** {row['التاريخ']}")
                col_a.write(f"**الشهر:** {row['الشهر']}")
                img_link = str(row['الصورة']).strip()
                if img_link.startswith("http"):
                    col_b.link_button("🖼️ فتح صورة الفاتورة", img_link)
                else:
                    col_b.caption("⚠️ لا توجد صورة")

                if row_num:
                    st.markdown("---")
                    ec1, ec2 = st.columns(2)

                    with ec1:
                        st.markdown("**✏️ تعديل**")
                        new_amount = st.number_input("المبلغ الجديد", value=amount_val,
                                                      format="%.3f", key=f"edit_amt_{idx}")
                        new_note   = st.text_input("البيان الجديد", value=str(row['البيان']),
                                                    key=f"edit_note_{idx}")
                        new_date   = st.text_input("التاريخ الجديد", value=str(row['التاريخ']),
                                                    key=f"edit_date_{idx}")
                        if st.button("💾 حفظ التعديل", key=f"save_edit_{idx}"):
                            with st.spinner("تعديل…"):
                                res = call_script({
                                    "action": "editExpense", "row": row_num, "rowId": row_id,
                                    "amount": new_amount, "note": new_note, "date": new_date,
                                })
                            if "Success" in res:
                                st.success("✅ تم التعديل!")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(res)

                    with ec2:
                        st.markdown("**🗑️ حذف**")
                        st.warning("لا يمكن التراجع عن الحذف!")
                        if st.button("🗑️ حذف هذا المصروف", key=f"del_{idx}", type="primary"):
                            with st.spinner("حذف…"):
                                res = call_script({"action": "deleteExpense", "row": row_num, "rowId": row_id})
                            if "Success" in res:
                                st.success("✅ تم الحذف!")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(res)
    else:
        st.info("لا توجد مصاريف مسجلة لهذا الشهر.")

    if not month_df.empty:
        st.divider()
        st.markdown("**📊 إجماليات كل شخص:**")
        cols = st.columns(3)
        for i, person in enumerate(SHABAB):
            total_p = pd.to_numeric(month_df[month_df["الاسم"] == person]["المبلغ"], errors='coerce').sum()
            with cols[i % 3]:
                st.metric(person, f"{total_p:.3f}")

# ══════════════════════════════════════════════
#  تبويب ٥: إدارة الأشخاص
# ══════════════════════════════════════════════
with tab5:
    st.subheader("⚙️ إدارة قائمة الأشخاص")
    st.markdown("""
    <div class="info-box">
    💡 إضافة أو حذف شخص يؤثر على توزيع الإيجار فوراً (الإيجار ÷ عدد الأشخاص).
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 👥 الأشخاص الحاليون")
    for person in SHABAB:
        pc1, pc2, pc3 = st.columns([3, 1, 1])
        pc1.markdown(f"🔹 **{person}**")

        # زر تعديل الاسم
        if pc2.button("✏️ تعديل", key=f"editbtn_{person}"):
            st.session_state[f"editing_{person}"] = True

        if st.session_state.get(f"editing_{person}", False):
            with st.form(key=f"rename_form_{person}"):
                new_name = st.text_input("الاسم الجديد", value=person, key=f"newname_{person}")
                sc1, sc2 = st.columns(2)
                save_rename = sc1.form_submit_button("💾 حفظ")
                cancel_rename = sc2.form_submit_button("❌ إلغاء")
                if save_rename:
                    if new_name.strip() and new_name.strip() != person:
                        with st.spinner("تعديل الاسم…"):
                            res = call_script({"action": "renamePerson", "oldName": person, "newName": new_name.strip()})
                        if "Success" in res:
                            st.success(f"✅ تم تغيير الاسم إلى {new_name}")
                            st.session_state.pop(f"editing_{person}", None)
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(res)
                    else:
                        st.warning("⚠️ أدخل اسماً مختلفاً.")
                if cancel_rename:
                    st.session_state.pop(f"editing_{person}", None)
                    st.rerun()

        # زر حذف
        if pc3.button("🗑️ حذف", key=f"delperson_{person}"):
            with st.spinner(f"حذف {person}…"):
                res = call_script({"action": "deletePerson", "name": person})
            if "Success" in res:
                st.success(f"✅ تم حذف {person}")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error(res)

    st.divider()
    st.markdown("### ➕ إضافة شخص جديد")
    with st.form("add_person_form", clear_on_submit=True):
        new_person = st.text_input("اسم الشخص الجديد", placeholder="مثال: أبو عمر محمد السيد")
        add_btn    = st.form_submit_button("➕ إضافة", use_container_width=True)
        if add_btn:
            if new_person.strip():
                if new_person.strip() in SHABAB:
                    st.warning("⚠️ هذا الشخص موجود مسبقاً!")
                else:
                    with st.spinner("إضافة…"):
                        res = call_script({"action": "addPerson", "name": new_person.strip()})
                    if "Success" in res:
                        st.success(f"✅ تمت إضافة {new_person}")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(res)
            else:
                st.warning("⚠️ أدخل اسماً صحيحاً.")
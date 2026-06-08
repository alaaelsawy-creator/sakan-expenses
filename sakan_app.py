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
    page_title="تنظيم السكن",
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
.badge-vacation { background:#1a2e3b;color:#60a5fa;border:1px solid #1d4ed8;border-radius:20px;padding:4px 14px;font-weight:700;font-size:0.85rem; }
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
SCRIPT_URL    = "https://script.google.com/macros/s/AKfycbxPsmytLQIo0GHas-PEpM0d33uStRYdMVKRfgU31V6wOTT3Q2k98hHGHHvncNx88b_o/exec"

MONTHS_AR = {
    "January":"يناير","February":"فبراير","March":"مارس","April":"أبريل",
    "May":"مايو","June":"يونيو","July":"يوليو","August":"أغسطس",
    "September":"سبتمبر","October":"أكتوبر","November":"نوفمبر","December":"ديسمبر",
}

# ─────────────────────────────────────────────
#  دوال التحميل من Sheets
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
    return []

def load_settings():
    try:
        resp = requests.get(SCRIPT_URL + "?type=settings", timeout=10)
        return resp.json()
    except:
        return {}

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
            if row.get("days"):      entry["days"]         = int(row["days"])
            if row.get("vacDate"):   entry["date"]          = _parse_date(row["vacDate"])
            if row.get("deductAmt"): entry["deduct_amount"] = float(row["deductAmt"])
            result[m][n] = entry
        return result
    except:
        return {}

def _parse_date(val):
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try: return datetime.strptime(str(val), fmt).date()
        except: pass
    return None

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(f"{SHEET_CSV_URL}&cachebust={datetime.now().timestamp()}")
        df["_row"]   = range(2, len(df)+2)
        df["_rowId"] = (df["الشهر"].astype(str)+"|"+df["الاسم"].astype(str)+"|"+
                        df["المبلغ"].astype(str)+"|"+df["التاريخ"].astype(str))
        return df
    except:
        return pd.DataFrame(columns=["الشهر","الاسم","المبلغ","البيان","التاريخ","الصورة","_row","_rowId"])

def load_log():
    try:
        resp = requests.get(SCRIPT_URL + "?type=log", timeout=10)
        return resp.json()
    except:
        return []

def call_script(payload):
    """إرسال طلب POST للـ Apps Script مع التحقق من الرد."""
    try:
        resp = requests.post(SCRIPT_URL, data=payload, timeout=30)
        return resp.text
    except Exception as e:
        return f"Error: {e}"

def clear_all_cache():
    """مسح جميع الـ cache والـ session_state المؤقت دفعة واحدة."""
    st.cache_data.clear()
    for key in ["gas_log", "refresh_gas", "cleaning_log", "refresh_cleaning"]:
        st.session_state.pop(key, None)

# ─────────────────────────────────────────────
#  العنوان
# ─────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <h1>🏠 تنظيم السكن</h1>
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
month_opts_ar = [f"{m:02d} – {MONTHS_AR[datetime(2026,m,1).strftime('%B')]} 2026" for m in range(1, 13)]

c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
with c1:
    selected_month_ar = st.selectbox("📅 الشهر", month_opts_ar, index=current_date.month - 1)
with c2:
    month_idx     = month_opts_ar.index(selected_month_ar)
    sel_month     = month_idx + 1
    sel_year      = 2026
    days_in_month = calendar.monthrange(sel_year, sel_month)[1]
    st.metric("📆 أيام الشهر", days_in_month)
with c3:
    _sheet_rent = float(sheet_settings.get("total_rent", 0.0))
    total_rent_input = st.number_input(
        "🏠 إجمالي الإيجار", min_value=0.0,
        value=_sheet_rent, format="%.3f"
    )
with c4:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 حفظ الإيجار", type="primary", use_container_width=True):
        res = call_script({"action": "saveSetting", "key": "total_rent",
                           "value": str(total_rent_input)})
        if "Success" in res:
            st.success("✅ تم الحفظ")
            st.cache_data.clear()
            st.rerun()
        else:
            st.error(res)
with c5:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 تحديث", use_container_width=True):
        clear_all_cache()
        st.rerun()

st.markdown("""
<div class="rule-box">
⚠️ <b>قاعدة التوزيع:</b>
الإيجار يُقسَّم بالتساوي على <b>جميع الأشخاص</b> حتى من في إجازة. |
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
        return 1.0
    return 1.0

# ─────────────────────────────────────────────
#  الحسابات الرئيسية
# ─────────────────────────────────────────────
_raw_month = all_data[all_data["الشهر"] == selected_month_ar] if not all_data.empty else pd.DataFrame()
if not _raw_month.empty:
    _valid = pd.to_numeric(_raw_month["المبلغ"], errors='coerce').fillna(0) > 0
    month_df = _raw_month[_valid].copy()
else:
    month_df = pd.DataFrame()

total_extra = pd.to_numeric(month_df["المبلغ"], errors='coerce').sum() if not month_df.empty else 0.0

expense_ratios = {}
deduct_map     = {}
total_ratio    = 0.0
for person in SHABAB:
    vac = month_vacations.get(person, {})
    r   = calc_expense_ratio(vac, days_in_month, sel_year, sel_month)
    expense_ratios[person] = r
    total_ratio           += r
    deduct_map[person]     = float(vac.get("deduct_amount", 0)) if vac.get("type") == "deduct" else 0.0

rent_per_person = total_rent_input / len(SHABAB) if SHABAB else 0.0

def get_expense_share(person):
    if total_ratio == 0: return 0.0
    vac = month_vacations.get(person, {})
    if vac.get("type") == "deduct":
        base = (expense_ratios[person] / total_ratio) * total_extra
        return max(0.0, base - deduct_map[person])
    return (expense_ratios[person] / total_ratio) * total_extra

summary = []
for person in SHABAB:
    paid      = pd.to_numeric(month_df[month_df["الاسم"]==person]["المبلغ"], errors='coerce').sum() if not month_df.empty else 0.0
    exp_share = get_expense_share(person)
    total_due = exp_share + rent_per_person
    balance   = paid - total_due
    vac       = month_vacations.get(person, {})
    summary.append({
        "الاسم": person, "مدفوع": paid,
        "حصة_مصاريف": exp_share, "إيجار": rent_per_person,
        "المستحق": total_due, "الرصيد": balance,
        "إجازة": vac.get("type","none"), "النسبة": expense_ratios[person],
    })

active_count = sum(1 for p in SHABAB if expense_ratios[p] > 0)

# ─────────────────────────────────────────────
#  رسالة إذا لا يوجد أشخاص
# ─────────────────────────────────────────────
if not SHABAB:
    st.warning("⚠️ لا يوجد أشخاص مسجلون. اذهب إلى تبويب **⚙️ إدارة الأشخاص** لإضافة الأشخاص أولاً.")

# ─────────────────────────────────────────────
#  تنبيهات خدمات الشقة (تظهر دائماً في الأعلى)
# ─────────────────────────────────────────────
@st.cache_data(ttl=120)
def load_cleaning_cached():
    try:
        resp = requests.get(SCRIPT_URL + "?type=cleaning", timeout=10)
        return resp.json()
    except:
        return []

@st.cache_data(ttl=120)
def load_gas_cached():
    try:
        resp = requests.get(SCRIPT_URL + "?type=gas", timeout=10)
        return resp.json()
    except:
        return []

def compute_next_cleaner_from_log(log, persons):
    if not persons or len(persons) == 0:
        return [], 1
    if not log:
        if len(persons) >= 2:
            return [persons[0], persons[1]], 1
        return [persons[0]], 1
    last = log[0]
    last_pair = [x.strip() for x in last.get("cleaner","").split("،") if x.strip()]
    try:
        week_num = int(str(last.get("weekNum", 1)).strip() or 1)
    except (ValueError, TypeError):
        week_num = 1
    if week_num >= 2:
        seen, seen_set = [], set()
        for entry in log:
            pair_str = entry.get("cleaner","")
            if pair_str not in seen_set:
                seen.append(pair_str)
                seen_set.add(pair_str)
        current_pair_str = last.get("cleaner","")
        all_pairs = build_pairs(persons)
        if not all_pairs:
            return [], 1
        pair_strs = ["، ".join(p) for p in all_pairs]
        if current_pair_str in pair_strs:
            idx = pair_strs.index(current_pair_str)
            next_pair = all_pairs[(idx + 1) % len(all_pairs)]
        else:
            next_pair = all_pairs[0]
        return next_pair, 1
    else:
        return last_pair, 2

def build_pairs(persons):
    n = len(persons)
    if n == 0: return []
    if n == 1: return [[persons[0]]]
    pairs = []
    i = 0
    while i < n:
        pairs.append(persons[i:i+2])
        i += 2
    return pairs

_cleaning_log_alert = load_cleaning_cached()
_gas_log_alert      = load_gas_cached()

_next_cleaners, _next_week_num = compute_next_cleaner_from_log(_cleaning_log_alert, SHABAB)

def get_next_gas_alert(log, persons):
    if not persons: return None
    if not log: return persons[0]
    last_filler = log[0].get("filler","")
    if last_filler in persons:
        return persons[(persons.index(last_filler) + 1) % len(persons)]
    return persons[0]

_next_gas_person = get_next_gas_alert(_gas_log_alert, SHABAB)

if SHABAB:
    al1, al2 = st.columns(2)
    with al1:
        _wlabel = "الأسبوع الأول 🆕" if _next_week_num == 1 else "الأسبوع الثاني 🔁"
        _names  = " و ".join(_next_cleaners) if _next_cleaners else "—"
        st.markdown(f"""
<div style="background:linear-gradient(135deg,#0d3b2e,#1a4a38);border:2px solid #4ade80;
     border-radius:14px;padding:14px 20px;margin-bottom:10px;">
  <div style="color:#86efac;font-size:0.8rem;margin-bottom:2px;">🧹 دور التنظيف هذا الأسبوع</div>
  <div style="color:#4ade80;font-size:1.4rem;font-weight:800;">{_names}</div>
  <div style="color:#6ee7b7;font-size:0.8rem;margin-top:2px;">{_wlabel}</div>
</div>""", unsafe_allow_html=True)
    with al2:
        _gname = _next_gas_person or "—"
        st.markdown(f"""
<div style="background:linear-gradient(135deg,#0d1f3c,#1a2e4a);border:2px solid #60a5fa;
     border-radius:14px;padding:14px 20px;margin-bottom:10px;">
  <div style="color:#93c5fd;font-size:0.8rem;margin-bottom:2px;">🔵 دور ملء الأنبوبة</div>
  <div style="color:#60a5fa;font-size:1.4rem;font-weight:800;">{_gname}</div>
  <div style="color:#7dd3fc;font-size:0.8rem;margin-top:2px;">عليه الدور القادم</div>
</div>""", unsafe_allow_html=True)
    st.divider()

# ─────────────────────────────────────────────
#  التبويبات
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 الملخص", "➕ إضافة مصروف", "📜 سجل المصاريف",
    "🏠 خدمات الشقة", "🏖️ الإجازات", "⚙️ إدارة الأشخاص", "📋 سجل الأحداث"
])

# ══════════════════════════════════════════════
#  تبويب ١: الملخص
# ══════════════════════════════════════════════
with tab1:
    if not SHABAB:
        st.info("أضف أشخاصاً أولاً من تبويب ⚙️ إدارة الأشخاص.")
    else:
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
            st.markdown(f'<div class="stat-card"><div class="value">{active_count}/{len(SHABAB)}</div><div class="label">👥 المتواجدون</div></div>', unsafe_allow_html=True)

        st.markdown("### 👥 وضع كل شخص")
        for row in summary:
            bal   = row["الرصيد"]
            vtype = row["إجازة"]
            if vtype and vtype != "none":
                vac_labels = {
                    "full":       f"🏖️ إجازة كاملة",
                    "from_start": f"🗓️ نسبة مصاريف {row['النسبة']*100:.0f}%",
                    "from_date":  f"📅 نسبة مصاريف {row['النسبة']*100:.0f}%",
                    "deduct":     f"➖ خصم من المصاريف",
                }
                badge = f'<span class="badge-vacation">{vac_labels.get(vtype,"")} + إيجار كامل</span>'
            elif abs(bal) < 0.01:
                badge = '<span class="badge-zero">➖ صفر</span>'
            elif bal > 0:
                badge = f'<span class="badge-green">🟢 له {bal:.3f}</span>'
            else:
                badge = f'<span class="badge-red">🔴 عليه {abs(bal):.3f}</span>'

            details = f"دفع: {row['مدفوع']:.3f} | مصاريف: {row['حصة_مصاريف']:.3f} | إيجار: {row['إيجار']:.3f} | المستحق: {row['المستحق']:.3f}"
            st.markdown(f"""<div class="person-row">
                <span class="person-name">{row['الاسم']}</span>
                <span class="person-paid">{details}</span>
                {badge}
            </div>""", unsafe_allow_html=True)

        st.markdown("### 📱 تقرير الواتساب")
        lines = [
            f"*تقرير مصاريف السكن – {selected_month_ar}*",
            f"🏠 الإيجار الكلي: {total_rent_input:.3f} (على كل فرد: {rent_per_person:.3f})",
            f"💰 إجمالي المصاريف: {total_extra:.3f}",
            f"📊 الإجمالي الكلي: {total_extra+total_rent_input:.3f}",
            "─────────────────",
        ]
        for row in summary:
            bal    = row["الرصيد"]
            vtype  = row["إجازة"]
            status = "له 🟢" if bal > 0 else ("عليه 🔴" if bal < 0 else "صفر ➖")
            note   = ""
            if vtype == "full": note = " (إجازة – بدون مصاريف)"
            elif vtype in ("from_start","from_date"): note = f" (مصاريف {row['النسبة']*100:.0f}%)"
            elif vtype == "deduct": note = " (خصم من المصاريف)"
            lines.append(f"• {row['الاسم']}{note}: {status} *{abs(bal):.3f}*")

        report_text = "\n".join(lines)
        st.markdown(f'<div class="whatsapp-box">{report_text}</div>', unsafe_allow_html=True)
        st.button("📋 نسخ التقرير", help="انسخ النص أعلاه يدوياً")

# ══════════════════════════════════════════════
#  تبويب ٢: إضافة مصروف
# ══════════════════════════════════════════════
with tab2:
    if not SHABAB:
        st.info("أضف أشخاصاً أولاً من تبويب ⚙️ إدارة الأشخاص.")
    else:
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
                            res = call_script({
                                "action": "addExpense",
                                "month": selected_month_ar, "name": name,
                                "amount": amount, "note": note, "date": str(expense_date),
                                "imgData": img_base64, "imgName": img_name,
                            })
                        if "Success" in res:
                            st.success("✅ تم التسجيل!")
                            st.balloons()
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"رد الخادم: {res}")
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
#  تبويب ٣: سجل المصاريف
# ══════════════════════════════════════════════
with tab3:
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
                        if st.button("🗑️ حذف", key=f"del_{idx}", type="primary"):
                            with st.spinner("حذف…"):
                                res = call_script({"action": "deleteExpense",
                                                   "row": row_num, "rowId": row_id})
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
            total_p = pd.to_numeric(month_df[month_df["الاسم"]==person]["المبلغ"], errors='coerce').sum()
            with cols[i % 3]:
                st.metric(person, f"{total_p:.3f}")

# ══════════════════════════════════════════════
#  تبويب ٤: خدمات الشقة
# ══════════════════════════════════════════════
with tab4:
    st.subheader("🏠 خدمات الشقة")
    svc_tab1, svc_tab2 = st.tabs(["🧹 تنظيف الشقة", "🔵 ملء الأنبوبة"])

    # ─────────────────────────────────────────
    #  قسم التنظيف
    # ─────────────────────────────────────────
    with svc_tab1:
        st.markdown("""
<div class="info-box">
🧹 <b>نظام دور التنظيف:</b> كل أسبوع يُنظّف شخصان. ينظفان معاً أسبوعاً ثم أسبوعاً ثانياً،
ثم ينتقل الدور لشخصين آخرين وهكذا. فترة التنظيف من <b>الخميس إلى السبت</b>.
من يكون <b>في إجازة أو مريضاً أو مسافراً</b> يُستثنى ويأخذ دوره عند عودته.
</div>""", unsafe_allow_html=True)

        # ── تحميل سجل التنظيف (بدون cache لضمان التحديث الفوري) ──
        def load_cleaning_fresh():
            try:
                resp = requests.get(SCRIPT_URL + "?type=cleaning", timeout=15)
                return resp.json()
            except:
                return []

        if "cleaning_log" not in st.session_state:
            st.session_state.cleaning_log = load_cleaning_fresh()

        cleaning_log = st.session_state.cleaning_log

        # ── بناء الأزواج وحساب الدور ──
        def build_rotation_pairs(persons):
            pairs = []
            i = 0
            while i < len(persons):
                if i + 1 < len(persons):
                    pairs.append([persons[i], persons[i+1]])
                else:
                    pairs.append([persons[i]])
                i += 2
            return pairs

        def get_current_turn(log, persons):
            if not persons:
                return [], 1, []
            all_pairs = build_rotation_pairs(persons)
            if not log:
                return all_pairs[0] if all_pairs else [], 1, all_pairs

            last_entry   = log[0]
            last_pair    = [x.strip() for x in last_entry.get("cleaner","").split("،") if x.strip()]
            try:
                last_week_n = int(str(last_entry.get("weekNum", 1)).strip() or 1)
            except (ValueError, TypeError):
                last_week_n = 1

            if last_week_n >= 2:
                pair_strs = ["،".join(p) for p in all_pairs]
                last_str  = "،".join(last_pair)
                if last_str in pair_strs:
                    idx = pair_strs.index(last_str)
                    next_pair = all_pairs[(idx + 1) % len(all_pairs)]
                else:
                    next_pair = all_pairs[0]
                return next_pair, 1, all_pairs
            else:
                return last_pair, 2, all_pairs

        if not SHABAB:
            st.info("أضف أشخاصاً أولاً.")
        else:
            current_pair, current_week_n, all_pairs = get_current_turn(cleaning_log, SHABAB)

            _pair_label = " و ".join(current_pair) if current_pair else "—"
            _wk_label   = "الأسبوع الأول 🆕" if current_week_n == 1 else "الأسبوع الثاني 🔁"
            st.markdown(f"""
<div style="background:linear-gradient(135deg,#0d3b2e,#1a4a38);border:2px solid #4ade80;
     border-radius:16px;padding:18px;text-align:center;margin-bottom:20px;">
  <div style="color:#86efac;font-size:0.85rem;">🧹 دور التنظيف الحالي</div>
  <div style="color:#4ade80;font-size:1.8rem;font-weight:800;margin:6px 0;">{_pair_label}</div>
  <div style="color:#6ee7b7;font-size:0.85rem;">{_wk_label}</div>
</div>""", unsafe_allow_html=True)

            if len(all_pairs) > 1:
                st.markdown("##### 🔄 ترتيب دوران الأزواج")
                pair_cols = st.columns(len(all_pairs))
                for i, pair in enumerate(all_pairs):
                    is_current = (sorted(pair) == sorted(current_pair))
                    with pair_cols[i]:
                        border = "#4ade80" if is_current else "#2a2f45"
                        icon   = "🧹" if is_current else f"{i+1}"
                        st.markdown(f"""
<div style="background:#1a1e2e;border:1px solid {border};border-radius:10px;
     padding:10px;text-align:center;margin-bottom:10px;">
  <div style="font-size:1.2rem;">{icon}</div>
  <div style="color:{'#4ade80' if is_current else '#8892b0'};font-weight:700;font-size:0.85rem;">
    {"<br>".join(pair)}
  </div>
</div>""", unsafe_allow_html=True)

            st.markdown("### ✅ تسجيل دور التنظيف هذا الأسبوع")
            st.caption("ضع ✓ بجانب من نظّف فعلاً هذا الأسبوع، ثم اضغط حفظ.")

            from datetime import timedelta
            today = date.today()
            days_to_thu = (3 - today.weekday()) % 7
            if days_to_thu == 0: days_to_thu = 7
            default_thu = today + timedelta(days=days_to_thu)
            default_sat = default_thu + timedelta(days=2)

            DAYS_AR = ["الاثنين","الثلاثاء","الأربعاء","الخميس","الجمعة","السبت","الأحد"]

            with st.form("cleaning_form_v2", clear_on_submit=True):
                st.markdown("**👥 من نظّف هذا الأسبوع؟**")
                checked = {}
                cb_cols = st.columns(min(len(SHABAB), 4))
                for i, person in enumerate(SHABAB):
                    is_suggested = person in current_pair
                    with cb_cols[i % len(cb_cols)]:
                        checked[person] = st.checkbox(
                            person,
                            value=is_suggested,
                            key=f"cb_clean_{person}"
                        )

                st.markdown("**📅 أيام التنظيف**")
                date_cols = st.columns(3)
                with date_cols[0]:
                    week_from = st.date_input("من يوم", value=default_thu, key="cl_from")
                with date_cols[1]:
                    week_to   = st.date_input("إلى يوم", value=default_sat, key="cl_to")
                with date_cols[2]:
                    week_num_sel = st.selectbox("رقم الأسبوع في الدور",
                                                options=[1, 2],
                                                index=current_week_n - 1,
                                                format_func=lambda x: f"الأسبوع {x}",
                                                key="cl_weeknum")

                if week_from and week_to:
                    d = week_from
                    days_list = []
                    while d <= week_to:
                        days_list.append(f"{DAYS_AR[d.weekday()]} {d.strftime('%d/%m')}")
                        d += timedelta(days=1)
                    st.caption("📅 أيام التنظيف: " + " ، ".join(days_list))

                cleaning_note = st.text_input("ملاحظة (اختياري)", placeholder="مثال: تنظيف عميق")

                submitted = st.form_submit_button("💾 حفظ", use_container_width=True, type="primary")
                if submitted:
                    selected_cleaners = [p for p, v in checked.items() if v]
                    if not selected_cleaners:
                        st.warning("⚠️ اختر شخصاً واحداً على الأقل.")
                    else:
                        cleaner_str = "، ".join(selected_cleaners)
                        with st.spinner("جاري الحفظ…"):
                            res = call_script({
                                "action":   "addCleaningEntry",
                                "cleaner":  cleaner_str,
                                "weekFrom": str(week_from),
                                "weekTo":   str(week_to),
                                "weekNum":  str(week_num_sel),
                                "note":     cleaning_note,
                            })
                        if "Success" in res:
                            st.success(f"✅ تم تسجيل دور {cleaner_str}!")
                            # ── إصلاح: مسح cache والـ session_state معاً ──
                            st.session_state.pop("cleaning_log", None)
                            load_cleaning_cached.cache_clear()
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"خطأ: {res}")

            st.markdown("### 📋 سجل التنظيف")
            if cleaning_log:
                for entry in cleaning_log[:15]:
                    wn = entry.get("weekNum","")
                    wn_badge = f'<span style="background:#1a3b2e;color:#6ee7b7;border-radius:8px;padding:2px 8px;font-size:0.75rem;">أسبوع {wn}</span>' if wn else ""
                    note_txt  = f' | {entry.get("note","")}' if entry.get("note") else ""
                    st.markdown(f"""
<div style="background:#1a1e2e;border:1px solid #2a2f45;border-radius:10px;
     padding:11px 16px;margin-bottom:7px;direction:rtl;">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;">
    <span style="color:#4ade80;font-weight:700;">🧹 {entry.get("cleaner","")}</span>
    <span style="color:#8892b0;font-size:0.82rem;">📅 {entry.get("weekFrom","")} → {entry.get("weekTo","")}{note_txt}</span>
    {wn_badge}
  </div>
</div>""", unsafe_allow_html=True)
            else:
                st.info("لا يوجد سجل تنظيف بعد.")

    # ─────────────────────────────────────────
    #  قسم الأنبوبة ← الإصلاح الرئيسي هنا
    # ─────────────────────────────────────────
    with svc_tab2:
        st.markdown("""
<div class="info-box">
🔵 <b>نظام ملء الأنبوبة:</b> الدور يدور على الجميع بالتسلسل. كل شخص يملأ مرة واحدة.
</div>""", unsafe_allow_html=True)

        def load_gas_fresh():
            try:
                resp = requests.get(SCRIPT_URL + "?type=gas", timeout=15)
                return resp.json()
            except:
                return []

        if "gas_log" not in st.session_state:
            st.session_state.gas_log = load_gas_fresh()

        gas_log = st.session_state.gas_log

        def get_next_gas(log, persons):
            if not persons: return None
            if not log: return persons[0]
            last_filler = log[0].get("filler","")
            if last_filler in persons:
                return persons[(persons.index(last_filler) + 1) % len(persons)]
            return persons[0]

        if not SHABAB:
            st.info("أضف أشخاصاً أولاً.")
        else:
            next_gas = get_next_gas(gas_log, SHABAB)

            st.markdown(f"""
<div style="background:linear-gradient(135deg,#0d1f3c,#1a2e4a);border:2px solid #60a5fa;
     border-radius:16px;padding:18px;text-align:center;margin-bottom:20px;">
  <div style="color:#93c5fd;font-size:0.85rem;">🔵 دور ملء الأنبوبة القادم</div>
  <div style="color:#60a5fa;font-size:1.8rem;font-weight:800;margin:6px 0;">{next_gas or "—"}</div>
</div>""", unsafe_allow_html=True)

            st.markdown("##### 🔄 ترتيب الدور")
            gas_cols = st.columns(min(len(SHABAB), 5))
            for i, person in enumerate(SHABAB):
                is_next = (person == next_gas)
                with gas_cols[i % len(gas_cols)]:
                    total_fills = sum(1 for e in gas_log if e.get("filler") == person)
                    st.markdown(f"""
<div style="background:#1a1e2e;border:1px solid {'#60a5fa' if is_next else '#2a2f45'};
     border-radius:10px;padding:10px;text-align:center;margin-bottom:8px;">
  <div style="font-size:1.1rem;">{'🔵' if is_next else '⏳'}</div>
  <div style="color:{'#60a5fa' if is_next else '#8892b0'};font-weight:700;font-size:0.85rem;">{person}</div>
  <div style="color:#6b7280;font-size:0.75rem;">ملأ {total_fills}×</div>
</div>""", unsafe_allow_html=True)

            # ── نموذج التسجيل ──
            st.markdown("### ✅ تسجيل ملء الأنبوبة")
            st.caption("ضع ✓ بجانب من ملأ الأنبوبة، ثم اضغط حفظ.")

            with st.form("gas_form_v2", clear_on_submit=True):
                st.markdown("**👤 من ملأ الأنبوبة؟**")
                gas_checked = {}
                gas_cb_cols = st.columns(min(len(SHABAB), 4))
                for i, person in enumerate(SHABAB):
                    is_suggested = (person == next_gas)
                    with gas_cb_cols[i % len(gas_cb_cols)]:
                        gas_checked[person] = st.checkbox(
                            person,
                            value=is_suggested,
                            key=f"cb_gas_{person}"
                        )

                gas_submitted = st.form_submit_button("💾 حفظ", use_container_width=True, type="primary")

                if gas_submitted:
                    selected_filler = [p for p, v in gas_checked.items() if v]
                    if len(selected_filler) != 1:
                        st.warning("⚠️ اختر شخصاً واحداً فقط لملء الأنبوبة.")
                    else:
                        filler = selected_filler[0]
                        with st.spinner("جاري الحفظ…"):
                            # ── إصلاح: لا نرسل nextPerson — يحسبها الـ Script ──
                            res = call_script({
                                "action": "addGasEntry",
                                "filler": filler,
                            })
                        if "Success" in res:
                            # استخرج nextPerson من رد الـ Script
                            parts    = res.split("|")
                            next_p   = parts[1].strip() if len(parts) > 1 else "—"
                            st.success(f"✅ تم تسجيل {filler}! الدور القادم: {next_p}")
                            # ── إصلاح: مسح cache والـ session_state معاً ──
                            st.session_state.pop("gas_log", None)
                            load_gas_cached.cache_clear()
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"خطأ: {res}")

            # ── سجل الأنبوبة ──
            st.markdown("### 📋 سجل الأنبوبة")
            if gas_log:
                for entry in gas_log[:15]:
                    st.markdown(f"""
<div style="background:#1a1e2e;border:1px solid #2a2f45;border-radius:10px;
     padding:11px 16px;margin-bottom:7px;direction:rtl;">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;">
    <span style="color:#60a5fa;font-weight:700;">🔵 {entry.get("filler","")}</span>
    <span style="color:#8892b0;font-size:0.82rem;">
      📅 {str(entry.get("date",""))[:10]}
      &nbsp;|&nbsp; التالي: <b style="color:#93c5fd;">{entry.get("nextPerson","")}</b>
    </span>
  </div>
</div>""", unsafe_allow_html=True)
            else:
                st.info("لا يوجد سجل أنبوبة بعد.")

# ══════════════════════════════════════════════
#  تبويب ٥: الإجازات
# ══════════════════════════════════════════════
with tab5:
    if not SHABAB:
        st.info("أضف أشخاصاً أولاً من تبويب ⚙️ إدارة الأشخاص.")
    else:
        st.subheader(f"🏖️ إدارة الإجازات – {selected_month_ar}")
        st.markdown("""<div class="info-box">
        💡 <b>الإجازة تؤثر على المصاريف المشتركة فقط.</b> الإيجار ثابت على الجميع.<br>
        • <b>إجازة كاملة</b>: بدون مصاريف مشتركة (الإيجار يبقى).<br>
        • <b>غياب من أول الشهر</b>: يُحسب بنسبة أيام حضوره.<br>
        • <b>إجازة من تاريخ</b>: يُحسب مصاريف الأيام الحاضرة فقط.<br>
        • <b>خصم مبلغ ثابت</b>: يشارك كامل مع خصم مبلغ محدد.
        </div>""", unsafe_allow_html=True)

        for person in SHABAB:
            with st.expander(f"⚙️ {person}", expanded=False):
                vac   = month_vacations.get(person, {})
                vtype = st.radio(
                    "نوع الإجازة",
                    options=["none","full","from_start","from_date","deduct"],
                    format_func=lambda x: {
                        "none":       "✅ لا توجد إجازة",
                        "full":       "🏖️ إجازة كاملة (بدون مصاريف)",
                        "from_start": "🗓️ غياب من أول الشهر",
                        "from_date":  "📅 إجازة من تاريخ معين",
                        "deduct":     "➖ خصم مبلغ ثابت",
                    }[x],
                    index=["none","full","from_start","from_date","deduct"].index(vac.get("type","none")),
                    key=f"vtype_{person}",
                )

                extra = {}
                if vtype == "from_start":
                    absent = st.number_input("عدد أيام الغياب", min_value=1,
                        max_value=days_in_month, step=1,
                        value=int(vac.get("days",1)), key=f"days_{person}")
                    present = days_in_month - absent
                    st.info(f"مصاريف: {present}/{days_in_month} يوم ({present/days_in_month*100:.1f}%) | إيجار: {rent_per_person:.3f} (كامل)")
                    extra["days"] = absent
                elif vtype == "from_date":
                    vd = vac.get("date") or date(sel_year, sel_month, 15)
                    vac_date = st.date_input("تاريخ بداية الإجازة", value=vd,
                        min_value=date(sel_year, sel_month, 1),
                        max_value=date(sel_year, sel_month, days_in_month),
                        key=f"vdate_{person}")
                    present = max(0, min((vac_date-date(sel_year,sel_month,1)).days, days_in_month))
                    st.info(f"مصاريف: {present}/{days_in_month} يوم ({present/days_in_month*100:.1f}%) | إيجار: {rent_per_person:.3f} (كامل)")
                    extra["date"] = vac_date
                elif vtype == "deduct":
                    ded = st.number_input("المبلغ المخصوم", min_value=0.0, step=0.5,
                        format="%.3f", value=float(vac.get("deduct_amount",0.0)),
                        key=f"ded_{person}")
                    st.info(f"خصم {ded:.3f} من المصاريف | إيجار: {rent_per_person:.3f} (كامل)")
                    extra["deduct_amount"] = ded
                elif vtype == "full":
                    st.info(f"لا مصاريف مشتركة | إيجار: {rent_per_person:.3f} (كامل)")

                if st.button(f"💾 حفظ {person}", key=f"save_{person}"):
                    if selected_month_ar not in st.session_state.vacations:
                        st.session_state.vacations[selected_month_ar] = {}
                    if vtype == "none":
                        st.session_state.vacations[selected_month_ar].pop(person, None)
                    else:
                        st.session_state.vacations[selected_month_ar][person] = {"type": vtype, **extra}

                    with st.spinner("حفظ…"):
                        res = call_script({
                            "action": "saveVacation", "month": selected_month_ar,
                            "name": person, "vtype": vtype,
                            "days": extra.get("days",""),
                            "vacDate": str(extra.get("date","")),
                            "deductAmt": extra.get("deduct_amount",""),
                        })
                    if "Success" in res:
                        st.success(f"✅ تم حفظ إجازة {person}")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(res)

        if month_vacations:
            st.divider()
            st.markdown("**📋 الإجازات المسجلة:**")
            for person, vac in month_vacations.items():
                vtype = vac.get("type","")
                desc_map = {
                    "full":       "إجازة كاملة",
                    "from_start": f"غياب {vac.get('days',0)} يوم",
                    "from_date":  f"إجازة من {vac.get('date','')}",
                    "deduct":     f"خصم {vac.get('deduct_amount',0):.3f}",
                }
                st.markdown(f'<div class="vacation-notice">🏖️ <strong>{person}</strong>: {desc_map.get(vtype,"")} | إيجار ثابت: {rent_per_person:.3f}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  تبويب ٦: إدارة الأشخاص
# ══════════════════════════════════════════════
with tab6:
    st.subheader("⚙️ إدارة قائمة الأشخاص")
    st.markdown('<div class="info-box">💡 إضافة أو حذف شخص يؤثر على توزيع الإيجار فوراً.</div>',
                unsafe_allow_html=True)

    if SHABAB:
        st.markdown("### 👥 الأشخاص الحاليون")
        for person in SHABAB:
            pc1, pc2, pc3 = st.columns([3, 1, 1])
            pc1.markdown(f"🔹 **{person}**")

            if pc2.button("✏️ تعديل", key=f"editbtn_{person}"):
                st.session_state[f"editing_{person}"] = True

            if st.session_state.get(f"editing_{person}", False):
                with st.form(key=f"rename_form_{person}"):
                    new_name = st.text_input("الاسم الجديد", value=person)
                    sc1, sc2 = st.columns(2)
                    save_r   = sc1.form_submit_button("💾 حفظ")
                    cancel_r = sc2.form_submit_button("❌ إلغاء")
                    if save_r:
                        if new_name.strip() and new_name.strip() != person:
                            with st.spinner("تعديل…"):
                                res = call_script({"action": "renamePerson",
                                                   "oldName": person, "newName": new_name.strip()})
                            if "Success" in res:
                                st.success(f"✅ تم التغيير إلى {new_name}")
                                st.session_state.pop(f"editing_{person}", None)
                                clear_all_cache()
                                st.rerun()
                            else:
                                st.error(res)
                        else:
                            st.warning("⚠️ أدخل اسماً مختلفاً.")
                    if cancel_r:
                        st.session_state.pop(f"editing_{person}", None)
                        st.rerun()

            if pc3.button("🗑️ حذف", key=f"delperson_{person}"):
                with st.spinner(f"حذف {person}…"):
                    res = call_script({"action": "deletePerson", "name": person})
                if "Success" in res:
                    st.success(f"✅ تم حذف {person}")
                    clear_all_cache()
                    st.rerun()
                else:
                    st.error(res)
    else:
        st.info("لا يوجد أشخاص بعد. أضف أول شخص من الأسفل.")

    st.divider()
    st.markdown("### ➕ إضافة شخص جديد")
    with st.form("add_person_form", clear_on_submit=True):
        new_person = st.text_input("اسم الشخص", placeholder="مثال: أبو عمر محمد السيد")
        if st.form_submit_button("➕ إضافة", use_container_width=True):
            if new_person.strip():
                if new_person.strip() in SHABAB:
                    st.warning("⚠️ هذا الشخص موجود مسبقاً!")
                else:
                    with st.spinner("إضافة…"):
                        res = call_script({"action": "addPerson", "name": new_person.strip()})
                    if "Success" in res:
                        st.success(f"✅ تمت إضافة {new_person}")
                        clear_all_cache()
                        st.rerun()
                    else:
                        st.error(res)
            else:
                st.warning("⚠️ أدخل اسماً صحيحاً.")

# ══════════════════════════════════════════════
#  تبويب ٧: سجل الأحداث
# ══════════════════════════════════════════════
with tab7:
    st.subheader("📋 سجل الأحداث التاريخي")

    col_r1, col_r2 = st.columns([1, 1])
    with col_r1:
        filter_type = st.selectbox("فلتر النوع", [
            "الكل", "➕ إضافة مصروف", "✏️ تعديل مصروف", "🗑️ حذف مصروف",
            "🏖️ تسجيل إجازة", "🏖️ إلغاء إجازة",
            "👤 إضافة شخص", "🗑️ حذف شخص", "✏️ تغيير اسم",
            "⚙️ تغيير إعداد", "⚙️ إعداد جديد"
        ])
    with col_r2:
        if st.button("🔄 تحديث السجل", use_container_width=True):
            st.rerun()

    with st.spinner("جاري تحميل السجل…"):
        log_data = load_log()

    if filter_type != "الكل":
        log_data = [r for r in log_data if r.get("type","") == filter_type]

    if log_data:
        st.markdown(f"**إجمالي الأحداث: {len(log_data)}**")
        st.divider()

        type_colors = {
            "➕ إضافة مصروف":  "#0d3b2e",
            "✏️ تعديل مصروف":  "#1a2e1a",
            "🗑️ حذف مصروف":   "#3b0d0d",
            "🏖️ تسجيل إجازة": "#0d1f3c",
            "🏖️ إلغاء إجازة": "#1a1a2e",
            "👤 إضافة شخص":    "#1a2e1a",
            "🗑️ حذف شخص":     "#3b0d0d",
            "✏️ تغيير اسم":    "#1a1f3c",
            "⚙️ تغيير إعداد":  "#2a1a0d",
            "⚙️ إعداد جديد":   "#2a1a0d",
        }
        type_text_colors = {
            "➕ إضافة مصروف":  "#4ade80",
            "✏️ تعديل مصروف":  "#86efac",
            "🗑️ حذف مصروف":   "#f87171",
            "🏖️ تسجيل إجازة": "#60a5fa",
            "🏖️ إلغاء إجازة": "#93c5fd",
            "👤 إضافة شخص":    "#4ade80",
            "🗑️ حذف شخص":     "#f87171",
            "✏️ تغيير اسم":    "#a78bfa",
            "⚙️ تغيير إعداد":  "#fbbf24",
            "⚙️ إعداد جديد":   "#fbbf24",
        }

        for entry in log_data:
            bg    = type_colors.get(entry.get("type",""), "#1a1e2e")
            color = type_text_colors.get(entry.get("type",""), "#e0e6ff")
            month_badge = f'<span style="background:#1a237e;color:#90caf9;border-radius:10px;padding:2px 10px;font-size:0.8rem;margin-right:8px;">{entry.get("month","")}</span>' if entry.get("month") else ""
            st.markdown(f"""
            <div style="background:{bg};border-radius:10px;padding:12px 18px;
                        margin-bottom:8px;direction:rtl;border:1px solid #2a2f45;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <span style="color:{color};font-weight:700;font-size:0.95rem;">
                        {entry.get("type","")}
                    </span>
                    <span style="color:#8892b0;font-size:0.8rem;">
                        🕐 {entry.get("datetime","")}
                    </span>
                </div>
                <div style="color:#c8cfd8;margin-top:6px;font-size:0.9rem;">
                    {month_badge}{entry.get("details","")}
                </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("لا توجد أحداث مسجلة بعد.")

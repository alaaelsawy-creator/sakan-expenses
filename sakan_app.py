import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime, date, timedelta
import calendar
from PIL import Image
import io
import json

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
.exempt-badge { background:#2a1a0d;color:#fbbf24;border:1px solid #854d0e;
    border-radius:20px;padding:3px 12px;font-size:0.8rem;font-weight:700; }
.next-badge { background:#0d3b2e;color:#4ade80;border:1px solid #166534;
    border-radius:20px;padding:3px 12px;font-size:0.8rem;font-weight:700; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  الثوابت
# ─────────────────────────────────────────────
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1g0VfbnUVwNXjV0c2BFlmlX3RSh5eZnpzLUrzwLeqG2I/export?format=csv&gid=0"
SCRIPT_URL    = "https://script.google.com/macros/s/AKfycbzv2bG2CawNoTB5z4501xTczXe5tRcA0gGxsJqX2YgZgTB4ayfnSxuE2_d4Uli7hYqs/exec"

MONTHS_AR = {
    "January":"يناير","February":"فبراير","March":"مارس","April":"أبريل",
    "May":"مايو","June":"يونيو","July":"يوليو","August":"أغسطس",
    "September":"سبتمبر","October":"أكتوبر","November":"نوفمبر","December":"ديسمبر",
}
DAYS_AR = ["الاثنين","الثلاثاء","الأربعاء","الخميس","الجمعة","السبت","الأحد"]

# ─────────────────────────────────────────────
#  إعدادات Green API (واتساب)
# ─────────────────────────────────────────────
def _wa_cfg():
    """يقرأ إعدادات Green API من st.secrets بأمان."""
    try:
        return {
            "instance": st.secrets["GREEN_API_INSTANCE"],
            "token":    st.secrets["GREEN_API_TOKEN"],
            "chat_id":  st.secrets["GREEN_API_CHAT_ID"],
        }
    except Exception:
        return None

def send_whatsapp(message: str) -> bool:
    """
    يرسل رسالة نصية لجروب الواتساب عبر Green API.
    يعيد True إذا نجح، False إذا فشل (صامت - لا يوقف التطبيق).
    """
    cfg = _wa_cfg()
    if not cfg:
        return False   # الـ secrets غير مضبوطة
    try:
        url  = (f"https://api.green-api.com/waInstance{cfg['instance']}"
                f"/sendMessage/{cfg['token']}")
        body = {"chatId": cfg["chat_id"], "message": message}
        resp = requests.post(url, json=body, timeout=15)
        return resp.status_code == 200
    except Exception:
        return False

# ── قوالب الرسائل ──
def _now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def notify_expense_add(name, amount, note, month):
    msg = ("🏠 *تنظيم السكن*\n"
           "➕ مصروف جديد\n"
           f"👤 {name}  |  💰 {float(amount):.3f}\n"
           f"📝 {note}  |  📅 {month}\n"
           f"🕐 {_now_str()}")
    send_whatsapp(msg)

def notify_expense_edit(amount, note):
    msg = ("🏠 *تنظيم السكن*\n"
           "✏️ تعديل مصروف\n"
           f"💰 المبلغ الجديد: {float(amount):.3f}  |  📝 {note}\n"
           f"🕐 {_now_str()}")
    send_whatsapp(msg)

def notify_expense_delete(row_id):
    msg = ("🏠 *تنظيم السكن*\n"
           "🗑️ حذف مصروف\n"
           f"🔑 {row_id}\n"
           f"🕐 {_now_str()}")
    send_whatsapp(msg)

def notify_vacation(name, vtype, month):
    vtype_ar = {
        "full":       "إجازة كاملة 🏖️",
        "from_start": "غياب من أول الشهر 🗓️",
        "from_date":  "إجازة من تاريخ 📅",
        "deduct":     "خصم مبلغ ➖",
        "none":       "إلغاء الإجازة ✅",
    }.get(vtype, vtype)
    msg = ("🏠 *تنظيم السكن*\n"
           "🏖️ تحديث إجازة\n"
           f"👤 {name}  |  {vtype_ar}\n"
           f"📅 {month}\n"
           f"🕐 {_now_str()}")
    send_whatsapp(msg)

def notify_cleaning(cleaner, week_from, week_to, next_pair, note=""):
    note_line = f"📝 {note}\n" if note else ""
    msg = ("🏠 *تنظيم السكن*\n"
           "🧹 دور التنظيف\n"
           f"👥 نظّف: *{cleaner}*\n"
           f"📅 {week_from} ← {week_to}\n"
           f"{note_line}"
           f"🔜 الدور القادم: *{next_pair}*\n"
           f"🕐 {_now_str()}")
    send_whatsapp(msg)

def notify_gas(filler, next_person):
    msg = ("🏠 *تنظيم السكن*\n"
           "🔵 ملء الأنبوبة\n"
           f"👤 ملأ: *{filler}*\n"
           f"🔜 الدور القادم: *{next_person}*\n"
           f"🕐 {_now_str()}")
    send_whatsapp(msg)

def notify_person_add(name):
    msg = ("🏠 *تنظيم السكن*\n"
           f"👤 إضافة شخص جديد: *{name}*\n"
           f"🕐 {_now_str()}")
    send_whatsapp(msg)

def notify_person_delete(name):
    msg = ("🏠 *تنظيم السكن*\n"
           f"🗑️ حذف شخص: *{name}*\n"
           f"🕐 {_now_str()}")
    send_whatsapp(msg)

def notify_person_rename(old_name, new_name):
    msg = ("🏠 *تنظيم السكن*\n"
           "✏️ تغيير اسم\n"
           f"📛 {old_name} ← *{new_name}*\n"
           f"🕐 {_now_str()}")
    send_whatsapp(msg)

def notify_rent_change(amount):
    msg = ("🏠 *تنظيم السكن*\n"
           "🏠 تغيير الإيجار\n"
           f"💰 الإيجار الجديد: *{float(amount):.3f}*\n"
           f"🕐 {_now_str()}")
    send_whatsapp(msg)

def notify_exemption(name, service, action):
    svc_ar = "التنظيف 🧹" if service == "cleaning" else "الأنبوبة 🔵"
    act_ar = "إعفاء 🚫" if action == "add" else "إلغاء إعفاء ✅"
    msg = ("🏠 *تنظيم السكن*\n"
           f"⚙️ {act_ar} من {svc_ar}\n"
           f"👤 {name}\n"
           f"🕐 {_now_str()}")
    send_whatsapp(msg)

# ─────────────────────────────────────────────
#  دوال التحميل من Sheets  (مُعرَّفة في أعلى المستوى)
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

# ── دوال الخدمات مُعرَّفة في أعلى المستوى لتجنب AttributeError ──
@st.cache_data(ttl=60)
def load_cleaning_cached():
    try:
        resp = requests.get(SCRIPT_URL + "?type=cleaning", timeout=15)
        return resp.json()
    except:
        return []

@st.cache_data(ttl=60)
def load_gas_cached():
    try:
        resp = requests.get(SCRIPT_URL + "?type=gas", timeout=15)
        return resp.json()
    except:
        return []

@st.cache_data(ttl=60)
def load_exemptions_cached():
    """تحميل قائمة المعفيين من الخدمات."""
    try:
        resp = requests.get(SCRIPT_URL + "?type=exemptions", timeout=10)
        return resp.json()
    except:
        return {}

def load_log():
    try:
        resp = requests.get(SCRIPT_URL + "?type=log", timeout=10)
        return resp.json()
    except:
        return []

def call_script(payload):
    try:
        resp = requests.post(SCRIPT_URL, data=payload, timeout=30)
        return resp.text
    except Exception as e:
        return f"Error: {e}"

def clear_all_cache():
    """مسح كل الـ cache والـ session_state المؤقت دفعة واحدة."""
    st.cache_data.clear()
    for key in ["gas_log", "cleaning_log"]:
        st.session_state.pop(key, None)

# ─────────────────────────────────────────────
#  دوال مساعدة للخدمات
# ─────────────────────────────────────────────
def get_active_persons(persons, month_vacations, exemptions=None):
    """الأشخاص المتاحون للخدمات (غير في إجازة كاملة وغير معفيين)."""
    exempt_set = set(exemptions or [])
    active = []
    for p in persons:
        vac = month_vacations.get(p, {})
        if vac.get("type") == "full":
            continue  # في إجازة كاملة → معفى تلقائياً
        if p in exempt_set:
            continue  # معفى يدوياً
        active.append(p)
    return active

def get_next_gas(log, active_persons):
    """من عليه دور ملء الأنبوبة من الأشخاص المتاحين."""
    if not active_persons:
        return None
    if not log:
        return active_persons[0]
    # آخر من ملأ
    last_filler = log[0].get("filler", "")
    # إذا آخر ملأ موجود في المتاحين → التالي بعده
    if last_filler in active_persons:
        idx = active_persons.index(last_filler)
        return active_persons[(idx + 1) % len(active_persons)]
    # إذا لم يوجد → أول متاح
    return active_persons[0]

def build_weekly_schedule(active_persons):
    """
    يبني جدول الأسابيع الكامل للدورة.

    النظام:
    • كل أسبوع شخصان ينظفان معاً.
    • الأول عليه أسبوعه الثاني، والثاني عليه أسبوعه الأول.
    • كل شخص ينظف أسبوعين متتاليين: أسبوعه الأول أولاً ثم أسبوعه الثاني.

    مثال 4 أشخاص (أ،ب،ج،د):
      أسبوع 1: أ(ثانيه) + ب(أوله)
      أسبوع 2: ب(ثانيه) + ج(أوله)
      أسبوع 3: ج(ثانيه) + د(أوله)
      أسبوع 4: د(ثانيه) + أ(أوله)  ← تبدأ الدورة من جديد

    الخوارزمية: أسبوع k:
      p_second = persons[k % n]      ← عليه أسبوعه الثاني
      p_first  = persons[(k+1) % n]  ← عليه أسبوعه الأول
    """
    n = len(active_persons)
    if n == 0:
        return []
    if n == 1:
        return [{"week_idx": 0, "p_first": active_persons[0], "p_second": None}]
    schedule = []
    for k in range(n):
        p_second = active_persons[k % n]
        p_first  = active_persons[(k + 1) % n]
        schedule.append({
            "week_idx": k,
            "p_first":  p_first,
            "p_second": p_second,
        })
    return schedule


def get_next_cleaning_week(log, active_persons):
    """
    يحسب الأسبوع القادم من السجل والمتاحين.
    يعيد dict: {"p_first": ..., "p_second": ..., "week_idx": N}
    أو None إذا لا يوجد أشخاص.
    """
    schedule = build_weekly_schedule(active_persons)
    if not schedule:
        return None
    if not log:
        return schedule[0]

    last      = log[0]
    last_next = last.get("nextPair", "").strip()

    if last_next:
        # الدور القادم محدد صراحةً في السجل → ابحث عنه في الجدول
        parts    = [x.strip() for x in last_next.split("،") if x.strip()]
        p_first  = parts[0] if len(parts) > 0 else None
        p_second = parts[1] if len(parts) > 1 else None
        for w in schedule:
            if w["p_first"] == p_first and w["p_second"] == p_second:
                return w
        # لم يوجد (تغيّر الأشخاص) → أعد بناء من السجل مباشرة
        return {"week_idx": -1, "p_first": p_first, "p_second": p_second}

    # لا يوجد nextPair → احسب من الجدول بناءً على آخر منظّف
    last_cleaners = sorted([x.strip() for x in last.get("cleaner","").split("،") if x.strip()])
    for idx, w in enumerate(schedule):
        pair = sorted([x for x in [w["p_first"], w["p_second"]] if x])
        if pair == last_cleaners:
            return schedule[(idx + 1) % len(schedule)]

    return schedule[0]

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
#  تحميل البيانات الأساسية
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
        "🏠 إجمالي الإيجار", min_value=0.0, value=_sheet_rent, format="%.3f"
    )
with c4:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 حفظ الإيجار", type="primary", use_container_width=True):
        res = call_script({"action": "saveSetting", "key": "total_rent", "value": str(total_rent_input)})
        if "Success" in res:
            st.success("✅ تم الحفظ")
            notify_rent_change(total_rent_input)
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
#  الإجازات للشهر المحدد
# ─────────────────────────────────────────────
month_vacations = st.session_state.vacations.get(selected_month_ar, {})

# ─────────────────────────────────────────────
#  حساب نسبة الحضور
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
    _valid   = pd.to_numeric(_raw_month["المبلغ"], errors='coerce').fillna(0) > 0
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

if not SHABAB:
    st.warning("⚠️ لا يوجد أشخاص مسجلون. اذهب إلى تبويب **⚙️ إدارة الأشخاص** لإضافة الأشخاص أولاً.")

# ─────────────────────────────────────────────
#  تحميل بيانات الخدمات للشاشة الرئيسية
# ─────────────────────────────────────────────
if "cleaning_log" not in st.session_state:
    st.session_state.cleaning_log = load_cleaning_cached()
if "gas_log" not in st.session_state:
    st.session_state.gas_log = load_gas_cached()

cleaning_log = st.session_state.cleaning_log
gas_log      = st.session_state.gas_log

# ── تحميل المعفيين ──
exemptions_data = load_exemptions_cached()
cleaning_exempt = set(exemptions_data.get("cleaning", []))
gas_exempt      = set(exemptions_data.get("gas", []))

# ── الأشخاص المتاحون لكل خدمة (مع مراعاة الإجازات والإعفاءات) ──
active_for_cleaning = get_active_persons(SHABAB, month_vacations, cleaning_exempt)
active_for_gas      = get_active_persons(SHABAB, month_vacations, gas_exempt)

next_gas_person  = get_next_gas(gas_log, active_for_gas)
next_clean_week  = get_next_cleaning_week(cleaning_log, active_for_cleaning)

# ─────────────────────────────────────────────
#  بطاقات التنبيه العلوية
# ─────────────────────────────────────────────
if SHABAB:
    al1, al2 = st.columns(2)
    with al1:
        if next_clean_week:
            _p1    = next_clean_week.get("p_first","—")
            _p2    = next_clean_week.get("p_second","")
            _names = f"{_p1} و {_p2}" if _p2 else _p1
            _lbl1  = f"{_p1} (أسبوعه الأول)"
            _lbl2  = f"{_p2} (أسبوعه الثاني)" if _p2 else ""
            _sub   = f"{_lbl1}  |  {_lbl2}" if _lbl2 else _lbl1
        else:
            _names = "—"; _sub = ""
        st.markdown(f"""
<div style="background:linear-gradient(135deg,#0d3b2e,#1a4a38);border:2px solid #4ade80;
     border-radius:14px;padding:14px 20px;margin-bottom:10px;">
  <div style="color:#86efac;font-size:0.8rem;margin-bottom:2px;">🧹 دور التنظيف هذا الأسبوع</div>
  <div style="color:#4ade80;font-size:1.4rem;font-weight:800;">{_names}</div>
  <div style="color:#6ee7b7;font-size:0.8rem;margin-top:2px;">{_sub}</div>
</div>""", unsafe_allow_html=True)
    with al2:
        _gname = next_gas_person or "—"
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
                    "full":       "🏖️ إجازة كاملة",
                    "from_start": f"🗓️ نسبة مصاريف {row['النسبة']*100:.0f}%",
                    "from_date":  f"📅 نسبة مصاريف {row['النسبة']*100:.0f}%",
                    "deduct":     "➖ خصم من المصاريف",
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
                            notify_expense_add(name, amount, note, selected_month_ar)
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
                        new_amount = st.number_input("المبلغ الجديد", value=amount_val, format="%.3f", key=f"edit_amt_{idx}")
                        new_note   = st.text_input("البيان الجديد", value=str(row['البيان']), key=f"edit_note_{idx}")
                        new_date   = st.text_input("التاريخ الجديد", value=str(row['التاريخ']), key=f"edit_date_{idx}")
                        if st.button("💾 حفظ التعديل", key=f"save_edit_{idx}"):
                            with st.spinner("تعديل…"):
                                res = call_script({"action": "editExpense", "row": row_num, "rowId": row_id,
                                                   "amount": new_amount, "note": new_note, "date": new_date})
                            if "Success" in res:
                                st.success("✅ تم التعديل!")
                                notify_expense_edit(new_amount, new_note)
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(res)
                    with ec2:
                        st.markdown("**🗑️ حذف**")
                        st.warning("لا يمكن التراجع عن الحذف!")
                        if st.button("🗑️ حذف", key=f"del_{idx}", type="primary"):
                            with st.spinner("حذف…"):
                                res = call_script({"action": "deleteExpense", "row": row_num, "rowId": row_id})
                            if "Success" in res:
                                st.success("✅ تم الحذف!")
                                notify_expense_delete(row_id)
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
#  تبويب ٤: خدمات الشقة  ← الإصلاح الكامل هنا
# ══════════════════════════════════════════════
with tab4:
    st.subheader("🏠 خدمات الشقة")
    svc_tab1, svc_tab2, svc_tab3 = st.tabs(["🧹 تنظيف الشقة", "🔵 ملء الأنبوبة", "🚫 إدارة الإعفاءات"])

    # ══════════════════════════════════════════
    #  قسم التنظيف
    # ══════════════════════════════════════════
    with svc_tab1:
        st.markdown("""
<div class="info-box">
🧹 <b>نظام دور التنظيف:</b> كل أسبوع شخصان ينظفان معاً.<br>
• الأول في <b>أسبوعه الأول</b> والثاني في <b>أسبوعه الثاني</b>.<br>
• مثال (أ،ب،ج،د): أسبوع1: أ(1)+ب(1) | أسبوع2: أ(2)+ج(1) | أسبوع3: ب(2)+د(1) | أسبوع4: ج(2)+د(2)<br>
• من في <b>إجازة كاملة</b> يُعفى تلقائياً. يمكن الإعفاء اليدوي من تبويب <b>إدارة الإعفاءات</b>.
</div>""", unsafe_allow_html=True)

        if not SHABAB:
            st.info("أضف أشخاصاً أولاً.")
        else:
            # ── حالة كل شخص ──
            st.markdown("#### 👥 حالة الأشخاص")
            person_cols = st.columns(min(len(SHABAB), 4))
            for i, person in enumerate(SHABAB):
                vac       = month_vacations.get(person, {})
                is_vac    = vac.get("type") == "full"
                is_exmpt  = person in cleaning_exempt
                is_active = person in active_for_cleaning
                with person_cols[i % len(person_cols)]:
                    if is_vac:
                        status_html = '<span class="exempt-badge">🏖️ إجازة</span>'
                    elif is_exmpt:
                        status_html = '<span class="exempt-badge">🚫 معفى</span>'
                    else:
                        status_html = '<span class="next-badge">✅ متاح</span>'
                    st.markdown(f"""
<div style="background:#1a1e2e;border:1px solid {'#4ade80' if is_active else '#3b0d1a'};
     border-radius:10px;padding:10px;text-align:center;margin-bottom:8px;">
  <div style="color:{'#4ade80' if is_active else '#8892b0'};font-weight:700;font-size:0.9rem;">{person}</div>
  <div style="margin-top:4px;">{status_html}</div>
</div>""", unsafe_allow_html=True)

            st.divider()

            # ── الدور القادم ──
            cw = next_clean_week
            if cw:
                _p1   = cw.get("p_first","—")
                _p2   = cw.get("p_second","")
                _disp = f"{_p1} و {_p2}" if _p2 else _p1
                _sub1 = f"🔵 {_p1} — أسبوعه الثاني"
                _sub2 = f"  |  🟢 {_p2} — أسبوعه الأول" if _p2 else ""
            else:
                _disp = "—"; _sub1 = ""; _sub2 = ""

            st.markdown(f"""
<div style="background:linear-gradient(135deg,#0d3b2e,#1a4a38);border:2px solid #4ade80;
     border-radius:16px;padding:18px;text-align:center;margin-bottom:16px;">
  <div style="color:#86efac;font-size:0.85rem;">🧹 دور التنظيف القادم</div>
  <div style="color:#4ade80;font-size:1.8rem;font-weight:800;margin:6px 0;">{_disp}</div>
  <div style="color:#6ee7b7;font-size:0.82rem;">{_sub1}{_sub2}</div>
</div>""", unsafe_allow_html=True)

            # ── جدول الدورة الكاملة ──
            schedule = build_weekly_schedule(active_for_cleaning)
            if len(schedule) > 1:
                st.markdown("##### 🗓️ جدول الدورة الكاملة")
                cw_idx = cw.get("week_idx", -1) if cw else -1
                sch_cols = st.columns(min(len(schedule), 4))
                for i, w in enumerate(schedule):
                    is_now   = (i == cw_idx)
                    p1_name  = w.get("p_first","")
                    p2_name  = w.get("p_second","")
                    border   = "#4ade80" if is_now else "#2a2f45"
                    txt_col  = "#4ade80" if is_now else "#8892b0"
                    icon     = "🧹" if is_now else f"{i+1}"
                    p2_line  = ""  # handled in main display
                    with sch_cols[i % len(sch_cols)]:
                        st.markdown(f"""
<div style="background:#1a1e2e;border:1px solid {border};border-radius:10px;
     padding:10px;text-align:center;margin-bottom:8px;">
  <div style="font-size:1rem;margin-bottom:4px;">{icon}</div>
  <div style="color:{txt_col};font-weight:700;font-size:0.82rem;"><span style='color:#60a5fa;'>({p2_name}) ثانيه</span><br>{p1_name} (أوله)</div>
</div>""", unsafe_allow_html=True)

            # ── نموذج التسجيل ──
            st.markdown("### ✅ تسجيل دور التنظيف")
            st.caption("اختر من نظّف هذا الأسبوع، ثم حدد من عليه الدور القادم.")

            today = date.today()
            days_to_thu = (3 - today.weekday()) % 7
            if days_to_thu == 0: days_to_thu = 7
            default_thu = today + timedelta(days=days_to_thu)
            default_sat = default_thu + timedelta(days=2)

            with st.form("cleaning_form", clear_on_submit=True):

                # من نظّف؟ — مُقترَح من الجدول
                st.markdown("**👥 من نظّف هذا الأسبوع؟**")
                suggested_now = [cw.get("p_first",""), cw.get("p_second","") or ""] if cw else []
                checked  = {}
                cb_cols  = st.columns(min(len(SHABAB), 4))
                for i, person in enumerate(SHABAB):
                    vac         = month_vacations.get(person, {})
                    is_vac_full = vac.get("type") == "full"
                    is_exmpt    = person in cleaning_exempt
                    label       = person
                    if is_vac_full: label += " 🏖️"
                    elif is_exmpt:  label += " 🚫"
                    # تحديد الدور (أسبوع أول/ثاني) في الاسم
                    if cw and person == cw.get("p_first"):
                        label += " 🟢(أوله)"
                    elif cw and person == cw.get("p_second"):
                        label += " 🔵(ثانيه)"
                    with cb_cols[i % len(cb_cols)]:
                        checked[person] = st.checkbox(
                            label,
                            value=(person in suggested_now and person),
                            key=f"cb_clean_{person}"
                        )

                st.markdown("---")
                st.markdown("**📅 أيام التنظيف**")
                date_cols = st.columns(2)
                with date_cols[0]:
                    week_from = st.date_input("من يوم", value=default_thu, key="cl_from")
                with date_cols[1]:
                    week_to   = st.date_input("إلى يوم", value=default_sat, key="cl_to")

                if week_from and week_to and week_from <= week_to:
                    d = week_from
                    days_list = []
                    while d <= week_to:
                        days_list.append(f"{DAYS_AR[d.weekday()]} {d.strftime('%d/%m')}")
                        d += timedelta(days=1)
                    st.caption("📅 " + " ، ".join(days_list))

                # ── الدور القادم يختاره المستخدم ──
                st.markdown("---")
                st.markdown("**🔜 من عليه الدور القادم؟** (الشخص الأول في أسبوعه الأول والثاني في أسبوعه الثاني)")

                # اقتراح الأسبوع التالي من الجدول
                if cw and cw.get("week_idx", -1) >= 0:
                    next_idx = (cw["week_idx"] + 1) % len(schedule)
                    sug_next = schedule[next_idx]
                else:
                    sug_next = schedule[0] if schedule else None

                sug_p1 = sug_next.get("p_first","") if sug_next else ""
                sug_p2 = sug_next.get("p_second","") if sug_next else ""

                nc1, nc2 = st.columns(2)
                with nc1:
                    st.markdown("**🟢 الشخص الجديد في الدور (أسبوعه الأول)**")
                    next_p1_opts = {}
                    for person in active_for_cleaning:
                        next_p1_opts[person] = st.checkbox(
                            person, value=(person == sug_p1),
                            key=f"cb_np1_{person}"
                        )
                with nc2:
                    st.markdown("**🔵 الشخص المكمِّل دورته (أسبوعه الثاني)**")
                    next_p2_opts = {}
                    for person in active_for_cleaning:
                        next_p2_opts[person] = st.checkbox(
                            person, value=(person == sug_p2),
                            key=f"cb_np2_{person}"
                        )

                cleaning_note = st.text_input("ملاحظة (اختياري)", placeholder="مثال: تنظيف عميق")
                submitted = st.form_submit_button("💾 حفظ", use_container_width=True, type="primary")

                if submitted:
                    selected_cleaners = [p for p, v in checked.items() if v]
                    sel_p1_next       = [p for p, v in next_p1_opts.items() if v]
                    sel_p2_next       = [p for p, v in next_p2_opts.items() if v]

                    if not selected_cleaners:
                        st.warning("⚠️ اختر من نظّف هذا الأسبوع.")
                    elif len(sel_p1_next) != 1:
                        st.warning("⚠️ اختر شخصاً واحداً في الدور القادم (أسبوع أول).")
                    elif len(sel_p2_next) != 1:
                        st.warning("⚠️ اختر شخصاً واحداً في الدور القادم (أسبوع ثاني).")
                    elif sel_p1_next[0] == sel_p2_next[0]:
                        st.warning("⚠️ الشخص الأول والثاني يجب أن يكونا مختلفَين.")
                    else:
                        cleaner_str = "، ".join(selected_cleaners)
                        next_str    = f"{sel_p2_next[0]}، {sel_p1_next[0]}"
                        with st.spinner("جاري الحفظ…"):
                            res = call_script({
                                "action":   "addCleaningEntry",
                                "cleaner":  cleaner_str,
                                "weekFrom": str(week_from),
                                "weekTo":   str(week_to),
                                "weekNum":  "1",
                                "nextPair": next_str,
                                "note":     cleaning_note,
                            })
                        if "Success" in res:
                            st.success(f"✅ تم التسجيل! الدور القادم: {next_str}")
                            notify_cleaning(cleaner_str, str(week_from), str(week_to), next_str, cleaning_note)
                            st.session_state.pop("cleaning_log", None)
                            clear_all_cache()
                            st.rerun()
                        else:
                            st.error(f"خطأ: {res}")

            # ── سجل التنظيف ──
            st.markdown("### 📋 سجل التنظيف")
            if cleaning_log:
                for entry in cleaning_log[:15]:
                    next_p   = entry.get("nextPair","")
                    note_txt = f' | {entry.get("note","")}' if entry.get("note") else ""
                    next_badge = f'<span style="color:#93c5fd;font-size:0.8rem;"> | القادم: <b>{next_p}</b></span>' if next_p else ""
                    st.markdown(f"""
<div style="background:#1a1e2e;border:1px solid #2a2f45;border-radius:10px;
     padding:11px 16px;margin-bottom:7px;direction:rtl;">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;">
    <span style="color:#4ade80;font-weight:700;">🧹 {entry.get("cleaner","")}</span>
    <span style="color:#8892b0;font-size:0.82rem;">📅 {entry.get("weekFrom","")} → {entry.get("weekTo","")}{note_txt}</span>
    <span>{next_badge}</span>
  </div>
</div>""", unsafe_allow_html=True)
            else:
                st.info("لا يوجد سجل تنظيف بعد.")
    # ══════════════════════════════════════════
    #  قسم الأنبوبة
    # ══════════════════════════════════════════
    with svc_tab2:
        st.markdown("""
<div class="info-box">
🔵 <b>نظام ملء الأنبوبة:</b> الدور يدور على المتاحين بالتسلسل.<br>
• من في <b>إجازة كاملة</b> يُعفى تلقائياً.<br>
• يمكن إعفاء أي شخص يدوياً من تبويب <b>إدارة الإعفاءات</b>.
</div>""", unsafe_allow_html=True)

        if not SHABAB:
            st.info("أضف أشخاصاً أولاً.")
        else:
            # ── بطاقة الدور القادم ──
            st.markdown(f"""
<div style="background:linear-gradient(135deg,#0d1f3c,#1a2e4a);border:2px solid #60a5fa;
     border-radius:16px;padding:18px;text-align:center;margin-bottom:20px;">
  <div style="color:#93c5fd;font-size:0.85rem;">🔵 دور ملء الأنبوبة القادم (من المتاحين)</div>
  <div style="color:#60a5fa;font-size:1.8rem;font-weight:800;margin:6px 0;">{next_gas_person or "—"}</div>
</div>""", unsafe_allow_html=True)

            # ── شبكة الأشخاص ──
            st.markdown("##### 🔄 ترتيب الدور")
            gas_cols = st.columns(min(len(SHABAB), 5))
            for i, person in enumerate(SHABAB):
                is_next  = (person == next_gas_person)
                vac      = month_vacations.get(person, {})
                is_vac   = vac.get("type") == "full"
                is_exmpt = person in gas_exempt
                total_fills = sum(1 for e in gas_log if e.get("filler") == person)
                with gas_cols[i % len(gas_cols)]:
                    if is_vac:
                        status_lbl = "🏖️ إجازة"
                        border_col = "#3b2a0d"
                        name_col   = "#8892b0"
                    elif is_exmpt:
                        status_lbl = "🚫 معفى"
                        border_col = "#3b0d0d"
                        name_col   = "#8892b0"
                    elif is_next:
                        status_lbl = "🔵 دوره"
                        border_col = "#60a5fa"
                        name_col   = "#60a5fa"
                    else:
                        status_lbl = f"⏳ {total_fills}×"
                        border_col = "#2a2f45"
                        name_col   = "#8892b0"
                    st.markdown(f"""
<div style="background:#1a1e2e;border:1px solid {border_col};
     border-radius:10px;padding:10px;text-align:center;margin-bottom:8px;">
  <div style="color:{name_col};font-weight:700;font-size:0.85rem;">{person}</div>
  <div style="color:#6b7280;font-size:0.75rem;margin-top:4px;">{status_lbl}</div>
</div>""", unsafe_allow_html=True)

            # ── نموذج التسجيل ──
            st.markdown("### ✅ تسجيل ملء الأنبوبة")
            st.caption("اختر من ملأ الأنبوبة، ثم حدد من عليه الدور القادم.")

            with st.form("gas_form", clear_on_submit=True):
                # من ملأ
                st.markdown("**👤 من ملأ الأنبوبة؟** (اختر شخصاً واحداً فقط)")
                gas_checked = {}
                gas_cb_cols = st.columns(min(len(SHABAB), 4))
                for i, person in enumerate(SHABAB):
                    is_suggested = (person == next_gas_person)
                    vac          = month_vacations.get(person, {})
                    is_vac_full  = vac.get("type") == "full"
                    is_exmpt     = person in gas_exempt
                    label        = person
                    if is_vac_full: label += " 🏖️"
                    elif is_exmpt:  label += " 🚫"
                    with gas_cb_cols[i % len(gas_cb_cols)]:
                        gas_checked[person] = st.checkbox(label, value=is_suggested, key=f"cb_gas_{person}")

                st.markdown("---")
                # من عليه الدور القادم
                st.markdown("**🔜 من عليه الدور القادم؟** (اختر شخصاً واحداً)")
                next_gas_opts   = {}
                next_gas_cols   = st.columns(min(len(active_for_gas), 4))
                # اقتراح: التالي بعد المقترح الحالي
                if next_gas_person and next_gas_person in active_for_gas:
                    idx_ng = active_for_gas.index(next_gas_person)
                    suggested_next_gas = active_for_gas[(idx_ng + 1) % len(active_for_gas)] if len(active_for_gas) > 1 else next_gas_person
                else:
                    suggested_next_gas = active_for_gas[0] if active_for_gas else None

                for i, person in enumerate(active_for_gas):
                    with next_gas_cols[i % len(next_gas_cols)]:
                        next_gas_opts[person] = st.checkbox(
                            person, value=(person == suggested_next_gas),
                            key=f"cb_next_gas_{person}"
                        )

                gas_submitted = st.form_submit_button("💾 حفظ", use_container_width=True, type="primary")

                if gas_submitted:
                    selected_filler   = [p for p, v in gas_checked.items() if v]
                    selected_next_gas = [p for p, v in next_gas_opts.items() if v]
                    if len(selected_filler) != 1:
                        st.warning("⚠️ اختر شخصاً واحداً فقط لملء الأنبوبة.")
                    elif len(selected_next_gas) != 1:
                        st.warning("⚠️ اختر شخصاً واحداً فقط للدور القادم.")
                    else:
                        filler    = selected_filler[0]
                        next_p    = selected_next_gas[0]
                        with st.spinner("جاري الحفظ…"):
                            res = call_script({
                                "action":     "addGasEntry",
                                "filler":     filler,
                                "nextPerson": next_p,
                            })
                        if "Success" in res:
                            st.success(f"✅ تم تسجيل {filler}! الدور القادم: {next_p}")
                            st.session_state.pop("gas_log", None)
                            clear_all_cache()
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

    # ══════════════════════════════════════════
    #  قسم إدارة الإعفاءات
    # ══════════════════════════════════════════
    with svc_tab3:
        st.markdown("""
<div class="info-box">
🚫 <b>إدارة الإعفاءات الدائمة من الخدمات:</b><br>
• الإعفاء هنا <b>دائم</b> حتى تلغيه يدوياً (غير مرتبط بشهر).<br>
• من في <b>إجازة كاملة</b> في الشهر المحدد يُعفى <b>تلقائياً</b> بدون الحاجة لإضافته هنا.<br>
• هذا القسم للإعفاءات الدائمة مثل: مريض، عمل خاص، إلخ.
</div>""", unsafe_allow_html=True)

        if not SHABAB:
            st.info("أضف أشخاصاً أولاً.")
        else:
            col_ex1, col_ex2 = st.columns(2)

            with col_ex1:
                st.markdown("### 🧹 إعفاءات التنظيف")
                for person in SHABAB:
                    vac      = month_vacations.get(person, {})
                    is_vac   = vac.get("type") == "full"
                    is_exmpt = person in cleaning_exempt
                    ex_row1, ex_row2 = st.columns([3, 1])
                    with ex_row1:
                        if is_vac:
                            st.markdown(f"🏖️ **{person}** — معفى تلقائياً (إجازة)")
                        elif is_exmpt:
                            st.markdown(f"🚫 **{person}** — معفى يدوياً")
                        else:
                            st.markdown(f"✅ **{person}** — متاح")
                    with ex_row2:
                        if not is_vac:
                            if is_exmpt:
                                if st.button("إلغاء", key=f"unexmpt_cl_{person}", use_container_width=True):
                                    res = call_script({"action": "removeExemption", "service": "cleaning", "name": person})
                                    if "Success" in res:
                                        notify_exemption(person, "cleaning", "remove")
                                        clear_all_cache()
                                        st.rerun()
                            else:
                                if st.button("إعفاء", key=f"exmpt_cl_{person}", use_container_width=True):
                                    res = call_script({"action": "addExemption", "service": "cleaning", "name": person})
                                    if "Success" in res:
                                        notify_exemption(person, "cleaning", "add")
                                        clear_all_cache()
                                        st.rerun()

            with col_ex2:
                st.markdown("### 🔵 إعفاءات الأنبوبة")
                for person in SHABAB:
                    vac      = month_vacations.get(person, {})
                    is_vac   = vac.get("type") == "full"
                    is_exmpt = person in gas_exempt
                    ex_row1, ex_row2 = st.columns([3, 1])
                    with ex_row1:
                        if is_vac:
                            st.markdown(f"🏖️ **{person}** — معفى تلقائياً (إجازة)")
                        elif is_exmpt:
                            st.markdown(f"🚫 **{person}** — معفى يدوياً")
                        else:
                            st.markdown(f"✅ **{person}** — متاح")
                    with ex_row2:
                        if not is_vac:
                            if is_exmpt:
                                if st.button("إلغاء", key=f"unexmpt_gs_{person}", use_container_width=True):
                                    res = call_script({"action": "removeExemption", "service": "gas", "name": person})
                                    if "Success" in res:
                                        notify_exemption(person, "gas", "remove")
                                        clear_all_cache()
                                        st.rerun()
                            else:
                                if st.button("إعفاء", key=f"exmpt_gs_{person}", use_container_width=True):
                                    res = call_script({"action": "addExemption", "service": "gas", "name": person})
                                    if "Success" in res:
                                        notify_exemption(person, "gas", "add")
                                        clear_all_cache()
                                        st.rerun()

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
        • <b>إجازة كاملة</b>: بدون مصاريف مشتركة + يُعفى تلقائياً من التنظيف والأنبوبة.<br>
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
                        "full":       "🏖️ إجازة كاملة (بدون مصاريف + إعفاء من الخدمات)",
                        "from_start": "🗓️ غياب من أول الشهر",
                        "from_date":  "📅 إجازة من تاريخ معين",
                        "deduct":     "➖ خصم مبلغ ثابت",
                    }[x],
                    index=["none","full","from_start","from_date","deduct"].index(vac.get("type","none")),
                    key=f"vtype_{person}",
                )
                extra = {}
                if vtype == "from_start":
                    absent = st.number_input("عدد أيام الغياب", min_value=1, max_value=days_in_month, step=1,
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
                    ded = st.number_input("المبلغ المخصوم", min_value=0.0, step=0.5, format="%.3f",
                                           value=float(vac.get("deduct_amount",0.0)), key=f"ded_{person}")
                    st.info(f"خصم {ded:.3f} من المصاريف | إيجار: {rent_per_person:.3f} (كامل)")
                    extra["deduct_amount"] = ded
                elif vtype == "full":
                    st.info(f"لا مصاريف مشتركة | إيجار: {rent_per_person:.3f} (كامل) | معفى من التنظيف والأنبوبة ✅")

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
                        notify_vacation(person, vtype, selected_month_ar)
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
                    "full":       "إجازة كاملة (+ إعفاء خدمات)",
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
    st.markdown('<div class="info-box">💡 إضافة أو حذف شخص يؤثر على توزيع الإيجار فوراً.</div>', unsafe_allow_html=True)

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
                                res = call_script({"action": "renamePerson", "oldName": person, "newName": new_name.strip()})
                            if "Success" in res:
                                st.success(f"✅ تم التغيير إلى {new_name}")
                                notify_person_rename(person, new_name.strip())
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
                    notify_person_delete(person)
                    clear_all_cache()
                    st.rerun()
                else:
                    st.error(res)
    else:
        st.info("لا يوجد أشخاص بعد. أضف أول شخص من الأسفل.")

    st.divider()
    st.markdown("### ➕ إضافة شخص جديد")
    with st.form("add_person_form", clear_on_submit=True):
        new_person = st.text_input("اسم الشخص", placeholder="مثال: أبو عمر")
        if st.form_submit_button("➕ إضافة", use_container_width=True):
            if new_person.strip():
                if new_person.strip() in SHABAB:
                    st.warning("⚠️ هذا الشخص موجود مسبقاً!")
                else:
                    with st.spinner("إضافة…"):
                        res = call_script({"action": "addPerson", "name": new_person.strip()})
                    if "Success" in res:
                        st.success(f"✅ تمت إضافة {new_person}")
                        notify_person_add(new_person.strip())
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
            "➕ إضافة مصروف": "#0d3b2e", "✏️ تعديل مصروف": "#1a2e1a",
            "🗑️ حذف مصروف":  "#3b0d0d", "🏖️ تسجيل إجازة": "#0d1f3c",
            "🏖️ إلغاء إجازة":"#1a1a2e", "👤 إضافة شخص":   "#1a2e1a",
            "🗑️ حذف شخص":    "#3b0d0d", "✏️ تغيير اسم":   "#1a1f3c",
            "⚙️ تغيير إعداد":"#2a1a0d", "⚙️ إعداد جديد":  "#2a1a0d",
        }
        type_text_colors = {
            "➕ إضافة مصروف": "#4ade80", "✏️ تعديل مصروف": "#86efac",
            "🗑️ حذف مصروف":  "#f87171", "🏖️ تسجيل إجازة": "#60a5fa",
            "🏖️ إلغاء إجازة":"#93c5fd", "👤 إضافة شخص":   "#4ade80",
            "🗑️ حذف شخص":    "#f87171", "✏️ تغيير اسم":   "#a78bfa",
            "⚙️ تغيير إعداد":"#fbbf24", "⚙️ إعداد جديد":  "#fbbf24",
        }
        for entry in log_data:
            bg    = type_colors.get(entry.get("type",""), "#1a1e2e")
            color = type_text_colors.get(entry.get("type",""), "#e0e6ff")
            month_badge = f'<span style="background:#1a237e;color:#90caf9;border-radius:10px;padding:2px 10px;font-size:0.8rem;margin-right:8px;">{entry.get("month","")}</span>' if entry.get("month") else ""
            st.markdown(f"""
<div style="background:{bg};border-radius:10px;padding:12px 18px;
            margin-bottom:8px;direction:rtl;border:1px solid #2a2f45;">
    <div style="display:flex;justify-content:space-between;align-items:center;">
        <span style="color:{color};font-weight:700;font-size:0.95rem;">{entry.get("type","")}</span>
        <span style="color:#8892b0;font-size:0.8rem;">🕐 {entry.get("datetime","")}</span>
    </div>
    <div style="color:#c8cfd8;margin-top:6px;font-size:0.9rem;">
        {month_badge}{entry.get("details","")}
    </div>
</div>""", unsafe_allow_html=True)
    else:
        st.info("لا توجد أحداث مسجلة بعد.")

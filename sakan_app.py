import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime, date, timedelta
import calendar
from PIL import Image
import io

# ─────────────────────────────────────────────
#  إعدادات الصفحة
# ─────────────────────────────────────────────
st.set_page_config(page_title="تنظيم السكن", page_icon="🏠", layout="wide",
                   initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;800&display=swap');
html,body,[class*="css"]{font-family:'Tajawal',sans-serif!important;direction:rtl}
.main{background:#0f1117}
.stat-card{background:linear-gradient(135deg,#1e2130,#252840);border:1px solid #2e3250;
  border-radius:16px;padding:20px;text-align:center;margin-bottom:16px;
  box-shadow:0 4px 20px rgba(0,0,0,.3)}
.stat-card .value{font-size:1.8rem;font-weight:800;color:#fff}
.stat-card .label{font-size:.85rem;color:#8892b0;margin-top:4px}
.person-row{display:flex;align-items:center;justify-content:space-between;
  background:#1a1e2e;border:1px solid #2a2f45;border-radius:12px;
  padding:14px 20px;margin-bottom:10px;direction:rtl}
.person-name{font-weight:700;font-size:1rem;color:#e0e6ff}
.person-paid{font-size:.85rem;color:#7ecfb3}
.badge-green{background:#0d3b2e;color:#4ade80;border:1px solid #166534;border-radius:20px;padding:4px 14px;font-weight:700;font-size:.85rem}
.badge-red{background:#3b0d0d;color:#f87171;border:1px solid #991b1b;border-radius:20px;padding:4px 14px;font-weight:700;font-size:.85rem}
.badge-vacation{background:#1a2e3b;color:#60a5fa;border:1px solid #1d4ed8;border-radius:20px;padding:4px 14px;font-weight:700;font-size:.85rem}
.badge-zero{background:#2a2a2a;color:#aaa;border:1px solid #444;border-radius:20px;padding:4px 14px;font-weight:700;font-size:.85rem}
.whatsapp-box{background:#0a1a0f;border:1px solid #166534;border-radius:12px;padding:20px;
  font-family:'Tajawal',monospace;white-space:pre-wrap;color:#4ade80;font-size:.95rem;direction:rtl}
.app-header{background:linear-gradient(135deg,#1a237e,#283593 50%,#1565c0);
  border-radius:20px;padding:30px;text-align:center;margin-bottom:30px;
  box-shadow:0 8px 32px rgba(26,35,126,.4)}
.app-header h1{color:#fff;font-size:2rem;font-weight:800;margin:0}
.app-header p{color:#90caf9;margin:8px 0 0;font-size:.95rem}
.stTabs [data-baseweb="tab-list"]{gap:8px}
.stTabs [data-baseweb="tab"]{background:#1a1e2e;border-radius:10px;border:1px solid #2e3250;
  color:#8892b0;font-family:'Tajawal',sans-serif;font-weight:600}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,#1a237e,#1565c0)!important;
  color:#fff!important;border-color:#1565c0!important}
.vacation-notice{background:#0d1f3c;border:1px solid #1d4ed8;border-right:4px solid #60a5fa;
  border-radius:10px;padding:12px 16px;color:#93c5fd;font-size:.9rem;margin-bottom:8px}
.info-box{background:#0d1f3c;border:1px solid #1d4ed8;border-radius:10px;
  padding:14px 18px;color:#93c5fd;margin-bottom:20px}
.rule-box{background:#1a1a0d;border:1px solid #854d0e;border-radius:10px;
  padding:14px 18px;color:#fde047;margin-bottom:20px;font-size:.9rem}
.exempt-badge{background:#2a1a0d;color:#fbbf24;border:1px solid #854d0e;
  border-radius:20px;padding:3px 12px;font-size:.8rem;font-weight:700}
.next-badge{background:#0d3b2e;color:#4ade80;border:1px solid #166534;
  border-radius:20px;padding:3px 12px;font-size:.8rem;font-weight:700}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  الثوابت
# ─────────────────────────────────────────────
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1g0VfbnUVwNXjV0c2BFlmlX3RSh5eZnpzLUrzwLeqG2I/export?format=csv&gid=0"
SCRIPT_URL    = "https://script.google.com/macros/s/AKfycbx8d9YH9c2LgvOR_OGw9wDFDGqE0pLHojPmv139wdRnbNHtML-AlBjW2BLtT7JFXxTI/exec"
MONTHS_AR = {"January":"يناير","February":"فبراير","March":"مارس","April":"أبريل",
             "May":"مايو","June":"يونيو","July":"يوليو","August":"أغسطس",
             "September":"سبتمبر","October":"أكتوبر","November":"نوفمبر","December":"ديسمبر"}
DAYS_AR = ["الاثنين","الثلاثاء","الأربعاء","الخميس","الجمعة","السبت","الأحد"]

# ─────────────────────────────────────────────
#  واتساب – Green API
# ─────────────────────────────────────────────
def _wa_cfg():
    try:
        return {"instance": st.secrets["GREEN_API_INSTANCE"],
                "token":    st.secrets["GREEN_API_TOKEN"],
                "chat_id":  st.secrets["GREEN_API_CHAT_ID"]}
    except Exception:
        return None

def send_whatsapp(msg: str) -> bool:
    cfg = _wa_cfg()
    if not cfg:
        return False
    try:
        url  = f"https://api.green-api.com/waInstance{cfg['instance']}/sendMessage/{cfg['token']}"
        resp = requests.post(url, json={"chatId": cfg["chat_id"], "message": msg}, timeout=15)
        return resp.status_code == 200
    except Exception:
        return False

def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def wa_expense_add(name, amount, note, month):
    send_whatsapp("🏠 *تنظيم السكن*\n➕ مصروف جديد\n"
                  f"👤 {name}  |  💰 {float(amount):.3f}\n📝 {note}  |  📅 {month}\n🕐 {_now()}")

def wa_expense_edit(amount, note):
    send_whatsapp("🏠 *تنظيم السكن*\n✏️ تعديل مصروف\n"
                  f"💰 المبلغ الجديد: {float(amount):.3f}  |  📝 {note}\n🕐 {_now()}")

def wa_expense_delete(row_id):
    send_whatsapp(f"🏠 *تنظيم السكن*\n🗑️ حذف مصروف\n🔑 {row_id}\n🕐 {_now()}")

def wa_vacation(name, vtype, month):
    vt = {"full":"إجازة كاملة 🏖️","from_start":"غياب من أول الشهر 🗓️",
          "from_date":"إجازة من تاريخ 📅","deduct":"خصم مبلغ ➖","none":"إلغاء الإجازة ✅"}.get(vtype, vtype)
    send_whatsapp(f"🏠 *تنظيم السكن*\n🏖️ تحديث إجازة\n👤 {name}  |  {vt}\n📅 {month}\n🕐 {_now()}")

def wa_cleaning(cleaner_second, cleaner_first, clean_date, next_second, next_first, note=""):
    note_line = f"📝 {note}\n" if note else ""
    send_whatsapp("🏠 *تنظيم السكن*\n🧹 تسجيل دور التنظيف\n"
                  f"🔵 {cleaner_second} (أسبوعه الثاني)\n"
                  f"🟢 {cleaner_first} (أسبوعه الأول)\n"
                  f"📅 الجمعة {clean_date}\n"
                  f"{note_line}"
                  f"🔜 الدور القادم:\n"
                  f"   🔵 {next_second} (ثانيه)  +  🟢 {next_first} (أوله)\n"
                  f"🕐 {_now()}")

def wa_gas(filler, next_person):
    send_whatsapp("🏠 *تنظيم السكن*\n🔵 ملء الأنبوبة\n"
                  f"👤 ملأ: *{filler}*\n🔜 الدور القادم: *{next_person}*\n🕐 {_now()}")

def wa_person_add(name):
    send_whatsapp(f"🏠 *تنظيم السكن*\n👤 إضافة شخص جديد: *{name}*\n🕐 {_now()}")

def wa_person_delete(name):
    send_whatsapp(f"🏠 *تنظيم السكن*\n🗑️ حذف شخص: *{name}*\n🕐 {_now()}")

def wa_person_rename(old, new):
    send_whatsapp(f"🏠 *تنظيم السكن*\n✏️ تغيير اسم\n📛 {old} ← *{new}*\n🕐 {_now()}")

def wa_rent(amount):
    send_whatsapp(f"🏠 *تنظيم السكن*\n🏠 تغيير الإيجار\n💰 الإيجار الجديد: *{float(amount):.3f}*\n🕐 {_now()}")

def wa_exemption(name, service, action):
    svc = "التنظيف 🧹" if service == "cleaning" else "الأنبوبة 🔵"
    act = "إعفاء 🚫" if action == "add" else "إلغاء إعفاء ✅"
    send_whatsapp(f"🏠 *تنظيم السكن*\n⚙️ {act} من {svc}\n👤 {name}\n🕐 {_now()}")

# ─────────────────────────────────────────────
#  دوال التحميل
# ─────────────────────────────────────────────
@st.cache_data(ttl=120)
def load_persons():
    try:
        data = requests.get(SCRIPT_URL + "?type=persons", timeout=10).json()
        return sorted([d["name"] for d in data],
                      key=lambda x: next((d["order"] for d in data if d["name"]==x), 99))
    except:
        return []

def load_settings():
    try:
        return requests.get(SCRIPT_URL + "?type=settings", timeout=10).json()
    except:
        return {}

@st.cache_data(ttl=60)
def load_vacations_from_sheet():
    try:
        data = requests.get(SCRIPT_URL + "?type=vacations", timeout=10).json()
        result = {}
        for row in data:
            m, n = row["month"], row["name"]
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
        df = pd.read_csv(f"{SHEET_CSV_URL}&cb={datetime.now().timestamp()}")
        df["_row"]   = range(2, len(df)+2)
        df["_rowId"] = (df["الشهر"].astype(str)+"|"+df["الاسم"].astype(str)+"|"+
                        df["المبلغ"].astype(str)+"|"+df["التاريخ"].astype(str))
        return df
    except:
        return pd.DataFrame(columns=["الشهر","الاسم","المبلغ","البيان","التاريخ","الصورة","_row","_rowId"])

@st.cache_data(ttl=60)
def load_cleaning_cached():
    try:
        return requests.get(SCRIPT_URL + "?type=cleaning", timeout=15).json()
    except:
        return []

@st.cache_data(ttl=60)
def load_gas_cached():
    try:
        return requests.get(SCRIPT_URL + "?type=gas", timeout=15).json()
    except:
        return []

@st.cache_data(ttl=60)
def load_exemptions_cached():
    try:
        return requests.get(SCRIPT_URL + "?type=exemptions", timeout=10).json()
    except:
        return {}

def load_log():
    try:
        return requests.get(SCRIPT_URL + "?type=log", timeout=10).json()
    except:
        return []

def call_script(payload):
    try:
        return requests.post(SCRIPT_URL, data=payload, timeout=30).text
    except Exception as e:
        return f"Error: {e}"

def clear_all_cache():
    st.cache_data.clear()
    for k in ["gas_log", "cleaning_log"]:
        st.session_state.pop(k, None)

# ─────────────────────────────────────────────
#  منطق الخدمات
# ─────────────────────────────────────────────
def get_active_persons(persons, month_vacations, exemptions=None):
    exempt_set = set(exemptions or [])
    return [p for p in persons
            if month_vacations.get(p, {}).get("type") != "full"
            and p not in exempt_set]

def get_next_gas(log, active):
    if not active: return None
    if not log: return active[0]
    last = log[0].get("filler","")
    if last in active:
        return active[(active.index(last) + 1) % len(active)]
    return active[0]

def build_weekly_schedule(active):
    """
    النظام: أسبوع k:
      p_second = active[k % n]      ← عليه أسبوعه الثاني
      p_first  = active[(k+1) % n]  ← عليه أسبوعه الأول
    مثال 4 أشخاص (أ،ب،ج،د):
      أسبوع1: أ(ثانيه)+ب(أوله) | أسبوع2: ب(ثانيه)+ج(أوله)
      أسبوع3: ج(ثانيه)+د(أوله) | أسبوع4: د(ثانيه)+أ(أوله)
    """
    n = len(active)
    if n == 0: return []
    if n == 1: return [{"week_idx":0,"p_second":active[0],"p_first":None}]
    return [{"week_idx":k,
             "p_second": active[k % n],
             "p_first":  active[(k+1) % n]}
            for k in range(n)]

def get_next_cleaning_week(log, active):
    """
    يقرأ nextPair المحفوظ في السجل (p_second،p_first) ويبحث عنه في الجدول.
    إذا لم يوجد → الأسبوع الأول من الجدول.
    """
    schedule = build_weekly_schedule(active)
    if not schedule: return None
    if not log:      return schedule[0]

    last_next = log[0].get("nextPair","").strip()
    if last_next:
        parts    = [x.strip() for x in last_next.split("،") if x.strip()]
        p_second = parts[0] if len(parts) > 0 else None
        p_first  = parts[1] if len(parts) > 1 else None
        for w in schedule:
            if w["p_second"] == p_second and w["p_first"] == p_first:
                return w
        return {"week_idx":-1, "p_second":p_second, "p_first":p_first}

    last_cleaners = sorted([x.strip() for x in log[0].get("cleaner","").split("،") if x.strip()])
    for idx, w in enumerate(schedule):
        if sorted([x for x in [w["p_second"], w["p_first"]] if x]) == last_cleaners:
            return schedule[(idx+1) % len(schedule)]
    return schedule[0]

def build_rotation_table(all_persons, month_vacations, cleaning_exempt, log, weeks_ahead=10):
    """
    يبني جدول الجمع القادمة بذكاء:
    - من في إجازة كاملة أو معفى → يُتخطى ويحل مكانه التالي المتاح.
    - الدورة تستمر بلا توقف (تعود من الأول بعد الأخير).
    - كل أسبوع: p_second (ثانيه) + p_first (أوله).
    """
    from datetime import timedelta
    n = len(all_persons)
    if n == 0:
        return []

    def is_avail(person):
        if month_vacations.get(person,{}).get("type") == "full": return False
        if person in cleaning_exempt: return False
        return True

    def p_status(person):
        if not person: return "none"
        if month_vacations.get(person,{}).get("type") == "full": return "vacation"
        if person in cleaning_exempt: return "exempt"
        return "active"

    def next_avail(start_idx, skip=None):
        for offset in range(n):
            idx = (start_idx + offset) % n
            p   = all_persons[idx]
            if p == skip: continue
            if is_avail(p): return idx, p
        return None, None

    def skipped_between(from_idx, to_idx, skip=None):
        skipped = []
        steps = (to_idx - from_idx) % n
        for offset in range(steps):
            p = all_persons[(from_idx + offset) % n]
            if p != skip: skipped.append(p)
        return skipped

    # ── نقطة البداية من السجل ──
    last_next = log[0].get("nextPair","").strip() if log else ""
    if last_next:
        parts = [x.strip() for x in last_next.split("،") if x.strip()]
        p_sec_start = parts[0] if parts else None
        start_second_idx = all_persons.index(p_sec_start) if p_sec_start and p_sec_start in all_persons else 0
    else:
        start_second_idx = 0

    today       = date.today()
    days_to_fri = (4 - today.weekday()) % 7
    if days_to_fri == 0: days_to_fri = 7
    next_fri = today + timedelta(days=days_to_fri)

    rows = []
    cur_sec_idx = start_second_idx

    for i in range(weeks_ahead):
        fri = next_fri + timedelta(weeks=i)

        sec_idx, p_sec = next_avail(cur_sec_idx)
        if sec_idx is None:
            rows.append({"friday":fri,"fri_str":fri.strftime("%d/%m/%Y"),
                         "p_second":"—","p_first":"—",
                         "sec_status":"none","fir_status":"none",
                         "is_current":(i==0),"sec_skipped":[],"fir_skipped":[]})
            continue

        fir_idx, p_fir = next_avail((sec_idx+1)%n, skip=p_sec)

        sec_skipped = skipped_between(cur_sec_idx, sec_idx)
        fir_skipped = skipped_between((sec_idx+1)%n, fir_idx if fir_idx is not None else (sec_idx+1)%n, skip=p_sec) if fir_idx is not None else []

        rows.append({
            "friday":      fri,
            "fri_str":     fri.strftime("%d/%m/%Y"),
            "p_second":    p_sec or "—",
            "p_first":     p_fir or "—",
            "sec_status":  p_status(p_sec),
            "fir_status":  p_status(p_fir),
            "is_current":  (i == 0),
            "sec_skipped": sec_skipped,
            "fir_skipped": fir_skipped,
        })

        cur_sec_idx = (sec_idx + 1) % n

    return rows

# ─────────────────────────────────────────────
#  العنوان
# ─────────────────────────────────────────────
st.markdown("""
<div class="app-header">
  <h1>🏠 تنظيم السكن</h1>
  <p>إعداد أبو زين • تتبع وتوزيع المصاريف وتوزيع الأدوار بدقة وشفافية</p>
</div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  تحميل البيانات الأساسية
# ─────────────────────────────────────────────
SHABAB          = load_persons()
all_data        = load_data()
sheet_vacations = load_vacations_from_sheet()
sheet_settings  = load_settings()

# ── حفظ الإجازات في session_state لتفادي ضياعها عند refresh ──
if "vacations" not in st.session_state or not st.session_state.vacations:
    st.session_state.vacations = sheet_vacations.copy()
# مزامنة: أضف أي شهر جديد من الـ sheet
for m, v in sheet_vacations.items():
    if m not in st.session_state.vacations:
        st.session_state.vacations[m] = v

# ── حفظ سجلات الخدمات في session_state ──
if "cleaning_log" not in st.session_state:
    st.session_state.cleaning_log = load_cleaning_cached()
if "gas_log" not in st.session_state:
    st.session_state.gas_log = load_gas_cached()

cleaning_log = st.session_state.cleaning_log
gas_log      = st.session_state.gas_log

# ─────────────────────────────────────────────
#  شريط الإعدادات العلوي
# ─────────────────────────────────────────────
current_date  = datetime.now()
month_opts_ar = [f"{m:02d} – {MONTHS_AR[datetime(2026,m,1).strftime('%B')]} 2026" for m in range(1,13)]

c1,c2,c3,c4,c5 = st.columns([2,1,1,1,1])
with c1:
    selected_month_ar = st.selectbox("📅 الشهر", month_opts_ar, index=current_date.month-1)
with c2:
    month_idx     = month_opts_ar.index(selected_month_ar)
    sel_month     = month_idx + 1
    sel_year      = 2026
    days_in_month = calendar.monthrange(sel_year, sel_month)[1]
    st.metric("📆 أيام الشهر", days_in_month)
with c3:
    _sheet_rent = float(sheet_settings.get("total_rent", 0.0))
    total_rent_input = st.number_input("🏠 إجمالي الإيجار", min_value=0.0,
                                       value=_sheet_rent, format="%.3f")
with c4:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("💾 حفظ الإيجار", type="primary", use_container_width=True):
        res = call_script({"action":"saveSetting","key":"total_rent","value":str(total_rent_input)})
        if "Success" in res:
            wa_rent(total_rent_input)
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

st.markdown("""<div class="rule-box">
⚠️ <b>قاعدة التوزيع:</b>
الإيجار يُقسَّم بالتساوي على <b>جميع الأشخاص</b> حتى من في إجازة. |
المصاريف المشتركة تُوزَّع على <b>المتواجدين فقط</b> حسب نسبة حضورهم.
</div>""", unsafe_allow_html=True)
st.divider()

# ─────────────────────────────────────────────
#  الإجازات والحسابات
# ─────────────────────────────────────────────
month_vacations = st.session_state.vacations.get(selected_month_ar, {})

def calc_expense_ratio(vac_info, dim, sy, sm):
    vtype = vac_info.get("type","none")
    if vtype == "full": return 0.0
    elif vtype == "from_start":
        absent = min(int(vac_info.get("days",0)), dim)
        return max(0.0, (dim-absent)/dim)
    elif vtype == "from_date":
        vd = vac_info.get("date")
        if vd:
            present = max(0,(vd-date(sy,sm,1)).days)
            return min(present,dim)/dim
        return 1.0
    elif vtype == "deduct": return 1.0
    return 1.0

_raw = all_data[all_data["الشهر"]==selected_month_ar] if not all_data.empty else pd.DataFrame()
month_df = _raw[pd.to_numeric(_raw["المبلغ"],errors='coerce').fillna(0)>0].copy() if not _raw.empty else pd.DataFrame()
total_extra = pd.to_numeric(month_df["المبلغ"],errors='coerce').sum() if not month_df.empty else 0.0

expense_ratios = {}; deduct_map = {}; total_ratio = 0.0
for person in SHABAB:
    vac = month_vacations.get(person,{})
    r   = calc_expense_ratio(vac, days_in_month, sel_year, sel_month)
    expense_ratios[person] = r; total_ratio += r
    deduct_map[person] = float(vac.get("deduct_amount",0)) if vac.get("type")=="deduct" else 0.0

rent_per_person = total_rent_input/len(SHABAB) if SHABAB else 0.0

def get_expense_share(person):
    if total_ratio==0: return 0.0
    vac = month_vacations.get(person,{})
    if vac.get("type")=="deduct":
        return max(0.0,(expense_ratios[person]/total_ratio)*total_extra - deduct_map[person])
    return (expense_ratios[person]/total_ratio)*total_extra

summary = []
for person in SHABAB:
    paid      = pd.to_numeric(month_df[month_df["الاسم"]==person]["المبلغ"],errors='coerce').sum() if not month_df.empty else 0.0
    exp_share = get_expense_share(person)
    total_due = exp_share + rent_per_person
    vac       = month_vacations.get(person,{})
    summary.append({"الاسم":person,"مدفوع":paid,"حصة_مصاريف":exp_share,"إيجار":rent_per_person,
                    "المستحق":total_due,"الرصيد":paid-total_due,
                    "إجازة":vac.get("type","none"),"النسبة":expense_ratios[person]})

active_count = sum(1 for p in SHABAB if expense_ratios[p]>0)

if not SHABAB:
    st.warning("⚠️ لا يوجد أشخاص مسجلون. اذهب إلى تبويب **⚙️ إدارة الأشخاص**.")

# ─────────────────────────────────────────────
#  المعفيون والأشخاص المتاحون
# ─────────────────────────────────────────────
exemptions_data = load_exemptions_cached()
cleaning_exempt = set(exemptions_data.get("cleaning",[]))
gas_exempt      = set(exemptions_data.get("gas",[]))

active_for_cleaning = get_active_persons(SHABAB, month_vacations, cleaning_exempt)
active_for_gas      = get_active_persons(SHABAB, month_vacations, gas_exempt)

# ─────────────────────────────────────────────
#  حساب الدورين الحالي والقادم
# ─────────────────────────────────────────────
next_gas_person  = get_next_gas(gas_log, active_for_gas)
next_clean_week  = get_next_cleaning_week(cleaning_log, active_for_cleaning)

# ── البطاقات العلوية ──
# التنظيف: p_second = عليه ثانيه  |  p_first = عليه أوله
if SHABAB:
    al1, al2 = st.columns(2)
    with al1:
        if next_clean_week:
            _sec  = next_clean_week.get("p_second","—")
            _fir  = next_clean_week.get("p_first","")
            _disp = f"{_sec} و {_fir}" if _fir else _sec
            _sub  = f"🔵 {_sec} (ثانيه)  |  🟢 {_fir} (أوله)" if _fir else f"🔵 {_sec} (ثانيه)"
        else:
            _disp = "—"; _sub = ""
        st.markdown(f"""
<div style="background:linear-gradient(135deg,#0d3b2e,#1a4a38);border:2px solid #4ade80;
     border-radius:14px;padding:14px 20px;margin-bottom:10px;">
  <div style="color:#86efac;font-size:.8rem;margin-bottom:2px;">🧹 دور التنظيف هذا الأسبوع</div>
  <div style="color:#4ade80;font-size:1.4rem;font-weight:800;">{_disp}</div>
  <div style="color:#6ee7b7;font-size:.8rem;margin-top:2px;">{_sub}</div>
</div>""", unsafe_allow_html=True)
    with al2:
        _gname = next_gas_person or "—"
        st.markdown(f"""
<div style="background:linear-gradient(135deg,#0d1f3c,#1a2e4a);border:2px solid #60a5fa;
     border-radius:14px;padding:14px 20px;margin-bottom:10px;">
  <div style="color:#93c5fd;font-size:.8rem;margin-bottom:2px;">🔵 دور ملء الأنبوبة</div>
  <div style="color:#60a5fa;font-size:1.4rem;font-weight:800;">{_gname}</div>
  <div style="color:#7dd3fc;font-size:.8rem;margin-top:2px;">عليه الدور القادم</div>
</div>""", unsafe_allow_html=True)
    st.divider()

# ─────────────────────────────────────────────
#  التبويبات
# ─────────────────────────────────────────────
tab1,tab2,tab3,tab4,tab5,tab6,tab7 = st.tabs([
    "📊 الملخص","➕ إضافة مصروف","📜 سجل المصاريف",
    "🏠 خدمات الشقة","🏖️ الإجازات","⚙️ إدارة الأشخاص","📋 سجل الأحداث"])

# ══════════════════════════════════════════════
#  ١: الملخص
# ══════════════════════════════════════════════
with tab1:
    if not SHABAB:
        st.info("أضف أشخاصاً أولاً.")
    else:
        s1,s2,s3,s4,s5 = st.columns(5)
        s1.markdown(f'<div class="stat-card"><div class="value">{total_extra:.3f}</div><div class="label">💰 إجمالي المصاريف</div></div>',unsafe_allow_html=True)
        s2.markdown(f'<div class="stat-card"><div class="value">{total_rent_input:.3f}</div><div class="label">🏠 إجمالي الإيجار</div></div>',unsafe_allow_html=True)
        s3.markdown(f'<div class="stat-card"><div class="value">{rent_per_person:.3f}</div><div class="label">👤 إيجار الفرد</div></div>',unsafe_allow_html=True)
        s4.markdown(f'<div class="stat-card"><div class="value">{total_extra+total_rent_input:.3f}</div><div class="label">📊 الإجمالي الكلي</div></div>',unsafe_allow_html=True)
        s5.markdown(f'<div class="stat-card"><div class="value">{active_count}/{len(SHABAB)}</div><div class="label">👥 المتواجدون</div></div>',unsafe_allow_html=True)

        st.markdown("### 👥 وضع كل شخص")
        for row in summary:
            bal=row["الرصيد"]; vtype=row["إجازة"]
            if vtype and vtype!="none":
                vl={"full":"🏖️ إجازة كاملة","from_start":f"🗓️ مصاريف {row['النسبة']*100:.0f}%",
                    "from_date":f"📅 مصاريف {row['النسبة']*100:.0f}%","deduct":"➖ خصم"}.get(vtype,"")
                badge=f'<span class="badge-vacation">{vl} + إيجار كامل</span>'
            elif abs(bal)<0.01: badge='<span class="badge-zero">➖ صفر</span>'
            elif bal>0:         badge=f'<span class="badge-green">🟢 له {bal:.3f}</span>'
            else:               badge=f'<span class="badge-red">🔴 عليه {abs(bal):.3f}</span>'
            details=f"دفع: {row['مدفوع']:.3f} | مصاريف: {row['حصة_مصاريف']:.3f} | إيجار: {row['إيجار']:.3f} | المستحق: {row['المستحق']:.3f}"
            st.markdown(f'<div class="person-row"><span class="person-name">{row["الاسم"]}</span><span class="person-paid">{details}</span>{badge}</div>',unsafe_allow_html=True)

        st.markdown("### 📱 تقرير الواتساب")
        lines=[f"*تقرير مصاريف السكن – {selected_month_ar}*",
               f"🏠 الإيجار الكلي: {total_rent_input:.3f} (على كل فرد: {rent_per_person:.3f})",
               f"💰 إجمالي المصاريف: {total_extra:.3f}",
               f"📊 الإجمالي الكلي: {total_extra+total_rent_input:.3f}","─────────────────"]
        for row in summary:
            bal=row["الرصيد"]; vtype=row["إجازة"]
            status="له 🟢" if bal>0 else ("عليه 🔴" if bal<0 else "صفر ➖")
            note="" 
            if vtype=="full": note=" (إجازة)"
            elif vtype in("from_start","from_date"): note=f" (مصاريف {row['النسبة']*100:.0f}%)"
            elif vtype=="deduct": note=" (خصم)"
            lines.append(f"• {row['الاسم']}{note}: {status} *{abs(bal):.3f}*")
        report_text="\n".join(lines)
        st.markdown(f'<div class="whatsapp-box">{report_text}</div>',unsafe_allow_html=True)
        st.button("📋 نسخ التقرير",help="انسخ النص أعلاه يدوياً")

# ══════════════════════════════════════════════
#  ٢: إضافة مصروف
# ══════════════════════════════════════════════
with tab2:
    if not SHABAB:
        st.info("أضف أشخاصاً أولاً.")
    else:
        col_form,col_recent = st.columns([1,1])
        with col_form:
            st.subheader("➕ تسجيل مصروف جديد")
            with st.form("add_form", clear_on_submit=True):
                name         = st.selectbox("من دفع؟", SHABAB)
                amount       = st.number_input("المبلغ", min_value=0.0, step=0.1, format="%.3f")
                note         = st.text_input("البيان", placeholder="مثال: شاي، سكر…")
                expense_date = st.date_input("التاريخ", value=date.today())
                uploaded_img = st.file_uploader("📸 صورة الفاتورة (اختياري)", type=["png","jpg","jpeg"])
                if st.form_submit_button("✅ تسجيل", use_container_width=True):
                    if amount>0:
                        img_b64,img_name="",""
                        if uploaded_img:
                            img_name=uploaded_img.name
                            try:
                                img=Image.open(uploaded_img)
                                if img.mode in("RGBA","P"): img=img.convert("RGB")
                                img.thumbnail((800,800))
                                buf=io.BytesIO(); img.save(buf,format="JPEG",quality=70)
                                img_b64=base64.b64encode(buf.getvalue()).decode()
                            except Exception as ex:
                                st.error(f"خطأ في الصورة: {ex}")
                        with st.spinner("جاري الحفظ…"):
                            res=call_script({"action":"addExpense","month":selected_month_ar,"name":name,
                                             "amount":amount,"note":note,"date":str(expense_date),
                                             "imgData":img_b64,"imgName":img_name})
                        if "Success" in res:
                            wa_expense_add(name,amount,note,selected_month_ar)
                            st.success("✅ تم التسجيل!"); st.balloons()
                            st.cache_data.clear(); st.rerun()
                        else:
                            st.error(f"رد الخادم: {res}")
                    else:
                        st.warning("⚠️ أدخل مبلغاً صحيحاً.")
        with col_recent:
            st.subheader("🕐 آخر المصاريف")
            if not month_df.empty:
                for _,row in month_df.tail(6).iloc[::-1].iterrows():
                    st.info(f"**{row['الاسم']}** | {float(row['المبلغ']):.3f} | {row['البيان']}")
            else:
                st.info("لا توجد مصاريف بعد.")

# ══════════════════════════════════════════════
#  ٣: سجل المصاريف
# ══════════════════════════════════════════════
with tab3:
    st.subheader(f"📜 سجل مصاريف {selected_month_ar}")
    filter_name=st.selectbox("فلتر باسم",["الكل"]+SHABAB,key="filter_name")
    display_df=month_df.copy() if not month_df.empty else pd.DataFrame()
    if filter_name!="الكل" and not display_df.empty:
        display_df=display_df[display_df["الاسم"]==filter_name]
    if not display_df.empty:
        st.metric("إجمالي المبالغ المعروضة",f"{pd.to_numeric(display_df['المبلغ'],errors='coerce').sum():.3f}")
        for idx,row in display_df.iloc[::-1].iterrows():
            amount_val=float(row["المبلغ"]) if pd.notna(row["المبلغ"]) else 0.0
            row_num=int(row["_row"]) if "_row" in row else None
            row_id=str(row["_rowId"]) if "_rowId" in row else ""
            with st.expander(f"📌 {row['الاسم']}  |  {amount_val:.3f}  |  {row['البيان']}"):
                ca,cb=st.columns(2)
                ca.write(f"**التاريخ:** {row['التاريخ']}")
                ca.write(f"**الشهر:** {row['الشهر']}")
                img_link=str(row['الصورة']).strip()
                if img_link.startswith("http"): cb.link_button("🖼️ فتح صورة الفاتورة",img_link)
                else: cb.caption("⚠️ لا توجد صورة")
                if row_num:
                    st.markdown("---")
                    ec1,ec2=st.columns(2)
                    with ec1:
                        st.markdown("**✏️ تعديل**")
                        na=st.number_input("المبلغ الجديد",value=amount_val,format="%.3f",key=f"ea_{idx}")
                        nn=st.text_input("البيان الجديد",value=str(row['البيان']),key=f"en_{idx}")
                        nd=st.text_input("التاريخ الجديد",value=str(row['التاريخ']),key=f"ed_{idx}")
                        if st.button("💾 حفظ التعديل",key=f"se_{idx}"):
                            with st.spinner("تعديل…"):
                                res=call_script({"action":"editExpense","row":row_num,"rowId":row_id,
                                                 "amount":na,"note":nn,"date":nd})
                            if "Success" in res:
                                wa_expense_edit(na,nn)
                                st.success("✅ تم التعديل!")
                                st.cache_data.clear(); st.rerun()
                            else: st.error(res)
                    with ec2:
                        st.markdown("**🗑️ حذف**")
                        st.warning("لا يمكن التراجع عن الحذف!")
                        if st.button("🗑️ حذف",key=f"dl_{idx}",type="primary"):
                            with st.spinner("حذف…"):
                                res=call_script({"action":"deleteExpense","row":row_num,"rowId":row_id})
                            if "Success" in res:
                                wa_expense_delete(row_id)
                                st.success("✅ تم الحذف!")
                                st.cache_data.clear(); st.rerun()
                            else: st.error(res)
    else:
        st.info("لا توجد مصاريف مسجلة لهذا الشهر.")
    if not month_df.empty:
        st.divider()
        st.markdown("**📊 إجماليات كل شخص:**")
        cols=st.columns(3)
        for i,person in enumerate(SHABAB):
            total_p=pd.to_numeric(month_df[month_df["الاسم"]==person]["المبلغ"],errors='coerce').sum()
            cols[i%3].metric(person,f"{total_p:.3f}")

# ══════════════════════════════════════════════
#  ٤: خدمات الشقة
# ══════════════════════════════════════════════
with tab4:
    st.subheader("🏠 خدمات الشقة")
    svc_tab1,svc_tab2,svc_tab3 = st.tabs(["🧹 تنظيف الشقة","🔵 ملء الأنبوبة","🚫 إدارة الإعفاءات"])

    # ────────── التنظيف ──────────
    with svc_tab1:
        st.markdown("""<div class="info-box">
🧹 <b>نظام دور التنظيف:</b> كل جمعة شخصان ينظفان معاً.<br>
• 🔵 الأول عليه <b>أسبوعه الثاني</b>  |  🟢 الثاني عليه <b>أسبوعه الأول</b>.<br>
• الترتيب: أ(ثانيه)+ب(أوله) ← ب(ثانيه)+ج(أوله) ← ج(ثانيه)+د(أوله) ...<br>
• من في <b>إجازة كاملة أو معفى</b> يُستثنى تلقائياً.
</div>""", unsafe_allow_html=True)

        if not SHABAB:
            st.info("أضف أشخاصاً أولاً.")
        else:
            # حالة الأشخاص
            st.markdown("#### 👥 حالة الأشخاص")
            pc = st.columns(min(len(SHABAB),4))
            for i,person in enumerate(SHABAB):
                vac=month_vacations.get(person,{})
                is_vac=vac.get("type")=="full"
                is_ex=person in cleaning_exempt
                is_act=person in active_for_cleaning
                badge=('<span class="exempt-badge">🏖️ إجازة</span>' if is_vac else
                       '<span class="exempt-badge">🚫 معفى</span>' if is_ex else
                       '<span class="next-badge">✅ متاح</span>')
                with pc[i%len(pc)]:
                    st.markdown(f"""<div style="background:#1a1e2e;border:1px solid {'#4ade80' if is_act else '#3b0d1a'};
border-radius:10px;padding:10px;text-align:center;margin-bottom:8px;">
<div style="color:{'#4ade80' if is_act else '#8892b0'};font-weight:700;font-size:.9rem;">{person}</div>
<div style="margin-top:4px;">{badge}</div></div>""",unsafe_allow_html=True)

            st.divider()

            # بطاقة الدور الحالي
            cw = next_clean_week
            schedule = build_weekly_schedule(active_for_cleaning)

            if cw:
                _sec = cw.get("p_second","—")
                _fir = cw.get("p_first","")
                _disp = f"{_sec} و {_fir}" if _fir else _sec
                _sub = (f"🔵 {_sec} (أسبوعه الثاني)  |  🟢 {_fir} (أسبوعه الأول)"
                        if _fir else f"🔵 {_sec} (أسبوعه الثاني)")
            else:
                _disp="—"; _sub=""

            st.markdown(f"""<div style="background:linear-gradient(135deg,#0d3b2e,#1a4a38);
border:2px solid #4ade80;border-radius:16px;padding:18px;text-align:center;margin-bottom:16px;">
<div style="color:#86efac;font-size:.85rem;">🧹 دور التنظيف القادم (هذه الجمعة)</div>
<div style="color:#4ade80;font-size:1.8rem;font-weight:800;margin:6px 0;">{_disp}</div>
<div style="color:#6ee7b7;font-size:.82rem;">{_sub}</div>
</div>""",unsafe_allow_html=True)

            # ── جدول الدوران للجمع القادمة ──
            rotation = build_rotation_table(SHABAB, month_vacations, cleaning_exempt, cleaning_log,
                                            weeks_ahead=max(10, len(SHABAB)*2+2))

            if rotation:
                st.markdown("### 🗓️ جدول الدوران – الجمع القادمة")
                st.caption("يتحدث تلقائياً بعد كل تسجيل. 🔵 = أسبوعه الثاني  |  🟢 = أسبوعه الأول")

                # رسم الجدول كـ HTML واحد منسّق
                rows_html = ""
                for r in rotation:
                    is_cur = r["is_current"]
                    bg     = "linear-gradient(135deg,#0d3b2e,#1a4a38)" if is_cur else "#1a1e2e"
                    border = "2px solid #4ade80" if is_cur else "1px solid #2a2f45"
                    icon   = "🧹" if is_cur else ""

                    def _person_html(person, status, turn_icon, bold=False):
                        if not person or person == "—": return f'<span style="color:#555;">{turn_icon} —</span>'
                        if status == "vacation":
                            return f'<span style="color:#fbbf24;font-size:.82rem;">{turn_icon} {person} <small>🏖️إجازة</small></span>'
                        if status == "exempt":
                            return f'<span style="color:#f87171;font-size:.82rem;">{turn_icon} {person} <small>🚫معفى</small></span>'
                        color  = "#60a5fa" if turn_icon == "🔵" else "#4ade80"
                        weight = "800" if bold else "600"
                        size   = ".95rem" if bold else ".85rem"
                        return f'<span style="color:{color};font-weight:{weight};font-size:{size};">{turn_icon} {person}</span>'

                    sec_html = _person_html(r["p_second"], r["sec_status"], "🔵", bold=is_cur)
                    fir_html = _person_html(r["p_first"],  r["fir_status"], "🟢", bold=is_cur)

                    # من تم تخطيه
                    skip_all = r["sec_skipped"] + r["fir_skipped"]
                    skip_html = ""
                    if skip_all:
                        names = "، ".join(skip_all)
                        skip_html = f'<div style="color:#6b7280;font-size:.72rem;margin-top:3px;">⏭️ تخطي: {names}</div>'

                    fri_color = "#4ade80" if is_cur else "#8892b0"
                    cur_label = "<br><small style='color:#86efac;'>← هذه الجمعة 🧹</small>" if is_cur else ""

                    rows_html += f"""
<div style="background:{bg};border:{border};border-radius:12px;
     padding:12px 18px;margin-bottom:8px;direction:rtl;">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
    <div>
      {sec_html}<br>{fir_html}
      {skip_html}
    </div>
    <div style="text-align:left;">
      <span style="color:{fri_color};font-size:.85rem;font-weight:600;">
        📅 الجمعة {r["fri_str"]}{cur_label}
      </span>
    </div>
  </div>
</div>"""

                st.markdown(rows_html, unsafe_allow_html=True)

            # ── نموذج التسجيل بدون clear_on_submit لمنع تبدّل الاختيارات ──
            st.markdown("### ✅ تسجيل دور التنظيف")

            # تاريخ الجمعة القادمة
            today = date.today()
            days_to_fri = (4 - today.weekday()) % 7
            if days_to_fri == 0: days_to_fri = 7
            next_friday = today + timedelta(days=days_to_fri)
            fri_str = f"الجمعة {next_friday.strftime('%d/%m/%Y')}"

            st.markdown(f"**📅 يوم التنظيف: {fri_str}**")

            # اقتراح الدور القادم بعد هذا الأسبوع
            cw_idx_val = cw.get("week_idx",-1) if cw else -1
            if schedule and cw_idx_val >= 0:
                next_w = schedule[(cw_idx_val+1) % len(schedule)]
            elif schedule:
                next_w = schedule[1] if len(schedule)>1 else schedule[0]
            else:
                next_w = None

            sug_next_sec = next_w.get("p_second","") if next_w else ""
            sug_next_fir = next_w.get("p_first","")  if next_w else ""

            # ── اختيار من عليه الثاني (مُقترَح تلقائياً) ──
            st.markdown("**🔵 من عليه أسبوعه الثاني هذه الجمعة؟**")
            clean_second_choice = st.radio(
                "الشخص الأول (أسبوعه الثاني)",
                options=active_for_cleaning,
                index=active_for_cleaning.index(cw.get("p_second","")) if cw and cw.get("p_second","") in active_for_cleaning else 0,
                horizontal=True,
                key="clean_second_radio",
                label_visibility="collapsed"
            )

            # ── اختيار من عليه الأول (مُقترَح تلقائياً) ──
            st.markdown("**🟢 من عليه أسبوعه الأول هذه الجمعة؟**")
            # استثناء من اختير للثاني من قائمة الأول
            first_options = [p for p in active_for_cleaning if p != clean_second_choice]
            sug_first_idx = first_options.index(cw.get("p_first","")) if cw and cw.get("p_first","") in first_options else 0
            clean_first_choice = st.radio(
                "الشخص الثاني (أسبوعه الأول)",
                options=first_options if first_options else active_for_cleaning,
                index=min(sug_first_idx, max(0, len(first_options)-1)),
                horizontal=True,
                key="clean_first_radio",
                label_visibility="collapsed"
            )

            # ── الدور القادم ──
            st.markdown("---")
            st.markdown("**🔜 من عليه الدور القادم؟**")
            col_np1, col_np2 = st.columns(2)
            with col_np1:
                st.markdown("🔵 **أسبوعه الثاني (القادم)**")
                next_sec_opts = active_for_cleaning
                next_sec_idx  = next_sec_opts.index(sug_next_sec) if sug_next_sec in next_sec_opts else 0
                next_second_choice = st.radio(
                    "الدور القادم - ثانيه",
                    options=next_sec_opts,
                    index=next_sec_idx,
                    horizontal=True,
                    key="next_second_radio",
                    label_visibility="collapsed"
                )
            with col_np2:
                st.markdown("🟢 **أسبوعه الأول (القادم)**")
                next_fir_opts = [p for p in active_for_cleaning if p != next_second_choice]
                next_fir_idx  = next_fir_opts.index(sug_next_fir) if sug_next_fir in next_fir_opts else 0
                next_first_choice = st.radio(
                    "الدور القادم - أوله",
                    options=next_fir_opts if next_fir_opts else active_for_cleaning,
                    index=min(next_fir_idx, max(0, len(next_fir_opts)-1)),
                    horizontal=True,
                    key="next_first_radio",
                    label_visibility="collapsed"
                )

            cleaning_note = st.text_input("ملاحظة (اختياري)", placeholder="مثال: تنظيف عميق",
                                          key="cleaning_note_input")

            if st.button("💾 حفظ دور التنظيف", type="primary", use_container_width=True,
                         key="save_cleaning_btn"):
                if clean_second_choice == clean_first_choice:
                    st.warning("⚠️ يجب أن يكون الشخصان مختلفَين.")
                elif next_second_choice == next_first_choice:
                    st.warning("⚠️ الدور القادم: يجب أن يكون الشخصان مختلفَين.")
                else:
                    cleaner_str = f"{clean_second_choice}، {clean_first_choice}"
                    next_str    = f"{next_second_choice}، {next_first_choice}"
                    with st.spinner("جاري الحفظ…"):
                        res = call_script({
                            "action":   "addCleaningEntry",
                            "cleaner":  cleaner_str,
                            "weekFrom": str(next_friday),
                            "weekTo":   str(next_friday),
                            "weekNum":  "1",
                            "nextPair": next_str,
                            "note":     cleaning_note,
                        })
                    if "Success" in res:
                        wa_cleaning(clean_second_choice, clean_first_choice,
                                    next_friday.strftime("%d/%m/%Y"),
                                    next_second_choice, next_first_choice, cleaning_note)
                        st.success(f"✅ تم التسجيل!\n🔜 الدور القادم: 🔵{next_second_choice} + 🟢{next_first_choice}")
                        st.session_state.pop("cleaning_log", None)
                        clear_all_cache()
                        st.rerun()
                    else:
                        st.error(f"خطأ: {res}")

            # سجل التنظيف
            st.markdown("### 📋 سجل التنظيف")
            if cleaning_log:
                for entry in cleaning_log[:15]:
                    np_ = entry.get("nextPair","")
                    note_t = f' | {entry.get("note","")}' if entry.get("note") else ""
                    np_badge = f' | <span style="color:#93c5fd;">القادم: <b>{np_}</b></span>' if np_ else ""
                    st.markdown(f"""<div style="background:#1a1e2e;border:1px solid #2a2f45;
border-radius:10px;padding:11px 16px;margin-bottom:7px;direction:rtl;">
<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;">
  <span style="color:#4ade80;font-weight:700;">🧹 {entry.get("cleaner","")}</span>
  <span style="color:#8892b0;font-size:.82rem;">📅 {entry.get("weekFrom","")}{note_t}{np_badge}</span>
</div></div>""",unsafe_allow_html=True)
            else:
                st.info("لا يوجد سجل تنظيف بعد.")

    # ────────── الأنبوبة ──────────
    with svc_tab2:
        st.markdown("""<div class="info-box">
🔵 <b>نظام ملء الأنبوبة:</b> الدور يدور على المتاحين بالتسلسل.<br>
• من في <b>إجازة كاملة أو معفى</b> يُستثنى تلقائياً.
</div>""",unsafe_allow_html=True)

        if not SHABAB:
            st.info("أضف أشخاصاً أولاً.")
        else:
            # بطاقة الدور
            st.markdown(f"""<div style="background:linear-gradient(135deg,#0d1f3c,#1a2e4a);
border:2px solid #60a5fa;border-radius:16px;padding:18px;text-align:center;margin-bottom:20px;">
<div style="color:#93c5fd;font-size:.85rem;">🔵 دور ملء الأنبوبة القادم</div>
<div style="color:#60a5fa;font-size:1.8rem;font-weight:800;margin:6px 0;">{next_gas_person or "—"}</div>
</div>""",unsafe_allow_html=True)

            # شبكة الأشخاص
            st.markdown("##### 🔄 ترتيب الدور")
            gcols = st.columns(min(len(SHABAB),5))
            for i,person in enumerate(SHABAB):
                is_next=person==next_gas_person
                vac=month_vacations.get(person,{})
                is_vac=vac.get("type")=="full"
                is_ex=person in gas_exempt
                fills=sum(1 for e in gas_log if e.get("filler")==person)
                if is_vac:     slbl="🏖️ إجازة"; bcol="#3b2a0d"; ncol="#8892b0"
                elif is_ex:    slbl="🚫 معفى";  bcol="#3b0d0d"; ncol="#8892b0"
                elif is_next:  slbl="🔵 دوره";  bcol="#60a5fa"; ncol="#60a5fa"
                else:          slbl=f"⏳ {fills}×";bcol="#2a2f45";ncol="#8892b0"
                with gcols[i%len(gcols)]:
                    st.markdown(f"""<div style="background:#1a1e2e;border:1px solid {bcol};
border-radius:10px;padding:10px;text-align:center;margin-bottom:8px;">
<div style="color:{ncol};font-weight:700;font-size:.85rem;">{person}</div>
<div style="color:#6b7280;font-size:.75rem;margin-top:4px;">{slbl}</div>
</div>""",unsafe_allow_html=True)

            # نموذج التسجيل بـ radio بدلاً من checkbox
            st.markdown("### ✅ تسجيل ملء الأنبوبة")

            st.markdown("**👤 من ملأ الأنبوبة؟**")
            gas_filler_choice = st.radio(
                "من ملأ",
                options=active_for_gas if active_for_gas else SHABAB,
                index=active_for_gas.index(next_gas_person) if next_gas_person and next_gas_person in active_for_gas else 0,
                horizontal=True,
                key="gas_filler_radio",
                label_visibility="collapsed"
            )

            st.markdown("**🔜 من عليه الدور القادم؟**")
            next_gas_opts = [p for p in active_for_gas if p != gas_filler_choice]
            if not next_gas_opts:
                next_gas_opts = active_for_gas
            # اقتراح التالي بعد من ملأ
            if gas_filler_choice in active_for_gas:
                sug_ng_idx = (active_for_gas.index(gas_filler_choice)+1) % len(active_for_gas)
                sug_ng = active_for_gas[sug_ng_idx]
            else:
                sug_ng = next_gas_opts[0] if next_gas_opts else ""
            ng_idx = next_gas_opts.index(sug_ng) if sug_ng in next_gas_opts else 0
            next_gas_choice = st.radio(
                "الدور القادم",
                options=next_gas_opts,
                index=ng_idx,
                horizontal=True,
                key="next_gas_radio",
                label_visibility="collapsed"
            )

            if st.button("💾 حفظ", type="primary", use_container_width=True, key="save_gas_btn"):
                with st.spinner("جاري الحفظ…"):
                    res = call_script({"action":"addGasEntry",
                                       "filler":gas_filler_choice,
                                       "nextPerson":next_gas_choice})
                if "Success" in res:
                    wa_gas(gas_filler_choice, next_gas_choice)
                    st.success(f"✅ تم تسجيل {gas_filler_choice}! الدور القادم: {next_gas_choice}")
                    st.session_state.pop("gas_log",None)
                    clear_all_cache(); st.rerun()
                else:
                    st.error(f"خطأ: {res}")

            # سجل الأنبوبة
            st.markdown("### 📋 سجل الأنبوبة")
            if gas_log:
                for entry in gas_log[:15]:
                    st.markdown(f"""<div style="background:#1a1e2e;border:1px solid #2a2f45;
border-radius:10px;padding:11px 16px;margin-bottom:7px;direction:rtl;">
<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;">
  <span style="color:#60a5fa;font-weight:700;">🔵 {entry.get("filler","")}</span>
  <span style="color:#8892b0;font-size:.82rem;">
    📅 {str(entry.get("date",""))[:10]} | التالي: <b style="color:#93c5fd;">{entry.get("nextPerson","")}</b>
  </span>
</div></div>""",unsafe_allow_html=True)
            else:
                st.info("لا يوجد سجل أنبوبة بعد.")

    # ────────── إدارة الإعفاءات ──────────
    with svc_tab3:
        st.markdown("""<div class="info-box">
🚫 <b>إدارة الإعفاءات الدائمة:</b><br>
• من في <b>إجازة كاملة</b> يُعفى <b>تلقائياً</b> بدون الحاجة لإضافته هنا.<br>
• هذا القسم للإعفاءات الدائمة: مريض، عمل خاص، إلخ.
</div>""",unsafe_allow_html=True)
        if not SHABAB:
            st.info("أضف أشخاصاً أولاً.")
        else:
            col_ex1,col_ex2 = st.columns(2)
            for col_ex,svc,exempt_set,lbl in [
                (col_ex1,"cleaning",cleaning_exempt,"🧹 إعفاءات التنظيف"),
                (col_ex2,"gas",gas_exempt,"🔵 إعفاءات الأنبوبة")]:
                with col_ex:
                    st.markdown(f"### {lbl}")
                    for person in SHABAB:
                        vac=month_vacations.get(person,{})
                        is_vac=vac.get("type")=="full"
                        is_ex=person in exempt_set
                        r1,r2=st.columns([3,1])
                        with r1:
                            if is_vac:   st.markdown(f"🏖️ **{person}** — إجازة")
                            elif is_ex:  st.markdown(f"🚫 **{person}** — معفى")
                            else:        st.markdown(f"✅ **{person}** — متاح")
                        with r2:
                            if not is_vac:
                                if is_ex:
                                    if st.button("إلغاء",key=f"unex_{svc}_{person}",use_container_width=True):
                                        res=call_script({"action":"removeExemption","service":svc,"name":person})
                                        if "Success" in res:
                                            wa_exemption(person,svc,"remove")
                                            clear_all_cache(); st.rerun()
                                else:
                                    if st.button("إعفاء",key=f"ex_{svc}_{person}",use_container_width=True):
                                        res=call_script({"action":"addExemption","service":svc,"name":person})
                                        if "Success" in res:
                                            wa_exemption(person,svc,"add")
                                            clear_all_cache(); st.rerun()

# ══════════════════════════════════════════════
#  ٥: الإجازات
# ══════════════════════════════════════════════
with tab5:
    if not SHABAB:
        st.info("أضف أشخاصاً أولاً.")
    else:
        st.subheader(f"🏖️ إدارة الإجازات – {selected_month_ar}")
        st.markdown("""<div class="info-box">
💡 <b>الإجازة تؤثر على المصاريف المشتركة فقط.</b> الإيجار ثابت على الجميع.<br>
• <b>إجازة كاملة</b>: بدون مصاريف + إعفاء تلقائي من التنظيف والأنبوبة.<br>
• <b>غياب من أول الشهر</b>: يُحسب بنسبة أيام حضوره.<br>
• <b>إجازة من تاريخ</b>: يُحسب مصاريف الأيام الحاضرة فقط.<br>
• <b>خصم مبلغ ثابت</b>: يشارك كامل مع خصم مبلغ محدد.
</div>""",unsafe_allow_html=True)
        for person in SHABAB:
            with st.expander(f"⚙️ {person}",expanded=False):
                vac=month_vacations.get(person,{})
                vtype=st.radio("نوع الإجازة",
                    options=["none","full","from_start","from_date","deduct"],
                    format_func=lambda x:{"none":"✅ لا توجد إجازة","full":"🏖️ إجازة كاملة",
                        "from_start":"🗓️ غياب من أول الشهر","from_date":"📅 إجازة من تاريخ",
                        "deduct":"➖ خصم مبلغ ثابت"}[x],
                    index=["none","full","from_start","from_date","deduct"].index(vac.get("type","none")),
                    key=f"vtype_{person}")
                extra={}
                if vtype=="from_start":
                    absent=st.number_input("أيام الغياب",min_value=1,max_value=days_in_month,step=1,
                                           value=int(vac.get("days",1)),key=f"days_{person}")
                    present=days_in_month-absent
                    st.info(f"مصاريف: {present}/{days_in_month} يوم ({present/days_in_month*100:.1f}%) | إيجار: {rent_per_person:.3f}")
                    extra["days"]=absent
                elif vtype=="from_date":
                    vd=vac.get("date") or date(sel_year,sel_month,15)
                    vac_date=st.date_input("تاريخ بداية الإجازة",value=vd,
                        min_value=date(sel_year,sel_month,1),
                        max_value=date(sel_year,sel_month,days_in_month),key=f"vdate_{person}")
                    present=max(0,min((vac_date-date(sel_year,sel_month,1)).days,days_in_month))
                    st.info(f"مصاريف: {present}/{days_in_month} يوم ({present/days_in_month*100:.1f}%) | إيجار: {rent_per_person:.3f}")
                    extra["date"]=vac_date
                elif vtype=="deduct":
                    ded=st.number_input("المبلغ المخصوم",min_value=0.0,step=0.5,format="%.3f",
                                        value=float(vac.get("deduct_amount",0.0)),key=f"ded_{person}")
                    st.info(f"خصم {ded:.3f} من المصاريف | إيجار: {rent_per_person:.3f}")
                    extra["deduct_amount"]=ded
                elif vtype=="full":
                    st.info(f"لا مصاريف | إيجار: {rent_per_person:.3f} | معفى من الخدمات ✅")
                if st.button(f"💾 حفظ {person}",key=f"save_{person}"):
                    if selected_month_ar not in st.session_state.vacations:
                        st.session_state.vacations[selected_month_ar]={}
                    if vtype=="none":
                        st.session_state.vacations[selected_month_ar].pop(person,None)
                    else:
                        st.session_state.vacations[selected_month_ar][person]={"type":vtype,**extra}
                    with st.spinner("حفظ…"):
                        res=call_script({"action":"saveVacation","month":selected_month_ar,
                            "name":person,"vtype":vtype,"days":extra.get("days",""),
                            "vacDate":str(extra.get("date","")),
                            "deductAmt":extra.get("deduct_amount","")})
                    if "Success" in res:
                        wa_vacation(person,vtype,selected_month_ar)
                        st.success(f"✅ تم حفظ إجازة {person}")
                        st.cache_data.clear(); st.rerun()
                    else:
                        st.error(res)
        if month_vacations:
            st.divider()
            st.markdown("**📋 الإجازات المسجلة:**")
            for person,vac in month_vacations.items():
                vtype=vac.get("type","")
                desc={"full":"إجازة كاملة (+ إعفاء خدمات)","from_start":f"غياب {vac.get('days',0)} يوم",
                      "from_date":f"إجازة من {vac.get('date','')}",
                      "deduct":f"خصم {vac.get('deduct_amount',0):.3f}"}.get(vtype,"")
                st.markdown(f'<div class="vacation-notice">🏖️ <strong>{person}</strong>: {desc} | إيجار ثابت: {rent_per_person:.3f}</div>',unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  ٦: إدارة الأشخاص
# ══════════════════════════════════════════════
with tab6:
    st.subheader("⚙️ إدارة قائمة الأشخاص")
    st.markdown('<div class="info-box">💡 إضافة أو حذف شخص يؤثر على توزيع الإيجار فوراً.</div>',unsafe_allow_html=True)
    if SHABAB:
        st.markdown("### 👥 الأشخاص الحاليون")
        for person in SHABAB:
            pc1,pc2,pc3=st.columns([3,1,1])
            pc1.markdown(f"🔹 **{person}**")
            if pc2.button("✏️ تعديل",key=f"editbtn_{person}"):
                st.session_state[f"editing_{person}"]=True
            if st.session_state.get(f"editing_{person}",False):
                with st.form(key=f"rename_form_{person}"):
                    new_name=st.text_input("الاسم الجديد",value=person)
                    sc1,sc2=st.columns(2)
                    save_r=sc1.form_submit_button("💾 حفظ")
                    cancel_r=sc2.form_submit_button("❌ إلغاء")
                    if save_r:
                        if new_name.strip() and new_name.strip()!=person:
                            with st.spinner("تعديل…"):
                                res=call_script({"action":"renamePerson","oldName":person,"newName":new_name.strip()})
                            if "Success" in res:
                                wa_person_rename(person,new_name.strip())
                                st.success(f"✅ تم التغيير إلى {new_name}")
                                st.session_state.pop(f"editing_{person}",None)
                                clear_all_cache(); st.rerun()
                            else: st.error(res)
                        else: st.warning("⚠️ أدخل اسماً مختلفاً.")
                    if cancel_r:
                        st.session_state.pop(f"editing_{person}",None); st.rerun()
            if pc3.button("🗑️ حذف",key=f"delperson_{person}"):
                with st.spinner(f"حذف {person}…"):
                    res=call_script({"action":"deletePerson","name":person})
                if "Success" in res:
                    wa_person_delete(person)
                    st.success(f"✅ تم حذف {person}")
                    clear_all_cache(); st.rerun()
                else: st.error(res)
    else:
        st.info("لا يوجد أشخاص بعد. أضف أول شخص من الأسفل.")
    st.divider()
    st.markdown("### ➕ إضافة شخص جديد")
    with st.form("add_person_form",clear_on_submit=True):
        new_person=st.text_input("اسم الشخص",placeholder="مثال: أبو عمر")
        if st.form_submit_button("➕ إضافة",use_container_width=True):
            if new_person.strip():
                if new_person.strip() in SHABAB:
                    st.warning("⚠️ هذا الشخص موجود مسبقاً!")
                else:
                    with st.spinner("إضافة…"):
                        res=call_script({"action":"addPerson","name":new_person.strip()})
                    if "Success" in res:
                        wa_person_add(new_person.strip())
                        st.success(f"✅ تمت إضافة {new_person}")
                        clear_all_cache(); st.rerun()
                    else: st.error(res)
            else: st.warning("⚠️ أدخل اسماً صحيحاً.")

# ══════════════════════════════════════════════
#  ٧: سجل الأحداث
# ══════════════════════════════════════════════
with tab7:
    st.subheader("📋 سجل الأحداث التاريخي")
    cr1,cr2=st.columns([1,1])
    with cr1:
        filter_type=st.selectbox("فلتر النوع",["الكل","➕ إضافة مصروف","✏️ تعديل مصروف","🗑️ حذف مصروف",
            "🏖️ تسجيل إجازة","🏖️ إلغاء إجازة","👤 إضافة شخص","🗑️ حذف شخص","✏️ تغيير اسم",
            "⚙️ تغيير إعداد","⚙️ إعداد جديد"])
    with cr2:
        if st.button("🔄 تحديث السجل",use_container_width=True): st.rerun()
    with st.spinner("جاري تحميل السجل…"):
        log_data=load_log()
    if filter_type!="الكل":
        log_data=[r for r in log_data if r.get("type","")==filter_type]
    if log_data:
        st.markdown(f"**إجمالي الأحداث: {len(log_data)}**")
        st.divider()
        tc={"➕ إضافة مصروف":"#0d3b2e","✏️ تعديل مصروف":"#1a2e1a","🗑️ حذف مصروف":"#3b0d0d",
            "🏖️ تسجيل إجازة":"#0d1f3c","🏖️ إلغاء إجازة":"#1a1a2e","👤 إضافة شخص":"#1a2e1a",
            "🗑️ حذف شخص":"#3b0d0d","✏️ تغيير اسم":"#1a1f3c","⚙️ تغيير إعداد":"#2a1a0d","⚙️ إعداد جديد":"#2a1a0d"}
        tx={"➕ إضافة مصروف":"#4ade80","✏️ تعديل مصروف":"#86efac","🗑️ حذف مصروف":"#f87171",
            "🏖️ تسجيل إجازة":"#60a5fa","🏖️ إلغاء إجازة":"#93c5fd","👤 إضافة شخص":"#4ade80",
            "🗑️ حذف شخص":"#f87171","✏️ تغيير اسم":"#a78bfa","⚙️ تغيير إعداد":"#fbbf24","⚙️ إعداد جديد":"#fbbf24"}
        for entry in log_data:
            bg=tc.get(entry.get("type",""),"#1a1e2e"); color=tx.get(entry.get("type",""),"#e0e6ff")
            mb=f'<span style="background:#1a237e;color:#90caf9;border-radius:10px;padding:2px 10px;font-size:.8rem;margin-right:8px;">{entry.get("month","")}</span>' if entry.get("month") else ""
            st.markdown(f"""<div style="background:{bg};border-radius:10px;padding:12px 18px;
margin-bottom:8px;direction:rtl;border:1px solid #2a2f45;">
<div style="display:flex;justify-content:space-between;align-items:center;">
  <span style="color:{color};font-weight:700;font-size:.95rem;">{entry.get("type","")}</span>
  <span style="color:#8892b0;font-size:.8rem;">🕐 {entry.get("datetime","")}</span>
</div>
<div style="color:#c8cfd8;margin-top:6px;font-size:.9rem;">{mb}{entry.get("details","")}</div>
</div>""",unsafe_allow_html=True)
    else:
        st.info("لا توجد أحداث مسجلة بعد.")

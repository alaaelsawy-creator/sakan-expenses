import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime, date, timedelta
import calendar
from PIL import Image
import io

st.set_page_config(page_title="تنظيم السكن", page_icon="🏠",
                   layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;800&display=swap');
html,body,[class*="css"]{font-family:'Tajawal',sans-serif!important;direction:rtl}
.main{background:#0f1117}
.stat-card{background:linear-gradient(135deg,#1e2130,#252840);border:1px solid #2e3250;
  border-radius:16px;padding:20px;text-align:center;margin-bottom:16px}
.stat-card .value{font-size:1.8rem;font-weight:800;color:#fff}
.stat-card .label{font-size:.85rem;color:#8892b0;margin-top:4px}
.person-row{display:flex;align-items:center;justify-content:space-between;background:#1a1e2e;
  border:1px solid #2a2f45;border-radius:12px;padding:14px 20px;margin-bottom:10px;direction:rtl}
.badge-green{background:#0d3b2e;color:#4ade80;border:1px solid #166534;border-radius:20px;padding:4px 14px;font-weight:700;font-size:.85rem}
.badge-red{background:#3b0d0d;color:#f87171;border:1px solid #991b1b;border-radius:20px;padding:4px 14px;font-weight:700;font-size:.85rem}
.badge-vacation{background:#1a2e3b;color:#60a5fa;border:1px solid #1d4ed8;border-radius:20px;padding:4px 14px;font-weight:700;font-size:.85rem}
.badge-zero{background:#2a2a2a;color:#aaa;border:1px solid #444;border-radius:20px;padding:4px 14px;font-weight:700;font-size:.85rem}
.whatsapp-box{background:#0a1a0f;border:1px solid #166534;border-radius:12px;padding:20px;
  font-family:'Tajawal',monospace;white-space:pre-wrap;color:#4ade80;font-size:.95rem;direction:rtl}
.app-header{background:linear-gradient(135deg,#1a237e,#283593 50%,#1565c0);border-radius:20px;
  padding:30px;text-align:center;margin-bottom:30px}
.app-header h1{color:#fff;font-size:2rem;font-weight:800;margin:0}
.app-header p{color:#90caf9;margin:8px 0 0;font-size:.95rem}
.stTabs [data-baseweb="tab-list"]{gap:8px}
.stTabs [data-baseweb="tab"]{background:#1a1e2e;border-radius:10px;border:1px solid #2e3250;color:#8892b0;font-weight:600}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,#1a237e,#1565c0)!important;color:#fff!important;border-color:#1565c0!important}
.info-box{background:#0d1f3c;border:1px solid #1d4ed8;border-radius:10px;padding:14px 18px;color:#93c5fd;margin-bottom:20px}
.rule-box{background:#1a1a0d;border:1px solid #854d0e;border-radius:10px;padding:14px 18px;color:#fde047;margin-bottom:20px;font-size:.9rem}
.drag-list{list-style:none;padding:0;margin:0}
.drag-item{display:flex;align-items:center;background:#1a1e2e;border:1px solid #2a2f45;border-radius:12px;padding:12px 16px;margin-bottom:8px;cursor:grab;direction:rtl;gap:12px;transition:border-color .2s}
.drag-item.first-item{border:2px solid #4ade80;background:linear-gradient(135deg,#0d3b2e,#1a2e1e)}
.drag-item.first-item-gas{border:2px solid #60a5fa;background:linear-gradient(135deg,#0d1f3c,#1a2e4a)}
.drag-item:active{cursor:grabbing;border-color:#6366f1}
.drag-handle{color:#4a5568;font-size:1.1rem;flex-shrink:0}
.drag-name{font-weight:700;color:#e0e6ff;font-size:.95rem;flex:1}
.drag-badge{font-size:.75rem;padding:2px 10px;border-radius:20px;background:#0d3b2e;color:#4ade80;border:1px solid #166534}
.drag-badge-gas{background:#0d1f3c;color:#60a5fa;border:1px solid #1d4ed8}
</style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  الثوابت
# ══════════════════════════════════════════════
SHEET_CSV = "https://docs.google.com/spreadsheets/d/1g0VfbnUVwNXjV0c2BFlmlX3RSh5eZnpzLUrzwLeqG2I/export?format=csv&gid=0"
SCRIPT    = "https://script.google.com/macros/s/AKfycbxPIUzuOqp1wXHk1RiJKPZuSn96pYAxLyIqf5Y5vB_S1Ak1VMZH6zumIGNRAqVt2oRs/exec"
MONTHS_AR = {"January":"يناير","February":"فبراير","March":"مارس","April":"أبريل",
             "May":"مايو","June":"يونيو","July":"يوليو","August":"أغسطس",
             "September":"سبتمبر","October":"أكتوبر","November":"نوفمبر","December":"ديسمبر"}

def next_friday():
    t = date.today(); d = (4 - t.weekday()) % 7
    return t + timedelta(days=d if d else 7)

# ══════════════════════════════════════════════
#  واتساب
# ══════════════════════════════════════════════
def _wacfg():
    try: return {"i":st.secrets["GREEN_API_INSTANCE"],"t":st.secrets["GREEN_API_TOKEN"],"c":st.secrets["GREEN_API_CHAT_ID"]}
    except: return None

def wa(msg):
    cfg = _wacfg()
    if not cfg: return
    try: requests.post("https://api.green-api.com/waInstance"+cfg["i"]+"/sendMessage/"+cfg["t"],
                       json={"chatId":cfg["c"],"message":msg},timeout=15)
    except: pass

def _now(): return datetime.now().strftime("%Y-%m-%d %H:%M")

def wa_add_expense(name,amt,note,month):  wa("🏠 *تنظيم السكن*\n➕ مصروف جديد\n👤 "+name+"  |  💰 "+str(round(float(amt),3))+"\n📝 "+note+"  |  📅 "+month+"\n🕐 "+_now())
def wa_edit_expense(amt,note):            wa("🏠 *تنظيم السكن*\n✏️ تعديل مصروف\n💰 "+str(round(float(amt),3))+"  |  📝 "+note+"\n🕐 "+_now())
def wa_del_expense(rid):                  wa("🏠 *تنظيم السكن*\n🗑️ حذف مصروف\n🔑 "+rid+"\n🕐 "+_now())
def wa_vac(name,vt,month,vdate="",note=""):
    vta={"full":"إجازة كاملة 🏖️","from_start":"إجازة من أول الشهر حتى تاريخ 🗓️","from_date":"إجازة من تاريخ 📅","deduct":"خصم مبلغ ➖","fixed":"مبلغ ثابت للمصاريف 💰","none":"إلغاء الإجازة ✅"}.get(vt,vt)
    msg="🏠 *تنظيم السكن*\n🏖️ تحديث إجازة\n👤 "+name+"  |  "+vta+"\n📅 "+month
    if vt in("from_date","from_start") and vdate: msg+="\n🗓️ التاريخ: "+vdate
    if note: msg+="\n📝 "+note
    msg+="\n🕐 "+_now()
    wa(msg)
def wa_cleaning(cleaner,fri_str,nxt):
    wa("🏠 *تنظيم السكن*\n🧹 تسجيل التنظيف\n👤 نظّف: *"+cleaner+"*\n📅 الجمعة "+fri_str+"\n🔜 الدور القادم: *"+nxt+"*\n🕐 "+_now())
def wa_remind_cl(cleaner,fri_str):        wa("🏠 *تنظيم السكن*\n🔔 تذكير التنظيف\n📅 الجمعة "+fri_str+"\n👤 عليه الدور: *"+cleaner+"*\n🕐 "+_now())
def wa_gas(filler,nxt):                   wa("🏠 *تنظيم السكن*\n🔵 ملء الأنبوبة\n👤 ملأ: *"+filler+"*\n🔜 الدور القادم: *"+nxt+"*\n🕐 "+_now())
def wa_remind_gas(p):                     wa("🏠 *تنظيم السكن*\n🔔 تذكير الأنبوبة\n👤 عليه الدور: *"+p+"*\n🕐 "+_now())
def wa_add_person(n):                     wa("🏠 *تنظيم السكن*\n👤 إضافة شخص: *"+n+"*\n🕐 "+_now())
def wa_del_person(n):                     wa("🏠 *تنظيم السكن*\n🗑️ حذف شخص: *"+n+"*\n🕐 "+_now())
def wa_rename(o,n):                       wa("🏠 *تنظيم السكن*\n✏️ تغيير اسم\n📛 "+o+" ← *"+n+"*\n🕐 "+_now())
def wa_rent(amt):                         wa("🏠 *تنظيم السكن*\n🏠 تغيير الإيجار\n💰 الإيجار الجديد: *"+str(round(float(amt),3))+"*\n🕐 "+_now())
def wa_exempt(n,svc,act):
    s="التنظيف 🧹" if svc=="cleaning" else "الأنبوبة 🔵"
    a="إعفاء 🚫" if act=="add" else "إلغاء إعفاء ✅"
    wa("🏠 *تنظيم السكن*\n⚙️ "+a+" من "+s+"\n👤 "+n+"\n🕐 "+_now())
def wa_return_vac(n,fri_str):             wa("🏠 *تنظيم السكن*\n✅ عودة من الإجازة\n👤 "+n+"\n📅 يبدأ الجمعة "+fri_str+"\n🕐 "+_now())

# ══════════════════════════════════════════════
#  تحميل البيانات
# ══════════════════════════════════════════════
@st.cache_data(ttl=60)
def load_persons():
    try:
        resp=requests.get(SCRIPT+"?type=persons",timeout=15)
        d=resp.json()
        if not isinstance(d,list): return []
        return sorted([x["name"] for x in d if x.get("name")],
                      key=lambda n:next((x["order"] for x in d if x["name"]==n),99))
    except Exception as e:
        st.warning("⚠️ تعذّر تحميل الأشخاص: "+str(e))
        return []

def load_settings():
    for attempt in range(3):
        try:
            resp=requests.get(SCRIPT+"?type=settings",timeout=15)
            d=resp.json()
            if isinstance(d,dict): return d
        except: pass
    return {}

@st.cache_data(ttl=60)
def load_vac_sheet():
    try:
        d=requests.get(SCRIPT+"?type=vacations",timeout=10).json()
        r={}
        for row in d:
            m,n=row["month"],row["name"]
            if m not in r: r[m]={}
            e={"type":row["vtype"]}
            if row.get("days"):      e["days"]=int(row["days"])
            if row.get("vacDate"):
                pdv=_pd(row["vacDate"])
                if pdv: e["date"]=pdv
            if row.get("deductAmt"): e["deduct_amount"]=float(row["deductAmt"])
            if row.get("fixedAmt"):  e["fixed_amount"]=float(row["fixedAmt"])
            if row.get("note"):      e["note"]=str(row["note"])
            r[m][n]=e
        return r
    except: return {}

def _pd(v):
    s=str(v).strip()
    if not s or s=="None": return None
    if "T" in s: s=s.split("T")[0]
    for f in ("%Y-%m-%d","%m/%d/%Y","%d/%m/%Y"):
        try: return datetime.strptime(s,f).date()
        except: pass
    return None

@st.cache_data(ttl=60)
def load_data():
    try:
        df=pd.read_csv(SHEET_CSV+"&cb="+str(datetime.now().timestamp()))
        df["_row"]=range(2,len(df)+2)
        df["_rowId"]=df["الشهر"].astype(str)+"|"+df["الاسم"].astype(str)+"|"+df["المبلغ"].astype(str)+"|"+df["التاريخ"].astype(str)
        for col in ["ثابت","الصورة"]:
            if col not in df.columns: df[col]=""
        return df
    except: return pd.DataFrame(columns=["الشهر","الاسم","المبلغ","البيان","التاريخ","الصورة","ثابت","_row","_rowId"])

@st.cache_data(ttl=60)
def load_cl():
    try:
        d=requests.get(SCRIPT+"?type=cleaning",timeout=15).json()
        return d if isinstance(d,list) else []
    except: return []

@st.cache_data(ttl=60)
def load_gas():
    try:
        d=requests.get(SCRIPT+"?type=gas",timeout=15).json()
        return d if isinstance(d,list) else []
    except: return []

@st.cache_data(ttl=60)
def load_exempt():
    try: return requests.get(SCRIPT+"?type=exemptions",timeout=10).json()
    except: return {}

@st.cache_data(ttl=60)
def load_rotation_order(service):
    try:
        r=requests.get(SCRIPT+"?type=rotation_"+service,timeout=10).text.strip()
        if r: return [x.strip() for x in r.split(",") if x.strip()]
    except: pass
    return []

def resolve_order(service, persons, vac_month, exempts):
    """يرجع قائمة الأشخاص المتاحين بترتيب الدوران المحفوظ، يستثني كل من عليه إجازة من أي نوع"""
    on_vac={p for p in persons if vac_month.get(p,{}).get("type")}
    active=[p for p in persons if p not in on_vac and p not in exempts]
    saved=load_rotation_order(service)
    # رتّب بناءً على المحفوظ، ثم أضف الجدد في نهايته
    ordered=[p for p in saved if p in active]
    for p in active:
        if p not in ordered: ordered.append(p)
    return ordered

def load_log():
    try: return requests.get(SCRIPT+"?type=log",timeout=10).json()
    except: return []

def api(payload):
    try: return requests.post(SCRIPT,data=payload,timeout=30).text
    except Exception as e: return "Error: "+str(e)

def clr(): st.cache_data.clear()

# ══════════════════════════════════════════════
#  منطق التنظيف – مصدر حقيقة واحد
# ══════════════════════════════════════════════
def get_next_cleaner(cl_log, persons, vac_month, cl_exempt):
    active=[p for p in persons if not vac_month.get(p,{}).get("type") and p not in cl_exempt]
    if not active: return None
    if not cl_log: return active[0]
    np=cl_log[0].get("nextPerson","").strip()
    if np and np in active: return np
    last=cl_log[0].get("cleaner","").strip()
    if last in active: return active[(active.index(last)+1)%len(active)]
    return active[0]

def get_next_gas(gas_log, persons, vac_month, gas_exempt):
    active=[p for p in persons if not vac_month.get(p,{}).get("type") and p not in gas_exempt]
    if not active: return None
    if not gas_log: return active[0]
    np=gas_log[0].get("nextPerson","")
    if np and np in active: return np
    last=gas_log[0].get("filler","")
    if last in active: return active[(active.index(last)+1)%len(active)]
    return active[0]


# ══════════════════════════════════════════════
#  العنوان
# ══════════════════════════════════════════════
st.markdown("""<div class="app-header">
  <h1>🏠 تنظيم السكن</h1>
  <p>إعداد أبو زين • تتبع وتوزيع الأدوار والمصاريف بدقة وشفافية</p>
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  تحميل – دائماً من الـ Sheet
# ══════════════════════════════════════════════
SHABAB   = load_persons()
all_data = load_data()
vac_all  = load_vac_sheet()
settings = load_settings()

# ── تشخيص مشاكل التحميل ──
if not SHABAB:
    st.error("❌ لا يمكن تحميل الأشخاص من الـ Sheet. تأكد من:")
    st.markdown("- أن الـ Apps Script deployed بشكل صحيح\n- أن الـ SCRIPT_URL صحيح\n- اضغط 🔄 تحديث")
    if st.button("🔄 إعادة المحاولة"): clr(); st.rerun()
ex_data  = load_exempt()
cl_ex    = set(ex_data.get("cleaning",[]))
gas_ex   = set(ex_data.get("gas",[]))
cl_log   = load_cl()
gas_log  = load_gas()

# ══════════════════════════════════════════════
#  شريط الإعدادات
# ══════════════════════════════════════════════
cur_date=datetime.now()
month_opts=[f"{m:02d} – {MONTHS_AR[datetime(2026,m,1).strftime('%B')]} 2026" for m in range(1,13)]
c1,c2,c3,c4,c5=st.columns([2,1,1,1,1])
with c1: sel_month_ar=st.selectbox("📅 الشهر",month_opts,index=cur_date.month-1)
with c2:
    mi=month_opts.index(sel_month_ar); sel_m=mi+1; sel_y=2026
    dim=calendar.monthrange(sel_y,sel_m)[1]; st.metric("📆 أيام الشهر",dim)
with c3:
    rent_val=float(settings.get("total_rent",0.0))
    total_rent=st.number_input("🏠 إجمالي الإيجار",min_value=0.0,value=rent_val,format="%.3f")
with c4:
    st.markdown("<br>",unsafe_allow_html=True)
    if st.button("💾 حفظ الإيجار",type="primary",use_container_width=True):
        res=api({"action":"saveSetting","key":"total_rent","value":str(total_rent)})
        if "Success" in res: wa_rent(total_rent); st.success("✅"); clr(); st.rerun()
        else: st.error(res)
with c5:
    st.markdown("<br>",unsafe_allow_html=True)
    if st.button("🔄 تحديث",use_container_width=True): clr(); st.rerun()

st.markdown("""<div class="rule-box">⚠️ <b>قاعدة التوزيع:</b>
الإيجار يُقسَّم بالتساوي على <b>جميع الأشخاص</b>. المصاريف تُوزَّع على <b>المتواجدين</b> فقط.</div>""",unsafe_allow_html=True)
st.divider()

# ══════════════════════════════════════════════
#  حسابات المصاريف
# ══════════════════════════════════════════════
vac_month=vac_all.get(sel_month_ar,{})

def exp_ratio(vi,dim,sy,sm):
    vt=vi.get("type","none")
    if vt=="full": return 0.0
    if vt=="fixed": return 0.0
    if vt=="from_start":
        vd=vi.get("date")
        if vd:
            pr=max(0,dim-(vd.day-1))
            return pr/dim
        return 0.0
    if vt=="from_date":
        vd=vi.get("date")
        if vd: return min(max(0,(vd-date(sy,sm,1)).days),dim)/dim
        return 1.0
    if vt=="deduct": return 1.0
    return 1.0

_raw=all_data[all_data["الشهر"]==sel_month_ar] if not all_data.empty else pd.DataFrame()
mdf=_raw[pd.to_numeric(_raw["المبلغ"],errors='coerce').fillna(0)>0].copy() if not _raw.empty else pd.DataFrame()
if not mdf.empty:
    mdf["_amt"]=pd.to_numeric(mdf["المبلغ"],errors='coerce').fillna(0.0)
    mdf["_date"]=mdf["التاريخ"].apply(_pd)
    mdf["_fixed"]=mdf["ثابت"].fillna("").astype(str).str.strip().isin(["نعم","1","Yes","yes"])
tot_exp=mdf["_amt"].sum() if not mdf.empty else 0.0

er={}; dm={}; fm={}; tr=0.0
for p in SHABAB:
    v=vac_month.get(p,{}); r=exp_ratio(v,dim,sel_y,sel_m)
    er[p]=r; tr+=r
    dm[p]=float(v.get("deduct_amount",0)) if v.get("type")=="deduct" else 0.0
    fm[p]=float(v.get("fixed_amount",0)) if v.get("type")=="fixed" else 0.0
rpp=total_rent/len(SHABAB) if SHABAB else 0.0

# ── توزيع كل مصروف على حدة ──
# "إجازة من تاريخ": يشارك في المصاريف المسجّلة بتاريخ <= تاريخ إجازته فقط
# "إجازة من أول الشهر حتى تاريخ": يشارك في المصاريف المسجّلة بتاريخ >= تاريخ عودته فقط
_share={p:0.0 for p in SHABAB}
if not mdf.empty:
    for _,_row in mdf.iterrows():
        amt=_row["_amt"]; edate=_row["_date"]; is_fx=_row["_fixed"]
        if is_fx:
            # مصروف ثابت: يُقسَّم بالتساوي على الجميع بمن فيهم من في أجازة
            per=amt/len(SHABAB) if SHABAB else 0.0
            for p in SHABAB: _share[p]+=per
        else:
            wts={}
            for p in SHABAB:
                v=vac_month.get(p,{}); vt=v.get("type","none")
                if vt=="full": wts[p]=0.0
                elif vt=="from_date":
                    vd=v.get("date")
                    wts[p]=1.0 if (edate is None or edate<=vd) else 0.0
                elif vt=="from_start":
                    vd=v.get("date")
                    wts[p]=1.0 if (edate is None or edate>=vd) else 0.0
                else: wts[p]=er[p]
            tw=sum(wts.values())
            if tw>0:
                for p in SHABAB: _share[p]+=amt*wts[p]/tw

def exp_share(p):
    v=vac_month.get(p,{})
    if v.get("type")=="fixed": return fm[p]
    if v.get("type")=="deduct": return max(0.0,_share[p]-dm[p])
    return _share[p]

summary=[]
for p in SHABAB:
    paid=pd.to_numeric(mdf[mdf["الاسم"]==p]["المبلغ"],errors='coerce').sum() if not mdf.empty else 0.0
    es=exp_share(p); td=es+rpp; v=vac_month.get(p,{})
    summary.append({"الاسم":p,"مدفوع":paid,"حصة":es,"إيجار":rpp,"مستحق":td,"رصيد":paid-td,
                    "إجازة":v.get("type","none"),"نسبة":er[p]})
ac=sum(1 for p in SHABAB if not vac_month.get(p,{}).get("type"))
if not SHABAB: st.warning("⚠️ لا يوجد أشخاص.")

# ══════════════════════════════════════════════
#  التنظيف والأنبوبة — المصدر الوحيد
# ══════════════════════════════════════════════
nxt_cleaner = get_next_cleaner(cl_log, SHABAB, vac_month, cl_ex)
nxt_gas     = get_next_gas(gas_log, SHABAB, vac_month, gas_ex)


# ══════════════════════════════════════════════
#  بطاقات التنبيه العلوية
# ══════════════════════════════════════════════
if SHABAB:
    _t1, _t2 = st.columns(2)
    with _t1:
        _c  = nxt_cleaner or "—"
        _fd = next_friday().strftime("%d/%m/%Y")
        st.markdown(
            '<div style="background:linear-gradient(135deg,#0d3b2e,#1a4a38);border:2px solid #4ade80;'
            'border-radius:14px;padding:14px 18px;margin-bottom:10px;">'
            '<div style="color:#86efac;font-size:.78rem;">🧹 التنظيف – الجمعة '+_fd+'</div>'
            '<div style="color:#4ade80;font-size:1.4rem;font-weight:800;margin:3px 0;">'+_c+'</div>'
            '</div>', unsafe_allow_html=True)
    with _t2:
        _g = nxt_gas or "—"
        st.markdown(
            '<div style="background:linear-gradient(135deg,#0d1f3c,#1a2e4a);border:2px solid #60a5fa;'
            'border-radius:14px;padding:14px 18px;margin-bottom:10px;">'
            '<div style="color:#93c5fd;font-size:.78rem;">🔵 دور ملء الأنبوبة القادم</div>'
            '<div style="color:#60a5fa;font-size:1.4rem;font-weight:800;margin:3px 0;">'+_g+'</div>'
            '</div>', unsafe_allow_html=True)
    st.divider()

# ══════════════════════════════════════════════
#  التبويبات
# ══════════════════════════════════════════════
tab1,tab2,tab3,tab4,tab5,tab6,tab7=st.tabs([
    "📊 الملخص","➕ إضافة مصروف","📜 سجل المصاريف",
    "🏠 خدمات الشقة","🏖️ الإجازات","⚙️ إدارة الأشخاص","📋 سجل الأحداث"])

# ── ١ الملخص ──────────────────────────────────
with tab1:
    if not SHABAB: st.info("أضف أشخاصاً أولاً.")
    else:
        _vals = [f"{tot_exp:.3f}", f"{total_rent:.3f}", f"{rpp:.3f}",
                  f"{tot_exp+total_rent:.3f}", f"{ac}/{len(SHABAB)}"]
        _lbls = ["💰 إجمالي المصاريف","🏠 إجمالي الإيجار","👤 إيجار الفرد","📊 الإجمالي الكلي","👥 المتواجدون"]
        _cols = st.columns(5)
        for ci,val,lbl in zip(_cols,_vals,_lbls):
            ci.markdown('<div class="stat-card"><div class="value">'+val+'</div><div class="label">'+lbl+'</div></div>',unsafe_allow_html=True)
        st.markdown("### 👥 وضع كل شخص")
        for row in summary:
            b=row["رصيد"]; vt=row["إجازة"]
            if vt and vt!="none":
                vl={"full":"🏖️ إجازة كاملة","from_start":"🗓️ إجازة من أول الشهر",
                    "from_date":"📅 إجازة من تاريخ","deduct":"➖ خصم","fixed":"💰 مبلغ ثابت"}.get(vt,"")
                bg=f'<span class="badge-vacation">{vl} + إيجار كامل</span>'
            elif abs(b)<0.01: bg='<span class="badge-zero">➖ صفر</span>'
            elif b>0:         bg=f'<span class="badge-green">🟢 له {b:.3f}</span>'
            else:             bg=f'<span class="badge-red">🔴 عليه {abs(b):.3f}</span>'
            dt=f"دفع: {row['مدفوع']:.3f} | مصاريف: {row['حصة']:.3f} | إيجار: {row['إيجار']:.3f} | المستحق: {row['مستحق']:.3f}"
            st.markdown(f'<div class="person-row"><span style="font-weight:700;color:#e0e6ff">{row["الاسم"]}</span><span style="font-size:.85rem;color:#7ecfb3">{dt}</span>{bg}</div>',unsafe_allow_html=True)
        st.markdown("### 📱 تقرير الواتساب")
        lines=[f"*تقرير مصاريف السكن – {sel_month_ar}*",
               f"🏠 الإيجار: {total_rent:.3f} (فرد: {rpp:.3f})",
               f"💰 المصاريف: {tot_exp:.3f}",f"📊 الكلي: {tot_exp+total_rent:.3f}","─────────────"]
        for row in summary:
            b=row["رصيد"]; vt=row["إجازة"]
            st2="له 🟢" if b>0 else ("عليه 🔴" if b<0 else "صفر ➖")
            nt=(" (إجازة)" if vt=="full" else " (إجازة من أول الشهر)" if vt=="from_start" else " (إجازة من تاريخ)" if vt=="from_date" else " (خصم)" if vt=="deduct" else " (مبلغ ثابت)" if vt=="fixed" else "")
            lines.append(f"• {row['الاسم']}{nt}: {st2} *{abs(b):.3f}*")
        report_text = "\n".join(lines)
        st.markdown('<div class="whatsapp-box">'+report_text+'</div>',unsafe_allow_html=True)
        if st.button("📤 إرسال التقرير للواتساب", type="primary", use_container_width=True, key="send_report_wa"):
            if wa(report_text):
                st.success("✅ تم إرسال التقرير للجروب!")
            else:
                st.error("❌ فشل الإرسال — تأكد من إعدادات Green API")


# ── ٢ إضافة مصروف ─────────────────────────────
with tab2:
    if not SHABAB: st.info("أضف أشخاصاً أولاً.")
    else:
        cf,cr=st.columns([1,1])
        with cf:
            st.subheader("➕ تسجيل مصروف جديد")
            with st.form("add_exp",clear_on_submit=True):
                nm=st.selectbox("من دفع؟",SHABAB)
                am=st.number_input("المبلغ",min_value=0.0,step=0.1,format="%.3f")
                nt=st.text_input("البيان",placeholder="مثال: شاي، سكر…")
                ed=st.date_input("التاريخ",value=date.today())
                is_fixed=st.checkbox("📌 مصروف ثابت (يُقسَّم على الجميع بمن فيهم من في أجازة)")
                ui=st.file_uploader("📸 صورة الفاتورة",type=["png","jpg","jpeg"])
                if st.form_submit_button("✅ تسجيل",use_container_width=True):
                    if am>0:
                        ib,inm="",""
                        if ui:
                            inm=ui.name
                            try:
                                img=Image.open(ui)
                                if img.mode in("RGBA","P"): img=img.convert("RGB")
                                img.thumbnail((800,800)); buf=io.BytesIO()
                                img.save(buf,format="JPEG",quality=70)
                                ib=base64.b64encode(buf.getvalue()).decode()
                            except: pass
                        with st.spinner("حفظ…"):
                            res=api({"action":"addExpense","month":sel_month_ar,"name":nm,
                                     "amount":am,"note":nt,"date":str(ed),
                                     "imgData":ib,"imgName":inm,
                                     "isFixed":"1" if is_fixed else "0"})
                        if "Success" in res:
                            wa_add_expense(nm,am,nt,sel_month_ar); st.success("✅"); st.balloons(); clr(); st.rerun()
                        else: st.error(res)
                    else: st.warning("⚠️ أدخل مبلغاً صحيحاً.")
        with cr:
            st.subheader("🕐 آخر المصاريف")
            if not mdf.empty:
                for _,row in mdf.tail(6).iloc[::-1].iterrows():
                    st.info(f"**{row['الاسم']}** | {float(row['المبلغ']):.3f} | {row['البيان']}")
            else: st.info("لا توجد مصاريف بعد.")

# ── ٣ سجل المصاريف ────────────────────────────
with tab3:
    st.subheader(f"📜 سجل مصاريف {sel_month_ar}")
    fn=st.selectbox("فلتر باسم",["الكل"]+SHABAB,key="fn")
    ddf=mdf.copy() if not mdf.empty else pd.DataFrame()
    if fn!="الكل" and not ddf.empty: ddf=ddf[ddf["الاسم"]==fn]
    if not ddf.empty:
        st.metric("إجمالي",f"{pd.to_numeric(ddf['المبلغ'],errors='coerce').sum():.3f}")
        for idx,row in ddf.iloc[::-1].iterrows():
            av=float(row["المبلغ"]) if pd.notna(row["المبلغ"]) else 0.0
            rn=int(row["_row"]) if "_row" in row else None
            ri=str(row["_rowId"]) if "_rowId" in row else ""
            with st.expander(f"📌 {row['الاسم']}  |  {av:.3f}  |  {row['البيان']}"):
                ca,cb=st.columns(2); ca.write(f"**التاريخ:** {row['التاريخ']}"); ca.write(f"**الشهر:** {row['الشهر']}")
                il=str(row['الصورة']).strip()
                if il.startswith("http"): cb.link_button("🖼️ فتح الفاتورة",il)
                else: cb.caption("⚠️ لا توجد صورة")
                if rn:
                    st.markdown("---"); e1,e2=st.columns(2)
                    with e1:
                        st.markdown("**✏️ تعديل**")
                        na2=st.number_input("مبلغ جديد",value=av,format="%.3f",key=f"ea{idx}")
                        nn2=st.text_input("بيان جديد",value=str(row['البيان']),key=f"en{idx}")
                        nd2=st.text_input("تاريخ جديد",value=str(row['التاريخ']),key=f"ed{idx}")
                        if st.button("💾 حفظ",key=f"se{idx}"):
                            res=api({"action":"editExpense","row":rn,"rowId":ri,"amount":na2,"note":nn2,"date":nd2})
                            if "Success" in res: wa_edit_expense(na2,nn2); st.success("✅"); clr(); st.rerun()
                            else: st.error(res)
                    with e2:
                        st.markdown("**🗑️ حذف**"); st.warning("لا يمكن التراجع!")
                        if st.button("🗑️ حذف",key=f"dl{idx}",type="primary"):
                            res=api({"action":"deleteExpense","row":rn,"rowId":ri})
                            if "Success" in res: wa_del_expense(ri); st.success("✅"); clr(); st.rerun()
                            else: st.error(res)
    else: st.info("لا توجد مصاريف.")
    if not mdf.empty:
        st.divider(); st.markdown("**📊 إجماليات:**"); cols=st.columns(3)
        for i,p in enumerate(SHABAB):
            tp=pd.to_numeric(mdf[mdf["الاسم"]==p]["المبلغ"],errors='coerce').sum()
            cols[i%3].metric(p,f"{tp:.3f}")

# ── ٤ خدمات الشقة ────────────────────────────
with tab4:
    st.subheader("🏠 خدمات الشقة")
    sv1,sv2,sv3=st.tabs(["🧹 التنظيف","🔵 الأنبوبة","🚫 الإعفاءات"])

    # ────── التنظيف ──────
    with sv1:
        st.markdown("""<div class="info-box">
🧹 <b>نظام التنظيف:</b> رتّب الأسماء بالسحب والإفلات. أول اسم عليه الدور.
بعد التنظيف ينزل للأسفل تلقائياً. من عليه إجازة (أي نوع) أو معفى لا يظهر.
</div>""", unsafe_allow_html=True)

        if not SHABAB:
            st.info("أضف أشخاصاً أولاً.")
        else:
            cl_order = resolve_order("cleaning", SHABAB, vac_month, cl_ex)
            fri_str_cl = next_friday().strftime("%d/%m/%Y")
            cur_cleaner = cl_order[0] if cl_order else None

            # ── بطاقة الدور الحالي ──
            st.markdown(
                '<div style="background:linear-gradient(135deg,#0d3b2e,#1a4a38);border:2px solid #4ade80;'
                'border-radius:16px;padding:18px;text-align:center;margin-bottom:20px;">'
                '<div style="color:#93c5fd;font-size:.85rem;">🧹 دور التنظيف – الجمعة '+fri_str_cl+'</div>'
                '<div style="color:#4ade80;font-size:1.8rem;font-weight:800;margin:6px 0;">'+(cur_cleaner or "—")+'</div>'
                '</div>', unsafe_allow_html=True)

            # ── قائمة السحب والإفلات ──
            st.markdown("#### 📋 ترتيب الدوران")
            if "cl_order_draft" not in st.session_state:
                st.session_state["cl_order_draft"] = cl_order.copy()
            else:
                # تحديث إذا تغيّرت القائمة (شخص جديد / عودة من إجازة)
                existing = st.session_state["cl_order_draft"]
                for p in cl_order:
                    if p not in existing: existing.append(p)
                st.session_state["cl_order_draft"] = [p for p in existing if p in cl_order]

            draft_cl = st.session_state["cl_order_draft"]

            # عرض القائمة مع أزرار تحريك
            for i, p in enumerate(draft_cl):
                is_first = (i == 0)
                badge = '<span class="drag-badge">🧹 دوره الآن</span>' if is_first else f'<span style="color:#6b7280;font-size:.8rem;">#{i+1}</span>'
                item_class = "drag-item first-item" if is_first else "drag-item"
                col_name, col_up, col_down, col_done = st.columns([5, 1, 1, 2])
                with col_name:
                    st.markdown(f'<div class="{item_class}"><span class="drag-handle">⠿</span><span class="drag-name">{p}</span>{badge}</div>', unsafe_allow_html=True)
                with col_up:
                    if i > 0:
                        if st.button("⬆️", key=f"cl_up_{i}", help="تحريك لأعلى"):
                            draft_cl[i], draft_cl[i-1] = draft_cl[i-1], draft_cl[i]
                            st.session_state["cl_order_draft"] = draft_cl
                            st.rerun()
                with col_down:
                    if i < len(draft_cl)-1:
                        if st.button("⬇️", key=f"cl_dn_{i}", help="تحريك لأسفل"):
                            draft_cl[i], draft_cl[i+1] = draft_cl[i+1], draft_cl[i]
                            st.session_state["cl_order_draft"] = draft_cl
                            st.rerun()
                with col_done:
                    if is_first:
                        if st.button("✅ نظّف!", key="cl_done_btn", type="primary", use_container_width=True):
                            done = draft_cl.pop(0)
                            draft_cl.append(done)
                            st.session_state["cl_order_draft"] = draft_cl
                            new_order = ",".join(draft_cl)
                            next_p = draft_cl[0] if draft_cl else ""
                            res = api({
                                "action": "addCleaningEntry",
                                "cleaner": done,
                                "weekFrom": str(next_friday()),
                                "weekTo": str(next_friday()),
                                "weekNum": "1",
                                "nextPerson": next_p,
                                "note": "",
                            })
                            api({"action": "saveRotationOrder", "service": "cleaning", "order": new_order})
                            if "Success" in res:
                                wa_cleaning(done, fri_str_cl, next_p)
                                st.success(f"✅ {done} نظّف! القادم: {next_p}")
                                clr(); st.rerun()

            # ── زر حفظ الترتيب اليدوي ──
            st.markdown("---")
            if st.button("💾 حفظ الترتيب الحالي", key="save_cl_order", use_container_width=True):
                new_order = ",".join(st.session_state["cl_order_draft"])
                res = api({"action": "saveRotationOrder", "service": "cleaning", "order": new_order})
                if "Success" in res:
                    st.success("✅ تم حفظ الترتيب")
                    clr(); st.rerun()

            # ── سجل التنظيف ──
            st.markdown("### 📋 سجل التنظيف")
            if cl_log:
                for entry in cl_log[:15]:
                    np2 = entry.get("nextPerson","").strip()
                    np_b = ' | <span style="color:#93c5fd;">القادم: <b>'+np2+'</b></span>' if np2 else ""
                    st.markdown(
                        '<div style="background:#1a1e2e;border:1px solid #2a2f45;border-radius:10px;'
                        'padding:11px 16px;margin-bottom:7px;direction:rtl;">'
                        '<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;">'
                        '<span style="color:#4ade80;font-weight:700;">🧹 '+entry.get("cleaner","")+'</span>'
                        '<span style="color:#8892b0;font-size:.82rem;">📅 '+str(entry.get("weekFrom",""))[:10]+np_b+'</span>'
                        '</div></div>', unsafe_allow_html=True)
            else:
                st.info("لا يوجد سجل.")
    with sv2:
        st.markdown("""<div class="info-box">🔵 <b>نظام الأنبوبة:</b> رتّب الأسماء بالسحب والإفلات. أول اسم عليه الدور.
بعد الملء ينزل للأسفل تلقائياً. من عليه إجازة (أي نوع) أو معفى لا يظهر.</div>""",unsafe_allow_html=True)
        if not SHABAB: st.info("أضف أشخاصاً أولاً.")
        else:
            gas_order = resolve_order("gas", SHABAB, vac_month, gas_ex)
            cur_gas = gas_order[0] if gas_order else None

            st.markdown(
                '<div style="background:linear-gradient(135deg,#0d1f3c,#1a2e4a);border:2px solid #60a5fa;'
                'border-radius:16px;padding:18px;text-align:center;margin-bottom:20px;">'
                '<div style="color:#93c5fd;font-size:.85rem;">🔵 دور ملء الأنبوبة القادم</div>'
                '<div style="color:#60a5fa;font-size:1.8rem;font-weight:800;margin:6px 0;">'+(cur_gas or "—")+'</div>'
                '</div>',unsafe_allow_html=True)

            # ── قائمة السحب والإفلات ──
            st.markdown("#### 📋 ترتيب الدوران")
            if "gas_order_draft" not in st.session_state:
                st.session_state["gas_order_draft"] = gas_order.copy()
            else:
                existing = st.session_state["gas_order_draft"]
                for p in gas_order:
                    if p not in existing: existing.append(p)
                st.session_state["gas_order_draft"] = [p for p in existing if p in gas_order]

            draft_gas = st.session_state["gas_order_draft"]

            for i, p in enumerate(draft_gas):
                is_first = (i == 0)
                badge = '<span class="drag-badge drag-badge-gas">🔵 دوره الآن</span>' if is_first else f'<span style="color:#6b7280;font-size:.8rem;">#{i+1}</span>'
                item_class = "drag-item first-item-gas" if is_first else "drag-item"
                col_name, col_up, col_down, col_done = st.columns([5, 1, 1, 2])
                with col_name:
                    st.markdown(f'<div class="{item_class}"><span class="drag-handle">⠿</span><span class="drag-name">{p}</span>{badge}</div>', unsafe_allow_html=True)
                with col_up:
                    if i > 0:
                        if st.button("⬆️", key=f"gas_up_{i}", help="تحريك لأعلى"):
                            draft_gas[i], draft_gas[i-1] = draft_gas[i-1], draft_gas[i]
                            st.session_state["gas_order_draft"] = draft_gas
                            st.rerun()
                with col_down:
                    if i < len(draft_gas)-1:
                        if st.button("⬇️", key=f"gas_dn_{i}", help="تحريك لأسفل"):
                            draft_gas[i], draft_gas[i+1] = draft_gas[i+1], draft_gas[i]
                            st.session_state["gas_order_draft"] = draft_gas
                            st.rerun()
                with col_done:
                    if is_first:
                        if st.button("✅ ملأ!", key="gas_done_btn", type="primary", use_container_width=True):
                            done = draft_gas.pop(0)
                            draft_gas.append(done)
                            st.session_state["gas_order_draft"] = draft_gas
                            new_order = ",".join(draft_gas)
                            next_p = draft_gas[0] if draft_gas else ""
                            res = api({"action": "addGasEntry", "filler": done, "nextPerson": next_p})
                            api({"action": "saveRotationOrder", "service": "gas", "order": new_order})
                            if "Success" in res:
                                wa_gas(done, next_p)
                                st.success(f"✅ {done} ملأ! القادم: {next_p}")
                                clr(); st.rerun()

            st.markdown("---")
            if st.button("💾 حفظ الترتيب الحالي", key="save_gas_order", use_container_width=True):
                new_order = ",".join(st.session_state["gas_order_draft"])
                res = api({"action": "saveRotationOrder", "service": "gas", "order": new_order})
                if "Success" in res:
                    st.success("✅ تم حفظ الترتيب")
                    clr(); st.rerun()

            st.markdown("### 📋 سجل الأنبوبة")
            if gas_log:
                for entry in gas_log[:15]:
                    st.markdown(
                        '<div style="background:#1a1e2e;border:1px solid #2a2f45;border-radius:10px;'
                        'padding:11px 16px;margin-bottom:7px;direction:rtl;">'
                        '<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;">'
                        '<span style="color:#60a5fa;font-weight:700;">🔵 '+entry.get("filler","")+'</span>'
                        '<span style="color:#8892b0;font-size:.82rem;">📅 '+str(entry.get("date",""))[:10]+
                        ' | التالي: <b style="color:#93c5fd;">'+entry.get("nextPerson","")+'</b></span>'
                        '</div></div>',unsafe_allow_html=True)
            else: st.info("لا يوجد سجل.")

    # ────── الإعفاءات ──────
    with sv3:
        st.markdown("""<div class="info-box">🚫 <b>الإعفاءات الدائمة:</b>
من عليه إجازة (أي نوع) يُعفى تلقائياً. هذا القسم للإعفاءات الدائمة (مريض، عمل، إلخ).</div>""",unsafe_allow_html=True)
        if not SHABAB: st.info("أضف أشخاصاً أولاً.")
        else:
            xc1,xc2=st.columns(2)
            for xcol,svc,exs,lbl in[(xc1,"cleaning",cl_ex,"🧹 إعفاءات التنظيف"),(xc2,"gas",gas_ex,"🔵 إعفاءات الأنبوبة")]:
                with xcol:
                    st.markdown("### "+lbl)
                    visible=[p for p in SHABAB if not vac_month.get(p,{}).get("type")]
                    if not visible: st.info("الجميع في إجازة.")
                    for p in visible:
                        is_ex=p in exs
                        r1,r2=st.columns([3,1])
                        with r1:
                            if is_ex: st.markdown("🚫 **"+p+"** — معفى")
                            else:     st.markdown("✅ **"+p+"** — متاح")
                        with r2:
                            if is_ex:
                                if st.button("إلغاء",key="unex_"+svc+"_"+p,use_container_width=True):
                                    res=api({"action":"removeExemption","service":svc,"name":p})
                                    if "Success" in res: wa_exempt(p,svc,"remove"); clr(); st.rerun()
                            else:
                                if st.button("إعفاء",key="ex_"+svc+"_"+p,use_container_width=True):
                                    res=api({"action":"addExemption","service":svc,"name":p})
                                    if "Success" in res: wa_exempt(p,svc,"add"); clr(); st.rerun()

# ── ٥ الإجازات ────────────────────────────────
with tab5:
    if not SHABAB: st.info("أضف أشخاصاً أولاً.")
    else:
        st.subheader(f"🏖️ إدارة الإجازات – {sel_month_ar}")
        st.markdown("""<div class="info-box">💡 <b>الإجازة تؤثر على المصاريف، والإيجار يبقى ثابتاً على الجميع.</b><br>
⚠️ تسجيل أي نوع إجازة (أياً كان) يُعفي الشخص تلقائياً من دور التنظيف والأنبوبة طول هذا الشهر.<br>
• <b>إجازة كاملة</b>: بدون مصاريف.<br>
• <b>إجازة من أول الشهر حتى تاريخ</b>: لا يُحسب عليه أي مصروف تاريخه قبل تاريخ العودة، ويشارك بالكامل في كل مصروف من تاريخ العودة حتى آخر الشهر.<br>
• <b>إجازة من تاريخ</b>: يشارك بالكامل في كل مصروف تاريخه قبل أو يساوي تاريخ نزوله، ولا يُحسب عليه أي مصروف بعد ذلك التاريخ.<br>
• <b>خصم مبلغ</b>: يشارك بالكامل ثم يُخصم مبلغ ثابت من حصته.<br>
• <b>مبلغ ثابت للمصاريف</b>: يدفع الإيجار كاملاً + مبلغ ثابت تحدده كنصيبه الكامل من المصاريف (بدل الحساب النسبي).
</div>""",unsafe_allow_html=True)
        for p in SHABAB:
            with st.expander("⚙️ "+p,expanded=False):
                v=vac_month.get(p,{})
                vt=st.radio("نوع الإجازة",
                    options=["none","full","from_start","from_date","deduct","fixed"],
                    format_func=lambda x:{"none":"✅ لا توجد إجازة","full":"🏖️ إجازة كاملة",
                        "from_start":"🗓️ إجازة من أول الشهر حتى تاريخ","from_date":"📅 إجازة من تاريخ",
                        "deduct":"➖ خصم مبلغ ثابت","fixed":"💰 مبلغ ثابت للمصاريف"}[x],
                    index=["none","full","from_start","from_date","deduct","fixed"].index(v.get("type","none")),
                    key="vt_"+p)
                ex={}
                if vt=="from_start":
                    vd=v.get("date") or date(sel_y,sel_m,15)
                    vdt=st.date_input("تاريخ العودة (يبدأ المشاركة من هذا اليوم)",vd,date(sel_y,sel_m,1),date(sel_y,sel_m,dim),key="vdt_start_"+p)
                    pr=max(0,dim-(vdt.day-1)); st.info(f"مصاريف: {pr}/{dim} يوم (من {vdt.day} حتى آخر الشهر)")
                    ex["date"]=vdt
                elif vt=="from_date":
                    vd=v.get("date") or date(sel_y,sel_m,15)
                    vdt=st.date_input("تاريخ البداية",vd,date(sel_y,sel_m,1),date(sel_y,sel_m,dim),key="vdt_"+p)
                    pr=max(0,min((vdt-date(sel_y,sel_m,1)).days,dim)); st.info(f"مصاريف: {pr}/{dim} يوم")
                    ex["date"]=vdt
                elif vt=="deduct":
                    ded=st.number_input("المبلغ المخصوم",0.0,step=0.5,format="%.3f",value=float(v.get("deduct_amount",0.0)),key="vded_"+p)
                    st.info(f"خصم {ded:.3f}"); ex["deduct_amount"]=ded
                elif vt=="fixed":
                    fix=st.number_input("المبلغ الثابت (نصيبه الكامل من المصاريف)",0.0,step=0.5,format="%.3f",value=float(v.get("fixed_amount",0.0)),key="vfix_"+p)
                    st.info(f"يدفع الإيجار كاملاً + {fix:.3f} كنصيب ثابت من المصاريف"); ex["fixed_amount"]=fix
                elif vt=="full": st.info("لا مصاريف | معفى من الخدمات ✅")
                if vt!="none":
                    note=st.text_input("📝 ملاحظة",value=v.get("note",""),key="vnote_"+p)
                    ex["note"]=note
                if st.button("💾 حفظ "+p,key="sv_"+p):
                    with st.spinner("حفظ…"):
                        res=api({"action":"saveVacation","month":sel_month_ar,"name":p,"vtype":vt,
                                 "days":ex.get("days",""),"vacDate":str(ex.get("date","")),
                                 "deductAmt":ex.get("deduct_amount",""),"fixedAmt":ex.get("fixed_amount",""),
                                 "note":ex.get("note","")})
                    if "Success" in res:
                        vdate_str = ex.get("date","").strftime("%d/%m/%Y") if vt in("from_date","from_start") and ex.get("date") else ""
                        wa_vac(p,vt,sel_month_ar,vdate_str,ex.get("note","")); st.success("✅"); clr(); st.rerun()
                    else: st.error(res)
        if vac_month:
            st.divider(); st.markdown("**📋 الإجازات المسجلة:**")
            for p,v in vac_month.items():
                vt=v.get("type","")
                desc={"full":"إجازة كاملة","from_start":f"إجازة من أول الشهر حتى {v.get('date','')}",
                      "from_date":f"إجازة من {v.get('date','')}","deduct":f"خصم {v.get('deduct_amount',0):.3f}",
                      "fixed":f"إيجار كامل + مبلغ ثابت {v.get('fixed_amount',0):.3f} كنصيب من المصاريف"}.get(vt,"")
                desc+=" | 🚫 معفى من التنظيف/الأنبوبة"
                if v.get("note"): desc+=" | 📝 "+v["note"]
                col_desc, col_btn = st.columns([4,1])
                with col_desc:
                    st.markdown(f'<div class="vacation-notice">🏖️ <strong>{p}</strong>: {desc}</div>',unsafe_allow_html=True)
                with col_btn:
                    if st.button("🔙 عودة", key="ret_"+p, use_container_width=True, help="تسجيل عودة "+p+" من الإجازة"):
                        res=api({"action":"returnFromVacation","name":p,"month":sel_month_ar})
                        if "Success" in res:
                            # عند العودة: موضعه في التنظيف = الثاني، في الأنبوبة = الأخير
                            for svc in ("cleaning","gas"):
                                saved=load_rotation_order(svc)
                                others_on_vac={x for x in SHABAB if x!=p and vac_month.get(x,{}).get("type")}
                                cur=[x for x in saved if x not in others_on_vac and x!=p]
                                if svc=="cleaning":
                                    if len(cur)>=1: cur.insert(1,p)
                                    else: cur.append(p)
                                else:
                                    cur.append(p)
                                api({"action":"saveRotationOrder","service":svc,"order":",".join(cur)})
                            wa("🏠 *تنظيم السكن*\n🔙 عودة من الإجازة\n👤 "+p+"\n🕐 "+_now())
                            st.success(f"✅ تم تسجيل عودة {p}")
                            # مسح draft ليُعاد بناؤه
                            for k in ("cl_order_draft","gas_order_draft"):
                                if k in st.session_state: del st.session_state[k]
                            clr(); st.rerun()

# ── ٦ إدارة الأشخاص ──────────────────────────
with tab6:
    st.subheader("⚙️ إدارة الأشخاص")
    st.markdown('<div class="info-box">💡 إضافة أو حذف شخص يؤثر على الإيجار فوراً.</div>',unsafe_allow_html=True)
    if SHABAB:
        st.markdown("### 👥 الأشخاص الحاليون")
        for p in SHABAB:
            pc1,pc2,pc3=st.columns([3,1,1]); pc1.markdown("🔹 **"+p+"**")
            if pc2.button("✏️ تعديل",key="eb_"+p): st.session_state["ed_"+p]=True
            if st.session_state.get("ed_"+p,False):
                with st.form("rf_"+p):
                    nn=st.text_input("الاسم الجديد",value=p)
                    s1,s2=st.columns(2); sv=s1.form_submit_button("💾 حفظ"); cn=s2.form_submit_button("❌ إلغاء")
                    if sv:
                        if nn.strip() and nn.strip()!=p:
                            res=api({"action":"renamePerson","oldName":p,"newName":nn.strip()})
                            if "Success" in res:
                                wa_rename(p,nn.strip()); st.success("✅")
                                st.session_state.pop("ed_"+p,None); clr(); st.rerun()
                            else: st.error(res)
                        else: st.warning("⚠️ أدخل اسماً مختلفاً.")
                    if cn: st.session_state.pop("ed_"+p,None); st.rerun()
            if pc3.button("🗑️ حذف",key="dp_"+p):
                res=api({"action":"deletePerson","name":p})
                if "Success" in res: wa_del_person(p); st.success("✅"); clr(); st.rerun()
                else: st.error(res)
    else: st.info("لا يوجد أشخاص.")
    st.divider(); st.markdown("### ➕ إضافة شخص جديد")
    with st.form("add_p",clear_on_submit=True):
        np2=st.text_input("اسم الشخص",placeholder="مثال: أبو عمر")
        if st.form_submit_button("➕ إضافة",use_container_width=True):
            if np2.strip():
                if np2.strip() in SHABAB: st.warning("⚠️ موجود مسبقاً!")
                else:
                    res=api({"action":"addPerson","name":np2.strip()})
                    if "Success" in res: wa_add_person(np2.strip()); st.success("✅"); clr(); st.rerun()
                    else: st.error(res)
            else: st.warning("⚠️ أدخل اسماً.")

# ── ٧ سجل الأحداث ─────────────────────────────
with tab7:
    st.subheader("📋 سجل الأحداث التاريخي")
    lr1,lr2=st.columns([1,1])
    with lr1:
        ft=st.selectbox("فلتر",["الكل","➕ إضافة مصروف","✏️ تعديل مصروف","🗑️ حذف مصروف",
            "🏖️ تسجيل إجازة","🏖️ إلغاء إجازة","👤 إضافة شخص","🗑️ حذف شخص",
            "✏️ تغيير اسم","⚙️ تغيير إعداد","⚙️ إعداد جديد"])
    with lr2:
        if st.button("🔄 تحديث السجل",use_container_width=True): st.rerun()
    with st.spinner("تحميل…"): ld=load_log()
    if ft!="الكل": ld=[r for r in ld if r.get("type","")==ft]
    if ld:
        st.markdown(f"**إجمالي: {len(ld)}**"); st.divider()
        TC={"➕ إضافة مصروف":"#0d3b2e","✏️ تعديل مصروف":"#1a2e1a","🗑️ حذف مصروف":"#3b0d0d",
            "🏖️ تسجيل إجازة":"#0d1f3c","🏖️ إلغاء إجازة":"#1a1a2e","👤 إضافة شخص":"#1a2e1a",
            "🗑️ حذف شخص":"#3b0d0d","✏️ تغيير اسم":"#1a1f3c","⚙️ تغيير إعداد":"#2a1a0d","⚙️ إعداد جديد":"#2a1a0d"}
        TX={"➕ إضافة مصروف":"#4ade80","✏️ تعديل مصروف":"#86efac","🗑️ حذف مصروف":"#f87171",
            "🏖️ تسجيل إجازة":"#60a5fa","🏖️ إلغاء إجازة":"#93c5fd","👤 إضافة شخص":"#4ade80",
            "🗑️ حذف شخص":"#f87171","✏️ تغيير اسم":"#a78bfa","⚙️ تغيير إعداد":"#fbbf24","⚙️ إعداد جديد":"#fbbf24"}
        for e in ld:
            bg=TC.get(e.get("type",""),"#1a1e2e"); cl=TX.get(e.get("type",""),"#e0e6ff")
            mb=('<span style="background:#1a237e;color:#90caf9;border-radius:10px;padding:2px 10px;font-size:.8rem;margin-right:8px;">'+e.get("month","")+'</span>' if e.get("month") else "")
            st.markdown(
                '<div style="background:'+bg+';border-radius:10px;padding:12px 18px;margin-bottom:8px;direction:rtl;border:1px solid #2a2f45;">'
                '<div style="display:flex;justify-content:space-between;align-items:center;">'
                '<span style="color:'+cl+';font-weight:700;font-size:.95rem;">'+e.get("type","")+'</span>'
                '<span style="color:#8892b0;font-size:.8rem;">🕐 '+str(e.get("datetime",""))+'</span>'
                '</div>'
                '<div style="color:#c8cfd8;margin-top:6px;font-size:.9rem;">'+mb+str(e.get("details",""))+'</div>'
                '</div>',unsafe_allow_html=True)
    else: st.info("لا توجد أحداث.")

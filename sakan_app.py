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
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght=300;400;500;700;800&display=swap');
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
.vacation-notice{background:#0d1f3c;border:1px solid #1d4ed8;border-right:4px solid #60a5fa;border-radius:10px;padding:12px 16px;color:#93c5fd;font-size:.9rem;margin-bottom:8px}
</style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  الثوابت والإعدادات الأساسية
# ══════════════════════════════════════════════
SHEET_CSV = "https://docs.google.com/spreadsheets/d/1g0VfbnUVwNXjV0c2BFlmlX3RSh5eZnpzLUrzwLeqG2I/export?format=csv&gid=0"
SCRIPT    = "https://script.google.com/macros/s/AKfycbxPsmytLQIo0GHas-PEpM0d33uStRYdMVKRfgU31V6wOTT3Q2k98hHGHHvncNx88b_o/exec"
MONTHS_AR = {"January":"يناير","February":"فبراير","March":"مارس","April":"أبريل",
             "May":"مايو","June":"يونيو","July":"يوليو","August":"أغسطس",
             "September":"سبتمبر","October":"أكتوبر","November":"نوفمبر","December":"ديسمبر"}

def next_friday():
    t = date.today(); d = (4 - t.weekday()) % 7
    return t + timedelta(days=d if d else 7)

# ══════════════════════════════════════════════
#  إرسال تقارير وتحديثات الواتساب
# ══════════════════════════════════════════════
def _wacfg():
    try: 
        return {
            "i": st.secrets.get("GREEN_API_INSTANCE"),
            "t": st.secrets.get("GREEN_API_TOKEN"),
            "c": st.secrets.get("GREEN_API_CHAT_ID")
        }
    except: 
        return None

def wa(msg):
    cfg = _wacfg()
    if not cfg or not cfg["i"] or not cfg["t"]: return
    try: requests.post("https://api.green-api.com/waInstance"+str(cfg["i"])+"/sendMessage/"+str(cfg["t"]),
                       json={"chatId":cfg["c"],"message":msg},timeout=15)
    except: pass

def _now(): return datetime.now().strftime("%Y-%m-%d %H:%M")

def wa_add_expense(name,amt,note,month):  wa("🏠 *تنظيم السكن*\n➕ مصروف جديد\n👤 "+name+"  |  💰 "+str(round(float(amt),3))+"\n📝 "+note+"  |  📅 "+month+"\n🕐 "+_now())
def wa_edit_expense(amt,note):            wa("🏠 *تنظيم السكن*\n✏️ تعديل مصروف\n💰 "+str(round(float(amt),3))+"  |  📝 "+note+"\n🕐 "+_now())
def wa_del_expense(rid):                  wa("🏠 *تنظيم السكن*\n🗑️ حذف مصروف\n🔑 "+rid+"\n🕐 "+_now())
def wa_vac(name,vt,month):
    vta={"full":"إجازة كاملة 🏖️","from_start":"غياب من البداية 🗓️","from_date":"إجازة من تاريخ 📅","deduct":"خصم مبلغ ➖","none":"إلغاء الإجازة ✅"}.get(vt,vt)
    wa("🏠 *تنظيم السكن*\n🏖️ تحديث إجازة\n👤 "+name+"  |  "+vta+"\n📅 "+month+"\n🕐 "+_now())
def wa_cleaning(sec,fir,fri_str,nsec,nfir):
    wa("🏠 *تنظيم السكن*\n🧹 تسجيل التنظيف\n🔵 "+sec+" (أسبوعه الثاني)\n🟢 "+fir+" (أسبوعه الأول)\n📅 الجمعة "+fri_str+"\n🔜 الدور القادم:\n   🔵 "+nsec+" (ثانيه)  +  🟢 "+nfir+" (أوله)\n🕐 "+_now())
def wa_remind_cl(sec,fir,fri_str):        wa("🏠 *تنظيم السكن*\n🔔 تذكير التنظيف\n📅 الجمعة "+fri_str+"\n🔵 "+sec+" (أسبوعه الثاني)\n🟢 "+fir+" (أسبوعه الأول)\n🕐 "+_now())
def wa_gas(filler,nxt):                   wa("🏠 *تنظيم السكن*\n🔵 ملء الأنبوبة\n👤 ملأ: *"+filler+"*\n🔜 الدور القادم: *"+nxt+"*\n🕐 "+_now())
def wa_remind_gas(p):                     wa("🏠 *تنظيم السكن*\n🔔 تذكير الأنبوبة\n👤 عليه الدور: *"+p+"*\n🕐 "+_now())
def wa_add_person(n):                     wa("🏠 *تنظيم السكن*\n👤 إضافة شخص: *"+n+"*\n🕐 "+_now())
def wa_del_person(n):                     wa("🏠 *تنظيم السكن*\n🗑️ حذف شخص: *"+n+"*\n🕐 "+_now())
def wa_rename(o,n):                       wa("🏠 *تنظيم السكن*\n✏️ تغيير اسم\n📛 "+o+" ← *"+n+"*\n🕐 "+_now())
def wa_rent(amt):                         wa("🏠 *تنظيم السكن*\n🏠 تغيير الإيجار\n💰 الإيجار الجديد: *"+str(round(float(amt),3))+"*\n🕐 "+_now())
def wa_exempt(n,svc,act):
    s="التنظيف 🧹" if svc=="cleaning" else "الأنبوبة 🔵"
    a="إعماء 🚫" if act=="add" else "إلغاء إعفاء ✅"
    wa("🏠 *تنظيم السكن*\n⚙️ "+a+" من "+s+"\n👤 "+n+"\n🕐 "+_now())
def wa_return_vac(n,fri_str):             wa("🏠 *تنظيم السكن*\n✅ عودة من الإجازة\n👤 "+n+"\n📅 يبدأ الجمعة "+fri_str+"\n🕐 "+_now())

# ══════════════════════════════════════════════
#  دوال جلب البيانات من الخادم والـ API
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
            if row.get("vacDate"):   e["date"]=_pd(row["vacDate"])
            if row.get("deductAmt"): e["deduct_amount"]=float(row["deductAmt"])
            r[m][n]=e
        return r
    except: return {}

def _pd(v):
    for f in ("%Y-%m-%d","%m/%d/%Y","%d/%m/%Y"):
        try: return datetime.strptime(str(v),f).date()
        except: pass
    return None

@st.cache_data(ttl=60)
def load_data():
    try:
        df=pd.read_csv(SHEET_CSV+"&cb="+str(datetime.now().timestamp()))
        df["_row"]=range(2,len(df)+2)
        df["_rowId"]=df["الشهر"].astype(str)+"|"+df["الاسم"].astype(str)+"|"+df["المبلغ"].astype(str)+"|"+df["التاريخ"].astype(str)
        return df
    except: return pd.DataFrame(columns=["الشهر","الاسم","المبلغ","البيان","التاريخ","الصورة","_row","_rowId"])

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

def load_log():
    try: return requests.get(SCRIPT+"?type=log",timeout=10).json()
    except: return []

def api(payload):
    try: return requests.post(SCRIPT,data=payload,timeout=30).text
    except Exception as e: return "Error: "+str(e)

def clr(): st.cache_data.clear()

# ══════════════════════════════════════════════
#  منطق تدوير جدول خدمات التنظيف الذكي
# ══════════════════════════════════════════════
def p_status(p, vac_month, cl_exempt):
    if vac_month.get(p,{}).get("type")=="full": return "vacation"
    if p in cl_exempt: return "exempt"
    return "active"

def p_avail(p, vac_month, cl_exempt):
    return p_status(p,vac_month,cl_exempt)=="active"

def next_avail_idx(persons, start, vac_month, cl_exempt, skip=None):
    n=len(persons)
    for off in range(n):
        idx=(start+off)%n; p=persons[idx]
        if p==skip: continue
        if p_avail(p,vac_month,cl_exempt): return idx,p
    return None,None

def build_rotation(persons, vac_month, cl_exempt, cl_log, weeks=None):
    n=len(persons)
    if not n: return []
    if weeks is None: weeks=max(n,2)

    saved_np_sec = None
    saved_np_fir = None
    start_idx    = 0
    if cl_log:
        np_raw = (cl_log[0].get("nextPair","") or "").strip()
        if np_raw:
            parts = [x.strip() for x in np_raw.split("،") if x.strip()]
            if len(parts) >= 1 and parts[0] in persons:
                saved_np_sec = parts[0]
                start_idx    = persons.index(parts[0])
            if len(parts) >= 2 and parts[1] in persons:
                saved_np_fir = parts[1]

    fri0=next_friday(); rows=[]; cur=start_idx

    for i in range(weeks):
        fri=fri0+timedelta(weeks=i)

        if i == 0 and saved_np_sec:
            ps = saved_np_sec
            pf = saved_np_fir
            si = persons.index(ps) if ps in persons else 0
            rows.append({
                "fri":fri,"fri_str":fri.strftime("%d/%m/%Y"),
                "p_sec":ps,"p_fir":pf or "—",
                "sec_st":p_status(ps,vac_month,cl_exempt),
                "fir_st":p_status(pf,vac_month,cl_exempt) if pf else "none",
                "is_cur":True,"skipped":[]
            })
            cur=(si+1)%n
        else:
            si,ps=next_avail_idx(persons,cur,vac_month,cl_exempt)
            if si is None:
                rows.append({"fri":fri,"fri_str":fri.strftime("%d/%m/%Y"),
                             "p_sec":"—","p_fir":"—","sec_st":"none","fir_st":"none",
                             "is_cur":False,"skipped":[]})
                continue
            fi,pf=next_avail_idx(persons,(si+1)%n,vac_month,cl_exempt,skip=ps)
            sk=[]
            for off in range((si-cur)%n): sk.append(persons[(cur+off)%n])
            if fi is not None:
                ex=(si+1)%n
                for off in range((fi-ex)%n):
                    c=persons[(ex+off)%n]
                    if c!=ps: sk.append(c)
            rows.append({
                "fri":fri,"fri_str":fri.strftime("%d/%m/%Y"),
                "p_sec":ps,"p_fir":pf or "—",
                "sec_st":p_status(ps,vac_month,cl_exempt),
                "fir_st":p_status(pf,vac_month,cl_exempt) if pf else "none",
                "is_cur":False,"skipped":list(dict.fromkeys(sk))
            })
            cur=(si+1)%n

    return rows

def get_next_gas(gas_log, persons, vac_month, gas_exempt):
    active=[p for p in persons if vac_month.get(p,{}).get("type")!="full" and p not in gas_exempt]
    if not active: return None
    if not gas_log: return active[0]
    np=gas_log[0].get("nextPerson","")
    if np and np in active: return np
    last=gas_log[0].get("filler","")
    if last in active: return active[(active.index(last)+1)%len(active)]
    return active[0]

# ══════════════════════════════════════════════
#  التذكيرات الدورية التلقائية عبر الواتساب
# ══════════════════════════════════════════════
def maybe_remind(rotation, next_gas):
    today=date.today(); ts=today.strftime("%Y-%m-%d"); wd=today.weekday()
    if wd not in (4,1,3): return
    if rotation and st.session_state.get("last_cl_remind")!=ts:
        r=rotation[0]
        if r["p_sec"]!="—":
            wa_remind_cl(r["p_sec"],r["p_fir"],r["fri_str"])
            st.session_state["last_cl_remind"]=ts
    if next_gas and st.session_state.get("last_gas_remind")!=ts:
        wa_remind_gas(next_gas)
        st.session_state["last_gas_remind"]=ts

# ══════════════════════════════════════════════
#  تحميل العناصر الأساسية وتهيئة البيانات
# ══════════════════════════════════════════════
SHABAB   = load_persons()
all_data = load_data()
vac_all  = load_vac_sheet()
settings = load_settings()

if not SHABAB:
    st.error("❌ لا يمكن تحميل بيانات الأشخاص من الـ Google Sheet حالياً.")
    if st.button("🔄 إعادة محاولة جلب البيانات"): clr(); st.rerun()

ex_data  = load_exempt()
cl_ex    = set(ex_data.get("cleaning",[]))
gas_ex   = set(ex_data.get("gas",[]))
cl_log   = load_cl()
gas_log  = load_gas()

# ══════════════════════════════════════════════
#  شريط التحكم والمحددات العلوية المثبتة
# ══════════════════════════════════════════════
cur_date=datetime.now()
month_opts=[f"{m:02d} – {MONTHS_AR[datetime(2026,m,1).strftime('%B')]} 2026" for m in range(1,13)]
c1,c2,c3,c4,c5=st.columns([2,1,1,1,1])

with c1:
    # استخدام الـ Session State لمنع ارتداد محدد الشهر للقيم الافتراضية عند تحديث الجدول
    if "selected_month_index" not in st.session_state:
        st.session_state["selected_month_index"] = cur_date.month - 1

    sel_month_ar = st.selectbox(
        "📅 الشهر المُستهدف بالعملية", 
        month_opts, 
        index=st.session_state["selected_month_index"],
        key="month_selector_widget"
    )
    st.session_state["selected_month_index"] = month_opts.index(sel_month_ar)

with c2:
    mi=st.session_state["selected_month_index"]; sel_m=mi+1; sel_y=2026
    dim=calendar.monthrange(sel_y,sel_m)[1]; st.metric("📆 أيام الشهر",dim)
with c3:
    rent_val=float(settings.get("total_rent",0.0))
    total_rent=st.number_input("🏠 إجمالي إيجار السكن",min_value=0.0,value=rent_val,format="%.3f")
with c4:
    st.markdown("<br>",unsafe_allow_html=True)
    if st.button("💾 حفظ قيمة الإيجار",type="primary",use_container_width=True):
        res=api({"action":"saveSetting","key":"total_rent","value":str(total_rent)})
        if "Success" in res: wa_rent(total_rent); st.success("✅ تم الحفظ"); clr(); st.rerun()
        else: st.error(res)
with c5:
    st.markdown("<br>",unsafe_allow_html=True)
    if st.button("🔄 تحديث شامل للمزامنة",use_container_width=True): clr(); st.rerun()

st.markdown("""<div class="rule-box">⚠️ <b>قاعدة احتساب وتوزيع النسب المالية:</b><br>
قيمة الإيجار الأساسية تُقسَّم بالتساوي على <b>جميع الأسماء المدرجة بالسكن</b>. أما المصاريف الاستهلاكية المتغيرة فتُوزَّع على <b>المتواجدين الفعليين</b> فقط.</div>""",unsafe_allow_html=True)
st.divider()

# ══════════════════════════════════════════════
#  العمليات الرياضية لحساب الحصص والمدفوعات
# ══════════════════════════════════════════════
vac_month=vac_all.get(sel_month_ar,{})

def exp_ratio(vi,dim,sy,sm):
    vt=vi.get("type","none")
    if vt=="full": return 0.0
    if vt=="from_start": return max(0.0,(dim-min(int(vi.get("days",0)),dim))/dim)
    if vt=="from_date":
        vd=vi.get("date")
        if vd: return min(max(0,(vd-date(sy,sm,1)).days),dim)/dim
        return 1.0
    if vt=="deduct": return 1.0
    return 1.0

_raw=all_data[all_data["الشهر"]==sel_month_ar] if not all_data.empty else pd.DataFrame()
mdf=_raw[pd.to_numeric(_raw["المبلغ"],errors='coerce').fillna(0)>0].copy() if not _raw.empty else pd.DataFrame()
tot_exp=pd.to_numeric(mdf["المبلغ"],errors='coerce').sum() if not mdf.empty else 0.0
er={}; dm={}; tr=0.0
for p in SHABAB:
    v=vac_month.get(p,{}); r=exp_ratio(v,dim,sel_y,sel_m)
    er[p]=r; tr+=r; dm[p]=float(v.get("deduct_amount",0)) if v.get("type")=="deduct" else 0.0
rpp=total_rent/len(SHABAB) if SHABAB else 0.0

def exp_share(p):
    if tr==0: return 0.0
    v=vac_month.get(p,{})
    if v.get("type")=="deduct": return max(0.0,(er[p]/tr)*tot_exp-dm[p])
    return (er[p]/tr)*tot_exp

summary=[]
for p in SHABAB:
    paid=pd.to_numeric(mdf[mdf["الاسم"]==p]["المبلغ"],errors='coerce').sum() if not mdf.empty else 0.0
    es=exp_share(p); td=es+rpp; v=vac_month.get(p,{})
    summary.append({"الاسم":p,"مدفوع":paid,"حصة":es,"إيجار":rpp,"مستحق":td,"رصيد":paid-td,
                    "إجازة":v.get("type","none"),"نسبة":er[p]})
ac=sum(1 for p in SHABAB if er[p]>0)

# ══════════════════════════════════════════════
#  توليد مصفوفة الدوران المبدئية واستنتاج المسؤولين القادمين
# ══════════════════════════════════════════════
n_wks   = max(len(SHABAB),2)
rotation= build_rotation(SHABAB, vac_month, cl_ex, cl_log, weeks=n_wks)
nxt_gas = get_next_gas(gas_log, SHABAB, vac_month, gas_ex)

maybe_remind(rotation, nxt_gas)

if SHABAB:
    _g = nxt_gas or "—"
    st.markdown(
        '<div style="background:linear-gradient(135deg,#0d1f3c,#1a2e4a);border:2px solid #60a5fa;'
        'border-radius:14px;padding:14px 20px;margin-bottom:10px;max-width:400px;">'
        '<div style="color:#93c5fd;font-size:.8rem;">🔵 دور ملء الأنبوبة القادم</div>'
        '<div style="color:#60a5fa;font-size:1.4rem;font-weight:800;">'+_g+'</div>'
        '</div>', unsafe_allow_html=True)
    st.divider()

# ══════════════════════════════════════════════
#  تبويبات نظام توزيع وعرض الأقسام الفنية داخل لوحة القيادة
# ══════════════════════════════════════════════
tab1,tab2,tab3,tab4,tab5,tab6,tab7=st.tabs([
    "📊 الملخص المالي","➕ إضافة مصروف جديد","📜 سجل تتبع المصاريف",
    "🏠 جدول خدمات الشقة","🏖️ شؤون الإجازات والغياب","⚙️ تهيئة إدارة الأشخاص","📋 سجل الأحداث والمراقبة"])

# ── ١ الملخص المالي ───────────────────────────
with tab1:
    if not SHABAB: st.info("يرجى إضافة الأشخاص أولاً من علامة التبويب المخصصة.")
    else:
        _vals = [f"{tot_exp:.3f}", f"{total_rent:.3f}", f"{rpp:.3f}", f"{tot_exp+total_rent:.3f}", f"{ac}/{len(SHABAB)}"]
        _lbls = ["💰 إجمالي المصاريف","🏠 إجمالي الإيجار","👤 إيجار الفرد","📊 الإجمالي الكلي","👥 المتواجدون"]
        _cols = st.columns(5)
        for ci,val,lbl in zip(_cols,_vals,_lbls):
            ci.markdown('<div class="stat-card"><div class="value">'+val+'</div><div class="label">'+lbl+'</div></div>',unsafe_allow_html=True)
        st.markdown("### 👥 وضع المستحقات والتسويات لكل شخص")
        for row in summary:
            b=row["رصيد"]; vt=row["إجازة"]
            if vt and vt!="none":
                vl={"full":"🏖️ إجازة كاملة","from_start":f"🗓️ مصاريف {row['نسبة']*100:.0f}%",
                    "from_date":f"📅 مصاريف {row['نسبة']*100:.0f}%","deduct":"➖ خصم مقطوع"}.get(vt,"")
                bg=f'<span class="badge-vacation">{vl} + إيجار كامل</span>'
            elif abs(b)<0.01: bg='<span class="badge-zero">➖ رصيد مصفّر</span>'
            elif b>0:         bg=f'<span class="badge-green">🟢 دائن (له {b:.3f})</span>'
            else:             bg=f'<span class="badge-red">🔴 مدين (عليه {abs(b):.3f})</span>'
            dt=f"دفع فعلياً: {row['مدفوع']:.3f} | حصة المصاريف: {row['حصة']:.3f} | حصة الإيجار: {row['إيجار']:.3f} | المستحق الكلي: {row['مستحق']:.3f}"
            st.markdown(f'<div class="person-row"><span style="font-weight:700;color:#e0e6ff">{row["الاسم"]}</span><span style="font-size:.85rem;color:#7ecfb3">{dt}</span>{bg}</div>',unsafe_allow_html=True)
        st.markdown("### 📱 نص مخرجات تقرير تطبيق الـ WhatsApp")
        lines=[f"*تقرير مصاريف السكن المشترك – {sel_month_ar}*", f"🏠 الإيجار: {total_rent:.3f} (الفرد: {rpp:.3f})", f"💰 المصاريف الاستهلاكية: {tot_exp:.3f}",f"📊 المجموع الكلي: {tot_exp+total_rent:.3f}","─────────────"]
        for row in summary:
            b=row["رصيد"]; vt=row["إجازة"]
            st2="له 🟢" if b>0 else ("عليه 🔴" if b<0 else "مصفّر الرصيد ➖")
            nt=(" (إجازة كاملة)" if vt=="full" else f" (نسبة استهلاك {row['نسبة']*100:.0f}%)" if vt in("from_start","from_date") else " (خصم مباشر)" if vt=="deduct" else "")
            lines.append(f"• {row['الاسم']}{nt}: {st2} *{abs(b):.3f}*")
        st.markdown('<div class="whatsapp-box">'+"\n".join(lines)+'</div>',unsafe_allow_html=True)

# ── ٢ إضافة مصروف جديد ──────────────────────────
with tab2:
    if not SHABAB: st.info("يرجى إضافة الأسماء أولاً.")
    else:
        cf,cr=st.columns([1,1])
        with cf:
            st.subheader("➕ تسجيل فاتورة أو مصروف جديد")
            with st.form("add_exp",clear_on_submit=True):
                nm=st.selectbox("من الشخص القائم بالدفع؟",SHABAB)
                am=st.number_input("قيمة المبلغ المدفوع",min_value=0.0,step=0.1,format="%.3f")
                nt=st.text_input("البيان التفصيلي الفعلي",placeholder="مثال: شراء كرت ماء، أدوات نظافة للشقة…")
                ed=st.date_input("تاريخ الشراء",value=date.today())
                ui=st.file_uploader("📸 إرفاق صورة مستند الفاتورة",type=["png","jpg","jpeg"])
                if st.form_submit_button("✅ اعتماد وتسجيل الفاتورة",use_container_width=True):
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
                        with st.spinner("جاري المزامنة والحفظ بـ Google Sheets…"):
                            res=api({"action":"addExpense","month":sel_month_ar,"name":nm,
                                     "amount":am,"note":nt,"date":str(ed),"imgData":ib,"imgName":inm})
                        if "Success" in res:
                            wa_add_expense(nm,am,nt,sel_month_ar); st.success("✅ تم التسجيل بنجاح!"); st.balloons(); clr(); st.rerun()
                        else: st.error(res)
                    else: st.warning("⚠️ يرجى كتابة مبلغ أكبر من الصفر لاعتماده.")
        with cr:
            st.subheader("🕐 آخر المصاريف المقيدة مؤخراً")
            if not mdf.empty:
                for _,row in mdf.tail(6).iloc[::-1].iterrows():
                    st.info(f"**{row['الاسم']}** | المبلغ: {float(row['المبلغ']):.3f} | البيان: {row['البيان']}")
            else: st.info("لا توجد فواتير مقيدة لهذا الشهر حتى الآن.")

# ── ٣ سجل تتبع المصاريف ─────────────────────────
with tab3:
    st.subheader(f"📜 تفاصيل سجل فواتير شهر {sel_month_ar}")
    fn=st.selectbox("تصفية وعرض نتائج شخص معين",["عرض الكل"]+SHABAB,key="fn")
    ddf=mdf.copy() if not mdf.empty else pd.DataFrame()
    if fn!="عرض الكل" and not ddf.empty: ddf=ddf[ddf["الاسم"]==fn]
    if not ddf.empty:
        st.metric("مجموع المصاريف المفصلة في التصفية الحالية",f"{pd.to_numeric(ddf['المبلغ'],errors='coerce').sum():.3f}")
        for idx,row in ddf.iloc[::-1].iterrows():
            av=float(row["المبلغ"]) if pd.notna(row["المبلغ"]) else 0.0
            rn=int(row["_row"]) if "_row" in row else None
            ri=str(row["_rowId"]) if "_rowId" in row else ""
            with st.expander(f"📌 {row['الاسم']}  |  الدفعة: {av:.3f}  |  البيان: {row['البيان']}"):
                ca,cb=st.columns(2); ca.write(f"**التاريخ المقيد:** {row['التاريخ']}"); ca.write(f"**عن شهر:** {row['الشهر']}")
                il=str(row['الصورة']).strip()
                if il.startswith("http"): cb.link_button("🖼️ استعراض الفاتورة المرفقة",il)
                else: cb.caption("⚠️ لا توجد صورة مرفقة مع هذا المصروف")
                if rn:
                    st.markdown("---"); e1,e2=st.columns(2)
                    with e1:
                        st.markdown("**✏️ إجراء تعديل على البيانات**")
                        na2=st.number_input("تعديل قيمة المبلغ",value=av,format="%.3f",key=f"ea{idx}")
                        nn2=st.text_input("تعديل سطر البيان",value=str(row['البيان']),key=f"en{idx}")
                        nd2=st.text_input("تعديل التاريخ المقيد",value=str(row['التاريخ']),key=f"ed{idx}")
                        if st.button("💾 حفظ التعديلات الجديدة",key=f"se{idx}"):
                            res=api({"action":"editExpense","row":rn,"rowId":ri,"amount":na2,"note":nn2,"date":nd2})
                            if "Success" in res: wa_edit_expense(na2,nn2); st.success("✅ تم تحديث السجل الكلي بنجاح"); clr(); st.rerun()
                            else: st.error(res)
                    with e2:
                        st.markdown("**🗑️ إلغاء وشطب المصروف**"); st.warning("تنبيه: لا يمكن استرداد البيانات الممسوحة بعد الحذف!")
                        if st.button("🗑️ تأكيد شطب المصروف",key=f"dl{idx}",type="primary"):
                            res=api({"action":"deleteExpense","row":rn,"rowId":ri})
                            if "Success" in res: wa_del_expense(ri); st.success("✅ تم الشطب من النظام الخارجي"); clr(); st.rerun()
                            else: st.error(res)
    else: st.info("لا توجد أي مصاريف مسجلة توافق خيارات التصفية المعروضة.")

# ── ٤ جدول خدمات الشقة (النسخة المستقرة المحمية) ──
with tab4:
    st.subheader("🏠 إدارة وتوزيع جدول خدمات الشقة الدوري")
    sv1,sv2,sv3=st.tabs(["🧹 خدمات التنظيف الدورية","🔵 دور ملء أنبوبة الغاز","🚫 الإعفاءات والاستثناءات"])

    # ────── خدمات التنظيف الدورية ──────
    with sv1:
        st.markdown("""<div class="info-box">
🧹 <b>آلية عمل تدوير نظام النظافة الذكي:</b> في كل يوم جمعة يُكلف شخصان بالتنظيف — 🔵 (صاحب الأسبوع الثاني والأخير) + 🟢 (صاحب الأسبوع الأول والجديد).<br>
مسار الدوران: أ(ثانيه)+ب(أوله) ← ب(ثانيه)+ج(أوله) ← ج(ثانيه)+د(أوله) ← وهكذا بشكل دوري متتابع تلقائياً.<br>
يتم استثناء وتخطي أي شخص يمر بفترة إجازة أو يمتلك إعفاءً مسجلاً مسبقاً، ويحل مكانه الاسم التالي المتاح مباشرة دون إرباك الجدول.
</div>""",unsafe_allow_html=True)

        if not SHABAB:
            st.info("الرجاء إضافة طاقم السكن أولاً لإظهار الخصائص.")
        else:
            st.markdown("#### 👥 الحالة العامة الحالية للأشخاص")
            pc=st.columns(min(len(SHABAB), 4))
            for i,p in enumerate(SHABAB):
                st2=p_status(p,vac_month,cl_ex)
                badge=('<span style="background:#1a2e3b;color:#60a5fa;border-radius:20px;padding:3px 10px;font-size:.8rem;">🏖️ إجازة كاملة</span>' if st2=="vacation" else
                       '<span style="background:#2a1a0d;color:#fbbf24;border-radius:20px;padding:3px 10px;font-size:.8rem;">🚫 معفى حالياً</span>'  if st2=="exempt" else
                       '<span style="background:#0d3b2e;color:#4ade80;border-radius:20px;padding:3px 10px;font-size:.8rem;">✅ نشط ومتاح</span>')
                bc="#4ade80" if st2=="active" else "#2a2f45"
                with pc[i%len(pc)]:
                    st.markdown(
                        '<div style="background:#1a1e2e;border:1px solid '+bc+';border-radius:10px;'
                        'padding:10px;text-align:center;margin-bottom:8px;">'
                        '<div style="color:'+("#4ade80" if st2=="active" else "#8892b0")+';font-weight:700;font-size:.9rem;">'+p+'</div>'
                        '<div style="margin-top:4px;">'+badge+'</div></div>',unsafe_allow_html=True)

            st.divider()

            st.markdown("### 🗓️ جدول استقراء التدوير للأسابيع القادمة")
            st.caption("🔵 = أسبوعه الثاني الفعلي | 🟢 = أسبوعه الأول الجديد | يمكنك التعديل والتبديل اليدوي للأسماء ثم الضغط على زر الحفظ النهائي")

            if not rotation:
                st.info("لا توجد مصفوفة دوران منشأة.")
            else:
                next_fri_date = rotation[0]["fri"]

                # بناء عناصر التحكم (Selectboxes) بمفاتيح صلبة ومستقرة تماماً معتمدة على تاريخ الجمعة الفعلي
                for i, r in enumerate(rotation):
                    is_cur  = (i == 0)
                    bg   = "#0a1f14" if is_cur else "#141824"
                    bord = "2px solid #4ade80" if is_cur else "1px solid #2a2f45"
                    fcol = "#4ade80" if is_cur else "#8892b0"
                    ctag = "  ← 🧹 دور الجمعة القريبة الحالية" if is_cur else ""

                    st.markdown(
                        f'<div style="background:{bg};border:{bord};border-radius:14px;padding:12px 16px;margin-bottom:8px;">'
                        f'<div style="color:{fcol};font-weight:700;font-size:.9rem;margin-bottom:8px;">'
                        f'📅 جمعة تاريخ: {r["fri_str"]}{ctag}</div>',
                        unsafe_allow_html=True)

                    idx_sec = SHABAB.index(r["p_sec"]) if r["p_sec"] in SHABAB else 0
                    idx_fir = SHABAB.index(r["p_fir"]) if r["p_fir"] in SHABAB else (1 if len(SHABAB)>1 else 0)

                    c1, c2 = st.columns(2)
                    with c1:
                        st.selectbox("🔵 أسبوعه الثاني المكمل", options=SHABAB, index=idx_sec, key=f"cl_sec_{r['fri_str']}")
                    with c2:
                        st.selectbox("🟢 أسبوعه الأول الجديد",  options=SHABAB, index=idx_fir, key=f"cl_fir_{r['fri_str']}")

                    if r.get("skipped"):
                        st.markdown(
                            '<div style="color:#6b7280;font-size:.75rem;margin-top:4px;">⏭️ تم تخطي أسماء تلقائياً للغياب/الإعفاء: '
                            + "، ".join(r["skipped"]) + '</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                st.markdown("---")
                cl_note_val = st.text_input("إضافة ملاحظة إضافية للجدول (اختياري)", placeholder="مثال: تنظيف عميق للمطبخ…", key="cl_note_inp")

                # زر الحفظ الموحد والوحيد المسؤول عن سحب قيم القوائم دفعة واحدة ومنع الـ Rerun أثناء التصفح
                if st.button("💾 اعتماد وحفظ دور هذا الأسبوع نهائياً", type="primary", use_container_width=True, key="btn_save_cl"):
                    fri_str_0 = rotation[0]["fri_str"]
                    fri_str_1 = rotation[1]["fri_str"] if len(rotation) > 1 else fri_str_0

                    # قراءة الاختيارات المستقرة والمستقرة في الـ Session State عند لحظة الضغط الحالية فقط
                    _sec     = st.session_state[f"cl_sec_{fri_str_0}"]
                    _fir     = st.session_state[f"cl_fir_{fri_str_0}"]
                    _nxt_sec = st.session_state[f"cl_sec_{fri_str_1}"] if f"cl_sec_{fri_str_1}" in st.session_state else _sec
                    _nxt_fir = st.session_state[f"cl_fir_{fri_str_1}"] if f"cl_fir_{fri_str_1}" in st.session_state else _fir

                    if not _sec or not _fir:
                        st.warning("⚠️ لا توجد أسماء صالحة في الاختيارات.")
                    elif _sec == _fir:
                        st.warning("⚠️ خطأ في التخصيص: لا يمكن اختيار نفس الشخص للقيام بالدورين (الأول والثاني) في نفس الجمعة.")
                    else:
                        cleaner_str  = f"{_sec}، {_fir}"
                        next_str     = f"{_nxt_sec}، {_nxt_fir}"
                        fri_str_save = next_fri_date.strftime("%d/%m/%Y")
                        
                        with st.spinner("جاري ترحيل وإرسال التحديث لجدول قوقل وإعلام المجموعات…"):
                            res = api({
                                "action":   "addCleaningEntry",
                                "cleaner":  cleaner_str,
                                "weekFrom": str(next_fri_date),
                                "weekTo":   str(next_fri_date),
                                "weekNum":  "1",
                                "nextPair": next_str,
                                "note":     cl_note_val,
                            })
                        if "Success" in res:
                            wa_cleaning(_sec, _fir, fri_str_save, _nxt_sec, _nxt_fir)
                            st.success(f"✅ تم الحفظ بنجاح تام! الدور المقيد الحالي: {_sec} و {_fir} | المسار القادم المعتمد: {_nxt_sec} و {_nxt_fir}")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("❌ خطأ أثناء معالجة الخادم: " + res)

            # ── تسجيل عودة من إجازة ──
            st.markdown("---")
            with st.expander("🏠 لوحة تسجيل عودة سريعة لشخص من الإجازة الكاملة"):
                in_vac=[p for p in SHABAB if vac_month.get(p,{}).get("type")=="full"]
                if in_vac:
                    ret_p=st.selectbox("اختر اسم الشخص العائد",in_vac,key="ret_person")
                    if st.button("✅ تأكيد تسجيل العودة إلى نظام الدوران",key="btn_return"):
                        with st.spinner("جاري تعديل الحالة…"):
                            res=api({"action":"saveVacation","month":sel_month_ar,
                                     "name":ret_p,"vtype":"none","days":"","vacDate":"","deductAmt":""})
                        if "Success" in res:
                            ret_fri=(next_friday()+timedelta(weeks=1)).strftime("%d/%m/%Y")
                            wa_return_vac(ret_p,ret_fri)
                            st.success("✅ تفعيل ناجح! سيعود الاسم "+ret_p+" للظهور بالجدول ابتداءً من الجمعة القادمة بتاريخ "+ret_fri)
                            clr(); st.rerun()
                        else: st.error(res)
                else:
                    st.info("لا توجد أسماء مسجلة تحت بند (إجازة كاملة) في هذا الشهر حالياً.")

            # ── سجل التنظيف التاريخي ──
            st.markdown("### 📋 الأرشيف التاريخي لسجل عمليات التنظيف")
            if cl_log:
                for entry in cl_log[:15]:
                    np2=entry.get("nextPair",""); nt2=f' | الملاحظة: {entry.get("note","")}' if entry.get("note") else ""
                    nb=' | <span style="color:#93c5fd;">المسار القادم المجدول: <b>'+np2+'</b></span>' if np2 else ""
                    st.markdown(
                        '<div style="background:#1a1e2e;border:1px solid #2a2f45;border-radius:10px;'
                        'padding:11px 16px;margin-bottom:7px;direction:rtl;">'
                        '<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;">'
                        '<span style="color:#4ade80;font-weight:700;">🧹 المسؤولون: '+entry.get("cleaner","")+'</span>'
                        '<span style="color:#8892b0;font-size:.82rem;">📅 تاريخ أسبوع الجمعة: '+entry.get("weekFrom","")+nt2+nb+'</span>'
                        '</div></div>',unsafe_allow_html=True)
            else: st.info("لا توجد قيود مؤرشفة في سجل التنظيف.")

    # ────── دور ملء أنبوبة الغاز ──────
    with sv2:
        st.markdown("""<div class="info-box">🔵 <b>نظام إدارة وتبديل أنبوبة الغاز:</b> الدور ينتقل تلقائياً بشكل عادل بين المتاحين الفعليين بالسكن من غير أصحاب الإجازات أو الإعفاءات.</div>""",unsafe_allow_html=True)
        if not SHABAB: st.info("أضف أشخاصاً أولاً.")
        else:
            st.markdown(
                '<div style="background:linear-gradient(135deg,#0d1f3c,#1a2e4a);border:2px solid #60a5fa;'
                'border-radius:16px;padding:18px;text-align:center;margin-bottom:20px;">'
                '<div style="color:#93c5fd;font-size:#85rem;">🔵 الشخص المكلف بالدور القادم حالياً لملء الأنبوبة</div>'
                '<div style="color:#60a5fa;font-size:1.8rem;font-weight:800;margin:6px 0;">'+(nxt_gas or "—")+'</div>'
                '</div>',unsafe_allow_html=True)

            gas_active=[p for p in SHABAB if vac_month.get(p,{}).get("type")!="full" and p not in gas_ex]
            gcols=st.columns(min(len(SHABAB),5))
            for i,p in enumerate(SHABAB):
                is_n=p==nxt_gas; is_v=vac_month.get(p,{}).get("type")=="full"; is_ex=p in gas_ex
                fills=sum(1 for e in gas_log if e.get("filler")==p)
                if is_v:   sl="🏖️ في إجازة"; bc="#3b2a0d"; nc="#8892b0"
                elif is_ex: sl="🚫 معفى دائم";  bc="#3b0d0d"; nc="#8892b0"
                elif is_n:  sl="🔵 عليه الدور";  bc="#60a5fa"; nc="#60a5fa"
                else:       sl=f"⏳ عبّأ {fills}×"; bc="#2a2f45"; nc="#8892b0"
                with gcols[i%len(gcols)]:
                    st.markdown(
                        '<div style="background:#1a1e2e;border:1px solid '+bc+';border-radius:10px;'
                        'padding:10px;text-align:center;margin-bottom:8px;">'
                        '<div style="color:'+nc+';font-weight:700;font-size:.85rem;">'+p+'</div>'
                        '<div style="color:#6b7280;font-size:.75rem;margin-top:4px;">'+sl+'</div></div>',unsafe_allow_html=True)

            st.markdown("### ✅ إقرار وتسجيل عملية تعبئة الأنبوبة")
            g_opts=gas_active or SHABAB
            gi=g_opts.index(nxt_gas) if nxt_gas in g_opts else 0
            gfiller=st.radio("👤 من الشخص الذي قام بملئها فعلياً؟",g_opts,index=gi,horizontal=True,key="g_fill")
            ng_opts=[p for p in g_opts if p!=gfiller] or g_opts
            sug_ng=g_opts[(g_opts.index(gfiller)+1)%len(g_opts)] if gfiller in g_opts else ng_opts[0]
            ni=ng_opts.index(sug_ng) if sug_ng in ng_opts else 0
            gnext=st.radio("🔜 من يستلم ويصبح عليه الدور القادم؟",ng_opts,index=ni,horizontal=True,key="g_next")
            if st.button("💾 ترحيل وحفظ عملية الأنبوبة",type="primary",use_container_width=True,key="save_gas"):
                res=api({"action":"addGasEntry","filler":gfiller,"nextPerson":gnext})
                if "Success" in res:
                    wa_gas(gfiller,gnext); st.success("✅ تم التوثيق بنجاح! المكلف القادم رسمياً هو: "+gnext); clr(); st.rerun()
                else: st.error("خطأ أثناء الحفظ: "+res)

            st.markdown("### 📋 الأرشيف التاريخي للأنبوبة")
            if gas_log:
                for entry in gas_log[:15]:
                    st.markdown(
                        '<div style="background:#1a1e2e;border:1px solid #2a2f45;border-radius:10px;'
                        'padding:11px 16px;margin-bottom:7px;direction:rtl;">'
                        '<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;">'
                        '<span style="color:#60a5fa;font-weight:700;">🔵 القائم بالتعبئة: '+entry.get("filler","")+'</span>'
                        '<span style="color:#8892b0;font-size:.82rem;">📅 التاريخ: '+str(entry.get("date",""))[:10]+
                        ' | المكلف التالي المترتب: <b style="color:#93c5fd;">'+entry.get("nextPerson","")+'</b></span>'
                        '</div></div>',unsafe_allow_html=True)

    # ────── الإعفاءات والاستثناءات ──────
    with sv3:
        st.markdown("""<div class="info-box">🚫 <b>لوحة التحكم بالإعفاءات الدائمة المحددة مسبقاً للخدمات داخل الشقة</b></div>""",unsafe_allow_html=True)
        if not SHABAB: st.info("أضف أشخاصاً أولاً.")
        else:
            xc1,xc2=st.columns(2)
            for xcol,svc,exs,lbl in[(xc1,"cleaning",cl_ex,"🧹 إعفاءات طاقم التنظيف"),(xc2,"gas",gas_ex,"🔵 إعفاءات تعبئة الأنبوبة")]:
                with xcol:
                    st.markdown("### "+lbl)
                    for p in SHABAB:
                        is_v=vac_month.get(p,{}).get("type")=="full"; is_ex=p in exs
                        r1,r2=st.columns([3,1])
                        with r1:
                            if is_v:   st.markdown("🏖️ **"+p+"** — مستثنى بداعي الإجازة الحالية")
                            elif is_ex: st.markdown("🚫 **"+p+"** — يمتلك إعفاء ثابت مقيد")
                            else:       st.markdown("✅ **"+p+"** — نشط ومستعد للخدمة")
                        with r2:
                            if not is_v:
                                if is_ex:
                                    if st.button("إلغاء الإعفاء",key="unex_"+svc+"_"+p,use_container_width=True):
                                        res=api({"action":"removeExemption","service":svc,"name":p})
                                        if "Success" in res: wa_exempt(p,svc,"remove"); clr(); st.rerun()
                                else:
                                    if st.button("منح إعفاء",key="ex_"+svc+"_"+p,use_container_width=True):
                                        res=api({"action":"addExemption","service":svc,"name":p})
                                        if "Success" in res: wa_exempt(p,svc,"add"); clr(); st.rerun()

# ── ٥ شؤون الإجازات والغياب ────────────────────────
with tab5:
    if not SHABAB: st.info("أضف أشخاصاً أولاً.")
    else:
        st.subheader(f"🏖️ تعديل وهيكلة وضع فترات الإجازات والغياب لشهـر: {sel_month_ar}")
        for p in SHABAB:
            with st.expander("⚙️ تخصيص وضع وحالة الشخص: "+p,expanded=False):
                v=vac_month.get(p,{})
                vt=st.radio("تعديل بنية الحالة النشطة إلى:",
                    options=["none","full","from_start","from_date","deduct"],
                    format_func=lambda x:{"none":"✅ متواجد ونشط طيلة الشهر وبدون أي غياب","full":"🏖️ إجازة كاملة وشاملة للشهر بالكامل (يسقط الاستهلاك)",
                        "from_start":"🗓️ غياب جزئي محسوب بعدد الأيام (من بداية الشهر)","from_date":"📅 إجازة سنوية/ميدانية تبدأ من تاريخ معين",
                        "deduct":"➖ خصم مالي مقطوع ومحدد القيمة من الحصة الكلية"}[x],
                    index=["none","full","from_start","from_date","deduct"].index(v.get("type","none")),
                    key="vt_"+p)
                ex={}
                if vt=="from_start":
                    ab=st.number_input("إجمالي عدد أيام الغياب الفعلي بالشهر",1,dim,int(v.get("days",1)),key="vd_"+p)
                    pr=dim-ab; st.info(f"حصة احتساب الاستهلاك المترتبة: {pr}/{dim} يوم متواجد ({pr/dim*100:.1f}%)")
                    ex["days"]=ab
                elif vt=="from_date":
                    vd=v.get("date") or date(sel_y,sel_m,15)
                    vdt=st.date_input("تاريخ بداية سريان الإجازة بالشهر",vd,date(sel_y,sel_m,1),date(sel_y,sel_m,dim),key="vdt_"+p)
                    pr=max(0,min((vdt-date(sel_y,sel_m,1)).days,dim)); st.info(f"الأيام المحسوبة للاستهلاك قبل الإجازة: {pr}/{dim} يوم")
                    ex["date"]=vdt
                elif vt=="deduct":
                    ded=st.number_input("المبلغ المراد خصمه مباشرة من الحصة الكلية",0.0,step=0.5,format="%.3f",value=float(v.get("deduct_amount",0.0)),key="vded_"+p)
                    st.info(f"سيتم خصم {ded:.3f} دينار من حسابه المترتب"); ex["deduct_amount"]=ded
                if st.button("💾 اعتماد تحديث وضع حالة "+p,key="sv_"+p):
                    with st.spinner("جاري إرسال وتعديل البيانات بالخادم…"):
                        res=api({"action":"saveVacation","month":sel_month_ar,"name":p,"vtype":vt,
                                 "days":ex.get("days",""),"vacDate":str(ex.get("date","")),"deductAmt":ex.get("deduct_amount","")})
                    if "Success" in res:
                        wa_vac(p,vt,sel_month_ar); st.success("✅ تم تحديث بند الإجازات"); clr(); st.rerun()
                    else: st.error(res)
        if vac_month:
            st.divider(); st.markdown("**📋 ملخص بنود وضع الغياب المسجلة والمعتمدة لهذا الشهر:**")
            for p,v in vac_month.items():
                vt=v.get("type","")
                desc={"full":"إجازة كاملة عن الشهر (معفي من الفواتير والخدمات تماماً)","from_start":f"غياب جزئي قدره {v.get('days',0)} يوم عن الشقة",
                      "from_date":f"بدء إجازة رسمية ومغادرة من تاريخ {v.get('date','')}","deduct":f"خصم مالي مباشر من الحصة بقيمة {v.get('deduct_amount',0):.3f}"}.get(vt,"")
                if desc: st.markdown(f'<div class="vacation-notice">🏖️ <strong>{p}</strong>: {desc}</div>',unsafe_allow_html=True)

# ── ٦ تهيئة إدارة الأشخاص ─────────────────────────
with tab6:
    st.subheader("⚙️ إعدادات وتهيئة لوحة التحكم بطاقم السكن والأشخاص")
    if SHABAB:
        st.markdown("### 👥 طاقم السكن الحالي المقيد بالخادم")
        for p in SHABAB:
            pc1,pc2,pc3=st.columns([3,1,1]); pc1.markdown("🔹 الاسم المقيد: **"+p+"**")
            if pc2.button("✏️ تعديل وتصحيح الاسم",key="eb_"+p): st.session_state["ed_"+p]=True
            if st.session_state.get("ed_"+p,False):
                with st.form("rf_"+p):
                    nn=st.text_input("اكتب الاسم الجديد الصحيح بالكامل",value=p)
                    s1,s2=st.columns(2); sv=s1.form_submit_button("💾 حفظ وتثبيت الاسم"); cn=s2.form_submit_button("❌ إلغاء الإجراء")
                    if sv:
                        if nn.strip() and nn.strip()!=p:
                            res=api({"action":"renamePerson","oldName":p,"newName":nn.strip()})
                            if "Success" in res:
                                wa_rename(p,nn.strip()); st.success("✅ تم التعديل")
                                st.session_state.pop("ed_"+p,None); clr(); st.rerun()
                            else: st.error(res)
                    if cn: st.session_state.pop("ed_"+p,None); st.rerun()
            if pc3.button("🗑️ حذف الشخص نهائياً",key="dp_"+p):
                res=api({"action":"deletePerson","name":p})
                if "Success" in res: wa_del_person(p); st.success("✅ تم حذف الاسم من السجل الكلي بنجاح"); clr(); st.rerun()
                else: st.error(res)
    st.divider()
    with st.form("add_p",clear_on_submit=True):
        np2=st.text_input("اسم الشخص الجديد المراد إضافته لدفتر السكن")
        if st.form_submit_button("➕ إدراج وإضافة اسم الشخص للسكن رسمياً",use_container_width=True):
            if np2.strip() and np2.strip() not in SHABAB:
                res=api({"action":"addPerson","name":np2.strip()})
                if "Success" in res: wa_add_person(np2.strip()); st.success("✅ تم تسجيل وإدراج الاسم بنجاح"); clr(); st.rerun()

# ── ٧ سجل الأحداث والمراقبة ─────────────────────────
with tab7:
    st.subheader("📋 مراجعة سجل الأحداث وحركات النظام التاريخية للمطابقة")
    lr1,lr2=st.columns([1,1])
    with lr1:
        ft=st.selectbox("تصفية الحركات والعمليات حسب النوع",["عرض كافة العمليات","➕ إضافة مصروف","✏️ تعديل مصروف","🗑️ حذف مصروف","🏖️ تسجيل إجازة","👤 إضافة شخص","🗑️ حذف شخص"])
    with lr2:
        if st.button("🔄 تحديث وعرض آخر حركات السجل الآن",use_container_width=True): st.rerun()
    with st.spinner("جاري قراءة السجل الحركي الموثق…"): ld=load_log()
    if ft!="عرض كافة العمليات": ld=[r for r in ld if r.get("type","")==ft]
    if ld:
        TC={"➕ إضافة مصروف":"#0d3b2e","✏️ تعديل مصروف":"#1a2e1a","🗑️ حذف مصروف":"#3b0d0d","🏖️ تسجيل إجازة":"#0d1f3c"}
        TX={"➕ إضافة مصروف":"#4ade80","✏️ تعديل مصروف":"#86efac","🗑️ حذف مصروف":"#f87171","🏖️ تسجيل إجازة":"#60a5fa"}
        for e in ld:
            bg=TC.get(e.get("type",""),"#1a1e2e"); cl=TX.get(e.get("type",""),"#e0e6ff")
            mb=('<span style="background:#1a237e;color:#90caf9;border-radius:10px;padding:2px 10px;font-size:.8rem;margin-right:8px;">'+e.get("month","")+'</span>' if e.get("month") else "")
            st.markdown(
                '<div style="background:'+bg+';border-radius:10px;padding:12px 18px;margin-bottom:8px;direction:rtl;border:1px solid #2a2f45;">'
                '<div style="display:flex;justify-content:space-between;align-items:center;">'
                '<span style="color:'+cl+';font-weight:700;font-size:.95rem;">'+e.get("type","")+'</span>'
                '<span style="color:#8892b0;font-size:.8rem;">🕐 توقيت الحركة الكوني: '+str(e.get("datetime",""))+'</span>'
                '</div>'
                '<div style="color:#c8cfd8;margin-top:6px;font-size:.9rem;">'+mb+str(e.get("details",""))+'</div>'
                '</div>',unsafe_allow_html=True)

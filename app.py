import os, re, json, time, requests
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

BASE = "https://elearn.supmti.ac.ma"
HEAD = {"User-Agent":"Mozilla/5.0", "Accept":"text/html"}
COOKIE = {
    "MoodleSession": os.getenv("MOODLE_SESSION_TOKEN"),
    "MOODLEID1_": os.getenv("MOODLE_ID1_TOKEN")
}
WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
COURSES_FILE = "courses_list.json"
BBB_HISTORY = "bbb_history.json"
TZ = ZoneInfo("Africa/Casablanca")
NOTIFY_BEFORE_MIN = 15

MONTHS = {
    "janvier":1,"février":2,"fevrier":2,"mars":3,"avril":4,"mai":5,"juin":6,
    "juillet":7,"août":8,"aout":8,"septembre":9,"octobre":10,"novembre":11,"décembre":12,"decembre":12,
    "jan":1,"fév":2,"fev":2,"mar":3,"avr":4,"mai":5,"jun":6,"jul":7,"aoû":8,"aou":8,"sep":9,"oct":10,"nov":11,"déc":12,"dec":12
}

def jload(p): return json.load(open(p,encoding="utf-8")) if os.path.exists(p) else {}
def jsave(p,d): json.dump(d, open(p,"w",encoding="utf-8"), indent=2, ensure_ascii=False)

def nettoyer(txt: str) -> str:
    return re.sub(r"\s+"," ", txt.replace("\u00a0"," ")).strip() if txt else ""

def recuperer_cours_inscrits() -> List[Dict[str,Any]]:
    url = f"{BASE}/my/"
    r = requests.get(url, headers=HEAD, cookies=COOKIE, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    if 'login' in r.url or soup.find('form', id='login'):
        raise SystemExit("Cookies invalid / session expired.")
    liens = soup.find_all("a", href=re.compile(r"/course/view\.php\?id=\d+"))
    cours: Dict[int,Dict[str,Any]] = {}
    for a in liens:
        href = a.get("href","")
        m = re.search(r"id=(\d+)", href)
        if not m: continue
        cid = int(m.group(1))
        if cid in cours: continue
        title_tag = a.find(class_="course-name") or a.find(class_="coursename") or a
        name = nettoyer(title_tag.get_text(" ", strip=True))
        cours[cid] = {"id": cid, "fullname": name or f"Cours {cid}", "url": (href if href.startswith("http") else BASE+href)}
    jsave(COURSES_FILE, list(cours.values()))
    print(f"[OK] {len(cours)} cours saved -> {COURSES_FILE}")
    return list(cours.values())

def find_bbb_links_from_course(course_url: str) -> List[str]:
    r = requests.get(course_url, headers=HEAD, cookies=COOKIE, timeout=20)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    anchors = soup.find_all("a", href=re.compile(r"/mod/bigbluebuttonbn/view\.php\?id=\d+"))
    links = []
    for a in anchors:
        href = a.get("href","")
        if not href: continue
        full = href if href.startswith("http") else BASE + href
        links.append(full.split("#")[0])
    return sorted(set(links))

def parse_french_datetime(text: str) -> Optional[datetime]:
    if not text: return None
    s = text.lower().replace("\u00a0"," ")
    m = re.search(r"(\d{1,2})\s*(janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)\s*(\d{4}).*?(\d{1,2}:\d{2})", s)
    if m:
        d=int(m.group(1)); mon=m.group(2); y=int(m.group(3)); t=m.group(4)
        mm = MONTHS.get(mon, None)
        if mm:
            hh,mmn = map(int,t.split(":"))
            return datetime(y, mm, d, hh, mmn, tzinfo=TZ)
    m2 = re.search(r"(\d{1,2})\s*(janv|févr|fev|mar|avr|mai|jun|jul|aoû|aou|sep|oct|nov|déc|dec)[a-z]*\.?\s*(\d{4}).*?(\d{1,2}:\d{2})", s)
    if m2:
        d=int(m2.group(1)); mon=m2.group(2); y=int(m2.group(3)); t=m2.group(4)
        mm = MONTHS.get(mon, None) or MONTHS.get(mon[:3], None)
        if mm:
            hh,mmn = map(int,t.split(":"))
            return datetime(y, mm, d, hh, mmn, tzinfo=TZ)
    m3 = re.search(r"(\d{4}-\d{2}-\d{2}).*?(\d{2}:\d{2})", text)
    if m3:
        try:
            return datetime.fromisoformat(m3.group(1)+" "+m3.group(2)).replace(tzinfo=TZ)
        except:
            return None
    return None

def extract_start_from_bbb(html: str) -> Optional[Dict[str,str]]:
    soup = BeautifulSoup(html, "html.parser")
    tags = soup.find_all(
        ["span","p","div"], 
        string=re.compile(r"\d{1,2}\s+\w+.*\d{4}.*\d{1,2}:\d{2}")
    )
    for t in tags:
        txt = nettoyer(t.get_text(" ", strip=True))
        dt = parse_french_datetime(txt)
        if dt: return {"dt": dt.isoformat(), "excerpt": txt}
    txt = nettoyer(soup.get_text(" ", strip=True))
    dt = parse_french_datetime(txt)
    if dt:
        m = re.search(r".{0,60}\d{1,2}\s+\w+\s+\d{4}.*\d{1,2}:\d{2}.{0,60}", txt)
        excerpt = m.group(0).strip() if m else txt[:120]
        return {"dt": dt.isoformat(), "excerpt": excerpt}
    return None

def send_discord(title: str, desc: str, url: str) -> bool:
    if not WEBHOOK:
        print("[WARN] No DISCORD_WEBHOOK_URL")
        return False
    payload = {"embeds":[{"title": title, "description": desc, "timestamp": datetime.now(timezone.utc).isoformat(),
                         "fields":[{"name":"Lien","value":f"[Ouvrir]({url})"}], "color":3066993}]}
    try:
        r = requests.post(WEBHOOK, json=payload, timeout=15)
        r.raise_for_status()
        return True
    except Exception as e:
        print("Discord error", e); return False

def process_all_courses(course_list: List[Dict[str,Any]]):
    history = jload(BBB_HISTORY)
    now = datetime.now(TZ)
    for c in course_list:
        time.sleep(0.4)
        try:
            links = find_bbb_links_from_course(c["url"])
        except Exception as e:
            print("skip course", c["id"], e); continue
        if not links: continue
        for link in links:
            mid = re.search(r"id=(\d+)", link)
            keybase = f"bbb::{mid.group(1)}" if mid else link
            try:
                r = requests.get(link, headers=HEAD, cookies=COOKIE, timeout=15)
                r.raise_for_status()
            except Exception as e:
                print("skip link", link, e); continue
            info = extract_start_from_bbb(r.text)
            if not info: continue
            start = datetime.fromisoformat(info["dt"]).astimezone(TZ)
            key = f"{keybase}::{start.isoformat()}"
            if key in history and history[key].get("notified"): continue
            delta = (start - now).total_seconds()
            if 0 < delta <= NOTIFY_BEFORE_MIN*60:
                title = f"Session bientôt • {c['fullname']}"
                ok = send_discord(title, info.get("excerpt","Session"), link)
                history[key] = {"notified": ok, "course_id": c["id"], "when": datetime.now(timezone.utc).isoformat()}
                print(f"[NOTIF] {c['fullname']} @ {start.isoformat()} -> {ok}")
            else:
                history.setdefault(key, {"notified": False, "course_id": c["id"], "when": None})
    jsave(BBB_HISTORY, history)

if __name__ == "__main__":
    courses = recuperer_cours_inscrits()           
    for i,c in enumerate(courses,1):
        print(f"{i:03d}. {c['id']} - {c['fullname']}")
    while True:
        try:
            process_all_courses(courses)
        except Exception as e:
            print("loop error", e)
        time.sleep(60)

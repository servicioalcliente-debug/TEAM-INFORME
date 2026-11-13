import os
import sys
import io
import re
import csv
import json
import requests
import urllib3

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MOODLE_USER = os.getenv('MOODLE_USER', '1007305710')
MOODLE_PASS = os.getenv('MOODLE_PASS', 'Atcalsas2025*')
MOODLE_URL = os.getenv('MOODLE_URL', 'https://www.cursosatcal.com/team')

print(f"Starting extraction from Moodle for user: {MOODLE_USER}...")

session = requests.Session()
session.verify = False
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

login_url = f"{MOODLE_URL}/login/index.php"
r = session.get(login_url)
soup_token = re.search(r'name="logintoken"\s+value="([^"]+)"', r.text)
if not soup_token:
    print("Error: Could not obtain logintoken.")
    sys.exit(1)

logintoken = soup_token.group(1)

login_data = {
    'anchor': '',
    'logintoken': logintoken,
    'username': MOODLE_USER,
    'password': MOODLE_PASS
}

res = session.post(login_url, data=login_data)
sesskey_m = re.search(r'"sesskey":"([^"]+)"', res.text)
if not sesskey_m:
    print("Error: Could not login or sesskey not found.")
    sys.exit(1)

sesskey = sesskey_m.group(1)
print(f"Logged in successfully. Sesskey: {sesskey}")

# 1. Discover courses
courses_map = {}
for cat_id in [1, 2]:
    cat_url = f"{MOODLE_URL}/course/index.php?categoryid={cat_id}"
    rc = session.get(cat_url)
    c_links = re.findall(r'/course/view\.php\?id=(\d+)[^>]*>([^<]+)</a>', rc.text)
    for cid_str, name in c_links:
        clean_n = name.strip()
        if clean_n and cid_str != '1':
            courses_map[int(cid_str)] = clean_n

# Scan additional known course IDs
for cid in range(2, 35):
    if cid not in courses_map and cid != 1:
        rv = session.get(f"{MOODLE_URL}/course/view.php?id={cid}")
        if rv.status_code == 200:
            m_title = re.search(r'<title>([^<]+)</title>', rv.text)
            if m_title:
                t = m_title.group(1)
                if "Curso:" in t:
                    courses_map[cid] = t.split("Curso:")[1].split("|")[0].strip()

# Cleanup common name accents
for cid, cname in list(courses_map.items()):
    cname = cname.replace("Gestin", "Gestión").replace("Induccin", "Inducción")
    cname = cname.replace("Concientizacin", "Concientización").replace("fsica", "física")
    cname = cname.replace("Evaluacin", "Evaluación").replace("Econmico", "Económico")
    courses_map[cid] = cname

print(f"Total courses to scan: {len(courses_map)}")

students = {}
courses_summary = {}

for cid, cname in sorted(courses_map.items()):
    csv_url = f"{MOODLE_URL}/report/progress/index.php?course={cid}&activityinclude=all&activityorder=orderincourse&activitysection=-1&sesskey={sesskey}&format=csv"
    resp = session.get(csv_url)
    if resp.status_code != 200:
        continue

    content = resp.content.decode('utf-8-sig', errors='ignore')
    if "<html" in content[:300].lower() or "<!doctype" in content[:300].lower():
        continue

    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    if not rows or len(rows) < 2:
        continue

    headers = rows[0]
    all_named_cols = [(idx, headers[idx].strip()) for idx in range(2, len(headers)) if headers[idx].strip()]
    if all_named_cols:
        course_col_idx, _ = all_named_cols[-1]
        activity_cols = all_named_cols[:-1]
    else:
        activity_cols = []
        course_col_idx = None

    enrolled_count = 0
    completed_course_count = 0

    for row in rows[1:]:
        if not row or not any(row):
            continue
        s_name = row[0].strip() if len(row) > 0 else ""
        s_email = row[1].strip() if len(row) > 1 else ""

        if not s_email or "@" not in s_email or "<" in s_name or ">" in s_name or "<" in s_email:
            continue

        enrolled_count += 1
        user_key = s_email.lower().strip()

        if user_key not in students:
            students[user_key] = {
                'name': s_name,
                'email': s_email,
                'courses': {}
            }
        elif not students[user_key]['name'] and s_name:
            students[user_key]['name'] = s_name

        total_acts = len(activity_cols)
        completed_acts = 0
        act_details = {}
        act_dates = []

        for c_idx, act_title in activity_cols:
            if c_idx < len(row):
                val = row[c_idx].strip()
                date_val = row[c_idx + 1].strip() if c_idx + 1 < len(row) else ""
                is_done = (val.lower() == "finalizado")
                if is_done:
                    completed_acts += 1
                    if date_val:
                        act_dates.append(date_val)
                act_details[act_title] = {
                    'status': val,
                    'date': date_val
                }

        is_course_done = False
        course_done_date = ""
        if course_col_idx is not None and course_col_idx < len(row):
            val_course = row[course_col_idx].strip()
            date_course = row[course_col_idx + 1].strip() if course_col_idx + 1 < len(row) else ""
            if val_course.lower() == "finalizado":
                is_course_done = True
                course_done_date = date_course
                completed_course_count += 1

        if total_acts > 0:
            pct = round((completed_acts / total_acts) * 100, 1)
        else:
            pct = 100.0 if is_course_done else 0.0

        is_certified = (is_course_done or pct == 100.0)
        final_cert_date = course_done_date or (sorted(act_dates)[-1] if (is_certified and act_dates) else "")

        students[user_key]['courses'][str(cid)] = {
            'course_id': cid,
            'course_name': cname,
            'total_activities': total_acts,
            'completed_activities': completed_acts,
            'progress_pct': pct,
            'is_completed': is_certified,
            'completed_date': final_cert_date,
            'activities': act_details
        }

    courses_summary[str(cid)] = {
        'id': cid,
        'name': cname,
        'enrolled': enrolled_count,
        'completed': completed_course_count,
        'activities_count': len(activity_cols)
    }

print(f"Extracted {len(students)} verified students across {len(courses_summary)} courses.")

clean_data = {
    'courses_summary': courses_summary,
    'students': students
}

with open("moodle_progress_clean.json", "w", encoding="utf-8") as f:
    json.dump(clean_data, f, ensure_ascii=False, indent=2)

# Now update index.html & dashboard_estudiantes.html
with open("dashboard_estudiantes.html", "r", encoding="utf-8") as f:
    html_text = f.read()

# Replace the RAW_DATA json string safely
json_clean_str = json.dumps(clean_data, ensure_ascii=False)
html_updated = re.sub(
    r'const RAW_DATA = \{.*?\};\s+let flatRows =',
    f'const RAW_DATA = {json_clean_str};\n    let flatRows =',
    html_text,
    flags=re.DOTALL
)

with open("dashboard_estudiantes.html", "w", encoding="utf-8") as f:
    f.write(html_updated)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_updated)

print("Files index.html and moodle_progress_clean.json updated successfully!")

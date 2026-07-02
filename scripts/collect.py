#!/usr/bin/env python3
"""เก็บค่า PM2.5 รายชั่วโมงจาก GISTDA แล้วสรุปค่าเฉลี่ยรายวัน (วันปฏิทินไทย)
รันโดย GitHub Actions ทุก 6 ชม. — merge ข้อมูลใหม่เข้ากับของเดิม dedupe ตามชั่วโมง"""
import json, urllib.request, datetime, os, time
from concurrent.futures import ThreadPoolExecutor

CENTROIDS = json.load(open('data/centroids.json'))
HOURLY_DIR = 'data/hourly'
DAILY_FILE = 'data/daily.json'
KEEP_DAYS = 30

def fetch(code):
    lng, lat = CENTROIDS[code]
    url = f"https://pm25.gistda.or.th/rest/getPm25byLocation?lat={lat}&lng={lng}"
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=20) as r:
                j = json.load(r)
            return code, (j.get('data') or {}).get('graphHistory24hrs') or []
        except Exception:
            time.sleep(2)
    return code, []

def thai_parts(iso):
    t = datetime.datetime.fromisoformat(iso.replace('Z','+00:00')) + datetime.timedelta(hours=7)
    return t.strftime('%Y-%m-%d'), t.strftime('%H')

def main():
    os.makedirs(HOURLY_DIR, exist_ok=True)
    merged = {}  # date -> code -> hour -> val
    with ThreadPoolExecutor(max_workers=6) as ex:
        for code, hist in ex.map(fetch, CENTROIDS.keys()):
            for val, iso in hist:
                d, h = thai_parts(iso)
                merged.setdefault(d, {}).setdefault(code, {})[h] = round(float(val), 2)

    for d, codes in merged.items():
        path = f"{HOURLY_DIR}/{d}.json"
        existing = json.load(open(path)) if os.path.exists(path) else {}
        for code, hours in codes.items():
            existing.setdefault(code, {}).update(hours)
        json.dump(existing, open(path, 'w'), separators=(',',':'))

    # ตัดไฟล์เก่าเกิน KEEP_DAYS
    files = sorted(f for f in os.listdir(HOURLY_DIR) if f.endswith('.json'))
    for f in files[:-KEEP_DAYS]:
        os.remove(f"{HOURLY_DIR}/{f}")
        files.remove(f)

    # สรุป daily.json
    daily = []
    for f in sorted(os.listdir(HOURLY_DIR)):
        if not f.endswith('.json'): continue
        date = f[:-5]
        hourly = json.load(open(f"{HOURLY_DIR}/{f}"))
        data = {}
        for code, hours in hourly.items():
            vals = list(hours.values())
            data[code] = {'avg': round(sum(vals)/len(vals), 1), 'hours': len(vals)}
        daily.append({'date': date, 'data': data})
    json.dump(daily, open(DAILY_FILE, 'w'), separators=(',',':'), ensure_ascii=False)
    print(f"dates: {[d['date'] for d in daily]}")

if __name__ == '__main__':
    main()

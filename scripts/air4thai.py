#!/usr/bin/env python3
"""ดึงข้อมูลสถานีวัดจริง Air4Thai (กรมควบคุมมลพิษ) เฉพาะจังหวัดระยอง"""
import json, urllib.request, ssl, time, sys

URLS = [
    "https://air4thai.pcd.go.th/services/getNewAQI_JSON.php",
    "http://air4thai.pcd.go.th/services/getNewAQI_JSON.php",
    "https://air4thai.com/forweb/getAQI_JSON.php",
]

def try_fetch(url):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE  # cert ราชการบางทีไม่สมบูรณ์
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': 'application/json,*/*'})
    with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
        return json.load(r)

def main():
    j = None
    for url in URLS:
        for attempt in range(2):
            try:
                print(f"trying {url} (attempt {attempt+1})", flush=True)
                j = try_fetch(url)
                print("  -> OK")
                break
            except Exception as e:
                print(f"  -> {type(e).__name__}: {e}", flush=True)
                time.sleep(5)
        if j: break
    if not j:
        print("all sources failed"); sys.exit(1)

    out = []
    for st in j.get('stations', []):
        area = (st.get('areaTH') or '') + (st.get('nameTH') or '')
        if 'ระยอง' not in area: continue
        aqi = st.get('AQILast') or {}
        pm = (aqi.get('PM25') or {})
        val = pm.get('value')
        try: val = float(val)
        except (TypeError, ValueError): val = None
        if val is not None and val < 0: val = None
        try:
            lat=float(st.get('lat')); lng=float(st.get('long'))
        except (TypeError, ValueError):
            continue
        out.append({
            'id': st.get('stationID'), 'name': st.get('nameTH'),
            'area': st.get('areaTH'), 'lat': lat, 'lng': lng,
            'pm25': val, 'aqi': (aqi.get('AQI') or {}).get('aqi'),
            'date': aqi.get('date'), 'time': aqi.get('time')
        })
    json.dump(out, open('data/air4thai.json','w'), ensure_ascii=False, separators=(',',':'))
    print(f"stations: {len(out)}")
    if not out:
        print("WARNING: 0 Rayong stations — sample keys:", list((j.get('stations') or [{}])[0].keys()))

if __name__ == '__main__':
    main()

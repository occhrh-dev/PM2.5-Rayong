#!/usr/bin/env python3
"""ดึงข้อมูลสถานีวัดจริง Air4Thai (กรมควบคุมมลพิษ) เฉพาะจังหวัดระยอง"""
import json, urllib.request, time

URL = "http://air4thai.pcd.go.th/services/getNewAQI_JSON.php"

def main():
    for attempt in range(3):
        try:
            req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as r:
                j = json.load(r)
            break
        except Exception as e:
            if attempt == 2: raise
            time.sleep(5)

    out = []
    for st in j.get('stations', []):
        area = (st.get('areaTH') or '') + (st.get('nameTH') or '')
        if 'ระยอง' not in area: continue
        aqi = st.get('AQILast') or {}
        pm = (aqi.get('PM25') or {})
        out.append({
            'id': st.get('stationID'),
            'name': st.get('nameTH'),
            'area': st.get('areaTH'),
            'lat': float(st.get('lat')),
            'lng': float(st.get('long')),
            'pm25': None if pm.get('value') in (None,'-1','N/A') else float(pm.get('value')),
            'aqi': (aqi.get('AQI') or {}).get('aqi'),
            'date': aqi.get('date'), 'time': aqi.get('time')
        })
    json.dump(out, open('data/air4thai.json','w'), ensure_ascii=False, separators=(',',':'))
    print(f"stations: {len(out)}")

if __name__ == '__main__':
    main()

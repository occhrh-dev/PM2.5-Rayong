const AIR4THAI_URLS = [
  'https://air4thai.pcd.go.th/services/getNewAQI_JSON.php',
  // ปลายทางภาครัฐบางช่วงมีปัญหา TLS จึงเก็บ HTTP ไว้เป็น fallback ฝั่ง Worker เท่านั้น
  'http://air4thai.pcd.go.th/services/getNewAQI_JSON.php',
  'https://air4thai.com/forweb/getAQI_JSON.php',
];

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
  'Access-Control-Max-Age': '86400',
};

function jsonResponse(data, status = 200) {
  return Response.json(data, {
    status,
    headers: {
      ...CORS_HEADERS,
      'Cache-Control': status === 200
        ? 'public, max-age=60, s-maxage=60, must-revalidate'
        : 'no-store',
      'Vary': 'Origin',
    },
  });
}

function normalizeStations(payload) {
  const stations = Array.isArray(payload?.stations) ? payload.stations : [];

  return stations.flatMap((station) => {
    const area = `${station.areaTH || ''}${station.nameTH || ''}`;
    if (!area.includes('ระยอง')) return [];

    const latest = station.AQILast || {};
    const pm25 = Number(latest.PM25?.value);
    const lat = Number(station.lat);
    const lng = Number(station.long);
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) return [];

    return [{
      id: station.stationID || '',
      name: station.nameTH || '',
      area: station.areaTH || '',
      lat,
      lng,
      pm25: Number.isFinite(pm25) && pm25 >= 0 ? pm25 : null,
      aqi: latest.AQI?.aqi ?? null,
      date: latest.date || '',
      time: latest.time || '',
    }];
  });
}

export default {
  async fetch(request) {
    const url = new URL(request.url);

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }

    if (!['GET', 'HEAD'].includes(request.method)) {
      return jsonResponse({ error: 'Method not allowed' }, 405);
    }

    if (url.pathname !== '/' && url.pathname !== '/air4thai') {
      return jsonResponse({ error: 'Not found' }, 404);
    }

    const failures = [];
    for (const sourceUrl of AIR4THAI_URLS) {
      try {
        const upstream = await fetch(sourceUrl, {
          headers: {
            'Accept': 'application/json',
            'User-Agent': 'PM2.5-Rayong/1.0',
          },
          cf: { cacheEverything: true, cacheTtl: 60 },
        });
        if (!upstream.ok) {
          failures.push(`${new URL(sourceUrl).hostname}: HTTP ${upstream.status}`);
          continue;
        }

        const payload = await upstream.json();
        const stations = normalizeStations(payload);
        if (!stations.length) {
          failures.push(`${new URL(sourceUrl).hostname}: no Rayong stations`);
          continue;
        }

        return jsonResponse({
          stations,
          fetchedAt: new Date().toISOString(),
          source: new URL(sourceUrl).hostname,
        });
      } catch (error) {
        failures.push(`${new URL(sourceUrl).hostname}: ${error instanceof Error ? error.message : 'fetch failed'}`);
      }
    }

    console.error(JSON.stringify({ event: 'air4thai_fetch_failed', failures }));
    return jsonResponse({ error: 'Air4Thai unavailable' }, 502);
  },
};

// PM2.5 @RY service worker
const VERSION='v6';
const CORE=['./','index.html','rayong_tambon.geojson','data/centroids.json','manifest.json'];

self.addEventListener('install',e=>{
  e.waitUntil(caches.open(VERSION).then(c=>c.addAll(CORE)).then(()=>self.skipWaiting()));
});
self.addEventListener('activate',e=>{
  e.waitUntil(caches.keys().then(keys=>Promise.all(
    keys.filter(k=>k!==VERSION).map(k=>caches.delete(k))
  )).then(()=>self.clients.claim()));
});
self.addEventListener('fetch',e=>{
  const url=new URL(e.request.url);
  if(url.origin!==location.origin) return; // GISTDA/MapTiler ผ่านตรง ไม่ cache
  if(url.pathname.includes('/data/') || url.pathname.endsWith('/') || url.pathname.endsWith('/index.html')){
    // ข้อมูลฝุ่นและหน้าแรก: network-first, ออฟไลน์ค่อยใช้ cache
    e.respondWith(fetch(e.request).then(r=>{
      const cp=r.clone(); caches.open(VERSION).then(c=>c.put(e.request,cp)); return r;
    }).catch(()=>caches.match(e.request)));
  }else{
    // ไฟล์ static: cache-first
    e.respondWith(caches.match(e.request).then(hit=>hit||fetch(e.request).then(r=>{
      const cp=r.clone(); caches.open(VERSION).then(c=>c.put(e.request,cp)); return r;
    })));
  }
});

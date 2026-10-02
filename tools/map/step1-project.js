const fs = require('fs');
const g = JSON.parse(fs.readFileSync('adm1.geojson', 'utf8'));

const NEW = { 'UA-14': 'Донецкая Народная Республика', 'UA-09': 'Луганская Народная Республика',
              'UA-23': 'Запорожская область', 'UA-65': 'Херсонская область' };
const FIX = { 'UA-43': 'Республика Крым', 'RU-ALT': 'Алтайский край', 'RU-AL': 'Республика Алтай', 'RU-X01~': null };

const rad = Math.PI / 180, f1 = 52 * rad, f2 = 64 * rad, l0 = 100;
const t = f => Math.tan(Math.PI / 4 + f / 2);
const n = Math.log(Math.cos(f1) / Math.cos(f2)) / Math.log(t(f2) / t(f1));
const F = Math.cos(f1) * Math.pow(t(f1), n) / n;
function proj([lon, lat]) {
    if (lon < 0) lon += 360;
    const r = F / Math.pow(t(lat * rad), n), a = n * (lon - l0) * rad;
    return [r * Math.sin(a), -r * Math.cos(a)];
}
const walk = c => typeof c[0] === 'number' ? proj(c) : c.map(walk);

const out = [];
for (const f of g.features) {
    const p = f.properties, iso = p.iso_3166_2;
    if (!(p.adm0_a3 === 'RUS' || NEW[iso])) continue;
    let id = iso === 'RU-X01~' ? 'RU-YAN' : iso;
    const name = NEW[iso] || (iso in FIX ? FIX[iso] : p.name_ru);
    out.push({ type: 'Feature', properties: { id, name: name || '' },
        geometry: { type: f.geometry.type, coordinates: walk(f.geometry.coordinates) } });
}
fs.writeFileSync('ru-proj.json', JSON.stringify({ type: 'FeatureCollection', features: out }));
console.log('features:', out.length);

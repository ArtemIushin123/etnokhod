const fs = require('fs');
const rd = f => JSON.parse(fs.readFileSync(f, 'utf8'));
const outline = rd('ru-outline.json'), inner = rd('ru-inner.json'), regions = rd('ru-regions.json'), points = rd('ru-points.json');

const W = 1000, PAD = 8, MIN_AREA = 1.5;
let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
(function w(c) { if (typeof c[0] === 'number') { x0 = Math.min(x0, c[0]); x1 = Math.max(x1, c[0]); y0 = Math.min(y0, c[1]); y1 = Math.max(y1, c[1]); } else c.forEach(w); })(outline.geometries[0].coordinates);
const k = (W - 2 * PAD) / (x1 - x0), H = Math.ceil((y1 - y0) * k + 2 * PAD);
const P = ([x, y]) => [+(PAD + (x - x0) * k).toFixed(1), +(PAD + (y1 - y) * k).toFixed(1)];

const area = r => { let s = 0; for (let i = 0, j = r.length - 1; i < r.length; j = i++) s += (r[j][0] + r[i][0]) * (r[j][1] - r[i][1]); return Math.abs(s / 2); };
function ring(r, close) {
    const pts = r.map(P).filter((p, i, a) => i === 0 || p[0] !== a[i - 1][0] || p[1] !== a[i - 1][1]);
    return 'M' + pts.map(p => p.join(' ')).join('L') + (close ? 'Z' : '');
}
function polyPath(geom) {
    const polys = geom.type === 'Polygon' ? [geom.coordinates] : geom.coordinates;
    return polys.filter(p => area(p[0].map(P)) >= MIN_AREA).map(p => p.map(r => ring(r, true)).join('')).join('');
}
function linePath(geom) {
    const ls = geom.type === 'LineString' ? [geom.coordinates] : geom.coordinates;
    return ls.map(l => ring(l, false)).join('');
}

const res = {
    viewBox: `0 0 ${W} ${H}`,
    outline: polyPath(outline.geometries[0]),
    inner: inner.geometries.map(linePath).join(''),
    regions: {}, points: {}
};
for (const f of regions.features) res.regions[f.properties.id] = { name: f.properties.name, d: polyPath(f.geometry) };
for (const f of points.features) res.points[f.properties.id] = P(f.geometry.coordinates);
fs.writeFileSync('map-data.json', JSON.stringify(res));
console.log('viewBox', res.viewBox, 'outline', res.outline.length, 'inner', res.inner.length);
for (const id of ['RU-BA', 'RU-TA', 'RU-DA', 'RU-TY', 'RU-SA']) console.log(id, res.regions[id].name, res.points[id], res.regions[id].d.length);
console.log('names:', Object.values(res.regions).map(r => r.name).join(', '));

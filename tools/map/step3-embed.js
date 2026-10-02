// Шаг 3: печатает константу RU_MAP для index.html и координаты точек для MAP.
// Какие регионы нужны в игре: id в игре → код ISO 3166-2 в Natural Earth.
const m = require('./map-data.json');
// Регион игры может состоять из нескольких субъектов (массив кодов): Крым = Республика Крым + Севастополь.
const IDS = { bashkortostan: 'RU-BA', tatarstan: 'RU-TA', dagestan: 'RU-DA', tuva: 'RU-TY', yakutia: 'RU-SA',
              crimea: ['UA-43', 'UA-40'] };
const list = iso => [].concat(iso);

const regions = Object.entries(IDS).map(([id, iso]) => `            ${id}:'${list(iso).map(c => m.regions[c].d).join('')}'`).join(',\n');
const js = `    /* Карта РФ: 89 субъектов, Natural Earth admin-1 1:10m (общественное достояние) + ДНР, ЛНР,
       Запорожская и Херсонская области. Проекция +proj=lcc +lat_1=52 +lat_2=64 +lon_0=100,
       ширина 1000. Пересобрать: tools/map/README (скрипты step1–step3). */
    const RU_MAP = {
        viewBox:'${m.viewBox}',
        outline:'${m.outline}',
        inner:'${m.inner}',
        regions:{
${regions}
        }
    };`;
require('fs').writeFileSync('ru-map.js', js);
for (const [id, iso] of Object.entries(IDS)) console.log(id, m.points[list(iso)[0]].map(Math.round).join(', '));

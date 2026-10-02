const m = require('./map-data.json');
const IDS = { bashkortostan: 'RU-BA', tatarstan: 'RU-TA', dagestan: 'RU-DA', tuva: 'RU-TY', yakutia: 'RU-SA',
              crimea: ['UA-43', 'UA-40'] };
const list = iso => [].concat(iso);

const regions = Object.entries(IDS).map(([id, iso]) => `            ${id}:'${list(iso).map(c => m.regions[c].d).join('')}'`).join(',\n');
const js = `    const RU_MAP = {
        viewBox:'${m.viewBox}',
        outline:'${m.outline}',
        inner:'${m.inner}',
        regions:{
${regions}
        }
    };`;
require('fs').writeFileSync('ru-map.js', js);
for (const [id, iso] of Object.entries(IDS)) console.log(id, m.points[list(iso)[0]].map(Math.round).join(', '));

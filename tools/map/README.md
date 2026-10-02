# Карта РФ для index.html

Скрипты, которыми собрана константа `RU_MAP` в `index.html`. Игре они не нужны, только для пересборки карты.

- Источник: Natural Earth admin-1, 1:10m (общественное достояние, https://www.naturalearthdata.com).
- В Natural Earth ДНР, ЛНР, Запорожская и Херсонская области числятся за Украиной, `step1` добавляет их к РФ. Итого 89 субъектов.
- Проекция: `+proj=lcc +lat_1=52 +lat_2=64 +lon_0=100`, ширина 1000.

## Пересборка

Запускать из этой папки (`tools/map`). Нужен Node.js; mapshaper запускается через `npx`, в проект не ставится.

```sh
curl -L -o adm1.geojson https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_1_states_provinces.geojson
node step1-project.js
npx mapshaper -i ru-proj.json -dissolve id copy-fields=name -simplify 3% keep-shapes -o ru-regions.json format=geojson precision=0.000001
npx mapshaper -i ru-regions.json -innerlines -o ru-inner.json format=geojson
npx mapshaper -i ru-regions.json -dissolve -o ru-outline.json format=geojson
npx mapshaper -i ru-regions.json -points inner -o ru-points.json format=geojson
node step2-svg.js
node step3-embed.js
```

`step3-embed.js` пишет `ru-map.js` (заменить им блок `const RU_MAP = {...}` в `index.html`) и печатает `x, y` для `MAP`.

Новый регион в игре: добавить `id игры: 'код ISO'` (или массив кодов, если регион из нескольких субъектов, как Крым) в `IDS` в `step3-embed.js` (коды печатает `step2-svg.js`, например `RU-TA`), пересобрать и добавить точку в `MAP`.

Промежуточные файлы (`adm1.geojson` около 40 МБ, `ru-*.json`, `map-data.json`, `ru-map.js`) в репозиторий не кладём.

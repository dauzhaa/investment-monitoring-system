<template>
  <v-container fluid class="pa-4 bg-grey-lighten-4" style="min-height: 100vh;">
    <v-card elevation="2" class="rounded-lg mb-4 px-4 py-3">
      <v-row align="center" dense>
        <v-col cols="12" md="3">
          <h2 class="text-h5 font-weight-bold text-blue-darken-4 mb-1">Центр ИПО</h2>
          <div class="text-caption text-grey-darken-1">Аналитика надёжности (2024-2025)</div>
        </v-col>
        <v-col cols="12" md="9">
          <v-row dense>
            <v-col cols="12" sm="3">
              <v-autocomplete v-model="filters.districts" :items="districtList" label="Район" multiple chips closable-chips density="compact" variant="outlined" hide-details clearable></v-autocomplete>
            </v-col>
            <v-col cols="12" sm="2">
              <v-select v-model="filters.year" :items="['Все', 2024, 2025]" label="Год" density="compact" variant="outlined" hide-details></v-select>
            </v-col>
            <v-col cols="12" sm="3">
              <v-select v-model="filters.category" :items="['Все', 'МО', 'Подвед', 'ВУЗ', 'Иные']" label="Категория" density="compact" variant="outlined" hide-details></v-select>
            </v-col>
            <v-col cols="12" sm="2">
              <v-select v-model="filters.smp" :items="['Все', 'Только СМП', 'Без СМП']" label="СМП" density="compact" variant="outlined" hide-details></v-select>
            </v-col>
            <v-col cols="12" sm="2">
              <v-select v-model="filters.ipoType" :items="['Все', 'Проблемные']" label="Тип ИПО" density="compact" variant="outlined" hide-details></v-select>
            </v-col>
          </v-row>
        </v-col>
      </v-row>
    </v-card>

    <v-row class="mb-4" dense>
      <v-col cols="12" md="4" v-for="(kpi, idx) in kpiData" :key="idx">
        <v-card elevation="2" class="rounded-lg text-center pa-2">
          <div class="text-subtitle-2 font-weight-bold text-grey-darken-2 mt-2">{{ kpi.title }}</div>
          <div :ref="el => gaugeRefs[idx] = el" style="height: 160px; margin-top: -10px;"></div>
          <div class="d-flex justify-center align-center pb-3" style="margin-top: -20px;">
            <span class="text-caption text-grey mr-2">Регион: {{ kpi.avg }}</span>
            <v-chip size="x-small" :color="kpi.delta > 0 ? 'success' : 'error'" variant="flat">
              <v-icon start size="12">{{ kpi.delta > 0 ? 'mdi-arrow-up' : 'mdi-arrow-down' }}</v-icon>
              {{ Math.abs(kpi.delta) }} ({{ kpi.desc }})
            </v-chip>
          </div>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mb-4" dense>
      <v-col cols="12" md="8">
        <v-card elevation="2" class="rounded-lg h-100">
          <v-card-title class="text-subtitle-1 font-weight-bold">Динамика ИПО по кварталам</v-card-title>
          <v-card-text><div ref="lineRef" style="height: 300px; width: 100%;"></div></v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="4">
        <v-card elevation="2" class="rounded-lg h-100">
          <v-card-title class="text-subtitle-1 font-weight-bold">Воронка: План → Факт → Отчёт</v-card-title>
          <v-card-text><div ref="funnelRef" style="height: 300px; width: 100%;"></div></v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mb-4" dense>
      <v-col cols="12" md="7">
        <v-card elevation="2" class="rounded-lg h-100">
          <v-card-title class="text-subtitle-1 font-weight-bold">Матрица организаций: Дисциплина × Исполнение</v-card-title>
          <v-card-text><div ref="scatterRef" style="height: 450px; width: 100%;"></div></v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="5">
        <v-card elevation="2" class="rounded-lg h-100">
          <v-card-title class="text-subtitle-1 font-weight-bold">Профиль надёжности</v-card-title>
          <v-card-text><div ref="radarRef" style="height: 450px; width: 100%;"></div></v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mb-4" dense>
      <v-col cols="12" md="8">
        <v-card elevation="2" class="rounded-lg h-100">
          <v-card-title class="text-subtitle-1 font-weight-bold">Распределение профилей по районам (Стек)</v-card-title>
          <v-card-text><div ref="stackRef" style="height: 400px; width: 100%;"></div></v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="4">
        <v-card elevation="2" class="rounded-lg h-100 d-flex flex-column">
          <v-card-title class="text-subtitle-1 font-weight-bold bg-green-lighten-5 text-green-darken-3">ТОП-5 Организаций</v-card-title>
          <v-table density="compact" class="text-caption">
            <tbody>
              <tr v-for="org in topOrgs" :key="org.name">
                <td>{{ org.name }}</td><td class="text-right font-weight-bold text-green">{{ org.ipo }}</td>
              </tr>
            </tbody>
          </v-table>
          <v-divider></v-divider>
          <v-card-title class="text-subtitle-1 font-weight-bold bg-red-lighten-5 text-red-darken-3 mt-auto">АНТИ-ТОП 5 Организаций</v-card-title>
          <v-table density="compact" class="text-caption">
            <tbody>
              <tr v-for="org in bottomOrgs" :key="org.name">
                <td>{{ org.name }}</td><td class="text-right font-weight-bold text-red">{{ org.ipo }}</td>
              </tr>
            </tbody>
          </v-table>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mb-4" dense>
      <v-col cols="12">
        <v-card elevation="2" class="rounded-lg">
          <v-card-title class="text-subtitle-1 font-weight-bold">Детальная матрица компонентов ИПО (по убыванию рейтинга)</v-card-title>
          <v-card-text><div ref="heatmapRef" :style="{ height: heatmapHeight + 'px', width: '100%' }"></div></v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row dense>
      <v-col cols="12">
        <v-card elevation="2" class="rounded-lg">
          <v-card-title class="text-subtitle-1 font-weight-bold">Календарь сдачи отчётов (Эффект дедлайна 14-го числа)</v-card-title>
          <v-card-text><div ref="calendarRef" style="height: 250px; width: 100%;"></div></v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, shallowRef, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import axios from 'axios'

// --- СОСТОЯНИЕ И ФИЛЬТРЫ ---
const filters = reactive({
  districts: [], year: 2024, category: 'Все', smp: 'Все', ipoType: 'Все'
})
const districtList = ['Тюмень г.', 'Тобольск г.', 'Ишим г.', 'Тюменский', 'Вагайский', 'Уватский', 'Ялуторовск г.', 'Заводоуковский', 'Абатский', 'Викуловский']

// --- РЕФЫ ДОМ-ЭЛЕМЕНТОВ ---
const gaugeRefs = ref([])
const lineRef = ref(null)
const funnelRef = ref(null)
const scatterRef = ref(null)
const radarRef = ref(null)
const stackRef = ref(null)
const heatmapRef = ref(null)
const calendarRef = ref(null)
const charts = shallowRef({})

const heatmapHeight = ref(500) // Реактивная переменная для высоты матрицы

// --- РЕАКТИВНЫЕ ДАННЫЕ (Пустые по умолчанию) ---
const kpiData = ref([
  { title: 'Дисциплина (ρ)', val: 0, avg: 0, delta: 0, desc: '-' },
  { title: 'Качество (α)', val: 0, avg: 0, delta: 0, desc: '-' },
  { title: 'Исполнение (β)', val: 0, avg: 0, delta: 0, desc: '-' }
])
const topOrgs = ref([])
const bottomOrgs = ref([])

// --- ЗАГРУЗКА ДАННЫХ С БЭКЕНДА ---
const fetchData = async () => {
  try {
    const response = await axios.get('/api/v1/analytics/ipo', { params: filters })
    const data = response.data

    // 1. Обновляем таблицы и KPI
    if (data.kpi) kpiData.value = data.kpi
    if (data.top_orgs) topOrgs.value = data.top_orgs
    if (data.bottom_orgs) bottomOrgs.value = data.bottom_orgs

    // 2. Спидометры (KPI)
    if (data.kpi) {
      data.kpi.forEach((kpi, idx) => {
        if (charts.value[`gauge${idx}`]) {
          charts.value[`gauge${idx}`].setOption({ series: [{ data: [{ value: kpi.val }] }] })
        }
      })
    }

    // 3. Воронка
    if (data.funnel && charts.value.funnel) {
      const funnelColors = ['#1976D2', '#FFB300', '#4CAF50']
      const formattedFunnel = data.funnel.map((item, idx) => ({ ...item, itemStyle: { color: funnelColors[idx] } }))
      charts.value.funnel.setOption({ series: [{ data: formattedFunnel }] })
    }

    // 4. Матрица (Scatter)
    if (data.scatter && charts.value.scatter) {
      charts.value.scatter.setOption({ series: [{ data: data.scatter }] })
    }

    // 5. Профиль надежности (Radar)
    if (data.radar && charts.value.radar) {
      charts.value.radar.setOption({
        series: [{
          data: [
            { value: data.radar, name: 'Выбранный срез', areaStyle: { color: 'rgba(25, 118, 210, 0.4)' }, lineStyle: { color: '#1976D2' } },
            { value: [100, 100, 100, 100], name: 'Идеал', areaStyle: { color: 'transparent' }, lineStyle: { type: 'dashed', color: '#9E9E9E' } }
          ]
        }]
      })
    }

    // 6. Распределение по районам (Stacked Bar)
    if (data.stack && charts.value.stack) {
      charts.value.stack.setOption({
        yAxis: { data: data.stack.categories },
        series: data.stack.series
      })
    }

    // 7. Детальная матрица (Heatmap)
    if (data.heatmap && charts.value.heatmap) {
      // ИЗМЕНЕНО: Динамическая высота матрицы
      heatmapHeight.value = Math.max(400, data.heatmap.xAxis.length * 28 + 150)
      
      // Даем DOM обновиться, чтобы контейнер принял новую высоту перед ресайзом
      await nextTick()
      charts.value.heatmap.resize()

      // ПЕРЕВОРАЧИВАЕМ координаты: [район, метрика, значение] -> [метрика, район, значение]
      const transposedData = data.heatmap.data.map(item => [item[1], item[0], item[2]])

      charts.value.heatmap.setOption({
        yAxis: { data: data.heatmap.xAxis }, // <-- КЛАДЕМ РАЙОНЫ В ОСЬ Y (а не в X)
        series: [{ data: transposedData }]
      })
    }

    // 8. Календарь сдачи отчетов
    if (data.calendar && charts.value.calendar) {
      // Защита от NaN: если выбран фильтр "Все", берем 2024 год по умолчанию
      const currentYear = filters.year === 'Все' ? 2024 : parseInt(filters.year)
      const nextYear = currentYear + 1

      charts.value.calendar.setOption({
        calendar: {
          range: [`${currentYear}-01-01`, `${nextYear}-03-31`] // Динамически обновляем диапазон
        },
        series: { data: data.calendar }
      })
    }

    // 9. Динамика по кварталам (Line Chart)
    if (data.line && charts.value.line) {
      charts.value.line.setOption({
        xAxis: { data: data.line.xAxis },
        series: [
          { data: data.line.seriesData, name: 'Выбранный срез' },
          { data: data.line.avgData, name: 'Регион (среднее)' }
        ]
      })
    }

  } catch (error) {
    console.error("Ошибка загрузки аналитики ИПО:", error)
  }
}

// Автоматически перезапрашивать данные, если изменились фильтры
watch(filters, () => {
  fetchData()
}, { deep: true })

// --- ИНИЦИАЛИЗАЦИЯ ГРАФИКОВ (КАРКАСЫ БЕЗ ДАННЫХ) ---

const initGauges = () => {
  gaugeRefs.value.forEach((el, idx) => {
    if (!el) return
    const chart = echarts.init(el)
    chart.setOption({
      series: [{
        type: 'gauge', startAngle: 180, endAngle: 0, min: 0, max: 100, radius: '120%', center: ['50%', '75%'],
        axisLine: { lineStyle: { width: 15, color: [[0.3, '#d32f2f'], [0.5, '#f57c00'], [0.7, '#fbc02d'], [0.9, '#81c784'], [1, '#388e3c']] } },
        pointer: { length: '60%', width: 5 }, axisTick: { show: false }, splitLine: { show: false }, axisLabel: { show: false },
        detail: { fontSize: 24, offsetCenter: [0, '-20%'], formatter: '{value}', color: 'inherit', fontWeight: 'bold' },
        data: [{ value: 0 }] // Начинаем с нуля
      }]
    })
    charts.value[`gauge${idx}`] = chart
  })
}

const initLineChart = () => {
  const chart = echarts.init(lineRef.value)
  chart.setOption({
    tooltip: { trigger: 'axis' }, legend: { data: ['Выбранный срез', 'Регион (среднее)'], bottom: 0 },
    grid: { left: '8%', right: '5%', top: '10%', bottom: '15%' },
    xAxis: { type: 'category', data: ['Q1 2024', 'Q2 2024', 'Q3 2024', 'Q4 2024', 'Q1 2025', 'Q2 2025'], boundaryGap: false },
    yAxis: { type: 'value', min: 40, max: 100 },
    series: [
      { name: 'Выбранный срез', type: 'line', data: [], smooth: true, lineStyle: { width: 3, color: '#1976D2' }, symbolSize: 8 },
      { name: 'Регион (среднее)', type: 'line', data: [], smooth: true, lineStyle: { type: 'dashed', color: '#9E9E9E' }, symbol: 'none' }
    ]
  })
  return chart
}

const initFunnel = () => {
  const chart = echarts.init(funnelRef.value)
  chart.setOption({
    tooltip: { trigger: 'item', formatter: '{b} <br/>{c} млн ₽' },
    series: [{
      type: 'funnel', left: '10%', top: '5%', bottom: '5%', width: '80%', gap: 2,
      label: { show: true, position: 'inside', formatter: '{b}\n{c} млн', fontSize: 12 },
      itemStyle: { borderColor: '#fff', borderWidth: 1 },
      data: [] // Ожидаем из API
    }]
  })
  return chart
}

const initScatter2x2 = () => {
  const chart = echarts.init(scatterRef.value)
  chart.setOption({
    tooltip: { formatter: p => `<b>${p.data[3]} (${p.data[4]})</b><br/>Дисциплина (X): ${p.data[0]}<br/>Исполнение (Y): ${p.data[1]}<br/>Объем: ${p.data[2]} млн ₽` },
    grid: { left: '8%', right: '5%', bottom: '10%', top: '5%' },
    xAxis: { name: 'Дисциплина (ρ)', min: 0, max: 100, splitLine: { show: false } },
    yAxis: { name: 'Исполнение (β)', min: 0, max: 100, splitLine: { show: false } },
    series: [{
      type: 'scatter', symbolSize: d => Math.sqrt(d[2]) * 2, data: [], // Ожидаем из API
      itemStyle: { color: '#1976D2', opacity: 0.8 },
      markArea: {
        silent: true, label: { position: 'insideTopLeft', color: '#000', opacity: 0.5, fontSize: 14, fontWeight: 'bold' },
        data: [
          [{ xAxis: 50, yAxis: 50, itemStyle: { color: 'rgba(56, 142, 60, 0.1)' }, name: 'Образцовые' }, { xAxis: 100, yAxis: 100 }],
          [{ xAxis: 0, yAxis: 50, itemStyle: { color: 'rgba(245, 124, 0, 0.1)' }, name: 'Безалаберные' }, { xAxis: 50, yAxis: 100 }],
          [{ xAxis: 50, yAxis: 0, itemStyle: { color: 'rgba(251, 192, 45, 0.1)' }, name: 'Слабые в освоении' }, { xAxis: 100, yAxis: 50 }],
          [{ xAxis: 0, yAxis: 0, itemStyle: { color: 'rgba(211, 47, 47, 0.1)' }, name: 'Проблемные' }, { xAxis: 50, yAxis: 50 }]
        ]
      }
    }]
  })
  return chart
}

const initRadar = () => {
  const chart = echarts.init(radarRef.value)
  chart.setOption({
    tooltip: {}, legend: { data: ['Выбранный срез', 'Идеал'], bottom: 0 },
    radar: { radius: '65%', indicator: [{ name: 'Дисциплина', max: 100 }, { name: 'Качество', max: 100 }, { name: 'Исполнение', max: 100 }, { name: 'Общий ИПО', max: 100 }] },
    series: [{
      type: 'radar',
      data: [
        { value: [], name: 'Выбранный срез', areaStyle: { color: 'rgba(25, 118, 210, 0.4)' }, lineStyle: { color: '#1976D2' } },
        { value: [100, 100, 100, 100], name: 'Идеал', areaStyle: { color: 'transparent' }, lineStyle: { type: 'dashed', color: '#9E9E9E' } }
      ]
    }]
  })
  return chart
}

const initStackedBar = () => {
  const chart = echarts.init(stackRef.value)
  const dists = ['Тюмень г.', 'Тюменский', 'Тобольск г.', 'Ишим г.', 'Заводоуковский', 'Вагайский'].reverse()
  chart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } }, legend: { bottom: 0 },
    grid: { left: '15%', right: '5%', top: '5%', bottom: '15%' },
    xAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
    yAxis: { type: 'category', data: dists },
    series: [] // Пока пусто, ждем данные от API в будущем
  })
  return chart
}

const initHeatmap = () => {
  const chart = echarts.init(heatmapRef.value)
  chart.setOption({
    tooltip: { 
      position: 'top',
      formatter: (p) => {
        const metric = p.name
        const district = chart.getOption().yAxis[0].data[p.data[1]]
        return `<b>${district}</b><br/>${metric}: <b>${p.data[2]}</b>`
      }
    },
    grid: { 
      left: 180,    // больше места под длинные названия районов
      right: 40, 
      top: 50, 
      bottom: 100   // место под visualMap
    },
    xAxis: { 
      type: 'category', 
      data: ['Дисциплина (ρ)', 'Качество (α)', 'Исполнение (β)', '% вовремя', '% плана', 'Орг.'],
      position: 'top',
      axisLabel: { interval: 0, fontSize: 12 },
      splitArea: { show: true }
    },
    yAxis: { 
      type: 'category', 
      data: [], // Районы будут здесь
      inverse: true,
      axisLabel: { 
        interval: 0,        // показывать ВСЕ метки без пропусков
        fontSize: 11,
        width: 170,
        overflow: 'truncate'
      },
      splitArea: { show: true }
    },
    visualMap: {
      min: 0, max: 100, calculable: true, 
      orient: 'horizontal', left: 'center', bottom: 10,
      inRange: { color: ['#FFEBEE', '#FFF59D', '#C8E6C9', '#4CAF50'] }
    },
    series: [{
      type: 'heatmap',
      data: [],
      label: { 
        show: true, 
        fontSize: 11,
        formatter: (p) => p.data[2] != null ? p.data[2] : ''
      },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
    }]
  })
  return chart
}

const initCalendar = () => {
  const chart = echarts.init(calendarRef.value)
  
  // Защита от NaN при первичной инициализации
  const currentYear = filters.year === 'Все' ? 2024 : parseInt(filters.year)
  const nextYear = currentYear + 1
  
  chart.setOption({
    tooltip: { formatter: p => `${p.value[0]}: <b>${p.value[1]} отчётов</b>` },
    visualMap: {
      min: 0, max: 20, calculable: true, orient: 'horizontal', left: 'center', top: 0,
      inRange: { color: ['#ebedf0', '#c6e48b', '#7bc96f', '#239a3b', '#196127'] }
    },
    calendar: {
      top: 60, bottom: 10, left: 30, right: 30,
      range: [`${currentYear}-01-01`, `${nextYear}-03-31`],
      cellSize: ['auto', 18],
      dayLabel: { firstDay: 1, nameMap: 'ru' },
      monthLabel: { nameMap: 'ru' },
      itemStyle: { borderWidth: 0.5, borderColor: '#fff' }
    },
    series: { type: 'heatmap', coordinateSystem: 'calendar', data: [] }
  })
  return chart
}

onMounted(() => {
  setTimeout(() => {
    initGauges()
    charts.value.line = initLineChart()
    charts.value.funnel = initFunnel()
    charts.value.scatter = initScatter2x2()
    charts.value.radar = initRadar()
    charts.value.stack = initStackedBar()
    charts.value.heatmap = initHeatmap()
    charts.value.calendar = initCalendar()

    // Как только графики инициализированы, запрашиваем реальные данные!
    fetchData()
  }, 100)
  window.addEventListener('resize', resizeCharts)
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeCharts)
  Object.values(charts.value).forEach(c => c?.dispose())
})

const resizeCharts = () => { Object.values(charts.value).forEach(c => c?.resize()) }
</script>
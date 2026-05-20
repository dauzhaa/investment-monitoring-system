<template>
  <v-container fluid class="pa-4 bg-grey-lighten-4" style="min-height: 100vh;">
    <v-dialog v-model="matrixDialog.show" max-width="500">
      <v-card class="rounded-lg">
        <v-card-title class="bg-blue-darken-4 text-white text-subtitle-1">Детали организации</v-card-title>
        <v-card-text class="pt-4">
          <div class="text-h6 mb-2">{{ matrixDialog.data.name }}</div>
          <v-divider class="mb-3"></v-divider>
          <div class="d-flex justify-space-between mb-1">
            <span class="text-grey">Дисциплина:</span><span class="font-weight-bold">{{ matrixDialog.data.x }}%</span>
          </div>
          <div class="d-flex justify-space-between mb-1">
            <span class="text-grey">Исполнение:</span><span class="font-weight-bold">{{ matrixDialog.data.y }}%</span>
          </div>
          <div class="d-flex justify-space-between">
            <span class="text-grey">Объем инвестиций:</span><span class="font-weight-bold text-green">{{ matrixDialog.data.val }} млн ₽</span>
          </div>
        </v-card-text>
        <v-card-actions><v-spacer></v-spacer><v-btn color="primary" variant="text" @click="matrixDialog.show = false">Закрыть</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="matrixAreaDialog.show" max-width="600" scrollable>
      <v-card class="rounded-lg">
        <v-card-title class="bg-blue-darken-4 text-white text-subtitle-1">
          Зона: {{ matrixAreaDialog.title }}
        </v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-0" style="max-height: 400px;">
          <v-table density="compact" class="text-caption">
            <thead class="bg-grey-lighten-4">
              <tr>
                <th class="text-left font-weight-bold">Организация</th>
                <th class="text-right font-weight-bold">Дисциплина</th>
                <th class="text-right font-weight-bold">Исполнение</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="org in matrixAreaDialog.orgs" :key="org.name">
                <td>{{ org.name }}</td>
                <td class="text-right">{{ org.x }}%</td>
                <td class="text-right">{{ org.y }}%</td>
              </tr>
              <tr v-if="matrixAreaDialog.orgs.length === 0">
                <td colspan="3" class="text-center text-grey py-4">В этой зоне нет активных организаций</td>
              </tr>
            </tbody>
          </v-table>
        </v-card-text>
        <v-divider></v-divider>
        <v-card-actions><v-spacer></v-spacer><v-btn color="primary" variant="text" @click="matrixAreaDialog.show = false">Закрыть</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-card elevation="2" class="rounded-lg mb-4 px-4 py-3">
      <v-row align="center" dense>
        <v-col cols="12" md="3">
          <div class="d-flex align-center mb-1">
            <h2 class="text-h5 font-weight-bold text-blue-darken-4 mb-0">Центр ИПО</h2>
            <v-tooltip text="Индекс Поведения Организации: учитывает дисциплину, качество и процент исполнения бюджета" location="bottom">
              <template v-slot:activator="{ props }"><v-icon v-bind="props" color="grey-darken-1" size="small" class="ml-2 cursor-pointer">mdi-help-circle-outline</v-icon></template>
            </v-tooltip>
          </div>
          <div class="text-caption text-grey-darken-1">Аналитика надёжности (2024-2025)</div>
        </v-col>
        <v-col cols="12" md="9">
          <v-row dense>
            <v-col cols="12" sm="3"><v-autocomplete v-model="filters.districts" :items="districtList" label="Район" multiple chips closable-chips density="compact" variant="outlined" hide-details clearable></v-autocomplete></v-col>
            <v-col cols="12" sm="2"><v-select v-model="filters.year" :items="['Все', 2024, 2025]" label="Год" density="compact" variant="outlined" hide-details></v-select></v-col>
            <v-col cols="12" sm="3"><v-select v-model="filters.category" :items="['Все', 'МО', 'Подвед', 'ВУЗ', 'Иные']" label="Категория" density="compact" variant="outlined" hide-details></v-select></v-col>
            <v-col cols="12" sm="2"><v-select v-model="filters.smp" :items="['Все', 'Только СМП', 'Без СМП']" label="СМП" density="compact" variant="outlined" hide-details></v-select></v-col>
            <v-col cols="12" sm="2"><v-select v-model="filters.ipoType" :items="['Все', 'Проблемные']" label="Тип ИПО" density="compact" variant="outlined" hide-details></v-select></v-col>
          </v-row>
        </v-col>
      </v-row>
    </v-card>

    <v-row class="mb-4" dense>
      <v-col cols="12" md="4" v-for="(kpi, idx) in kpiData" :key="idx">
        <v-card elevation="2" class="rounded-lg text-center pa-2 pb-6">
          <div class="text-subtitle-2 font-weight-bold text-grey-darken-2 mt-2">{{ kpi.title }}</div>
          <div :ref="el => gaugeRefs[idx] = el" style="height: 220px; margin-top: -10px;"></div>
          <div class="d-flex justify-center align-center" style="margin-top: -20px;">
            <span class="text-caption text-grey mr-2">Регион: {{ kpi.avg }}%</span>
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
            <tbody><tr v-for="org in topOrgs" :key="org.name"><td>{{ org.name }}</td><td class="text-right font-weight-bold text-green">{{ org.ipo }}</td></tr></tbody>
          </v-table>
          <v-divider></v-divider>
          <v-card-title class="text-subtitle-1 font-weight-bold bg-red-lighten-5 text-red-darken-3 mt-auto">АНТИ-ТОП 5 Организаций</v-card-title>
          <v-table density="compact" class="text-caption">
            <tbody><tr v-for="org in bottomOrgs" :key="org.name"><td>{{ org.name }}</td><td class="text-right font-weight-bold text-red">{{ org.ipo }}</td></tr></tbody>
          </v-table>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mb-4" dense>
      <v-col cols="12">
        <v-card elevation="2" class="rounded-lg">
          <v-card-title class="text-subtitle-1 font-weight-bold">Детальная матрица компонентов ИПО</v-card-title>
          <v-card-text><div ref="heatmapRef" :style="{ height: heatmapHeight + 'px', width: '100%' }"></div></v-card-text>
        </v-card>
      </v-col>
    </v-row>

  </v-container>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, shallowRef, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import axios from 'axios'

const filters = reactive({ districts: [], year: 2024, category: 'Все', smp: 'Все', ipoType: 'Все' })
const districtList = ['Тюмень г.', 'Тобольск г.', 'Ишим г.', 'Тюменский', 'Вагайский', 'Уватский', 'Ялуторовск г.', 'Заводоуковский', 'Абатский', 'Викуловский']

const gaugeRefs = ref([])
const lineRef = ref(null)
const funnelRef = ref(null)
const scatterRef = ref(null)
const radarRef = ref(null)
const stackRef = ref(null)
const heatmapRef = ref(null)
const charts = shallowRef({})

const heatmapHeight = ref(500)
const matrixDialog = reactive({ show: false, data: {} })
const matrixAreaDialog = reactive({ show: false, title: '', orgs: [] })

const kpiData = ref([
  { title: 'Дисциплина (ρ)', val: 0, avg: 0, delta: 0, desc: '-' },
  { title: 'Качество (α)', val: 0, avg: 0, delta: 0, desc: '-' },
  { title: 'Исполнение (β)', val: 0, avg: 0, delta: 0, desc: '-' }
])
const topOrgs = ref([])
const bottomOrgs = ref([])

const fetchData = async () => {
  try {
    const response = await axios.get('/api/v1/analytics/ipo', { params: filters })
    const data = response.data

    if (data.kpi) kpiData.value = data.kpi
    if (data.top_orgs) topOrgs.value = data.top_orgs
    if (data.bottom_orgs) bottomOrgs.value = data.bottom_orgs

    if (data.kpi) {
      data.kpi.forEach((kpi, idx) => {
        if (charts.value[`gauge${idx}`]) charts.value[`gauge${idx}`].setOption({ series: [{ data: [{ value: kpi.val }] }] })
      })
    }

    if (data.funnel && charts.value.funnel) {
      const funnelColors = ['#1976D2', '#FFB300', '#4CAF50']
      const formattedFunnel = data.funnel.map((item, idx) => ({ ...item, itemStyle: { color: funnelColors[idx] } }))
      charts.value.funnel.setOption({ series: [{ data: formattedFunnel }] })
    }

    if (data.scatter && charts.value.scatter) {
      charts.value.scatter.setOption({ series: [{ data: data.scatter }] })
    }

    if (data.radar && charts.value.radar) {
      charts.value.radar.setOption({
        series: [{
          data: [
            // ИЗМЕНЕНО: Точки, линия и заливка теперь полностью зеленые
            { value: data.radar, name: 'Выбранный срез', itemStyle: { color: '#4CAF50' }, areaStyle: { color: 'rgba(76, 175, 80, 0.4)' }, lineStyle: { color: '#4CAF50' } },
            { value: [100, 100, 100, 100], name: 'Идеал', itemStyle: { color: '#9E9E9E' }, areaStyle: { color: 'transparent' }, lineStyle: { type: 'dashed', color: '#9E9E9E' } }
          ]
        }]
      })
    }

    const highlightFormatter = (value) => {
      if (filters.districts && filters.districts.length > 0 && filters.districts.includes(value)) return '{active|' + value + '}'
      return value
    }

    if (data.stack && charts.value.stack) {
      charts.value.stack.setOption({
        yAxis: { data: data.stack.categories, axisLabel: { formatter: highlightFormatter, rich: { active: { color: '#1976D2', fontWeight: 'bold' } } } },
        series: data.stack.series
      })
    }

    if (data.heatmap && charts.value.heatmap) {
      heatmapHeight.value = Math.max(400, data.heatmap.xAxis.length * 28 + 150)
      await nextTick()
      charts.value.heatmap.resize()
      
      const metricsData = [];
      const orgsData = [];

      // ИЗМЕНЕНО: Разделяем данные процентов (0-4) и данные Организаций (5)
      data.heatmap.data.forEach(item => {
        // item: [district_idx, metric_idx, val]
        const val = item[2];
        if (item[1] === 5) {
          orgsData.push([5, item[0], val]); // Для Организаций
        } else {
          metricsData.push([item[1], item[0], val]); // Для Процентов
        }
      });

      charts.value.heatmap.setOption({
        yAxis: { data: data.heatmap.xAxis, axisLabel: { interval: 0, fontSize: 11, width: 170, overflow: 'truncate', formatter: highlightFormatter, rich: { active: { color: '#1976D2', fontWeight: 'bold' } } } },
        series: [
          { type: 'heatmap', data: metricsData, label: { show: true, fontSize: 11, formatter: (p) => p.data[2] != null ? p.data[2] : '' } },
          // ИЗМЕНЕНО: Жестко заданный светло-синий цвет для столбца Организаций, игнорирующий visualMap
          { type: 'heatmap', data: orgsData, itemStyle: { color: '#BBDEFB' }, label: { show: true, fontSize: 11, fontWeight: 'bold', color: '#000', formatter: (p) => p.data[2] != null ? p.data[2] : '' } }
        ]
      })
    }

    if (data.line && charts.value.line) {
      charts.value.line.setOption({
        xAxis: { data: data.line.xAxis },
        series: [
          { data: data.line.seriesData, name: 'Выбранный срез' },
          { data: data.line.avgData, name: 'Регион (Ожидание / Среднее)' }
        ]
      })
    }

  } catch (error) {
    console.error("Ошибка загрузки аналитики ИПО:", error)
  }
}

watch(filters, () => fetchData(), { deep: true })

const initGauges = () => {
  gaugeRefs.value.forEach((el, idx) => {
    if (!el) return
    const chart = echarts.init(el)
    chart.setOption({
      series: [{
        type: 'gauge', startAngle: 180, endAngle: 0, min: 0, max: 100, 
        radius: '90%', // Уменьшили, чтобы влезло название сверху
        center: ['50%', '60%'], // Опустили визуально ниже
        axisLine: { lineStyle: { width: 15, color: [[0.3, '#d32f2f'], [0.5, '#f57c00'], [0.7, '#fbc02d'], [0.9, '#81c784'], [1, '#388e3c']] } },
        pointer: { length: '45%', width: 5 }, axisTick: { show: false }, splitLine: { show: false }, axisLabel: { show: false },
        detail: { fontSize: 26, offsetCenter: [0, '35%'], formatter: '{value}%', color: 'inherit', fontWeight: 'bold' },
        data: [{ value: 0 }] 
      }]
    })
    charts.value[`gauge${idx}`] = chart
  })
}

const initLineChart = () => {
  const chart = echarts.init(lineRef.value)
  chart.setOption({
    tooltip: { trigger: 'axis' }, legend: { data: ['Выбранный срез', 'Регион (Ожидание / Среднее)'], bottom: 0 },
    grid: { left: '8%', right: '5%', top: '10%', bottom: '15%' },
    xAxis: { 
      type: 'category', 
      data: [],
      axisLabel: { 
        interval: 0,
        formatter: function(value) { return value.replace(/Q(\d)/g, '$1 кв.'); } 
      }
    },
    yAxis: { type: 'value', min: 40, max: 100 },
    series: [
      { name: 'Выбранный срез', type: 'bar', data: [], barWidth: '40%', itemStyle: { color: '#1976D2', borderRadius: [4, 4, 0, 0] } },
      { name: 'Регион (Ожидание / Среднее)', type: 'line', data: [], smooth: true, lineStyle: { type: 'dashed', color: '#FF5722', width: 2 }, symbol: 'none' }
    ]
  })
  return chart
}

const initFunnel = () => {
  const chart = echarts.init(funnelRef.value)
  chart.setOption({
    tooltip: { trigger: 'item', formatter: '{b} <br/>{c} млн ₽' },
    series: [{ type: 'funnel', left: '10%', top: '5%', bottom: '5%', width: '80%', gap: 2, label: { show: true, position: 'inside', formatter: '{b}\n{c} млн', fontSize: 12 }, itemStyle: { borderColor: '#fff', borderWidth: 1 }, data: [] }]
  })
  return chart
}

const initScatter2x2 = () => {
  const chart = echarts.init(scatterRef.value)
  chart.setOption({
    tooltip: { formatter: p => p.componentType === 'markArea' ? p.name : `<b>${p.data[3]}</b><br/>Дисциплина (X): ${p.data[0]}<br/>Исполнение (Y): ${p.data[1]}<br/>Объем: ${p.data[2]} млн ₽` },
    grid: { left: '8%', right: '5%', bottom: '10%', top: '5%' },
    xAxis: { name: 'Дисциплина (ρ)', min: 0, max: 100, splitLine: { show: false } },
    yAxis: { name: 'Исполнение (β)', min: 0, max: 100, splitLine: { show: false } },
    series: [{
      type: 'scatter', 
      // МИНИМАЛЬНЫЙ РАЗМЕР: 10px. Теперь точки с 0 бюджетом будут видны!
      symbolSize: d => Math.max(10, Math.sqrt(d[2]) * 2), 
      data: [],
      itemStyle: { color: '#1976D2', opacity: 0.6 }, // Сделали чуть прозрачнее, чтобы видеть наложения
      markArea: {
        silent: false, 
        label: { position: 'insideTopLeft', color: '#000', opacity: 0.5, fontSize: 14, fontWeight: 'bold' },
        data: [
          [{ xAxis: 50, yAxis: 50, itemStyle: { color: 'rgba(56, 142, 60, 0.1)' }, name: 'Образцовые' }, { xAxis: 100, yAxis: 100 }],
          [{ xAxis: 0, yAxis: 50, itemStyle: { color: 'rgba(245, 124, 0, 0.1)' }, name: 'Непунктуальные' }, { xAxis: 50, yAxis: 100 }],
          [{ xAxis: 50, yAxis: 0, itemStyle: { color: 'rgba(251, 192, 45, 0.1)' }, name: 'Слабые в освоении' }, { xAxis: 100, yAxis: 50 }],
          [{ xAxis: 0, yAxis: 0, itemStyle: { color: 'rgba(211, 47, 47, 0.1)' }, name: 'Проблемные' }, { xAxis: 50, yAxis: 50 }]
        ]
      }
    }]
  })

  chart.on('click', function (params) {
    if (params.componentType === 'series') {
      matrixDialog.data = { x: params.data[0], y: params.data[1], val: params.data[2], name: params.data[3] }
      matrixDialog.show = true
    } else if (params.componentType === 'markArea') {
      const areaName = params.name
      const allData = chart.getOption().series[0].data || []
      
      // ИЗМЕНЕНО: Отсекаем фантомные организации (у которых 0 дисциплина, 0 исполнение и 0 бюджет)
      const isRealOrg = d => !(d[0] === 0 && d[1] === 0 && d[2] === 0);
      
      let filtered = []
      if (areaName === 'Образцовые') filtered = allData.filter(d => d[0] >= 50 && d[1] >= 50 && isRealOrg(d))
      else if (areaName === 'Безалаберные') filtered = allData.filter(d => d[0] < 50 && d[1] >= 50 && isRealOrg(d))
      else if (areaName === 'Слабые в освоении') filtered = allData.filter(d => d[0] >= 50 && d[1] < 50 && isRealOrg(d))
      else if (areaName === 'Проблемные') filtered = allData.filter(d => d[0] < 50 && d[1] < 50 && isRealOrg(d))

      matrixAreaDialog.title = areaName
      matrixAreaDialog.orgs = filtered.map(d => ({ name: d[3], x: d[0], y: d[1] }))
      matrixAreaDialog.show = true
    }
  })

  return chart
}

const initRadar = () => {
  const chart = echarts.init(radarRef.value)
  chart.setOption({
    tooltip: {}, legend: { data: ['Выбранный срез', 'Идеал'], bottom: 0 },
    radar: { radius: '65%', indicator: [{ name: 'Дисциплина', max: 100 }, { name: 'Качество', max: 100 }, { name: 'Исполнение', max: 100 }, { name: 'Общий ИПО', max: 100 }] },
    series: [{ type: 'radar', data: [] }]
  })
  return chart
}

const initStackedBar = () => {
  const chart = echarts.init(stackRef.value)
  const dists = ['Тюмень г.', 'Тюменский', 'Тобольск г.', 'Ишим г.', 'Заводоуковский', 'Вагайский'].reverse()
  chart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } }, legend: { bottom: 0 },
    grid: { left: '15%', right: '5%', top: '5%', bottom: '15%' },
    xAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } }, yAxis: { type: 'category', data: dists }, series: [] 
  })
  return chart
}

const initHeatmap = () => {
  const chart = echarts.init(heatmapRef.value)
  chart.setOption({
    tooltip: { position: 'top', formatter: (p) => `<b>${chart.getOption().yAxis[0].data[p.data[1]]}</b><br/>${p.name}: <b>${p.data[2]}</b>` },
    grid: { left: 180, right: 40, top: 50, bottom: 80 },
    // ИЗМЕНЕНО: Заголовок "Организации" полностью
    xAxis: { type: 'category', data: ['Дисциплина (ρ)', 'Качество (α)', 'Исполнение (β)', '% вовремя', '% плана', 'Организации'], position: 'top', axisLabel: { interval: 0, fontSize: 12 }, splitArea: { show: true } },
    yAxis: { type: 'category', data: [], inverse: true, axisLabel: { interval: 0, fontSize: 11, width: 170, overflow: 'truncate' }, splitArea: { show: true } },
    
    visualMap: {
      seriesIndex: 0, // ИЗМЕНЕНО: Применяется только к процентам, игнорируя столбец Организаций
      type: 'piecewise',
      orient: 'horizontal', left: 'center', bottom: 0,
      itemWidth: 15,
      pieces: [
        { min: 80, max: 100, label: '80-100% (Отлично)', color: '#4CAF50' },
        { min: 60, max: 80, label: '60-80% (Хорошо)', color: '#C8E6C9' },
        { min: 40, max: 60, label: '40-60% (Риск)', color: '#FFF59D' },
        { min: 0, max: 40, label: '0-40% (Критично)', color: '#FFEBEE' }
      ]
    },
    series: [] // Данные заполняются в fetchData
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
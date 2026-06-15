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
        <v-card-title class="bg-blue-darken-4 text-white text-subtitle-1">Зона: {{ matrixAreaDialog.title }}</v-card-title>
        <v-divider></v-divider>
        <v-card-text class="pa-0" style="max-height: 400px;">
          <v-table density="compact" class="text-caption">
            <thead class="bg-grey-lighten-4">
              <tr>
                <th class="text-left font-weight-bold">Организация</th>
                <th class="text-right font-weight-bold">Дисциплина %</th>
                <th class="text-right font-weight-bold">Исполнение %</th>
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
            <h2 class="text-h4 font-weight-bold text-blue-darken-4 mb-0">Индекс Поведения Организации (ИПО)</h2>
            <v-tooltip text="Индекс Поведения Организации: учитывает дисциплину, качество и процент исполнения бюджета" location="bottom">
              <template v-slot:activator="{ props }"><v-icon v-bind="props" color="grey-darken-1" size="small" class="ml-2 cursor-pointer">mdi-help-circle-outline</v-icon></template>
            </v-tooltip>
          </div>
          <div class="text-subtitle-2 font-weight-bold text-grey-darken-1">Аналитика надёжности (2024-2025)</div>
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
          <div class="text-h6 font-weight-bold text-grey-darken-3 mt-2">{{ kpi.title }}</div>
          <div :ref="el => gaugeRefs[idx] = el" style="height: 240px; margin-top: -10px;"></div>
          <div class="d-flex justify-center align-center" style="margin-top: -20px;">
            <span class="text-subtitle-2 font-weight-bold text-grey mr-2">Регион: {{ kpi.avg }}%</span>
            <v-chip size="small" :color="kpi.delta > 0 ? 'success' : 'error'" variant="flat" class="font-weight-bold text-white">
              <v-icon start size="14">{{ kpi.delta > 0 ? 'mdi-arrow-up' : 'mdi-arrow-down' }}</v-icon>
              {{ Math.abs(kpi.delta) }} ({{ kpi.desc }})
            </v-chip>
          </div>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mb-4" dense>
      <v-col cols="12" md="8">
        <v-card elevation="2" class="rounded-lg h-100">
          <v-card-title class="text-h6 font-weight-bold pa-4">Динамика ИПО по кварталам</v-card-title>
          <v-card-text><div ref="lineRef" style="height: 320px; width: 100%;"></div></v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="4">
        <v-card elevation="2" class="rounded-lg h-100">
          <v-card-title class="text-h6 font-weight-bold pa-4">Воронка: Факт → План → Отчёт</v-card-title>
          <v-card-text><div ref="funnelRef" style="height: 320px; width: 100%;"></div></v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mb-4" dense>
      <v-col cols="12" md="7">
        <v-card elevation="2" class="rounded-lg h-100">
          <v-card-title class="text-h6 font-weight-bold pa-4">Матрица организаций: Дисциплина × Исполнение</v-card-title>
          <v-card-text><div ref="scatterRef" style="height: 470px; width: 100%;"></div></v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="5">
        <v-card elevation="2" class="rounded-lg h-100">
          <v-card-title class="text-h6 font-weight-bold pa-4">Профиль надёжности</v-card-title>
          <v-card-text><div ref="radarRef" style="height: 470px; width: 100%;"></div></v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mb-4" dense>
      <v-col cols="12" md="8">
        <v-card elevation="2" class="rounded-lg h-100">
          <v-card-title class="text-h6 font-weight-bold pa-4">Распределение профилей по районам (Стек)</v-card-title>
          <v-card-text><div ref="stackRef" style="height: 420px; width: 100%;"></div></v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="4">
        <v-card elevation="2" class="rounded-lg h-100 d-flex flex-column">
          <v-card-title class="text-subtitle-1 font-weight-bold bg-green-lighten-5 text-green-darken-4 pa-3">ТОП-5 Организаций</v-card-title>
          <v-table density="default" class="text-subtitle-2 font-weight-bold">
            <tbody><tr v-for="org in topOrgs" :key="org.name"><td>{{ org.name }}</td><td class="text-right text-success font-weight-bold">{{ org.ipo }}</td></tr></tbody>
          </v-table>
          <v-divider></v-divider>
          <v-card-title class="text-subtitle-1 font-weight-bold bg-red-lighten-5 text-red-darken-4 pa-3 mt-auto">АНТИ-ТОП 5 Организаций</v-card-title>
          <v-table density="default" class="text-subtitle-2 font-weight-bold">
            <tbody><tr v-for="org in bottomOrgs" :key="org.name"><td>{{ org.name }}</td><td class="text-right text-danger font-weight-bold">{{ org.ipo }}</td></tr></tbody>
          </v-table>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mb-4" dense>
      <v-col cols="12">
        <v-card elevation="2" class="rounded-lg">
          <v-card-title class="text-h6 font-weight-bold pa-4">Детальная матрица компонентов ИПО учреждений региона</v-card-title>
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

const heatmapHeight = ref(600)
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
      const funnelColors = ['#1B3A5C', '#E65100', '#2E7D32']
      const funnelNames = ['План', 'Факт', 'Отчёт']
      const formattedFunnel = data.funnel.map((item, idx) => ({ 
        ...item, 
        name: funnelNames[idx] || item.name,
        itemStyle: { color: funnelColors[idx] } 
      }))
      charts.value.funnel.setOption({ series: [{ data: formattedFunnel }] })
    }

    if (data.scatter && charts.value.scatter) {
      charts.value.scatter.setOption({ series: [{ data: data.scatter }] })
    }

    if (data.radar && charts.value.radar) {
      charts.value.radar.setOption({
        series: [{
          data: [
            { 
              value: data.radar, 
              name: 'Выбранный срез', 
              itemStyle: { color: '#2E7D32' }, 
              areaStyle: { color: 'rgba(46, 125, 50, 0.45)' }, 
              lineStyle: { color: '#2E7D32', width: 3 } 
            },
            { 
              value: [100, 100, 100, 100], 
              name: 'Идеал', 
              itemStyle: { color: '#3949AB' }, 
              areaStyle: { color: 'transparent' }, 
              lineStyle: { type: 'dashed', color: '#3949AB', width: 2 },
              label: { 
                show: true, 
                formatter: '{c}', 
                color: '#3949AB', 
                fontSize: 13, 
                fontWeight: 'bold',
                distance: -16 // Отрицательное значение тянет цифру внутрь
              }
            }
          ]
        }]
      })
    }

    const highlightFormatter = (value) => {
      if (filters.districts && filters.districts.length > 0 && filters.districts.includes(value)) return '{active|' + value + '}'
      return value
    }

    if (data.stack && charts.value.stack) {
      const isBad = (n) => !n || String(n).includes('Без района') || String(n).includes('Не указан')
      const cats = data.stack.categories
      const keep = cats.map((n, i) => (isBad(n) ? -1 : i)).filter(i => i >= 0)
      const newCats = keep.map(i => cats[i])
      const newSeries = data.stack.series.map(s => ({ ...s, data: keep.map(i => s.data[i]) }))
      charts.value.stack.setOption({
        yAxis: {
          data: newCats,
          axisLabel: { interval: 0, fontSize: 13, fontWeight: 'bold', formatter: highlightFormatter, rich: { active: { color: '#1976D2', fontWeight: 'bold' } } }
        },
        series: newSeries
      })
    }

    if (data.heatmap && charts.value.heatmap) {
      const isBad = (n) => !n || String(n).includes('Без района') || String(n).includes('Не указан')
      const rawNames = data.heatmap.xAxis
      const bad = new Set()
      const remap = {}
      const names = []
      rawNames.forEach((n, i) => {
        if (isBad(n)) { bad.add(i) }
        else { remap[i] = names.length; names.push(n) }
      })

      // Шаг увеличен до 38px под крупный шрифт на проекторе
      heatmapHeight.value = Math.max(450, names.length * 38 + 160)
      await nextTick()
      charts.value.heatmap.resize()

      const metricsData = [];
      const orgsData = [];
      data.heatmap.data.forEach(item => {
        if (bad.has(item[0])) return
        const di = remap[item[0]]
        const val = item[2];
        if (item[1] === 5) orgsData.push([5, di, val]);
        else metricsData.push([item[1], di, val]);
      });

      charts.value.heatmap.setOption({
        yAxis: { data: names, axisLabel: { interval: 0, fontSize: 13, fontWeight: 'bold', width: 200, overflow: 'truncate', formatter: highlightFormatter, rich: { active: { color: '#1B3A5C', fontWeight: 'bold' } } } },
        series: [
          { type: 'heatmap', data: metricsData, label: { show: true, fontSize: 13, fontWeight: 'bold', formatter: (p) => p.data[2] != null ? p.data[2] : '' } },
          { type: 'heatmap', data: orgsData, itemStyle: { color: '#BBDEFB' }, label: { show: true, fontSize: 13, fontWeight: 'bold', color: '#000', formatter: (p) => p.data[2] != null ? p.data[2] : '' } }
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
        radius: '95%', 
        center: ['50%', '65%'], 
        axisLine: { lineStyle: { width: 18, color: [[0.3, '#d32f2f'], [0.5, '#f57c00'], [0.7, '#fbc02d'], [0.9, '#81c784'], [1, '#2E7D32']] } },
        pointer: { length: '50%', width: 6 }, axisTick: { show: false }, splitLine: { show: false }, axisLabel: { show: false },
        detail: { fontSize: 30, offsetCenter: [0, '35%'], formatter: '{value}%', color: 'inherit', fontWeight: 'bold' },
        data: [{ value: 0 }] 
      }]
    })
    charts.value[`gauge${idx}`] = chart
  })
}

const initLineChart = () => {
  const chart = echarts.init(lineRef.value)
  chart.setOption({
    tooltip: { trigger: 'axis', textStyle: { fontSize: 14 } }, 
    legend: { data: ['Выбранный срез', 'Регион (Ожидание / Среднее)'], bottom: 0, textStyle: { fontSize: 14, fontWeight: 'bold' } },
    grid: { left: '10%', right: '5%', top: '12%', bottom: '18%', containLabel: true },
    xAxis: { 
      type: 'category', 
      data: [],
      axisLabel: { 
        interval: 0,
        fontSize: 14,
        fontWeight: 'bold',
        formatter: function(value) { return value.replace(/Q(\d)/g, '$1 кв.'); } 
      }
    },
    yAxis: { type: 'value', min: 40, max: 100, axisLabel: { fontSize: 14, fontWeight: 'bold' } },
    series: [
      { name: 'Выбранный срез', type: 'bar', data: [], barWidth: '45%', itemStyle: { color: '#1B3A5C', borderRadius: [5, 5, 0, 0] } },
      { name: 'Регион (Ожидание / Среднее)', type: 'line', data: [], smooth: false, lineStyle: { type: 'dashed', color: '#D32F2F', width: 3 }, symbol: 'circle', symbolSize: 8 }
    ]
  })
  return chart
}

const initFunnel = () => {
  const chart = echarts.init(funnelRef.value)
  chart.setOption({
    tooltip: { trigger: 'item', formatter: '{b} <br/><b>{c} млн ₽</b>', textStyle: { fontSize: 14 } },
    series: [{ type: 'funnel', left: '10%', top: '8%', bottom: '8%', width: '80%', gap: 3, label: { show: true, position: 'inside', formatter: '{b}\n{c} млн', fontSize: 14, fontWeight: 'bold', color: '#fff' }, itemStyle: { borderColor: '#fff', borderWidth: 2 }, data: [] }]
  })
  return chart
}

const initScatter2x2 = () => {
  const chart = echarts.init(scatterRef.value)
  chart.setOption({
    tooltip: { textStyle: { fontSize: 14 }, formatter: p => p.componentType === 'markArea' ? p.name : `<b>${p.data[3]}</b><br/>Дисциплина (X): ${p.data[0]}%<br/>Исполнение (Y): ${p.data[1]}%<br/>Объем: ${p.data[2]} млн ₽` },
    grid: { left: '10%', right: '8%', bottom: '12%', top: '8%', containLabel: true },
    xAxis: { name: 'Дисциплина', nameTextStyle: { fontSize: 14, fontWeight: 'bold' }, min: 0, max: 100, splitLine: { show: false }, axisLabel: { fontSize: 13, fontWeight: 'bold' } },
    yAxis: { name: 'Исполнение', nameTextStyle: { fontSize: 14, fontWeight: 'bold' }, min: 0, max: 100, splitLine: { show: false }, axisLabel: { fontSize: 13, fontWeight: 'bold' } },
    series: [{
      type: 'scatter', 
      symbolSize: d => Math.max(12, d[2] ? Math.sqrt(d[2]) * 2.5 : 12), 
      data: [],
      itemStyle: { color: '#1B3A5C', opacity: 0.75, borderColor: '#fff', borderWidth: 1 },
      markArea: {
        silent: false, 
        label: { position: 'insideTopLeft', color: '#222', opacity: 0.8, fontSize: 15, fontWeight: 'bold' },
        data: [
          [{ xAxis: 50, yAxis: 50, itemStyle: { color: 'rgba(46, 125, 50, 0.12)' }, name: 'Образцовые учреждения' }, { xAxis: 100, yAxis: 100 }],
          [{ xAxis: 0, yAxis: 50, itemStyle: { color: 'rgba(230, 81, 0, 0.12)' }, name: 'Непунктуальные' }, { xAxis: 50, yAxis: 100 }],
          [{ xAxis: 50, yAxis: 0, itemStyle: { color: 'rgba(251, 192, 45, 0.12)' }, name: 'Слабые в освоении бюджетных средств' }, { xAxis: 100, yAxis: 50 }],
          [{ xAxis: 0, yAxis: 0, itemStyle: { color: 'rgba(211, 47, 47, 0.12)' }, name: 'Критическая зона риска' }, { xAxis: 50, yAxis: 50 }]
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
      const isRealOrg = d => !(d[0] === 0 && d[1] === 0 && d[2] === 0);
      
      let filtered = []
      if (areaName.includes('Образцовые')) filtered = allData.filter(d => d[0] >= 50 && d[1] >= 50 && isRealOrg(d))
      else if (areaName.includes('Непунктуальные')) filtered = allData.filter(d => d[0] < 50 && d[1] >= 50 && isRealOrg(d))
      else if (areaName.includes('Слабые')) filtered = allData.filter(d => d[0] >= 50 && d[1] < 50 && isRealOrg(d))
      else if (areaName.includes('Критическая')) filtered = allData.filter(d => d[0] < 50 && d[1] < 50 && isRealOrg(d))

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
    tooltip: { textStyle: { fontSize: 14 } }, 
    legend: { data: ['Выбранный срез', 'Идеал'], bottom: 0, textStyle: { fontSize: 14, fontWeight: 'bold' } },
    radar: { 
      radius: '56%', 
      nameTextStyle: { fontSize: 14, fontWeight: 'bold', color: '#333' },
      indicator: [{ name: 'Дисциплина', max: 100 }, { name: 'Качество', max: 100 }, { name: 'Исполнение', max: 100 }, { name: 'Общий ИПО', max: 100 }] 
    },
    series: [{ type: 'radar', data: [] }]
  })
  return chart
}

const initStackedBar = () => {
  const chart = echarts.init(stackRef.value)
  const dists = ['Тюмень г.', 'Тюменский', 'Тобольск г.', 'Ишим г.', 'Заводоуковский', 'Вагайский'].reverse()
  chart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, textStyle: { fontSize: 14 } }, 
    legend: { bottom: 0, textStyle: { fontSize: 13, fontWeight: 'bold' } },
    grid: { left: '15%', right: '6%', top: '5%', bottom: '15%', containLabel: true },
    xAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%', fontSize: 13, fontWeight: 'bold' } }, 
    yAxis: { type: 'category', data: dists, axisLabel: { fontSize: 13, fontWeight: 'bold' } }, 
    series: [] 
  })
  return chart
}

const initHeatmap = () => {
  const chart = echarts.init(heatmapRef.value)
  chart.setOption({
    tooltip: { position: 'top', textStyle: { fontSize: 14 }, formatter: (p) => `<b>${chart.getOption().yAxis[0].data[p.data[1]]}</b><br/>${p.name}: <b>${p.data[2]}%</b>` },
    grid: { left: 220, right: 40, top: 70, bottom: 90 },
    xAxis: { type: 'category', data: ['Дисциплина (ρ), %', 'Качество (α), %', 'Исполнение (β), %', '% вовремя', '% плана', 'Организации'], position: 'top', axisLabel: { interval: 0, fontSize: 13, fontWeight: 'bold' }, splitArea: { show: true } },
    yAxis: { type: 'category', data: [], inverse: true, axisLabel: { interval: 0, fontSize: 13, fontWeight: 'bold', width: 200, overflow: 'truncate' }, splitArea: { show: true } },
    visualMap: {
      seriesIndex: 0,
      type: 'piecewise',
      orient: 'horizontal', left: 'center', bottom: 10,
      itemWidth: 18, itemHeight: 14,
      textStyle: { fontSize: 13, fontWeight: 'bold' },
      pieces: [
        { min: 80, max: 100, label: '80-100% (Отлично)', color: '#C8E6C9' },  // Мягкий зеленый
        { min: 60, max: 80, label: '60-80% (Хорошо)', color: '#E6EE9C' },   // Светло-салатовый
        { min: 40, max: 60, label: '40-60% (Риск)', color: '#FFE082' },     // Мягкий янтарный
        { min: 0, max: 40, label: '0-40% (Критично)', color: '#EF9A9A' }    // Мягкий красный
      ]
    },
    series: [] 
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
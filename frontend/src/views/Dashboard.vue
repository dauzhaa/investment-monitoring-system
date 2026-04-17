<template>
  <div class="dashboard">
    <div class="d-flex align-center mb-6" style="gap: 16px;">
      <v-select v-model="startYear" :items="availableYears" label="С года" variant="outlined" density="compact" hide-details color="primary" style="max-width: 140px;" />
      <span class="text-grey-darken-1">—</span>
      <v-select v-model="endYear" :items="availableYears" label="По год" variant="outlined" density="compact" hide-details color="primary" style="max-width: 140px;" />
      
      <v-spacer />
      
      <v-btn variant="flat" color="primary" size="small" prepend-icon="mdi-refresh" :loading="loading" @click="loadData">
        Обновить данные
      </v-btn>
      
      <v-btn variant="flat" color="#1B3A5C" size="small" prepend-icon="mdi-file-pdf-box" :loading="isExportingPdf" @click="downloadPdfReport" class="text-white">
        Скачать PDF
      </v-btn>
    </div>

    <v-row class="mb-4">
      <v-col cols="12" lg="6">
        <v-card class="stat-card hero-card pa-6 text-white" style="background: linear-gradient(135deg, #1B3A5C 0%, #0F2439 100%);">
          <div class="d-flex justify-space-between align-start h-100">
            <div>
              <div class="text-subtitle-1 font-weight-medium text-white-50 mb-1">Фактические инвестиции</div>
              <div class="text-h3 font-weight-bold mb-2">{{ formatMoney(animFact) }} <span class="text-h6 font-weight-regular">тыс. ₽</span></div>
              <v-chip size="small" color="success" variant="flat" class="font-weight-bold">
                <v-icon start size="14">mdi-trending-up</v-icon> {{ stats.executionPercent }}% освоение
              </v-chip>
            </div>
            <v-icon size="64" color="rgba(255,255,255,0.1)">mdi-cash-multiple</v-icon>
          </div>
        </v-card>
      </v-col>

      <v-col cols="12" sm="4" lg="2">
        <v-card class="stat-card pa-4 h-100 d-flex flex-column justify-center">
          <div class="text-caption text-grey-darken-1 font-weight-medium mb-1">ПЛАН (тыс. ₽)</div>
          <div class="text-h5 font-weight-bold text-warning mb-2">{{ formatMoney(animPlan) }}</div>
          <v-progress-linear :model-value="stats.executionPercent" color="warning" height="4" rounded />
        </v-card>
      </v-col>

      <v-col cols="12" sm="4" lg="2">
        <v-card class="stat-card pa-4 h-100 d-flex flex-column justify-center">
          <div class="text-caption text-grey-darken-1 font-weight-medium mb-1">ОРГАНИЗАЦИЙ</div>
          <div class="text-h5 font-weight-bold text-primary mb-2">{{ animTotalOrgs }}</div>
          <div class="text-caption text-success">С инвестициями: {{ animOrgsWithInvestments }}</div>
        </v-card>
      </v-col>

      <v-col cols="12" sm="4" lg="2">
        <v-card class="stat-card pa-4 h-100 d-flex flex-column justify-center">
          <div class="text-caption text-grey-darken-1 font-weight-medium mb-1">ОСВОЕНИЕ БЮДЖЕТА</div>
          <div class="text-h5 font-weight-bold" :class="stats.executionPercent >= 80 ? 'text-success' : 'text-error'">
            {{ animExec }}%
          </div>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mb-4">
      <v-col cols="12">
        <v-card class="stat-card pa-5" style="height: 550px">
          <div class="text-subtitle-1 font-weight-bold mb-4" style="color: #1B3A5C">Инвестиционная карта районов</div>
          <MapChart v-if="mapData.length" :data="mapData" @district-click="handleMapClick" />
          <div v-else class="d-flex align-center justify-center h-100 text-grey">Загрузка карты...</div>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" lg="5">
        <v-card class="stat-card pa-5" style="height: 420px">
          <div class="text-subtitle-1 font-weight-bold mb-2" style="color: #1B3A5C">Объем инвестиций по годам</div>
          <v-chart v-if="trends.history?.length" class="chart" :option="areaOption" autoresize />
          <div v-else class="text-center text-grey pa-10 mt-10">Нет данных</div>
        </v-card>
      </v-col>

      <v-col cols="12" lg="3">
        <v-card class="stat-card pa-5" style="height: 420px">
          <div class="text-subtitle-1 font-weight-bold mb-2" style="color: #1B3A5C">Квартальное распределение</div>
          <v-chart v-if="quarters.length" class="chart" :option="quarterGroupOption" autoresize />
          <div v-else class="text-center text-grey pa-10 mt-10">Нет данных</div>
        </v-card>
      </v-col>

      <v-col cols="12" lg="4">
        <v-card class="stat-card pa-5" style="height: 420px">
          <div class="text-subtitle-1 font-weight-bold mb-2" style="color: #1B3A5C">Топ-5 районов</div>
          <v-chart v-if="trends.rating?.length" class="chart" :option="topDistrictsOption" autoresize />
          <div v-else class="text-center text-grey pa-10">Нет данных</div>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { analyticsAPI } from '@/services/api'
import MapChart from '@/components/MapChart.vue'

import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import VChart from 'vue-echarts'

use([CanvasRenderer, BarChart, LineChart, GridComponent, TooltipComponent, LegendComponent])

const router = useRouter()
const availableYears = [2022, 2023, 2024, 2025]
const startYear = ref(2022)
const endYear = ref(2025)
const loading = ref(false)

const isExportingPdf = ref(false)

async function downloadPdfReport() {
  isExportingPdf.value = true
  try {
    const response = await analyticsAPI.exportPdf({ 
      start_year: startYear.value, 
      end_year: endYear.value 
    })

    // Магия браузера для скачивания файла
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    
    // Пытаемся достать оригинальное имя файла от бэкенда
    const contentDisposition = response.headers['content-disposition']
    let fileName = `Analytics_Report_${startYear.value}_${endYear.value}.pdf`
    if (contentDisposition) {
      const fileNameMatch = contentDisposition.match(/filename="?([^"]+)"?/)
      if (fileNameMatch && fileNameMatch.length === 2) {
        fileName = fileNameMatch[1]
      }
    }
    
    link.setAttribute('download', fileName)
    document.body.appendChild(link)
    link.click()
    link.parentNode.removeChild(link)
    window.URL.revokeObjectURL(url)

  } catch (error) {
    console.error("Ошибка при скачивании PDF:", error)
  } finally {
    isExportingPdf.value = false
  }
}

const stats = ref({ factTotal: 0, planTotal: 0, executionPercent: 0, orgsWithInvestments: 0, orgsWithoutInvestments: 0 })
const quarters = ref([])
const trends = ref({ history: [], rating: [] })
const mapData = ref([])

// Анимации чисел (State)
const animFact = ref(0);
const animPlan = ref(0);
const animTotalOrgs = ref(0);
const animOrgsWithInvestments = ref(0);
const animExec = ref(0);

const animateValue = (refVar, target, duration = 800) => {
  let startTimestamp = null;
  const initial = refVar.value;
  const step = (timestamp) => {
    if (!startTimestamp) startTimestamp = timestamp;
    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
    refVar.value = Math.floor(progress * (target - initial) + initial);
    if (progress < 1) window.requestAnimationFrame(step);
  };
  window.requestAnimationFrame(step);
}

watch(() => stats.value, (newStats) => {
  animateValue(animFact, newStats.factTotal);
  animateValue(animPlan, newStats.planTotal);
  animateValue(animTotalOrgs, newStats.orgsWithInvestments + newStats.orgsWithoutInvestments);
  animateValue(animOrgsWithInvestments, newStats.orgsWithInvestments);
  animateValue(animExec, newStats.executionPercent);
}, { deep: true });

function formatMoney(val) {
  if (!val) return '0'
  return new Intl.NumberFormat('ru-RU').format(Math.round(val))
}

// 1. Area Chart (Динамика)
const areaOption = computed(() => {
  const xData = trends.value.history?.map(d => d.year) || []
  return {
    tooltip: { trigger: 'axis', valueFormatter: (value) => formatMoney(value) + ' тыс. ₽' },
    legend: { data: ['Факт', 'План'], top: 0, left: 'center' }, // ИЗМЕНЕНО: Легенда сверху
    grid: { left: '2%', right: '4%', bottom: '5%', top: '15%', containLabel: true }, // ИЗМЕНЕНО: top: 15% дает место
    xAxis: { type: 'category', boundaryGap: false, data: xData },
    yAxis: { type: 'value', axisLabel: { formatter: v => formatMoney(v) } },
    series: [
      {
        name: 'Факт', type: 'line', smooth: true,
        itemStyle: { color: '#2E7D32' },
        areaStyle: { color: 'rgba(46, 125, 50, 0.2)' },
        data: trends.value.history?.map(d => d.amount) || []
      },
      {
        name: 'План', type: 'line', smooth: true,
        itemStyle: { color: '#F57C00' },
        lineStyle: { type: 'dashed', width: 2 },
        data: trends.value.history?.map(d => d.forecast) || []
      }
    ]
  }
})

// 2. Grouped Bar (Кварталы)
const quarterGroupOption = computed(() => {
  const xData = quarters.value.map(q => `${q.quarter} кв`)
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, valueFormatter: (value) => formatMoney(value) + ' тыс. ₽' },
    legend: { data: ['Факт', 'План'], top: 0, left: 'center', itemWidth: 10, itemHeight: 10 }, // ИЗМЕНЕНО: Легенда сверху
    grid: { left: '2%', right: '2%', bottom: '5%', top: '15%', containLabel: true }, // ИЗМЕНЕНО: top: 15% дает место
    xAxis: { type: 'category', data: xData },
    yAxis: { type: 'value', splitLine: { show: false }, axisLabel: { show: false } },
    series: [
      { name: 'Факт', type: 'bar', data: quarters.value.map(q => q.fact), itemStyle: { color: '#1B3A5C', borderRadius: [4,4,0,0] } },
      { name: 'План', type: 'bar', data: quarters.value.map(q => q.plan || q.fact * 1.2), itemStyle: { color: '#E0E0E0', borderRadius: [4,4,0,0] } }
    ]
  }
})

const topDistrictsOption = computed(() => {
  const top5 = [...(trends.value.rating || [])].sort((a,b) => a.value - b.value).slice(-5);
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, valueFormatter: (value) => formatMoney(value) + ' тыс. ₽' },
    grid: { left: '2%', right: '15%', bottom: '2%', top: '5%', containLabel: true },
    xAxis: { type: 'value', show: false },
    yAxis: { type: 'category', data: top5.map(d => d.name), axisLine: {show: false}, axisTick: {show: false} },
    series: [{
      type: 'bar',
      data: top5.map(d => d.value),
      itemStyle: { color: '#2E7D32', borderRadius: [0,4,4,0] },
      label: { show: true, position: 'right', formatter: (p) => formatMoney(p.value), color: '#1B3A5C', fontWeight: 'bold' }
    }]
  }
})

const handleMapClick = (name) => {
  // Навигация теперь внутри MapChart.vue
}

async function loadData() {
  loading.value = true
  try {
    const [dashRes, quartersRes, trendsRes, mapRes] = await Promise.allSettled([
      analyticsAPI.getDashboard({ start_year: startYear.value, end_year: endYear.value }),
      analyticsAPI.getQuarters({ start_year: startYear.value, end_year: endYear.value }),
      analyticsAPI.getTrends({ start_year: startYear.value, end_year: endYear.value }),
      analyticsAPI.getMapData({ start_year: startYear.value, end_year: endYear.value }),
    ])
    if (dashRes.status === 'fulfilled') stats.value = dashRes.value.data
    if (quartersRes.status === 'fulfilled') quarters.value = quartersRes.value.data
    if (trendsRes.status === 'fulfilled') trends.value = trendsRes.value.data
    if (mapRes.status === 'fulfilled') mapData.value = mapRes.value.data
  } catch (e) {
    console.error('Dashboard load error:', e)
  } finally {
    loading.value = false
  }
}

watch([startYear, endYear], loadData)
onMounted(loadData)
</script>

<style scoped>
.chart { height: 100%; width: 100%; }
.hero-card { overflow: hidden; position: relative; }
</style>
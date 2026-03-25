<template>
  <div class="dashboard">
    <div class="d-flex align-center mb-6" style="gap: 16px;">
      <v-select
        v-model="startYear"
        :items="availableYears"
        label="С года"
        variant="outlined"
        density="compact"
        hide-details
        color="#1B3A5C"
        style="max-width: 140px;"
      />
      <span class="text-grey-darken-1">—</span>
      <v-select
        v-model="endYear"
        :items="availableYears"
        label="По год"
        variant="outlined"
        density="compact"
        hide-details
        color="#1B3A5C"
        style="max-width: 140px;"
      />
      <v-spacer />
      <v-btn
        variant="tonal"
        color="#1B3A5C"
        size="small"
        prepend-icon="mdi-refresh"
        :loading="loading"
        @click="loadData"
      >
        Обновить данные
      </v-btn>
    </div>

    <v-row class="mb-4">
      <v-col cols="12" sm="6" lg="3">
        <v-card class="stat-card pa-5">
          <div class="d-flex align-center justify-space-between mb-2">
            <div class="kpi-icon kpi-icon--primary">
              <v-icon size="22" color="#1B3A5C">mdi-cash-multiple</v-icon>
            </div>
          </div>
          <div class="kpi-value" style="color: #1B3A5C">
            {{ formatMoney(stats.factTotal) }}
          </div>
          <div class="kpi-label">Инвестиции ФАКТ (тыс. ₽)</div>
          <div class="kpi-change" :style="{ color: executionColor }">
            <v-icon size="14">{{ stats.executionPercent >= 80 ? 'mdi-trending-up' : 'mdi-trending-down' }}</v-icon>
            {{ stats.executionPercent }}% от плана
          </div>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" lg="3">
        <v-card class="stat-card pa-5">
          <div class="d-flex align-center justify-space-between mb-2">
            <div class="kpi-icon kpi-icon--warning">
              <v-icon size="22" color="#F57C00">mdi-target</v-icon>
            </div>
          </div>
          <div class="kpi-value" style="color: #F57C00">
            {{ formatMoney(stats.planTotal) }}
          </div>
          <div class="kpi-label">Инвестиции ПЛАН (тыс. ₽)</div>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" lg="3">
        <v-card class="stat-card pa-5">
          <div class="d-flex align-center justify-space-between mb-2">
            <div class="kpi-icon kpi-icon--success">
              <v-icon size="22" color="#2E7D32">mdi-domain</v-icon>
            </div>
          </div>
          <div class="kpi-value" style="color: #2E7D32">
            {{ stats.orgsWithInvestments }}
          </div>
          <div class="kpi-label">Организаций с инвестициями</div>
          <div class="kpi-change" style="color: var(--text-secondary)">
            из {{ stats.orgsWithInvestments + stats.orgsWithoutInvestments }} всего
          </div>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" lg="3">
        <v-card class="stat-card pa-5">
          <div class="d-flex align-center justify-space-between mb-2">
            <div class="kpi-icon" :class="executionIconClass">
              <v-icon size="22" :color="executionColor">mdi-percent-outline</v-icon>
            </div>
          </div>
          <div class="kpi-value" :style="{ color: executionColor }">
            {{ stats.executionPercent }}%
          </div>
          <div class="kpi-label">Освоение бюджета</div>
          <v-progress-linear
            :model-value="stats.executionPercent"
            :color="executionColor"
            height="6"
            rounded
            class="mt-3"
          />
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mb-4">
      <v-col cols="12">
        <v-card class="stat-card pa-5" style="height: 500px">
          <div class="section-title">Инвестиционная карта районов (Факт)</div>
          <v-chart v-if="mapData.length" class="chart" :option="mapOption" autoresize @click="handleMapClick" />
          <div v-else class="map-placeholder">Загрузка карты...</div>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" lg="5">
        <v-card class="stat-card pa-5" style="height: 420px">
          <div class="section-title">Динамика освоения (Факт / План)</div>
          <v-chart v-if="trends.history?.length" class="chart" :option="historyOption" autoresize />
          <div v-else class="text-center text-grey pa-10 mt-10">Нет данных</div>
        </v-card>
      </v-col>

      <v-col cols="12" lg="3">
        <v-card class="stat-card pa-5" style="height: 420px">
          <div class="section-title">По кварталам (Факт)</div>
          <v-chart v-if="quarters.length" class="chart" :option="quartersOption" autoresize />
          <div v-else class="text-center text-grey pa-10 mt-10">Нет данных</div>
        </v-card>
      </v-col>

      <v-col cols="12" lg="4">
        <v-card class="stat-card pa-5" style="height: 420px; overflow-y: auto;">
          <div class="section-title">Топ-5 районов</div>
          <div v-if="trends.rating && trends.rating.length">
            <div
              v-for="(d, i) in trends.rating.slice(0, 5)"
              :key="d.name"
              class="top-district"
              @click="$router.push(`/districts/${encodeURIComponent(d.name)}`)"
            >
              <div class="top-district-rank" :style="{ background: i===0 ? 'rgba(27, 58, 92, 0.1)' : '#F0F2F5', color: i===0 ? '#1B3A5C' : '#757575' }">#{{ i + 1 }}</div>
              <div class="top-district-info">
                <div class="top-district-name">{{ d.name }}</div>
                <v-progress-linear
                  :model-value="(d.value / maxDistrictValue) * 100"
                  color="#1B3A5C"
                  height="6"
                  rounded
                  bg-color="#E5E7EB"
                />
              </div>
              <div class="top-district-value">{{ formatMoneyShort(d.value) }}</div>
            </div>
          </div>
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

// ECharts импорты
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, MapChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, VisualMapComponent, GeoComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import * as echarts from 'echarts/core'

// Тюменская карта
import tyumenMap from '@/assets/tyumen_districts.json'

use([CanvasRenderer, BarChart, MapChart, PieChart, GridComponent, TooltipComponent, LegendComponent, VisualMapComponent, GeoComponent])
echarts.registerMap('tyumen', tyumenMap)

const router = useRouter()
const availableYears = [2022, 2023, 2024, 2025]
const startYear = ref(2022)
const endYear = ref(2025)
const loading = ref(false)

const stats = ref({
  factTotal: 0, planTotal: 0, executionPercent: 0,
  orgsWithInvestments: 0, orgsWithoutInvestments: 0
})
const quarters = ref([])
const trends = ref({ history: [], rating: [] })
const mapData = ref([])

// --- Форматирование и Стили ---
const executionColor = computed(() => {
  const p = stats.value.executionPercent
  if (p >= 80) return '#2E7D32' // success
  if (p >= 50) return '#F57C00' // warning
  return '#D32F2F' // danger
})

const executionIconClass = computed(() => {
  const p = stats.value.executionPercent
  if (p >= 80) return 'kpi-icon--success'
  if (p >= 50) return 'kpi-icon--warning'
  return 'kpi-icon--danger'
})

const maxDistrictValue = computed(() => {
  if (!trends.value.rating?.length) return 1
  return Math.max(...trends.value.rating.map(d => d.value))
})

function formatMoney(val) {
  if (!val) return '0'
  return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 }).format(val)
}

function formatMoneyShort(val) {
  if (!val) return '0'
  if (val >= 1000000) return (val / 1000000).toFixed(1) + 'M'
  if (val >= 1000) return (val / 1000).toFixed(0) + 'K'
  return val
}

// --- ECharts Конфигурации ---

// 1. Карта на весь экран
const mapOption = computed(() => {
  const data = mapData.value.map(d => ({ name: d.district, value: d.fact || d.value || 0 }))
  const maxVal = Math.max(...data.map(d => d.value), 1)

  return {
    tooltip: { trigger: 'item', formatter: '{b}<br/>Факт: {c} тыс. ₽' },
    visualMap: {
      left: 'right',
      min: 0,
      max: maxVal,
      inRange: { color: ['#E5E7EB', '#1B3A5C'] }, // Твоя палитра
      text: ['Макс', 'Мин'],
      calculable: true
    },
    series: [{
      name: 'Тюменская область',
      type: 'map',
      map: 'tyumen',
      roam: true,
      itemStyle: { borderColor: '#fff', borderWidth: 0.5 },
      emphasis: { itemStyle: { areaColor: '#F57C00' }, label: { show: true, color: '#fff' } },
      data: data
    }]
  }
})

// 2. Stacked / Overlay график (План как фон, Факт внутри)
const historyOption = computed(() => {
  const xData = trends.value.history?.map(d => d.year) || []
  const factData = trends.value.history?.map(d => d.amount) || []
  const planData = trends.value.history?.map(d => d.forecast) || []

  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['ПЛАН', 'ФАКТ'], bottom: 0, icon: 'roundRect' },
    grid: { left: '3%', right: '4%', bottom: '15%', top: '10%', containLabel: true },
    xAxis: { type: 'category', data: xData },
    yAxis: { type: 'value', axisLabel: { formatter: v => formatMoneyShort(v) } },
    series: [
      { 
        name: 'ПЛАН', 
        type: 'bar', 
        barGap: '-100%', // Наложение друг на друга
        barWidth: '40%', // План шире
        itemStyle: { color: 'rgba(245, 124, 0, 0.2)', borderRadius: [4,4,0,0], borderColor: '#F57C00', borderWidth: 1 }, 
        data: planData 
      },
      { 
        name: 'ФАКТ', 
        type: 'bar', 
        barWidth: '20%', // Факт уже и внутри плана
        itemStyle: { color: '#2E7D32', borderRadius: [4,4,0,0] }, 
        data: factData 
      }
    ]
  }
})

// 3. Кварталы (Pie chart для разнообразия данных)
const quartersOption = computed(() => {
  const data = quarters.value.map(q => ({ name: `${q.quarter} кв`, value: q.fact }))
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} тыс. ₽ ({d}%)' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      color: ['#1B3A5C', '#2E7D32', '#F57C00', '#D32F2F'],
      data: data
    }]
  }
})

// --- Экшены ---
const handleMapClick = (params) => {
  if (params.name) router.push(`/districts/${encodeURIComponent(params.name)}`)
}

async function loadData() {
  if (startYear.value > endYear.value) {
    const temp = startYear.value
    startYear.value = endYear.value
    endYear.value = temp
  }

  loading.value = true
  try {
    const [dashRes, quartersRes, trendsRes, mapRes] = await Promise.allSettled([
      analyticsAPI.getDashboard(startYear.value, endYear.value), // Бэк должен уметь принимать 2 года, если нет - передавай startYear
      analyticsAPI.getQuarters(startYear.value, endYear.value),
      analyticsAPI.getTrends(startYear.value, endYear.value),
      analyticsAPI.getMapData(startYear.value, endYear.value),
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
.chart {
  height: 100%;
  width: 100%;
}
.kpi-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.kpi-icon--primary { background: rgba(27, 58, 92, 0.1); }
.kpi-icon--success { background: rgba(46, 125, 50, 0.1); }
.kpi-icon--warning { background: rgba(245, 124, 0, 0.1); }
.kpi-icon--danger  { background: rgba(211, 47, 47, 0.1); }

.map-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-secondary);
  background: #F8F9FB;
  border-radius: 8px;
  border: 1px dashed #E0E0E0;
}

.top-district {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
}
.top-district:hover { background: #F5F7FA; }
.top-district-rank {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}
.top-district-info { flex: 1; min-width: 0; }
.top-district-name { font-size: 13px; font-weight: 600; color: var(--text-primary); margin-bottom: 6px; }
.top-district-value { font-size: 13px; font-weight: 700; color: #1B3A5C; }
</style>
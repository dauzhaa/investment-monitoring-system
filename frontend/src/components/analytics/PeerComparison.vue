<template>
  <div>
    <v-row class="mb-4" align="center">
      <v-col cols="12" md="6">
        <v-autocomplete
          v-model="selectedOrgId"
          :items="organizations"
          item-title="name"
          item-value="id"
          label="Выберите организацию"
          variant="outlined"
          density="compact"
          hide-details
          :loading="loadingOrgs"
        />
      </v-col>
      <v-col cols="12" md="3">
        <v-select
          v-model="selectedYear"
          :items="[2024, 2025]"
          label="Год"
          variant="outlined"
          density="compact"
          hide-details
        />
      </v-col>
    </v-row>

    <v-row v-if="loading">
      <v-col class="text-center pa-12">
        <v-progress-circular indeterminate color="primary" size="48" />
      </v-col>
    </v-row>

    <v-card v-else-if="!data && selectedOrgId" class="pa-6 text-center">
      <v-icon size="48" color="grey-lighten-1">mdi-database-search</v-icon>
      <div class="text-body-1 mt-2">Нет данных для этой организации за {{ selectedYear }} год</div>
    </v-card>

    <v-card v-else-if="!selectedOrgId" class="pa-6 text-center bg-grey-lighten-4">
      <v-icon size="48" color="grey-lighten-1">mdi-account-question</v-icon>
      <div class="text-body-1 mt-2">Выберите организацию для сравнения</div>
    </v-card>

    <template v-else-if="data">
      <!-- Карточка организации -->
      <v-card class="mb-4 pa-4">
        <v-row align="center">
          <v-col cols="12" md="8">
            <div class="text-h6 font-weight-bold">{{ data.target.name }}</div>
            <div class="text-caption text-grey-darken-1 mt-1">
              {{ data.target.category }} · ОКВЭД {{ data.target.okved }} · {{ data.target.district }}
              · план {{ formatNumber(data.target.plan) }} тыс. ₽
            </div>
          </v-col>
          <v-col cols="12" md="4" class="text-md-right text-center">
            <v-chip :color="ipoColor(data.target.ipo)" size="x-large" variant="flat">
              <span class="text-h5 font-weight-bold">ИПО {{ data.target.ipo }}</span>
            </v-chip>
            <div class="text-caption mt-1">{{ ipoLabel(data.target.ipo) }}</div>
          </v-col>
        </v-row>
      </v-card>

      <!-- Сравнение с похожими -->
      <v-row dense>
        <v-col cols="12" md="6">
          <v-card class="pa-4 h-100">
            <div class="text-subtitle-1 font-weight-bold mb-3">
              Сравнение с похожими организациями
            </div>
            <div class="text-caption text-grey-darken-1 mb-3">
              Найдено {{ data.peers_summary.count }} похожих организаций по категории,
              виду деятельности и размеру плана
            </div>

            <div class="comparison-row">
              <div class="text-body-2">Ваш ИПО</div>
              <div class="text-h6 font-weight-bold" :class="getColorClass(data.target.ipo)">
                {{ data.target.ipo }}
              </div>
            </div>
            <div class="comparison-row">
              <div class="text-body-2">Медиана похожих</div>
              <div class="text-h6 font-weight-bold" :class="getColorClass(data.peers_summary.median_ipo)">
                {{ data.peers_summary.median_ipo }}
              </div>
            </div>

            <v-alert
              :color="data.target.ipo < data.peers_summary.median_ipo ? 'orange' : 'green'"
              variant="tonal"
              class="mt-3"
              density="compact"
            >
              <strong>{{ data.peers_summary.rank_text }}</strong>
            </v-alert>

            <div class="text-caption text-grey-darken-1 mt-3">
              Распределение похожих:
            </div>
            <div ref="dotPlotRef" style="height: 80px; width: 100%;"></div>
          </v-card>
        </v-col>

        <v-col cols="12" md="6">
          <v-card class="pa-4 h-100">
            <div class="text-subtitle-1 font-weight-bold mb-3">
              Где вы отстаёте?
            </div>

            <div
              v-for="comp in data.components_comparison"
              :key="comp.name"
              class="mb-4"
            >
              <div class="d-flex justify-space-between align-center mb-1">
                <div>
                  <span class="text-body-2 font-weight-medium">{{ comp.name }}</span>
                  <v-chip
                    v-if="comp.is_main_gap"
                    color="red"
                    size="x-small"
                    variant="tonal"
                    class="ml-2"
                  >
                    главная зона роста
                  </v-chip>
                </div>
                <div class="text-caption">
                  Вы: <strong>{{ comp.your }}</strong>
                  · медиана: <strong>{{ comp.median }}</strong>
                  · разрыв:
                  <span :class="comp.gap >= 0 ? 'text-green' : 'text-red'">
                    {{ comp.gap >= 0 ? '+' : '' }}{{ comp.gap }}
                  </span>
                </div>
              </div>
              <div class="progress-comparison">
                <div class="progress-bar-bg">
                  <div
                    class="progress-bar-median"
                    :style="{ width: comp.median + '%' }"
                  />
                  <div
                    class="progress-bar-your"
                    :style="{ width: comp.your + '%' }"
                  />
                </div>
              </div>
            </div>

            <v-divider class="my-3"></v-divider>

            <div class="text-caption text-grey-darken-1">
              <span class="dot-median"></span> Медиана похожих
              <span class="dot-your ml-3"></span> Ваш показатель
            </div>
          </v-card>
        </v-col>
      </v-row>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick, shallowRef } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'

const organizations = ref([])
const loadingOrgs = ref(false)
const selectedOrgId = ref(null)
const selectedYear = ref(2024)
const data = ref(null)
const loading = ref(false)
const dotPlotRef = ref(null)
const dotChart = shallowRef(null)

const formatNumber = (n) => new Intl.NumberFormat('ru-RU').format(Math.round(n))

const ipoColor = (ipo) => {
  if (ipo >= 90) return 'green'
  if (ipo >= 70) return 'light-green'
  if (ipo >= 50) return 'amber'
  if (ipo >= 30) return 'orange'
  return 'red'
}

const ipoLabel = (ipo) => {
  if (ipo >= 90) return 'Образцовая'
  if (ipo >= 70) return 'Надёжная'
  if (ipo >= 50) return 'Требует внимания'
  if (ipo >= 30) return 'Проблемная'
  return 'Критическая'
}

const getColorClass = (v) => {
  if (v >= 70) return 'text-green'
  if (v >= 50) return 'text-amber-darken-2'
  return 'text-red'
}

const fetchOrgs = async () => {
  loadingOrgs.value = true
  try {
    const r = await axios.get('/api/v1/organizations', { params: { size: 500 } })
    organizations.value = r.data.items ?? r.data
  } catch (e) {
    console.error('Не удалось загрузить организации:', e)
  } finally {
    loadingOrgs.value = false
  }
}

const fetchPeers = async () => {
  if (!selectedOrgId.value) return
  loading.value = true
  data.value = null
  try {
    const r = await axios.get(
      `/api/v1/analytics-center/peers/${selectedOrgId.value}`,
      { params: { year: selectedYear.value, n: 7 } }
    )
    data.value = r.data
    await nextTick()
    renderDotPlot()
  } catch (e) {
    if (e.response?.status === 404) {
      data.value = null
    } else {
      console.error('Не удалось загрузить похожие:', e)
    }
  } finally {
    loading.value = false
  }
}

const renderDotPlot = () => {
  if (!dotPlotRef.value || !data.value) return
  if (dotChart.value) dotChart.value.dispose()
  dotChart.value = echarts.init(dotPlotRef.value)

  const peersDots = data.value.peers_distribution.map(v => [v, 1])
  const yourDot = [[data.value.target.ipo, 1]]

  dotChart.value.setOption({
    grid: { left: 30, right: 30, top: 10, bottom: 30 },
    xAxis: {
      type: 'value',
      min: 0,
      max: 100,
      splitLine: { show: false },
    },
    yAxis: {
      show: false,
      min: 0,
      max: 2,
    },
    tooltip: {
      formatter: (p) => `ИПО: ${p.data[0].toFixed(1)}`,
    },
    series: [
      {
        name: 'Похожие',
        type: 'scatter',
        data: peersDots,
        symbolSize: 16,
        itemStyle: { color: '#90caf9', opacity: 0.8 },
      },
      {
        name: 'Ваш',
        type: 'scatter',
        data: yourDot,
        symbolSize: 22,
        itemStyle: { color: '#1976D2', borderColor: '#0D47A1', borderWidth: 2 },
      },
    ],
  })
}

watch([selectedOrgId, selectedYear], fetchPeers)
onMounted(fetchOrgs)
</script>

<style scoped>
.comparison-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid #f0f0f0;
}
.comparison-row:last-child { border-bottom: none; }

.progress-comparison {
  position: relative;
}
.progress-bar-bg {
  position: relative;
  height: 14px;
  background: #f5f5f5;
  border-radius: 7px;
  overflow: hidden;
}
.progress-bar-median {
  position: absolute;
  left: 0;
  top: 0;
  height: 14px;
  background: #bdbdbd;
  border-radius: 7px;
}
.progress-bar-your {
  position: absolute;
  left: 0;
  top: 0;
  height: 14px;
  background: linear-gradient(90deg, #1976D2 0%, #42A5F5 100%);
  border-radius: 7px;
  opacity: 0.85;
}
.dot-median, .dot-your {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  vertical-align: middle;
  margin-right: 4px;
}
.dot-median { background: #bdbdbd; }
.dot-your { background: #1976D2; }
</style>
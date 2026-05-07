<template>
  <div class="pa-4">
    <v-row class="mb-4" align="center">
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

    <template v-else-if="data">
      <v-row>
        <v-col cols="12" md="8">
          <v-card class="pa-4">
            <div class="text-subtitle-1 font-weight-bold mb-2">
              Типология районов Тюменской области
            </div>
            <div class="text-caption text-grey-darken-1 mb-3">
              Районы окрашены по кластерам сходства (метод k-means) на основе ИПО, просрочки, СМП и планов.
            </div>
            <!-- Контейнер для карты -->
            <div ref="chartRef" style="height: 600px; width: 100%;"></div>
          </v-card>
        </v-col>

        <v-col cols="12" md="4">
          <v-card class="pa-4 h-100">
            <div class="text-subtitle-1 font-weight-bold mb-3">
              Группы районов
            </div>
            <div
              v-for="cluster in data.clusters"
              :key="cluster.id"
              class="cluster-info mb-3 pa-3"
              :style="{ borderLeft: `4px solid ${cluster.color}` }"
            >
              <div class="d-flex justify-space-between align-center mb-1">
                <div class="text-body-1 font-weight-bold">{{ cluster.name }}</div>
                <v-chip size="x-small" :color="cluster.color" variant="flat">
                  {{ cluster.districts_count }}
                </v-chip>
              </div>
              <div class="text-caption text-grey-darken-1">{{ cluster.description }}</div>
              <div class="text-caption mt-1">
                Средний ИПО в группе: <strong>{{ cluster.avg_ipo }}</strong>
              </div>
            </div>
          </v-card>
        </v-col>
      </v-row>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick, shallowRef, onUnmounted } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'

const selectedYear = ref(2024)
const data = ref(null)
const loading = ref(false)
const chartRef = ref(null)
const chart = shallowRef(null)
let resizeObserver = null

const fetchData = async () => {
  loading.value = true
  try {
    const r = await axios.get('/api/v1/analytics-center/districts-clusters', {
      params: { year: selectedYear.value, n_clusters: 4 },
    })
    data.value = r.data
    await nextTick()
    renderChart()
  } catch (e) {
    console.error('Не удалось загрузить кластеры:', e)
  } finally {
    loading.value = false
  }
}

const renderChart = () => {
  if (!chartRef.value || !data.value) return
  if (chart.value) chart.value.dispose()
  chart.value = echarts.init(chartRef.value)

  // Подготовка данных для карты
  const mapData = data.value.districts.map(d => ({
    name: d.name,
    value: d.cluster_id, // Кластер определяет цвет
    // Пробрасываем доп. данные для тултипа
    avg_ipo: d.avg_ipo,
    avg_late_days: d.avg_late_days,
    org_count: d.organizations_count,
    median_plan: d.median_plan,
    smp_share: d.smp_share
  }))

  // Настройка цветов на основе кластеров из API
  const pieces = data.value.clusters.map(c => ({
    value: c.id,
    label: c.name,
    color: c.color
  }))

  chart.value.setOption({
    tooltip: {
      trigger: 'item',
      formatter: (p) => {
        if (!p.data) return p.name
        return `<b>${p.name}</b><br/>
          Средний ИПО: ${p.data.avg_ipo.toFixed(1)}<br/>
          Средняя просрочка: ${p.data.avg_late_days.toFixed(1)} дн.<br/>
          Организаций: ${p.data.org_count}<br/>
          Доля СМП: ${(p.data.smp_share * 100).toFixed(1)}%`
      }
    },
    visualMap: {
      type: 'piecewise',
      pieces: pieces,
      show: false // Скрываем, так как легенда отрисована справа во Vuetify
    },
    series: [
      {
        name: 'Кластеры',
        type: 'map',
        map: 'tyumen', // Имя зарегистрированной карты ТО
        roam: true,
        emphasis: {
          label: { show: true },
          itemStyle: { areaColor: '#ffd54f' }
        },
        data: mapData
      }
    ]
  })

  if (resizeObserver) resizeObserver.disconnect()
  resizeObserver = new ResizeObserver(() => {
    if (chart.value) chart.value.resize()
  })
  resizeObserver.observe(chartRef.value)
}

watch(selectedYear, fetchData)

onMounted(() => {
  fetchData()
})

onUnmounted(() => {
  if (resizeObserver) resizeObserver.disconnect()
  if (chart.value) chart.value.dispose()
})
</script>

<style scoped>
.cluster-info {
  background: #fafafa;
  border-radius: 4px;
}
</style>
<template>
  <div class="pa-4">
    <v-row class="mb-4" align="center">
      <v-col cols="12" sm="3">
        <v-select
          v-model="selectedYear"
          :items="[2024, 2025]"
          label="Год"
          density="compact"
          variant="outlined"
          hide-details
        />
      </v-col>
      <v-col cols="12" sm="9" class="text-right">
        <v-btn
          variant="text"
          size="small"
          @click="showHelp = !showHelp"
          prepend-icon="mdi-help-circle-outline"
        >
          Как это читать
        </v-btn>
      </v-col>
    </v-row>

    <v-expand-transition>
      <v-alert
        v-if="showHelp"
        type="info"
        variant="tonal"
        class="mb-4"
        closable
        @click:close="showHelp = false"
      >
        <div class="text-body-2">
          <strong>Box-plot</strong> показывает разброс ИПО внутри каждого района.
          Зелёная полоса — средние 50% организаций. Чёрная черта — медиана.
          Отдельные точки — выбросы (организации, заметно отличающиеся от района).
          <br /><br />
          <strong>ICC</strong> (внутригрупповая корреляция) — какая доля разброса
          ИПО объясняется именно тем, в каком районе находится организация.
          Высокий ICC значит, что районная среда сильно влияет на дисциплину;
          низкий — что дисциплина зависит от самих организаций.
        </div>
      </v-alert>
    </v-expand-transition>

    <v-row v-if="loading">
      <v-col class="text-center pa-12">
        <v-progress-circular indeterminate color="primary" size="48" />
      </v-col>
    </v-row>

    <template v-else-if="data">
      <v-card class="mb-4 pa-4" :color="iccColor" variant="tonal">
        <v-row align="center">
          <v-col cols="12" md="3" class="text-center">
            <div class="text-caption">Доля разброса ИПО,<br />объясняемая районом</div>
            <div class="text-h2 font-weight-bold mt-2">
              {{ Math.round(data.icc * 100) }}%
            </div>
          </v-col>
          <v-col cols="12" md="9">
            <div class="text-h6 font-weight-bold mb-2">{{ data.icc_text }}</div>
            <div class="text-body-2">{{ data.icc_explanation }}</div>
            <div class="text-caption mt-3 text-grey-darken-1">
              Анализ построен на {{ data.total_organizations }} организациях
              и {{ data.districts.length }} районах.
            </div>
          </v-col>
        </v-row>
      </v-card>

      <v-card class="pa-4">
        <div class="text-subtitle-1 font-weight-bold mb-2">
          Распределение ИПО по районам
        </div>
        <!-- Контейнер для графика -->
        <div ref="boxplotRef" :style="{ height: chartHeight + 'px', width: '100%' }"></div>
      </v-card>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick, computed, shallowRef } from 'vue'
import * as echarts from 'echarts'
import axios from 'axios'

const selectedYear = ref(2024)
const data = ref(null)
const loading = ref(false)
const showHelp = ref(false)
const boxplotRef = ref(null)
const chart = shallowRef(null)
let resizeObserver = null

const chartHeight = computed(() => {
  const count = data.value?.districts.length ?? 0
  return Math.max(400, count * 28 + 100)
})

const iccColor = computed(() => {
  if (!data.value) return 'grey-lighten-3'
  if (data.value.icc_level === 'high') return 'red-lighten-4'
  if (data.value.icc_level === 'moderate') return 'amber-lighten-4'
  return 'green-lighten-4'
})

const fetchData = async () => {
  loading.value = true
  try {
    const r = await axios.get('/api/v1/analytics-center/districts-dispersion', {
      params: { year: selectedYear.value },
    })
    data.value = r.data
    await nextTick()
    renderChart()
  } catch (e) {
    console.error('Не удалось загрузить данные дисперсии:', e)
  } finally {
    loading.value = false
  }
}

const renderChart = () => {
  if (!boxplotRef.value || !data.value) return
  if (chart.value) chart.value.dispose()
  
  chart.value = echarts.init(boxplotRef.value)
  
  const districts = data.value.districts
  const yAxisData = districts.map(d => `${d.name} (${d.count})`)
  const boxData = districts.map(d => [d.min, d.q25, d.median_ipo, d.q75, d.max])
  const outliersData = []
  districts.forEach((d, i) => {
    d.outliers.forEach(value => outliersData.push([value, i]))
  })

  chart.value.setOption({
    tooltip: {
      trigger: 'item',
      formatter: (p) => {
        if (p.seriesType === 'boxplot') {
          const d = districts[p.dataIndex]
          return `<b>${d.name}</b><br/>
            Организаций: ${d.count}<br/>
            Минимум: ${d.min.toFixed(1)}<br/>
            25-й перцентиль: ${d.q25.toFixed(1)}<br/>
            Медиана: ${d.median_ipo.toFixed(1)}<br/>
            75-й перцентиль: ${d.q75.toFixed(1)}<br/>
            Максимум: ${d.max.toFixed(1)}`
        }
        return `Выброс: ${p.data[0].toFixed(1)}`
      },
    },
    grid: { left: 200, right: 40, top: 20, bottom: 40 },
    xAxis: {
      type: 'value',
      min: 0,
      max: 100,
      name: 'ИПО',
      nameLocation: 'middle',
      nameGap: 28,
      splitLine: { show: true, lineStyle: { type: 'dashed', color: '#e0e0e0' } },
    },
    yAxis: {
      type: 'category',
      data: yAxisData,
      axisLabel: { fontSize: 11 },
      splitArea: { show: true },
    },
    series: [
      {
        type: 'boxplot',
        data: boxData,
        itemStyle: {
          color: '#81c784',
          borderColor: '#388e3c',
          borderWidth: 1.5,
        },
      },
      {
        type: 'scatter',
        data: outliersData,
        symbolSize: 7,
        itemStyle: { color: '#d32f2f' },
      },
    ],
  })

  // Инициализация обзервера для корректного ресайза
  if (resizeObserver) resizeObserver.disconnect()
  resizeObserver = new ResizeObserver(() => {
    if (chart.value) chart.value.resize()
  })
  resizeObserver.observe(boxplotRef.value)
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
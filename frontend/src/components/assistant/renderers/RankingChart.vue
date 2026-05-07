<template>
  <v-card variant="outlined" class="rounded-lg bg-white overflow-hidden">
    <v-card-title class="text-subtitle-2 bg-grey-lighten-4 py-2">
      <v-icon start size="18">mdi-chart-bar</v-icon>
      Топ-{{ data.items?.length || 0 }} ({{ data.year }} год)
    </v-card-title>
    <v-card-text class="pa-2">
      <div ref="chartRef" style="height: 250px; width: 100%;"></div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: Object
})
const chartRef = ref(null)
let chart = null

onMounted(() => {
  if (!chartRef.value || !props.data?.items) return
  chart = echarts.init(chartRef.value)
  
  // Разворачиваем массив, чтобы топ-1 был сверху в горизонтальном графике
  const reversedItems = [...props.data.items].reverse()
  const names = reversedItems.map(item => item.name)
  const values = reversedItems.map(item => item.ipo)

  chart.setOption({
    grid: { left: '3%', right: '10%', bottom: '0%', top: '5%', containLabel: true },
    xAxis: { type: 'value', max: 100, show: false },
    yAxis: { type: 'category', data: names, axisLabel: { fontWeight: 'bold' }, axisLine: { show: false }, axisTick: { show: false } },
    series: [{
      type: 'bar',
      data: values,
      itemStyle: { borderRadius: [0, 4, 4, 0], color: '#4CAF50' },
      label: { show: true, position: 'right', formatter: '{c}', fontWeight: 'bold' }
    }]
  })
})

onUnmounted(() => {
  chart?.dispose()
})
</script>
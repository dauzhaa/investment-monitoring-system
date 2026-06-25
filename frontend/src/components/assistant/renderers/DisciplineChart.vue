<template>
  <div class="chart-container border-md rounded-xl pa-4 bg-white mt-4 shadow-sm">
    <div ref="chartRef" style="width: 100%; height: 500px;"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

const chartRef = ref(null)
let chartInstance = null

onMounted(() => {
  chartInstance = echarts.init(chartRef.value)

  const option = {
    animationDuration: 1500,
    title: {
      text: 'Сравнение Индекса Дисциплины (ρ)',
      left: 'center',
      textStyle: {
        fontSize: 32, // Заголовок, который видно с задней парты
        fontWeight: '900',
        color: '#000000'
      },
      padding: [10, 0, 30, 0]
    },
    grid: {
      left: '5%',
      right: '5%',
      bottom: '10%',
      top: '25%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: ['ВУЗы', 'Школы'],
      axisLabel: {
        fontSize: 32,
        fontWeight: 'bold',
        color: '#000000',
        margin: 20
      },
      axisLine: {
        lineStyle: { width: 4, color: '#333' }
      }
    },
    yAxis: {
      type: 'value',
      max: 100, // ИПО считается до 100
      axisLabel: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#333'
      },
      splitLine: {
        lineStyle: { type: 'dashed', width: 2, color: '#CCC' }
      }
    },
    series: [
      {
        type: 'bar',
        barWidth: '50%', // Жирные столбцы
        data: [
          {
            value: 72,
            itemStyle: { color: '#1976D2', borderRadius: [8, 8, 0, 0] } // Синий
          },
          {
            value: 65,
            itemStyle: { color: '#D32F2F', borderRadius: [8, 8, 0, 0] } // Красный
          }
        ],
        label: {
          show: true,
          position: 'top',
          distance: 15,
          fontSize: 48, // Гигантские цифры над столбцами
          fontWeight: '900',
          color: '#000',
          formatter: '{c}' // Покажет просто "72" и "65"
        }
      }
    ]
  }

  chartInstance.setOption(option)

  // Адаптивность при ресайзе окна
  window.addEventListener('resize', () => {
    chartInstance.resize()
  })
})

onBeforeUnmount(() => {
  if (chartInstance) {
    chartInstance.dispose()
  }
})
</script>

<style scoped>
.chart-container {
  border: 2px solid #CBD5E1 !important;
}
</style>
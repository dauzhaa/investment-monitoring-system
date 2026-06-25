<template>
  <div class="chart-container border-md rounded-xl pa-6 bg-white mt-4 shadow-sm">
    <!-- Высота 700px нужна, чтобы 10 районов не слиплись -->
    <div ref="chartRef" style="width: 100%; height: 750px;"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: Object
})

const chartRef = ref(null)
let chartInstance = null

onMounted(() => {
  chartInstance = echarts.init(chartRef.value)

  // Исходные данные (отсортированы по убыванию)
  const rawData = [
    { name: 'Тюменский район', value: 88, color: '#1976D2' },
    { name: 'ГО Тюмень', value: 87, color: '#1976D2' },
    { name: 'Ханты-Мансийский', value: 86, color: '#1976D2' },
    { name: 'ГО Нягань', value: 85, color: '#1976D2' },
    { name: 'ГО Радужный', value: 84, color: '#1976D2' },
    { name: 'Бердюжский район', value: 48, color: '#D32F2F' },
    { name: 'Армизонский район', value: 47, color: '#D32F2F' },
    { name: 'Голышмановский', value: 46, color: '#D32F2F' },
    { name: 'Ярковский район', value: 45, color: '#D32F2F' },
    { name: 'Упоровский район', value: 44, color: '#D32F2F' }
  ]

  // ECharts строит горизонтальные графики снизу вверх, поэтому переворачиваем массив
  rawData.reverse()

  const option = {
    animationDuration: 1500,
    title: {
      text: 'ТОП-5 и АНТИ-ТОП-5 районов по качеству',
      left: 'center',
      textStyle: {
        fontSize: 34,
        fontWeight: '900',
        color: '#000000'
      },
      padding: [0, 0, 40, 0]
    },
    grid: {
      left: '2%',
      right: '12%', // Место для цифр справа
      bottom: '2%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      max: 100,
      splitLine: { show: false }, // Убираем вертикальные линии для чистоты
      axisLabel: { show: false }, // Прячем цифры оси X
      axisLine: { show: false },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'category',
      data: rawData.map(item => item.name),
      axisLabel: {
        fontSize: 24, // Огромный шрифт для проектора
        fontWeight: 'bold',
        color: '#000000',
        margin: 15
      },
      axisLine: {
        lineStyle: { width: 4, color: '#333' } // Толстая ось Y
      },
      axisTick: { show: false }
    },
    series: [
      {
        type: 'bar',
        barWidth: '60%', // Жирные горизонтальные столбцы
        data: rawData.map(item => ({
          value: item.value,
          itemStyle: { 
            color: item.color, 
            borderRadius: [0, 8, 8, 0] // Закругление правых краев
          }
        })),
        label: {
          show: true,
          position: 'right', // Цифры выводятся справа от столбца
          distance: 15,
          fontSize: 32, // Гигантские цифры
          fontWeight: '900',
          color: '#000',
          formatter: '{c}'
        }
      }
    ]
  }

  chartInstance.setOption(option)

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
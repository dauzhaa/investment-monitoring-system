<template>
  <div ref="chart" class="map-chart"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';
import * as echarts from 'echarts';
// Импортируем твой новый файл
import tyumenJson from '@/assets/tyumen_districts.json';

const chart = ref(null);
let myChart = null;

// Регистрируем карту в ECharts
echarts.registerMap('TYUMEN', tyumenJson);

onMounted(() => {
  if (!chart.value) return;
  
  myChart = echarts.init(chart.value);
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}' // Показывает название района при наведении
    },
    visualMap: {
      min: 0,
      max: 5000,
      text: ['Высокая', 'Низкая'],
      realtime: false,
      calculable: true,
      inRange: {
        color: ['#e0f2f1', '#00695c'] // От светлого к темному
      }
    },
    series: [
      {
        name: 'Инвестиции',
        type: 'map',
        map: 'TYUMEN', // Должно совпадать с именем при регистрации
        roam: true, // Можно двигать и зумить
        label: {
          show: false // Скрываем подписи, чтобы не засорять карту
        },
        emphasis: {
          label: {
            show: true
          },
          itemStyle: {
             areaColor: '#ffeb3b' // Цвет при наведении
          }
        },
        // Важный момент: ECharts ищет совпадение имени района в GeoJSON (поле name)
        // Если названия в базе данных не совпадут с картой, районы будут серыми.
        // Для теста покажем фейковые данные:
        data: [
          { name: 'Тюменский район', value: 4500 },
          { name: 'Тобольский район', value: 3200 },
          { name: 'Ишимский район', value: 2100 }
        ]
      }
    ]
  };

  myChart.setOption(option);
  window.addEventListener('resize', resizeChart);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeChart);
  if (myChart) myChart.dispose();
});

const resizeChart = () => {
  if (myChart) myChart.resize();
};
</script>

<style scoped>
.map-chart {
  width: 100%;
  height: 100%;
  min-height: 400px;
}
</style>
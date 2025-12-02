<template>
  <div ref="chart" class="map-chart"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import * as echarts from 'echarts';
import tyumenJson from '@/assets/tyumen_districts.json';

const chart = ref(null);
let myChart = null;

const props = defineProps(['mapData']);
const emit = defineEmits(['district-click']);

// Регистрируем карту
echarts.registerMap('TYUMEN', tyumenJson);

onMounted(() => {
  if (chart.value) {
    myChart = echarts.init(chart.value);
    updateChart();
    
    // Слушаем клик по области
    myChart.on('click', (params) => {
      if (params.componentType === 'series') {
        // params.name соответствует полю NAME_2 из GeoJSON
        emit('district-click', params.name);
      }
    });
    
    window.addEventListener('resize', resizeChart);
  }
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeChart);
  if (myChart) myChart.dispose();
});

watch(() => props.mapData, updateChart, { deep: true });

function updateChart() {
  if (!myChart) return;

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}<br/>Инвестиции: {c} млн ₽'
    },
    visualMap: {
      left: 'right',
      min: 0,
      max: 5000, 
      inRange: {
        color: ['#E0F7FA', '#006064']
      },
      text: ['Макс', 'Мин'],
      calculable: true
    },
    series: [
      {
        name: 'Инвестиции',
        type: 'map',
        map: 'TYUMEN',
        roam: true, // Разрешаем зум и движение
        scaleLimit: { min: 1, max: 10 },
        zoom: 1.2,
        label: {
          show: false
        },
        emphasis: {
          label: { show: true, color: '#000' },
          itemStyle: {
            areaColor: '#FFD700', // Цвет при наведении (золотой)
            borderColor: '#fff',
            borderWidth: 2
          }
        },
        select: {
          itemStyle: { areaColor: '#FFCA28' }
        },
        // Указываем, какое поле из GeoJSON использовать как имя
        // В предоставленном tyumen_districts.json имя района лежит в NAME_2
        nameProperty: 'NAME_2',
        data: props.mapData
      }
    ]
  };

  myChart.setOption(option);
}

const resizeChart = () => myChart && myChart.resize();
</script>

<style scoped>
.map-chart {
  width: 100%;
  height: 100%;
  min-height: 600px; /* Увеличенная высота */
}
</style>
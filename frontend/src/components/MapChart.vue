<template>
  <div ref="chart" class="map-chart"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import * as echarts from 'echarts';
import tyumenJson from '@/assets/tyumen_districts.json';

const chart = ref(null);
let myChart = null;

const props = defineProps({
  mapData: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits(['district-click']);

// Регистрируем карту в ECharts
echarts.registerMap('TYUMEN', tyumenJson);

onMounted(() => {
  if (!chart.value) return;
  
  myChart = echarts.init(chart.value);
  
  updateChart();
  
  // Обработчик клика по району
  myChart.on('click', (params) => {
    if (params.componentType === 'series' && params.seriesType === 'map') {
      emit('district-click', params.name);
    }
  });
  
  window.addEventListener('resize', resizeChart);
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeChart);
  if (myChart) myChart.dispose();
});

watch(() => props.mapData, () => {
  updateChart();
}, { deep: true });

const updateChart = () => {
  if (!myChart) return;
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        return `${params.name}<br/>Инвестиции: ${params.value ? params.value.toLocaleString('ru-RU') : 0} млн ₽`;
      }
    },
    visualMap: {
      min: 0,
      max: 5000,
      text: ['Высокая', 'Низкая'],
      realtime: false,
      calculable: true,
      inRange: {
        color: ['#e0f2f1', '#00695c']
      },
      textStyle: {
        fontSize: 10
      }
    },
    series: [
      {
        name: 'Инвестиции',
        type: 'map',
        map: 'TYUMEN',
        roam: true,
        label: {
          show: false
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 12,
            fontWeight: 'bold'
          },
          itemStyle: {
            areaColor: '#ffeb3b',
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        },
        data: props.mapData.length > 0 ? props.mapData : [
          { name: 'Тюменский район', value: 4500 },
          { name: 'Тобольский район', value: 3200 },
          { name: 'Ишимский район', value: 2100 }
        ]
      }
    ]
  };

  myChart.setOption(option);
};

const resizeChart = () => {
  if (myChart) myChart.resize();
};
</script>

<style scoped>
.map-chart {
  width: 100%;
  height: 100%;
  min-height: 400px;
  cursor: pointer;
}
</style>
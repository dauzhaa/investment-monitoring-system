<template>
  <div class="map-container">
    <div ref="chartEl" class="map-chart"></div>
    <!-- Легенда -->
    <div class="map-legend">
      <span class="legend-label">Мин</span>
      <div class="legend-gradient"></div>
      <span class="legend-label">Макс</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import * as echarts from 'echarts';
import tyumenJson from '@/assets/tyumen_districts.json';
import api from '@/services/api';

const props = defineProps({
  data: { type: Array, default: () => [] },
  selectedYear: { type: Number, default: 2022 }
});

const emit = defineEmits(['district-click']);

const chartEl = ref(null);
let chart = null;

echarts.registerMap('TYUMEN', tyumenJson);

const initChart = () => {
  if (!chartEl.value) return;
  
  chart = echarts.init(chartEl.value);
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const value = params.value || 0;
        return `<strong>${params.name}</strong><br/>Инвестиции: ${(value / 1000000).toFixed(1)} млн ₽`;
      }
    },
    visualMap: {
      show: false,
      min: 0,
      max: 200000000,
      inRange: {
        // Синяя градация
        color: ['#E3F2FD', '#90CAF9', '#42A5F5', '#1E88E5', '#1565C0']
      }
    },
    series: [{
      name: 'Инвестиции',
      type: 'map',
      map: 'TYUMEN',
      roam: true,
      zoom: 1.15,
      center: [68.5, 57.5],
      label: { show: false },
      emphasis: {
        label: { show: true, fontSize: 11, fontWeight: 'bold' },
        itemStyle: { areaColor: '#FFA726' }  // Оранжевый при наведении
      },
      select: {
        label: { show: true, fontSize: 11 },
        itemStyle: { areaColor: '#FFA726' }  // Оранжевый при выборе
      },
      selectedMode: 'single',
      itemStyle: {
        borderColor: '#fff',
        borderWidth: 1
      },
      data: props.data
    }]
  };

  chart.setOption(option);
  
  chart.on('click', (params) => {
    if (params.componentType === 'series') {
      emit('district-click', params.name);
    }
  });

  window.addEventListener('resize', handleResize);
};

const updateData = () => {
  if (!chart) return;
  chart.setOption({
    series: [{ data: props.data }]
  });
};

const handleResize = () => {
  if (chart) chart.resize();
};

watch(() => props.data, updateData, { deep: true });

onMounted(initChart);

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  if (chart) chart.dispose();
});
</script>

<style scoped>
.map-container {
  width: 100%;
  height: 100%;
  position: relative;
}
.map-chart {
  width: 100%;
  height: 100%;
  min-height: 380px;
}
.map-legend {
  position: absolute;
  bottom: 10px;
  right: 10px;
  display: flex;
  align-items: center;
  background: rgba(255,255,255,0.9);
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 11px;
}
.legend-gradient {
  width: 80px;
  height: 10px;
  margin: 0 8px;
  background: linear-gradient(to right, #E3F2FD, #90CAF9, #42A5F5, #1E88E5, #1565C0);
  border-radius: 3px;
}
.legend-label {
  color: #666;
}
</style>
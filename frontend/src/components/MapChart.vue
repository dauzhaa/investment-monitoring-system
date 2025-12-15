<template>
  <div class="map-container">
    <div ref="chartRef" class="map-chart"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import * as echarts from 'echarts';
import tyumenGeoJson from '@/assets/tyumen_districts.json';

const props = defineProps({
  data: { type: Array, default: () => [] },
  selectedYear: { type: Number, default: 2022 }
});

const emit = defineEmits(['district-click']);

const chartRef = ref(null);
let myChart = null;

// Мягкие цвета
const colors = {
  primary: '#5C6BC0',
  success: '#26A69A',
  warning: '#FF8A65',
  accent: '#FFCA28',
  selected: '#FFA726'  // Оранжевый для выделения
};

// Создаем карту соответствия NL_NAME_2 -> name для ECharts
const processGeoJson = () => {
  const processed = JSON.parse(JSON.stringify(tyumenGeoJson));
  processed.features.forEach(feature => {
    if (feature.properties.NL_NAME_2) {
      feature.properties.name = feature.properties.NL_NAME_2;
    }
  });
  return processed;
};

const formatMoney = (value) => {
  if (!value || value === 0) return '0 ₽';
  if (value >= 1000000) {
    return (value / 1000000).toFixed(1) + ' млн ₽';
  }
  if (value >= 1000) {
    return (value / 1000).toFixed(0) + ' тыс ₽';
  }
  return value.toLocaleString('ru-RU') + ' ₽';
};

const initChart = () => {
  if (!chartRef.value) return;

  // Регистрируем карту
  const processedGeoJson = processGeoJson();
  echarts.registerMap('TYUMEN', processedGeoJson);

  myChart = echarts.init(chartRef.value);

  // Подготавливаем данные
  const mapData = (props.data || []).map(item => ({
    name: item.name,
    value: item.value || 0
  }));

  const maxValue = Math.max(...mapData.map(d => d.value), 1);

  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#ddd',
      borderWidth: 1,
      textStyle: { color: '#333' },
      formatter: (params) => {
        const value = params.value || 0;
        return `<div style="padding: 8px;">
          <div style="font-size: 14px; font-weight: bold; margin-bottom: 4px;">${params.name}</div>
          <div style="color: ${colors.success}; font-weight: 500;">
            Инвестиции: ${formatMoney(value)}
          </div>
          <div style="color: #888; font-size: 11px; margin-top: 4px;">
            Нажмите для подробностей
          </div>
        </div>`;
      }
    },
    visualMap: {
      show: true,
      min: 0,
      max: maxValue,
      text: ['Макс', 'Мин'],
      realtime: false,
      calculable: false,
      orient: 'vertical',
      right: 10,
      bottom: 50,
      itemWidth: 12,
      itemHeight: 80,
      textStyle: { fontSize: 10, color: '#666' },
      inRange: {
        // Мягкая сине-бирюзовая палитра
        color: ['#E8F5E9', '#C8E6C9', '#A5D6A7', '#81C784', '#66BB6A', '#4CAF50', '#43A047', '#388E3C']
      }
    },
    series: [{
      name: 'Инвестиции',
      type: 'map',
      map: 'TYUMEN',
      roam: true,
      zoom: 1.1,
      center: [68.5, 57.5],
      aspectScale: 0.85,
      nameProperty: 'name',
      selectedMode: 'single',  // Разрешаем выделение
      label: {
        show: false
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 11,
          fontWeight: 'bold',
          color: '#333'
        },
        itemStyle: {
          areaColor: colors.accent,  // Жёлтый при наведении
          borderColor: colors.warning,
          borderWidth: 2
        }
      },
      select: {
        label: { 
          show: true,
          fontSize: 12,
          fontWeight: 'bold',
          color: '#fff'
        },
        itemStyle: {
          areaColor: colors.selected,  // Оранжевый при выборе
          borderColor: '#E65100',
          borderWidth: 2
        }
      },
      itemStyle: {
        areaColor: '#E3F2FD',
        borderColor: '#FFFFFF',
        borderWidth: 1.5
      },
      data: mapData
    }]
  };

  myChart.setOption(option);

  // Обработчик клика
  myChart.on('click', (params) => {
    if (params.componentType === 'series' && params.name) {
      emit('district-click', params.name);
    }
  });

  window.addEventListener('resize', handleResize);
};

const handleResize = () => {
  if (myChart) {
    myChart.resize();
  }
};

const updateData = () => {
  if (myChart && props.data) {
    const mapData = props.data.map(item => ({
      name: item.name,
      value: item.value || 0
    }));

    const maxValue = Math.max(...mapData.map(d => d.value), 1);

    myChart.setOption({
      visualMap: {
        max: maxValue
      },
      series: [{ data: mapData }]
    });
  }
};

watch(() => props.data, () => {
  nextTick(() => {
    updateData();
  });
}, { deep: true });

onMounted(() => {
  nextTick(() => {
    initChart();
  });
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  if (myChart) {
    myChart.off('click');
    myChart.dispose();
    myChart = null;
  }
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
  min-height: 400px;
}
</style>
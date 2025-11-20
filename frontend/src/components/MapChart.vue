<template>
  <div class="map-wrapper">
    <v-chart class="chart" :option="option" autoresize @click="onClick" />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { ScatterChart, EffectScatterChart } from 'echarts/charts';
import { TitleComponent, TooltipComponent, LegendComponent, GeoComponent, GraphicComponent } from 'echarts/components';
import VChart from 'vue-echarts';
import * as echarts from 'echarts';
import tyumenJson from '@/assets/tyumen_geo.json';

use([CanvasRenderer, ScatterChart, EffectScatterChart, TitleComponent, TooltipComponent, LegendComponent, GeoComponent, GraphicComponent]);

const props = defineProps(['clusteringData']);
const emit = defineEmits(['region-click']);

const option = ref({
  backgroundColor: '#fff',
  // ВОДЯНОЙ ЗНАК (Красиво подписали область)
  graphic: [
    {
      type: 'text',
      right: 20,
      bottom: 20,
      style: {
        text: 'Тюменская область',
        // Полупрозрачный белый, чтобы сочеталось с синей картой, но не мешало
        fill: 'rgba(25, 118, 210, 0.15)', 
        fontSize: 40,
        fontWeight: 'bold',
        fontFamily: 'Arial, sans-serif'
      },
      z: 0
    }
  ],
  tooltip: {
    trigger: 'item',
    backgroundColor: '#fff',
    textStyle: { color: '#000' },
    formatter: (params) => {
      if (params.componentType === 'series') {
         return `<b>${params.name}</b><br/>Статус: ${params.data.clusterName}`;
      }
      return params.name;
    }
  },
  geo: {
    map: 'tyumen',
    roam: false,
    zoom: 1.2,
    label: { show: false },
    itemStyle: {
      areaColor: '#1976D2', // Основной синий цвет
      borderColor: '#FFFFFF',
      borderWidth: 1.5,
      shadowColor: 'rgba(0, 0, 0, 0.3)',
      shadowBlur: 10
    },
    emphasis: {
      disabled: true,
      itemStyle: { areaColor: '#1976D2' }
    }
  },
  legend: { show: false },
  series: []
});

onMounted(() => {
  echarts.registerMap('tyumen', tyumenJson);
});

// КООРДИНАТЫ (Я их чуть раздвинул вручную, чтобы города не слипались с районами)
const DISTRICT_COORDS = {
    "г. Тюмень": [65.45, 57.15],          // Чуть левее
    "Тюменский район": [65.65, 57.25],    // Чуть правее и выше
    
    "г. Тобольск": [68.20, 58.15],        // Чуть ниже
    "Тобольский район": [68.45, 58.35],   // Чуть выше
    
    "г. Ишим": [69.40, 56.05],            // Чуть ниже
    "Ишимский район": [69.30, 56.20],     // Чуть выше
    
    "г. Ялуторовск": [66.3061, 56.6556],
    "Заводоуковский ГО": [66.55, 56.50],
    "Уватский район": [68.90, 59.14],
    "Вагайский район": [69.01, 57.93]
};

watch(() => props.clusteringData, (data) => {
  if (!data) return;

  const seriesData = [[], [], []]; 
  const clusterNames = ['Низкая актив.', 'Стабильные', 'Лидеры'];

  for (const [districtName, clusterId] of Object.entries(data)) {
    const coords = DISTRICT_COORDS[districtName];
    if (coords) {
       seriesData[clusterId].push({
         name: districtName,
         value: [...coords, 100],
         clusterName: clusterNames[clusterId]
       });
    }
  }

  // Настройки меток
  const labelOption = {
    show: true,
    position: 'top', // Пробуем ставить сверху
    distance: 8,
    formatter: '{b}',
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderColor: '#1976D2', // Синяя окантовка под цвет карты
    borderWidth: 1,
    borderRadius: 4,
    padding: [4, 6],
    fontSize: 11,
    fontWeight: 'bold',
    color: '#0D47A1', // Темно-синий текст
    shadowColor: 'rgba(0,0,0,0.2)',
    shadowBlur: 2
  };

  option.value.series = [
    { 
        name: 'Отстающие', 
        type: 'effectScatter', 
        coordinateSystem: 'geo', 
        data: seriesData[0], 
        symbolSize: 15, 
        itemStyle: { color: '#FF5252' }, 
        label: labelOption,
        // ВАЖНО: Разрешаем двигать метки, чтобы не скрывались
        labelLayout: { hideOverlap: false, moveOverlap: 'shiftY' } 
    },
    { 
        name: 'Средние', 
        type: 'effectScatter', 
        coordinateSystem: 'geo', 
        data: seriesData[1], 
        symbolSize: 15, 
        itemStyle: { color: '#FFAB40' }, 
        label: labelOption,
        labelLayout: { hideOverlap: false, moveOverlap: 'shiftY' }
    },
    { 
        name: 'Лидеры', 
        type: 'effectScatter', 
        coordinateSystem: 'geo', 
        data: seriesData[2], 
        symbolSize: 20, 
        itemStyle: { color: '#00E676' }, 
        label: labelOption,
        labelLayout: { hideOverlap: false, moveOverlap: 'shiftY' }
    }
  ];
}, { deep: true, immediate: true });

const onClick = (params) => {
  if (params.componentType === 'series') emit('region-click', params.name);
};
</script>

<style scoped>
.map-wrapper {
  height: 600px;
  width: 100%;
  background: #fff;
  border-radius: 0 0 8px 8px;
}
.chart { height: 100%; width: 100%; }
</style>
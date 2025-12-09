<template>
  <div class="map-container">
    <div ref="chart" class="map-chart"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import * as echarts from 'echarts';
import tyumenJson from '@/assets/tyumen_districts.json';
import axios from 'axios';

const props = defineProps({
  year: {
    type: Number,
    default: () => new Date().getFullYear()
  }
});

const chart = ref(null);
let myChart = null;

// Регистрируем карту в ECharts
echarts.registerMap('TYUMEN', tyumenJson);

const fetchMapData = async () => {
  let mapData = [];
  
  try {
    const res = await axios.get(`/api/v1/analytics/map?year=${props.year}`);
    if (res.data) {
      mapData = res.data;
    }
  } catch (e) {
    console.log('Using mock map data');
    // Заглушка с данными
    mapData = [
      { name: 'Тюменский район', value: 4500 },
      { name: 'Тобольский район', value: 3200 },
      { name: 'Ишимский район', value: 2100 },
      { name: 'Голышмановский район', value: 1800 },
      { name: 'Ялуторовский район', value: 1500 },
      { name: 'г. Тюмень', value: 8500 },
      { name: 'г. Тобольск', value: 2800 },
      { name: 'г. Ишим', value: 1200 }
    ];
  }
  
  return mapData;
};

const initChart = async () => {
  if (!chart.value) return;
  
  myChart = echarts.init(chart.value);
  const mapData = await fetchMapData();
  
  const option = {
    title: {
      text: 'Тюменская область',
      subtext: 'Инвестиции по районам',
      left: 'center',
      top: 5,
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#333'
      },
      subtextStyle: {
        fontSize: 12,
        color: '#666'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const value = params.value || 0;
        return `<strong>${params.name}</strong><br/>Инвестиции: ${(value / 1000).toFixed(1)} млн ₽`;
      }
    },
    visualMap: {
      min: 0,
      max: 10000,
      text: ['Высокие', 'Низкие'],
      realtime: false,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 10,
      itemWidth: 15,
      itemHeight: 80,
      inRange: {
        color: ['#ffebee', '#f44336', '#b71c1c'] // Оттенки красного для низких -> высоких
      }
    },
    series: [
      {
        name: 'Инвестиции',
        type: 'map',
        map: 'TYUMEN',
        roam: true,
        zoom: 1.1,
        label: {
          show: false
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 10
          },
          itemStyle: {
            areaColor: '#4CAF50' // Зеленый при наведении
          }
        },
        itemStyle: {
          borderColor: '#fff',
          borderWidth: 1
        },
        data: mapData
      }
    ]
  };

  myChart.setOption(option);
  window.addEventListener('resize', resizeChart);
};

onMounted(() => {
  initChart();
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeChart);
  if (myChart) myChart.dispose();
});

const resizeChart = () => {
  if (myChart) myChart.resize();
};

// Перезагрузка при изменении года
watch(() => props.year, async () => {
  if (myChart) {
    const mapData = await fetchMapData();
    myChart.setOption({
      series: [{ data: mapData }]
    });
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
  min-height: 350px;
}
</style>
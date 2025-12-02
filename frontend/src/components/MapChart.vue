<template>
  <div class="map-container">
    <div ref="chart" class="map-chart"></div>
    
    <!-- Popup со статистикой района -->
    <v-dialog v-model="showDialog" max-width="500">
      <v-card v-if="selectedDistrict">
        <v-card-title class="bg-primary text-white">
          {{ selectedDistrict.name }}
        </v-card-title>
        <v-card-text class="pa-4">
          <v-row>
            <v-col cols="6">
              <div class="text-caption text-grey">Организаций</div>
              <div class="text-h5 font-weight-bold">{{ selectedDistrict.organizationCount }}</div>
            </v-col>
            <v-col cols="6">
              <div class="text-caption text-grey">Инвестиции (факт)</div>
              <div class="text-h5 font-weight-bold">{{ formatMoney(selectedDistrict.totalFact) }}</div>
            </v-col>
          </v-row>
          <v-divider class="my-3"></v-divider>
          <div class="text-subtitle-2 mb-2">По годам:</div>
          <v-list density="compact">
            <v-list-item v-for="item in selectedDistrict.byYear" :key="item.year">
              <template v-slot:prepend>
                <span class="font-weight-medium">{{ item.year }}:</span>
              </template>
              <span class="ml-2">{{ formatMoney(item.amount) }}</span>
            </v-list-item>
          </v-list>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showDialog = false">Закрыть</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';
import * as echarts from 'echarts';
import tyumenJson from '@/assets/tyumen_districts.json';
import api from '@/services/api';

const props = defineProps({
  data: { type: Array, default: () => [] }
});

const chart = ref(null);
let myChart = null;
const showDialog = ref(false);
const selectedDistrict = ref(null);

echarts.registerMap('TYUMEN', tyumenJson);

const formatMoney = (value) => {
  if (!value) return '0 ₽';
  if (value >= 1000000) {
    return (value / 1000000).toFixed(1) + ' млн ₽';
  }
  return value.toLocaleString('ru-RU') + ' ₽';
};

const loadDistrictStats = async (districtName) => {
  try {
    const response = await api.get(`/analytics/district/${encodeURIComponent(districtName)}`);
    selectedDistrict.value = response.data;
    showDialog.value = true;
  } catch (error) {
    console.error('Ошибка загрузки статистики района:', error);
  }
};

const initChart = () => {
  if (!chart.value) return;
  
  myChart = echarts.init(chart.value);
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const value = params.value || 0;
        return `<b>${params.name}</b><br/>Инвестиции: ${formatMoney(value)}<br/><span style="color:#888;font-size:11px">Нажмите для подробностей</span>`;
      }
    },
    visualMap: {
      min: 0,
      max: 5000,
      text: ['Макс', 'Мин'],
      realtime: false,
      calculable: true,
      orient: 'vertical',
      right: 10,
      bottom: 20,
      inRange: {
        color: ['#e3f2fd', '#1976D2']
      }
    },
    series: [{
      name: 'Инвестиции',
      type: 'map',
      map: 'TYUMEN',
      roam: true,
      zoom: 1.2,
      label: {
        show: false
      },
      emphasis: {
        label: { show: true, fontSize: 12 },
        itemStyle: { areaColor: '#FFC107' }
      },
      select: {
        label: { show: true },
        itemStyle: { areaColor: '#FF9800' }
      },
      itemStyle: {
        borderColor: '#fff',
        borderWidth: 1
      },
      data: props.data || []
    }]
  };

  myChart.setOption(option);
  
  // Обработчик клика по району
  myChart.on('click', (params) => {
    if (params.componentType === 'series') {
      loadDistrictStats(params.name);
    }
  });
  
  window.addEventListener('resize', resizeChart);
};

watch(() => props.data, (newData) => {
  if (myChart && newData) {
    myChart.setOption({
      series: [{ data: newData }]
    });
  }
}, { deep: true });

onMounted(() => {
  initChart();
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeChart);
  if (myChart) {
    myChart.off('click');
    myChart.dispose();
  }
});

const resizeChart = () => {
  if (myChart) myChart.resize();
};
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
  min-height: 450px;
}
</style>
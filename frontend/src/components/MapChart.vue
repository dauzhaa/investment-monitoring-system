<template>
  <div class="map-container">
    <div ref="chartRef" class="map-chart"></div>
    
    <!-- Диалог со статистикой района -->
    <v-dialog v-model="showDialog" max-width="550">
      <v-card v-if="selectedDistrict" :loading="loadingStats">
        <v-card-title class="bg-primary text-white d-flex align-center">
          <v-icon class="mr-2">mdi-map-marker</v-icon>
          {{ selectedDistrict.name }}
        </v-card-title>
        <v-card-text class="pa-4">
          <v-row class="mb-3">
            <v-col cols="6">
              <v-card variant="tonal" color="primary" class="pa-3 text-center">
                <div class="text-caption text-grey-darken-1">Организаций</div>
                <div class="text-h4 font-weight-bold">{{ selectedDistrict.organizationCount || 0 }}</div>
              </v-card>
            </v-col>
            <v-col cols="6">
              <v-card variant="tonal" color="success" class="pa-3 text-center">
                <div class="text-caption text-grey-darken-1">Инвестиции (факт)</div>
                <div class="text-h5 font-weight-bold">{{ formatMoney(selectedDistrict.totalFact) }}</div>
              </v-card>
            </v-col>
          </v-row>
          
          <v-card variant="outlined" class="pa-3 mb-3">
            <div class="text-caption text-grey mb-1">Прогноз</div>
            <div class="text-h6">{{ formatMoney(selectedDistrict.totalForecast) }}</div>
          </v-card>
          
          <div class="text-subtitle-2 mb-2 font-weight-medium">Динамика по годам:</div>
          <v-table density="compact" v-if="selectedDistrict.byYear && selectedDistrict.byYear.length">
            <thead>
              <tr>
                <th>Год</th>
                <th class="text-right">Инвестиции</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in selectedDistrict.byYear" :key="item.year">
                <td>{{ item.year }}</td>
                <td class="text-right font-weight-medium">{{ formatMoney(item.amount) }}</td>
              </tr>
            </tbody>
          </v-table>
          <div v-else class="text-grey text-center pa-4">Нет данных за предыдущие годы</div>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="showDialog = false">Закрыть</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import * as echarts from 'echarts';
import tyumenGeoJson from '@/assets/tyumen_districts.json';
import api from '@/services/api';

const props = defineProps({
  data: { type: Array, default: () => [] }
});

const chartRef = ref(null);
let myChart = null;

const showDialog = ref(false);
const selectedDistrict = ref(null);
const loadingStats = ref(false);

// Создаем карту соответствия NL_NAME_2 -> name для ECharts
const processGeoJson = () => {
  // Копируем GeoJSON и добавляем name из NL_NAME_2
  const processed = JSON.parse(JSON.stringify(tyumenGeoJson));
  processed.features.forEach(feature => {
    // Используем русское название для отображения
    if (feature.properties.NL_NAME_2) {
      feature.properties.name = feature.properties.NL_NAME_2;
    }
  });
  return processed;
};

const formatMoney = (value) => {
  if (!value || value === 0) return '0 ₽';
  if (value >= 1000000) {
    return (value / 1000000).toFixed(2) + ' млн ₽';
  }
  if (value >= 1000) {
    return (value / 1000).toFixed(1) + ' тыс ₽';
  }
  return value.toLocaleString('ru-RU') + ' ₽';
};

const loadDistrictStats = async (districtName) => {
  loadingStats.value = true;
  selectedDistrict.value = { name: districtName };
  showDialog.value = true;
  
  try {
    const response = await api.get(`/analytics/district/${encodeURIComponent(districtName)}`);
    selectedDistrict.value = response.data;
  } catch (error) {
    console.error('Ошибка загрузки статистики района:', error);
    selectedDistrict.value = {
      name: districtName,
      organizationCount: 0,
      totalFact: 0,
      totalForecast: 0,
      byYear: []
    };
  } finally {
    loadingStats.value = false;
  }
};

const initChart = () => {
  if (!chartRef.value) return;
  
  // Регистрируем карту с обработанным GeoJSON
  const processedGeoJson = processGeoJson();
  echarts.registerMap('TYUMEN', processedGeoJson);
  
  myChart = echarts.init(chartRef.value);
  
  // Подготавливаем данные - сопоставляем с русскими названиями районов
  const mapData = (props.data || []).map(item => ({
    name: item.name,
    value: item.value || 0
  }));

  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#ccc',
      borderWidth: 1,
      textStyle: { color: '#333' },
      formatter: (params) => {
        const value = params.value || 0;
        return `<div style="padding: 5px;">
          <b style="font-size: 14px;">${params.name}</b><br/>
          <span style="color: #1976D2;">Инвестиции: ${formatMoney(value)}</span><br/>
          <span style="color: #888; font-size: 11px;">Нажмите для подробностей</span>
        </div>`;
      }
    },
    visualMap: {
      min: 0,
      max: 5000000,
      text: ['Макс', 'Мин'],
      realtime: false,
      calculable: false,
      orient: 'vertical',
      right: 10,
      bottom: 50,
      itemWidth: 15,
      itemHeight: 100,
      textStyle: { fontSize: 11 },
      inRange: {
        color: ['#E3F2FD', '#90CAF9', '#42A5F5', '#1E88E5', '#1565C0', '#0D47A1']
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
          areaColor: '#FFC107',
          borderColor: '#FF9800',
          borderWidth: 2
        }
      },
      select: {
        label: { show: true },
        itemStyle: {
          areaColor: '#FF9800'
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
  
  // Обработчик клика по району
  myChart.on('click', (params) => {
    if (params.componentType === 'series' && params.name) {
      loadDistrictStats(params.name);
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
    
    myChart.setOption({
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
  min-height: 450px;
}
</style>
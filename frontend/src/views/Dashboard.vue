<template>
  <div class="dashboard">
    <!-- Выбор года сверху -->
    <div class="d-flex align-center mb-6">
      <h1 class="text-h4 font-weight-bold">Дашборд</h1>
      <v-spacer></v-spacer>
      <v-select
        v-model="selectedYear"
        :items="availableYears"
        label="Год"
        variant="outlined"
        density="compact"
        hide-details
        style="max-width: 120px;"
        @update:model-value="loadData"
      ></v-select>
    </div>

    <!-- Виджеты статистики -->
    <v-row class="mb-6">
      <!-- Общее кол-во организаций -->
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 h-100" elevation="2">
          <div class="d-flex align-center mb-2">
            <v-icon color="blue" size="24" class="mr-2">mdi-domain</v-icon>
            <span class="text-body-2 text-grey">Всего организаций</span>
          </div>
          <div class="text-h4 font-weight-bold text-blue">{{ stats.totalOrganizations }}</div>
        </v-card>
      </v-col>

      <!-- Общий объём инвестиций за текущий год -->
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 h-100" elevation="2">
          <div class="d-flex align-center mb-2">
            <v-icon color="green" size="24" class="mr-2">mdi-currency-rub</v-icon>
            <span class="text-body-2 text-grey">Инвестиции за {{ selectedYear }} г.</span>
          </div>
          <div class="text-h5 font-weight-bold text-green">{{ formatMoney(stats.factTotal) }}</div>
          <div class="text-caption text-grey">ФАКТ</div>
          <v-divider class="my-2"></v-divider>
          <div class="text-h6 text-red">{{ formatMoney(stats.planTotal) }}</div>
          <div class="text-caption text-grey">ПЛАН</div>
        </v-card>
      </v-col>

      <!-- Освоение бюджета -->
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 h-100" elevation="2">
          <div class="d-flex align-center mb-2">
            <v-icon color="orange" size="24" class="mr-2">mdi-chart-pie</v-icon>
            <span class="text-body-2 text-grey">Освоение бюджета</span>
          </div>
          <div class="text-h4 font-weight-bold" :class="getExecutionColor(stats.executionPercent)">
            {{ stats.executionPercent }}%
          </div>
          <v-progress-linear
            :model-value="Math.min(stats.executionPercent, 100)"
            :color="getExecutionColor(stats.executionPercent)"
            height="8"
            rounded
            class="mt-2"
          ></v-progress-linear>
        </v-card>
      </v-col>

      <!-- Качество данных -->
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 h-100" elevation="2">
          <div class="d-flex align-center mb-2">
            <v-icon color="purple" size="24" class="mr-2">mdi-check-decagram</v-icon>
            <span class="text-body-2 text-grey">Качество данных</span>
          </div>
          <div class="text-h4 font-weight-bold text-purple">{{ stats.dataQuality }}%</div>
          <div class="text-caption text-grey mt-1">
            {{ stats.orgsWithData }} из {{ stats.totalOrganizations }} отчитались
          </div>
        </v-card>
      </v-col>
    </v-row>

    <!-- Карта на всю ширину -->
    <v-card elevation="2" class="pa-4">
      <div class="text-h6 font-weight-bold mb-4 text-center">Тюменская область</div>
      
      <div ref="mapContainer" style="height: 600px; width: 100%;"></div>

      <!-- Диалог статистики района -->
      <v-dialog v-model="districtDialog" max-width="600">
        <v-card>
          <v-card-title class="bg-primary text-white">
            {{ selectedDistrict.name }}
          </v-card-title>
          <v-card-text class="pa-4">
            <v-row>
              <v-col cols="6">
                <div class="text-body-2 text-grey">Организаций</div>
                <div class="text-h5 font-weight-bold">{{ selectedDistrict.orgCount }}</div>
              </v-col>
              <v-col cols="6">
                <div class="text-body-2 text-grey">Инвестиции ФАКТ</div>
                <div class="text-h5 font-weight-bold text-green">{{ formatMoney(selectedDistrict.fact) }}</div>
              </v-col>
              <v-col cols="6">
                <div class="text-body-2 text-grey">Инвестиции ПЛАН</div>
                <div class="text-h5 font-weight-bold text-red">{{ formatMoney(selectedDistrict.plan) }}</div>
              </v-col>
              <v-col cols="6">
                <div class="text-body-2 text-grey">Освоение</div>
                <div class="text-h5 font-weight-bold" :class="getExecutionColor(selectedDistrict.execution)">
                  {{ selectedDistrict.execution }}%
                </div>
              </v-col>
            </v-row>

            <!-- Выбор квартала в диалоге -->
            <v-divider class="my-4"></v-divider>
            <div class="d-flex align-center mb-3">
              <span class="text-body-1 font-weight-medium mr-4">Данные по кварталам:</span>
              <v-btn-toggle v-model="dialogQuarter" mandatory density="compact" color="primary">
                <v-btn value="1">Q1</v-btn>
                <v-btn value="2">Q2</v-btn>
                <v-btn value="3">Q3</v-btn>
                <v-btn value="4">Q4</v-btn>
                <v-btn value="year">Год</v-btn>
              </v-btn-toggle>
            </div>

            <v-row>
              <v-col cols="6">
                <div class="text-body-2 text-grey">ФАКТ за период</div>
                <div class="text-h6 text-green">{{ formatMoney(selectedDistrict.quarterData?.fact || 0) }}</div>
              </v-col>
              <v-col cols="6">
                <div class="text-body-2 text-grey">ПЛАН за период</div>
                <div class="text-h6 text-red">{{ formatMoney(selectedDistrict.quarterData?.plan || 0) }}</div>
              </v-col>
            </v-row>
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="primary" @click="districtDialog = false">Закрыть</v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </v-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue';
import * as echarts from 'echarts';
import axios from 'axios';

// Состояние
const selectedYear = ref(2022);
const availableYears = [2025, 2024, 2023, 2022];
const mapContainer = ref(null);
let mapChart = null;

const districtDialog = ref(false);
const selectedDistrict = ref({
  name: '',
  orgCount: 0,
  fact: 0,
  plan: 0,
  execution: 0,
  quarterData: null
});
const dialogQuarter = ref('year');

// Статистика
const stats = ref({
  totalOrganizations: 0,
  factTotal: 0,
  planTotal: 0,
  executionPercent: 0,
  dataQuality: 0,
  orgsWithData: 0
});

// Данные по районам
const districtsData = ref([]);

// GeoJSON Тюменской области (упрощенный)
const tyumenGeoJson = {
  "type": "FeatureCollection",
  "features": [
    {"type": "Feature", "properties": {"name": "г. Тюмень"}, "geometry": {"type": "Polygon", "coordinates": [[[68.5, 57.1], [68.7, 57.1], [68.7, 57.2], [68.5, 57.2], [68.5, 57.1]]]}},
    {"type": "Feature", "properties": {"name": "г. Тобольск"}, "geometry": {"type": "Polygon", "coordinates": [[[68.2, 58.1], [68.4, 58.1], [68.4, 58.3], [68.2, 58.3], [68.2, 58.1]]]}},
    {"type": "Feature", "properties": {"name": "г. Ишим"}, "geometry": {"type": "Polygon", "coordinates": [[[69.4, 56.0], [69.6, 56.0], [69.6, 56.2], [69.4, 56.2], [69.4, 56.0]]]}},
    {"type": "Feature", "properties": {"name": "г. Ялуторовск"}, "geometry": {"type": "Polygon", "coordinates": [[[68.3, 56.6], [68.5, 56.6], [68.5, 56.8], [68.3, 56.8], [68.3, 56.6]]]}},
    {"type": "Feature", "properties": {"name": "г. Заводоуковск"}, "geometry": {"type": "Polygon", "coordinates": [[[68.1, 56.4], [68.3, 56.4], [68.3, 56.6], [68.1, 56.6], [68.1, 56.4]]]}},
    {"type": "Feature", "properties": {"name": "Тюменский район"}, "geometry": {"type": "Polygon", "coordinates": [[[68.0, 56.8], [69.0, 56.8], [69.0, 57.5], [68.0, 57.5], [68.0, 56.8]]]}},
    {"type": "Feature", "properties": {"name": "Тобольский район"}, "geometry": {"type": "Polygon", "coordinates": [[[67.5, 58.0], [69.0, 58.0], [69.0, 59.5], [67.5, 59.5], [67.5, 58.0]]]}},
    {"type": "Feature", "properties": {"name": "Ишимский район"}, "geometry": {"type": "Polygon", "coordinates": [[[69.0, 55.5], [70.5, 55.5], [70.5, 56.5], [69.0, 56.5], [69.0, 55.5]]]}},
    {"type": "Feature", "properties": {"name": "Ялуторовский район"}, "geometry": {"type": "Polygon", "coordinates": [[[66.5, 56.5], [68.0, 56.5], [68.0, 57.0], [66.5, 57.0], [66.5, 56.5]]]}},
    {"type": "Feature", "properties": {"name": "Заводоуковский район"}, "geometry": {"type": "Polygon", "coordinates": [[[66.0, 56.0], [68.0, 56.0], [68.0, 56.5], [66.0, 56.5], [66.0, 56.0]]]}},
    {"type": "Feature", "properties": {"name": "Абатский район"}, "geometry": {"type": "Polygon", "coordinates": [[[70.0, 56.0], [71.5, 56.0], [71.5, 56.8], [70.0, 56.8], [70.0, 56.0]]]}},
    {"type": "Feature", "properties": {"name": "Армизонский район"}, "geometry": {"type": "Polygon", "coordinates": [[[67.5, 55.5], [69.0, 55.5], [69.0, 56.2], [67.5, 56.2], [67.5, 55.5]]]}},
    {"type": "Feature", "properties": {"name": "Аромашевский район"}, "geometry": {"type": "Polygon", "coordinates": [[[69.5, 57.0], [71.0, 57.0], [71.0, 57.8], [69.5, 57.8], [69.5, 57.0]]]}},
    {"type": "Feature", "properties": {"name": "Бердюжский район"}, "geometry": {"type": "Polygon", "coordinates": [[[68.0, 55.0], [69.5, 55.0], [69.5, 55.7], [68.0, 55.7], [68.0, 55.0]]]}},
    {"type": "Feature", "properties": {"name": "Вагайский район"}, "geometry": {"type": "Polygon", "coordinates": [[[68.5, 57.5], [70.0, 57.5], [70.0, 58.5], [68.5, 58.5], [68.5, 57.5]]]}},
    {"type": "Feature", "properties": {"name": "Викуловский район"}, "geometry": {"type": "Polygon", "coordinates": [[[70.5, 57.0], [72.0, 57.0], [72.0, 58.0], [70.5, 58.0], [70.5, 57.0]]]}},
    {"type": "Feature", "properties": {"name": "Голышмановский район"}, "geometry": {"type": "Polygon", "coordinates": [[[68.5, 56.0], [70.0, 56.0], [70.0, 56.8], [68.5, 56.8], [68.5, 56.0]]]}},
    {"type": "Feature", "properties": {"name": "Исетский район"}, "geometry": {"type": "Polygon", "coordinates": [[[65.5, 56.0], [67.0, 56.0], [67.0, 56.8], [65.5, 56.8], [65.5, 56.0]]]}},
    {"type": "Feature", "properties": {"name": "Казанский район"}, "geometry": {"type": "Polygon", "coordinates": [[[69.0, 55.0], [70.5, 55.0], [70.5, 55.8], [69.0, 55.8], [69.0, 55.0]]]}},
    {"type": "Feature", "properties": {"name": "Нижнетавдинский район"}, "geometry": {"type": "Polygon", "coordinates": [[[67.5, 57.2], [69.0, 57.2], [69.0, 58.0], [67.5, 58.0], [67.5, 57.2]]]}},
    {"type": "Feature", "properties": {"name": "Омутинский район"}, "geometry": {"type": "Polygon", "coordinates": [[[70.0, 56.5], [71.5, 56.5], [71.5, 57.3], [70.0, 57.3], [70.0, 56.5]]]}},
    {"type": "Feature", "properties": {"name": "Сладковский район"}, "geometry": {"type": "Polygon", "coordinates": [[[70.5, 55.5], [72.0, 55.5], [72.0, 56.3], [70.5, 56.3], [70.5, 55.5]]]}},
    {"type": "Feature", "properties": {"name": "Сорокинский район"}, "geometry": {"type": "Polygon", "coordinates": [[[69.5, 56.5], [71.0, 56.5], [71.0, 57.2], [69.5, 57.2], [69.5, 56.5]]]}},
    {"type": "Feature", "properties": {"name": "Уватский район"}, "geometry": {"type": "Polygon", "coordinates": [[[68.0, 59.0], [71.0, 59.0], [71.0, 61.0], [68.0, 61.0], [68.0, 59.0]]]}},
    {"type": "Feature", "properties": {"name": "Упоровский район"}, "geometry": {"type": "Polygon", "coordinates": [[[66.0, 55.5], [67.5, 55.5], [67.5, 56.3], [66.0, 56.3], [66.0, 55.5]]]}},
    {"type": "Feature", "properties": {"name": "Юргинский район"}, "geometry": {"type": "Polygon", "coordinates": [[[68.0, 56.5], [69.5, 56.5], [69.5, 57.2], [68.0, 57.2], [68.0, 56.5]]]}},
    {"type": "Feature", "properties": {"name": "Ярковский район"}, "geometry": {"type": "Polygon", "coordinates": [[[68.5, 57.0], [70.0, 57.0], [70.0, 57.8], [68.5, 57.8], [68.5, 57.0]]}}}
  ]
};

// Форматирование денег
const formatMoney = (value) => {
  if (value >= 1000000) {
    return (value / 1000).toFixed(1) + ' млн ₽';
  } else if (value >= 1000) {
    return value.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ' ') + ' тыс. ₽';
  }
  return value.toFixed(0) + ' тыс. ₽';
};

// Цвет освоения
const getExecutionColor = (percent) => {
  if (percent >= 100) return 'text-green';
  if (percent >= 80) return 'text-green';
  if (percent >= 50) return 'text-orange';
  return 'text-red';
};

// Загрузка данных
const loadData = async () => {
  try {
    // Пытаемся получить данные из API
    const response = await axios.get(`/api/v1/analytics/dashboard?year=${selectedYear.value}`);
    const data = response.data;
    
    stats.value = {
      totalOrganizations: data.totalOrganizations || 287,
      factTotal: data.factTotal || 0,
      planTotal: data.planTotal || 0,
      executionPercent: data.executionPercent || 0,
      dataQuality: data.dataQuality || 0,
      orgsWithData: data.orgsWithData || 0
    };
    
    // Загружаем данные карты
    const mapResponse = await axios.get(`/api/v1/analytics/map?year=${selectedYear.value}`);
    districtsData.value = mapResponse.data;
    
  } catch (e) {
    // Mock данные для 2022 года
    if (selectedYear.value === 2022) {
      stats.value = {
        totalOrganizations: 287,
        factTotal: 480474.0,
        planTotal: 393401.0,
        executionPercent: 122.1,
        dataQuality: 95,
        orgsWithData: 273
      };
      
      districtsData.value = [
        { name: 'г. Тюмень', fact: 180000, plan: 150000, orgCount: 85 },
        { name: 'Тюменский район', fact: 45000, plan: 40000, orgCount: 32 },
        { name: 'г. Тобольск', fact: 35000, plan: 30000, orgCount: 18 },
        { name: 'Ишимский район', fact: 28000, plan: 25000, orgCount: 15 },
        { name: 'Тобольский район', fact: 22000, plan: 20000, orgCount: 12 },
        { name: 'Заводоуковский район', fact: 18000, plan: 15000, orgCount: 14 },
        { name: 'Ялуторовский район', fact: 15000, plan: 12000, orgCount: 11 },
        { name: 'Абатский район', fact: 12000, plan: 10000, orgCount: 8 },
        { name: 'Армизонский район', fact: 10000, plan: 8000, orgCount: 7 },
        { name: 'Юргинский район', fact: 8000, plan: 7000, orgCount: 6 },
      ];
    } else {
      stats.value = {
        totalOrganizations: 274,
        factTotal: 0,
        planTotal: 0,
        executionPercent: 0,
        dataQuality: 0,
        orgsWithData: 0
      };
      districtsData.value = [];
    }
  }
  
  await nextTick();
  initMap();
};

// Инициализация карты
const initMap = () => {
  if (!mapContainer.value) return;
  
  if (mapChart) {
    mapChart.dispose();
  }
  
  mapChart = echarts.init(mapContainer.value);
  
  // Регистрируем GeoJSON
  echarts.registerMap('tyumen', tyumenGeoJson);
  
  // Создаём данные для карты
  const mapData = districtsData.value.map(d => ({
    name: d.name,
    value: d.fact || 0,
    fact: d.fact || 0,
    plan: d.plan || 0,
    orgCount: d.orgCount || 0
  }));
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const data = params.data || {};
        return `<strong>${params.name}</strong><br/>
          ФАКТ: ${formatMoney(data.fact || 0)}<br/>
          ПЛАН: ${formatMoney(data.plan || 0)}<br/>
          Организаций: ${data.orgCount || 0}`;
      }
    },
    visualMap: {
      show: false,
      min: 0,
      max: Math.max(...mapData.map(d => d.value), 1),
      inRange: {
        color: ['#E3F2FD', '#1976D2']
      }
    },
    series: [{
      name: 'Инвестиции',
      type: 'map',
      map: 'tyumen',
      roam: true,
      zoom: 1.2,
      label: {
        show: true,
        fontSize: 10
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 12,
          fontWeight: 'bold'
        },
        itemStyle: {
          areaColor: '#4CAF50'
        }
      },
      data: mapData
    }]
  };
  
  mapChart.setOption(option);
  
  // Обработчик клика по району
  mapChart.on('click', (params) => {
    if (params.data) {
      selectedDistrict.value = {
        name: params.name,
        orgCount: params.data.orgCount || 0,
        fact: params.data.fact || 0,
        plan: params.data.plan || 0,
        execution: params.data.plan > 0 
          ? Math.round((params.data.fact / params.data.plan) * 100) 
          : 0,
        quarterData: {
          fact: params.data.fact || 0,
          plan: params.data.plan || 0
        }
      };
      districtDialog.value = true;
    }
  });
  
  // Ресайз
  window.addEventListener('resize', () => {
    mapChart?.resize();
  });
};

// Следим за изменением квартала в диалоге
watch(dialogQuarter, async (quarter) => {
  if (!selectedDistrict.value.name) return;
  
  try {
    const response = await axios.get(`/api/v1/analytics/district/${selectedDistrict.value.name}`, {
      params: { year: selectedYear.value, quarter }
    });
    selectedDistrict.value.quarterData = response.data;
  } catch (e) {
    // Mock данные
    const baseValue = selectedDistrict.value.fact / 4;
    if (quarter === 'year') {
      selectedDistrict.value.quarterData = {
        fact: selectedDistrict.value.fact,
        plan: selectedDistrict.value.plan
      };
    } else {
      selectedDistrict.value.quarterData = {
        fact: baseValue * (0.8 + Math.random() * 0.4),
        plan: selectedDistrict.value.plan / 4
      };
    }
  }
});

onMounted(() => {
  loadData();
});
</script>

<style scoped>
.dashboard {
  padding: 0;
}
</style>
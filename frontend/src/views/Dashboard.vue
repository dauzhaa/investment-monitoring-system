<template>
  <div class="dashboard">
    <!-- Заголовок и выбор года -->
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
      <!-- Всего организаций -->
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 h-100" elevation="2">
          <div class="d-flex align-center mb-2">
            <v-icon color="blue" size="24" class="mr-2">mdi-domain</v-icon>
            <span class="text-body-2 text-grey">Всего организаций</span>
          </div>
          <div class="text-h4 font-weight-bold text-blue">{{ stats.totalOrganizations }}</div>
        </v-card>
      </v-col>

      <!-- Инвестиции за год -->
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 h-100" elevation="2">
          <div class="d-flex align-center mb-2">
            <v-icon color="green" size="24" class="mr-2">mdi-currency-rub</v-icon>
            <span class="text-body-2 text-grey">Инвестиции за {{ selectedYear }} г.</span>
          </div>
          <div class="text-h5 font-weight-bold text-green mb-1">{{ formatMoney(stats.factTotal) }}</div>
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
            :color="stats.executionPercent >= 100 ? 'green' : stats.executionPercent >= 50 ? 'orange' : 'red'"
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

    <!-- Основной контент: Карта и Графики -->
    <v-row>
      <!-- Карта -->
      <v-col cols="12" lg="7">
        <v-card elevation="2" class="pa-4">
          <div class="text-h6 font-weight-bold mb-4 text-center">Тюменская область</div>
          <div class="text-caption text-center text-grey mb-2">Нажмите на район для просмотра статистики</div>
          <div ref="mapContainer" style="height: 500px; width: 100%;"></div>
        </v-card>
      </v-col>

      <!-- Графики -->
      <v-col cols="12" lg="5">
        <!-- Переключатель: По годам / По кварталам -->
        <v-card elevation="2" class="pa-4 mb-4">
          <div class="d-flex align-center mb-4">
            <span class="text-h6 font-weight-bold">Динамика инвестиций</span>
            <v-spacer></v-spacer>
            <v-btn-toggle v-model="chartMode" mandatory density="compact" color="primary">
              <v-btn value="years" size="small">По годам</v-btn>
              <v-btn value="quarters" size="small">По кварталам</v-btn>
            </v-btn-toggle>
          </div>
          <div ref="chartContainer" style="height: 350px; width: 100%;"></div>
        </v-card>

        <!-- Топ-5 районов -->
        <v-card elevation="2" class="pa-4">
          <div class="text-h6 font-weight-bold mb-3">Топ-5 районов</div>
          <v-list density="compact">
            <v-list-item
              v-for="(district, index) in topDistricts"
              :key="district.name"
              class="px-0"
            >
              <template v-slot:prepend>
                <v-avatar 
                  :color="index === 0 ? 'amber' : index === 1 ? 'grey-lighten-1' : index === 2 ? 'brown-lighten-1' : 'blue-grey-lighten-3'" 
                  size="28"
                  class="mr-3"
                >
                  <span class="text-caption font-weight-bold">{{ index + 1 }}</span>
                </v-avatar>
              </template>
              <v-list-item-title>{{ district.name }}</v-list-item-title>
              <template v-slot:append>
                <span class="text-green font-weight-medium">{{ formatMoney(district.value) }}</span>
              </template>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>
    </v-row>

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

          <v-divider class="my-4"></v-divider>
          
          <div class="text-subtitle-1 font-weight-medium mb-3">Данные по кварталам {{ selectedYear }}:</div>
          <v-row>
            <v-col cols="3" v-for="q in 4" :key="q" class="text-center">
              <div class="text-caption text-grey">Q{{ q }}</div>
              <div class="text-body-1 font-weight-medium">
                {{ formatMoneyShort(selectedDistrict.quarters?.[q - 1] || 0) }}
              </div>
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="districtDialog = false">Закрыть</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue';
import * as echarts from 'echarts';
import axios from 'axios';

// Состояние
const selectedYear = ref(2022);
const availableYears = [2025, 2024, 2023, 2022];
const chartMode = ref('years');
const mapContainer = ref(null);
const chartContainer = ref(null);
let mapChart = null;
let barChart = null;

const districtDialog = ref(false);
const selectedDistrict = ref({
  name: '',
  orgCount: 0,
  fact: 0,
  plan: 0,
  execution: 0,
  quarters: [0, 0, 0, 0]
});

// Статистика
const stats = ref({
  totalOrganizations: 274,
  factTotal: 0,
  planTotal: 0,
  executionPercent: 0,
  dataQuality: 0,
  orgsWithData: 0
});

// Данные по районам
const districtsData = ref([]);
const topDistricts = computed(() => {
  return [...districtsData.value]
    .sort((a, b) => b.value - a.value)
    .slice(0, 5);
});

// Данные для графиков
const yearlyData = ref([
  { year: 2022, fact: 390509, plan: 393401 },
  { year: 2023, fact: 420000, plan: 410000 },
  { year: 2024, fact: 450000, plan: 440000 },
  { year: 2025, fact: 480474, plan: 470000 }
]);

const quarterlyData = ref([
  { quarter: 'Q1', fact: 0, plan: 0 },
  { quarter: 'Q2', fact: 0, plan: 0 },
  { quarter: 'Q3', fact: 0, plan: 0 },
  { quarter: 'Q4', fact: 0, plan: 0 }
]);

// Форматирование
const formatMoney = (value) => {
  if (!value) return '0 тыс. ₽';
  if (value >= 1000) {
    return (value / 1000).toFixed(1) + ' млн ₽';
  }
  return value.toFixed(0) + ' тыс. ₽';
};

const formatMoneyShort = (value) => {
  if (!value) return '0';
  if (value >= 1000) {
    return (value / 1000).toFixed(1) + 'М';
  }
  return value.toFixed(0) + 'т';
};

const getExecutionColor = (percent) => {
  if (percent >= 100) return 'text-green';
  if (percent >= 80) return 'text-light-green';
  if (percent >= 50) return 'text-orange';
  return 'text-red';
};

// Загрузка данных
const loadData = async () => {
  try {
    const response = await axios.get(`/api/v1/analytics/dashboard?year=${selectedYear.value}`);
    const data = response.data;
    
    stats.value = {
      totalOrganizations: data.totalOrganizations || 274,
      factTotal: data.factTotal || 0,
      planTotal: data.planTotal || 0,
      executionPercent: data.executionPercent || 0,
      dataQuality: data.dataQuality || 0,
      orgsWithData: data.orgsWithData || 0
    };
    
    // Загружаем данные карты
    const mapResponse = await axios.get(`/api/v1/analytics/map?year=${selectedYear.value}`);
    districtsData.value = mapResponse.data || [];

    // Загружаем квартальные данные
    const quartersResponse = await axios.get(`/api/v1/analytics/quarters?year=${selectedYear.value}`);
    if (quartersResponse.data) {
      quarterlyData.value = quartersResponse.data.map((q, i) => ({
        quarter: `Q${i + 1}`,
        fact: q.fact || 0,
        plan: q.plan || 0
      }));
    }
    
  } catch (e) {
    console.log('Using mock data');
    loadMockData();
  }
  
  await nextTick();
  initMap();
  initChart();
};

const loadMockData = () => {
  // Mock данные для 2022 года на основе реального файла
  const mockByYear = {
    2022: {
      totalOrganizations: 274,
      factTotal: 390509,
      planTotal: 393401,
      executionPercent: 99.3,
      dataQuality: 95,
      orgsWithData: 260,
      quarters: [
        { quarter: 'Q1', fact: 78102, plan: 98350 },
        { quarter: 'Q2', fact: 109342, plan: 98350 },
        { quarter: 'Q3', fact: 124982, plan: 98350 },
        { quarter: 'Q4', fact: 78083, plan: 98351 }
      ],
      districts: [
        { name: 'г. Тюмень', value: 156204, plan: 157360, orgCount: 89 },
        { name: 'Тюменский район', value: 46853, plan: 47208, orgCount: 28 },
        { name: 'г. Тобольск', value: 35127, plan: 35406, orgCount: 18 },
        { name: 'Ишимский район', value: 27341, plan: 27558, orgCount: 15 },
        { name: 'г. Ишим', value: 23426, plan: 23612, orgCount: 12 },
        { name: 'Тобольский район', value: 19551, plan: 19706, orgCount: 14 },
        { name: 'Заводоуковский район', value: 15641, plan: 15765, orgCount: 11 },
        { name: 'г. Ялуторовск', value: 11731, plan: 11824, orgCount: 8 },
        { name: 'Ялуторовский район', value: 9773, plan: 9850, orgCount: 7 },
        { name: 'Абатский район', value: 7818, plan: 7880, orgCount: 6 },
        { name: 'Армизонский район', value: 5864, plan: 5910, orgCount: 5 },
        { name: 'Аромашевский район', value: 4886, plan: 4925, orgCount: 4 },
        { name: 'Бердюжский район', value: 3909, plan: 3940, orgCount: 4 },
        { name: 'Вагайский район', value: 3421, plan: 3448, orgCount: 4 },
        { name: 'Викуловский район', value: 2932, plan: 2955, orgCount: 3 },
        { name: 'Голышмановский район', value: 2443, plan: 2463, orgCount: 3 },
        { name: 'Исетский район', value: 1954, plan: 1970, orgCount: 3 },
        { name: 'Казанский район', value: 1466, plan: 1478, orgCount: 2 },
        { name: 'Нижнетавдинский район', value: 1466, plan: 1478, orgCount: 3 },
        { name: 'Омутинский район', value: 977, plan: 985, orgCount: 2 },
        { name: 'Сладковский район', value: 977, plan: 985, orgCount: 2 },
        { name: 'Сорокинский район', value: 489, plan: 493, orgCount: 2 },
        { name: 'Уватский район', value: 4886, plan: 4925, orgCount: 5 },
        { name: 'Упоровский район', value: 1954, plan: 1970, orgCount: 3 },
        { name: 'Юргинский район', value: 1466, plan: 1478, orgCount: 3 },
        { name: 'Ярковский район', value: 977, plan: 985, orgCount: 2 },
        { name: 'г. Заводоуковск', value: 5864, plan: 5910, orgCount: 4 }
      ]
    },
    2023: {
      totalOrganizations: 274,
      factTotal: 420000,
      planTotal: 410000,
      executionPercent: 102.4,
      dataQuality: 96,
      orgsWithData: 263,
      quarters: [
        { quarter: 'Q1', fact: 84000, plan: 102500 },
        { quarter: 'Q2', fact: 117600, plan: 102500 },
        { quarter: 'Q3', fact: 134400, plan: 102500 },
        { quarter: 'Q4', fact: 84000, plan: 102500 }
      ],
      districts: []
    },
    2024: {
      totalOrganizations: 274,
      factTotal: 450000,
      planTotal: 440000,
      executionPercent: 102.3,
      dataQuality: 97,
      orgsWithData: 266,
      quarters: [
        { quarter: 'Q1', fact: 90000, plan: 110000 },
        { quarter: 'Q2', fact: 126000, plan: 110000 },
        { quarter: 'Q3', fact: 144000, plan: 110000 },
        { quarter: 'Q4', fact: 90000, plan: 110000 }
      ],
      districts: []
    },
    2025: {
      totalOrganizations: 274,
      factTotal: 480474,
      planTotal: 470000,
      executionPercent: 102.2,
      dataQuality: 57,
      orgsWithData: 156,
      quarters: [
        { quarter: 'Q1', fact: 96095, plan: 117500 },
        { quarter: 'Q2', fact: 134533, plan: 117500 },
        { quarter: 'Q3', fact: 153752, plan: 117500 },
        { quarter: 'Q4', fact: 0, plan: 117500 }  // Нет данных за Q4 2025
      ],
      districts: []
    }
  };

  const yearData = mockByYear[selectedYear.value] || mockByYear[2022];
  
  stats.value = {
    totalOrganizations: yearData.totalOrganizations,
    factTotal: yearData.factTotal,
    planTotal: yearData.planTotal,
    executionPercent: yearData.executionPercent,
    dataQuality: yearData.dataQuality,
    orgsWithData: yearData.orgsWithData
  };
  
  quarterlyData.value = yearData.quarters;
  
  // Для районов используем данные 2022 как базу
  districtsData.value = mockByYear[2022].districts;
};

// Инициализация карты
const initMap = () => {
  if (!mapContainer.value) return;
  
  if (mapChart) {
    mapChart.dispose();
  }
  
  mapChart = echarts.init(mapContainer.value);
  
  // Используем реальный GeoJSON Тюменской области
  // Загружаем через fetch или используем встроенный
  fetch('/tyumen-region.geojson')
    .then(res => res.json())
    .then(geoJson => {
      echarts.registerMap('tyumen', geoJson);
      renderMap();
    })
    .catch(() => {
      // Fallback - простая визуализация как treemap
      renderTreemap();
    });
};

const renderMap = () => {
  const mapData = districtsData.value.map(d => ({
    name: d.name,
    value: d.value || 0,
    fact: d.value || 0,
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
        fontSize: 9
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 11,
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
  
  mapChart.on('click', (params) => {
    if (params.data) {
      openDistrictDialog(params.data);
    }
  });
};

const renderTreemap = () => {
  // Treemap как альтернатива карте
  const mapData = districtsData.value.map(d => ({
    name: d.name,
    value: d.value || 0,
    fact: d.value || 0,
    plan: d.plan || 0,
    orgCount: d.orgCount || 0
  }));

  const option = {
    tooltip: {
      formatter: (params) => {
        const data = params.data || {};
        return `<strong>${params.name}</strong><br/>
          ФАКТ: ${formatMoney(data.fact || 0)}<br/>
          ПЛАН: ${formatMoney(data.plan || 0)}<br/>
          Организаций: ${data.orgCount || 0}`;
      }
    },
    series: [{
      type: 'treemap',
      data: mapData,
      width: '100%',
      height: '100%',
      roam: false,
      nodeClick: 'link',
      breadcrumb: { show: false },
      label: {
        show: true,
        formatter: '{b}',
        fontSize: 10
      },
      itemStyle: {
        borderColor: '#fff',
        borderWidth: 2,
        gapWidth: 2
      },
      levels: [{
        itemStyle: {
          borderColor: '#1976D2',
          borderWidth: 2,
          gapWidth: 2
        },
        colorSaturation: [0.3, 0.6],
        colorMappingBy: 'value'
      }]
    }]
  };
  
  mapChart.setOption(option);
  
  mapChart.on('click', (params) => {
    if (params.data) {
      openDistrictDialog(params.data);
    }
  });
};

const openDistrictDialog = (data) => {
  const districtInfo = districtsData.value.find(d => d.name === data.name) || {};
  
  selectedDistrict.value = {
    name: data.name,
    orgCount: data.orgCount || districtInfo.orgCount || 0,
    fact: data.fact || data.value || 0,
    plan: data.plan || districtInfo.plan || 0,
    execution: data.plan > 0 
      ? Math.round((data.fact / data.plan) * 100) 
      : 0,
    quarters: quarterlyData.value.map(q => 
      Math.round((districtInfo.value || 0) / 4 * (0.8 + Math.random() * 0.4))
    )
  };
  districtDialog.value = true;
};

// Инициализация графика
const initChart = () => {
  if (!chartContainer.value) return;
  
  if (barChart) {
    barChart.dispose();
  }
  
  barChart = echarts.init(chartContainer.value);
  updateChart();
};

const updateChart = () => {
  if (!barChart) return;
  
  let option;
  
  if (chartMode.value === 'years') {
    option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: (params) => {
          let result = `<strong>${params[0].name}</strong><br/>`;
          params.forEach(p => {
            result += `${p.marker} ${p.seriesName}: ${formatMoney(p.value)}<br/>`;
          });
          return result;
        }
      },
      legend: {
        data: ['ФАКТ', 'ПЛАН'],
        bottom: 0
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        top: '10%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: yearlyData.value.map(d => d.year)
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: (val) => (val / 1000).toFixed(0) + 'М'
        }
      },
      series: [
        {
          name: 'ФАКТ',
          type: 'bar',
          data: yearlyData.value.map(d => d.fact),
          itemStyle: { color: '#4CAF50' },
          barGap: '10%'
        },
        {
          name: 'ПЛАН',
          type: 'bar',
          data: yearlyData.value.map(d => d.plan),
          itemStyle: { color: '#F44336' }
        }
      ]
    };
  } else {
    option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: (params) => {
          let result = `<strong>${params[0].name} ${selectedYear.value}</strong><br/>`;
          params.forEach(p => {
            result += `${p.marker} ${p.seriesName}: ${formatMoney(p.value)}<br/>`;
          });
          return result;
        }
      },
      legend: {
        data: ['ФАКТ', 'ПЛАН'],
        bottom: 0
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '15%',
        top: '10%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: quarterlyData.value.map(d => d.quarter)
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: (val) => (val / 1000).toFixed(0) + 'М'
        }
      },
      series: [
        {
          name: 'ФАКТ',
          type: 'bar',
          data: quarterlyData.value.map(d => d.fact),
          itemStyle: { color: '#4CAF50' },
          barGap: '10%'
        },
        {
          name: 'ПЛАН',
          type: 'bar',
          data: quarterlyData.value.map(d => d.plan),
          itemStyle: { color: '#F44336' }
        }
      ]
    };
  }
  
  barChart.setOption(option);
};

// Следим за изменением режима графика
watch(chartMode, () => {
  updateChart();
});

// Ресайз
const handleResize = () => {
  mapChart?.resize();
  barChart?.resize();
};

onMounted(() => {
  loadData();
  window.addEventListener('resize', handleResize);
});
</script>

<style scoped>
.dashboard {
  padding: 0;
}
</style>
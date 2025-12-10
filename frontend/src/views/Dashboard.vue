<template>
  <v-container fluid>
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
        @update:model-value="loadStats"
      ></v-select>
    </div>

    <!-- KPI Cards -->
    <v-row class="mb-4">
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 rounded-lg" elevation="2">
          <div class="d-flex align-center mb-2">
            <v-icon color="blue" size="24" class="mr-2">mdi-domain</v-icon>
            <span class="text-body-2 text-grey">Всего организаций</span>
          </div>
          <div class="text-h4 font-weight-bold text-blue">{{ stats.organizationCount }}</div>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 rounded-lg" elevation="2">
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

      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 rounded-lg" elevation="2">
          <div class="d-flex align-center mb-2">
            <v-icon color="orange" size="24" class="mr-2">mdi-chart-pie</v-icon>
            <span class="text-body-2 text-grey">Освоение бюджета</span>
          </div>
          <div class="text-h4 font-weight-bold" :class="getExecutionColor(stats.budgetExecution)">
            {{ stats.budgetExecution }}%
          </div>
          <v-progress-linear
            :model-value="Math.min(stats.budgetExecution, 100)"
            :color="stats.budgetExecution >= 100 ? 'green' : stats.budgetExecution >= 50 ? 'orange' : 'red'"
            height="8"
            rounded
            class="mt-2"
          ></v-progress-linear>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 rounded-lg" elevation="2">
          <div class="d-flex align-center mb-2">
            <v-icon color="purple" size="24" class="mr-2">mdi-check-decagram</v-icon>
            <span class="text-body-2 text-grey">Качество данных</span>
          </div>
          <div class="text-h4 font-weight-bold text-purple">{{ stats.dataQuality }}%</div>
          <div class="text-caption text-grey mt-1">
            {{ stats.orgsWithData }} из {{ stats.organizationCount }} отчитались
          </div>
        </v-card>
      </v-col>
    </v-row>

    <!-- Main Content -->
    <v-row>
      <!-- Столбчатая диаграмма -->
      <v-col cols="12" md="6">
        <v-card class="rounded-lg fill-height" elevation="2">
          <v-card-title class="d-flex align-center">
            <span>Динамика инвестиций</span>
            <v-spacer></v-spacer>
            <v-btn-toggle v-model="chartMode" mandatory density="compact" color="primary">
              <v-btn value="years" size="small">По годам</v-btn>
              <v-btn value="quarters" size="small">По кварталам</v-btn>
            </v-btn-toggle>
          </v-card-title>
          <v-card-text style="height: 400px;">
            <v-chart class="chart" :option="barChartOption" autoresize />
          </v-card-text>
          <v-card-actions class="px-4 pb-4">
            <v-chip size="small" color="green" variant="flat" class="mr-2">ФАКТ</v-chip>
            <v-chip size="small" color="red" variant="flat">ПЛАН</v-chip>
          </v-card-actions>
        </v-card>
      </v-col>

      <!-- Карта -->
      <v-col cols="12" md="6">
        <v-card class="rounded-lg fill-height" elevation="2">
          <v-card-title>Интерактивная карта области</v-card-title>
          <v-card-text style="height: 450px; padding: 8px;">
            <map-chart :data="mapData" @district-click="openDistrictDialog" />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Диалог статистики района -->
    <v-dialog v-model="districtDialog" max-width="600">
      <v-card>
        <v-card-title class="bg-primary text-white d-flex align-center">
          <v-icon class="mr-2">mdi-map-marker</v-icon>
          {{ selectedDistrict.name }}
        </v-card-title>
        <v-card-text class="pa-4">
          <v-row class="mb-3">
            <v-col cols="6">
              <v-card variant="tonal" color="primary" class="pa-3 text-center">
                <div class="text-caption text-grey-darken-1">Организаций</div>
                <div class="text-h4 font-weight-bold">{{ selectedDistrict.orgCount }}</div>
              </v-card>
            </v-col>
            <v-col cols="6">
              <v-card variant="tonal" color="success" class="pa-3 text-center">
                <div class="text-caption text-grey-darken-1">Инвестиции (факт)</div>
                <div class="text-h5 font-weight-bold">{{ formatMoney(selectedDistrict.fact) }}</div>
              </v-card>
            </v-col>
          </v-row>

          <v-row class="mb-3">
            <v-col cols="6">
              <v-card variant="outlined" class="pa-3">
                <div class="text-caption text-grey mb-1">План</div>
                <div class="text-h6 text-red">{{ formatMoney(selectedDistrict.plan) }}</div>
              </v-card>
            </v-col>
            <v-col cols="6">
              <v-card variant="outlined" class="pa-3">
                <div class="text-caption text-grey mb-1">Освоение</div>
                <div class="text-h6" :class="getExecutionColor(selectedDistrict.execution)">
                  {{ selectedDistrict.execution }}%
                </div>
              </v-card>
            </v-col>
          </v-row>

          <div class="text-subtitle-2 mb-2 font-weight-medium">Данные по кварталам {{ selectedYear }}:</div>
          <v-row>
            <v-col cols="3" v-for="q in 4" :key="q" class="text-center">
              <v-card variant="tonal" :color="q === 4 && selectedYear === 2025 ? 'grey' : 'blue-lighten-4'" class="pa-2">
                <div class="text-caption text-grey">Q{{ q }}</div>
                <div class="text-body-1 font-weight-medium">
                  {{ formatMoneyShort(selectedDistrict.quarters?.[q - 1] || 0) }}
                </div>
              </v-card>
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" variant="text" @click="districtDialog = false">Закрыть</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import VChart from 'vue-echarts';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { BarChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components';
import MapChart from '@/components/MapChart.vue';
import api from '@/services/api';

use([CanvasRenderer, BarChart, GridComponent, TooltipComponent, LegendComponent]);

// Состояние
const currentYear = new Date().getFullYear();
const selectedYear = ref(2022);
const availableYears = [2025, 2024, 2023, 2022];
const chartMode = ref('years');

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
  organizationCount: 274,
  factTotal: 0,
  planTotal: 0,
  budgetExecution: 0,
  dataQuality: 0,
  orgsWithData: 0
});

// Данные для карты
const mapData = ref([]);

// Данные для графиков
const yearlyData = ref([]);
const quarterlyData = ref([]);
const barChartOption = ref({});

// Mock данные по годам
const mockDataByYear = {
  2022: {
    organizationCount: 274,
    factTotal: 390509000,
    planTotal: 393401000,
    budgetExecution: 99.3,
    dataQuality: 95,
    orgsWithData: 260,
    quarters: [
      { quarter: 'Q1', fact: 78102000, plan: 98350000 },
      { quarter: 'Q2', fact: 109342000, plan: 98350000 },
      { quarter: 'Q3', fact: 124982000, plan: 98350000 },
      { quarter: 'Q4', fact: 78083000, plan: 98351000 }
    ],
    districts: [
      { name: 'Тюмень', value: 169154000, plan: 170000000, orgCount: 89 },
      { name: 'Тюменский район', value: 51465000, plan: 52000000, orgCount: 28 },
      { name: 'Ишим', value: 22902000, plan: 23000000, orgCount: 12 },
      { name: 'Тобольск', value: 19551000, plan: 20000000, orgCount: 18 },
      { name: 'Тобольский район', value: 15641000, plan: 16000000, orgCount: 14 },
      { name: 'Ишимский район', value: 14500000, plan: 15000000, orgCount: 15 },
      { name: 'Ялуторовск', value: 11731000, plan: 12000000, orgCount: 8 },
      { name: 'Ялуторовский район', value: 9773000, plan: 10000000, orgCount: 7 },
      { name: 'Заводоуковск', value: 8500000, plan: 9000000, orgCount: 6 },
      { name: 'Заводоуковский район', value: 7818000, plan: 8000000, orgCount: 6 },
      { name: 'Голышмановский район', value: 6500000, plan: 7000000, orgCount: 5 },
      { name: 'Исетский район', value: 5864000, plan: 6000000, orgCount: 5 },
      { name: 'Уватский район', value: 5500000, plan: 5800000, orgCount: 5 },
      { name: 'Нижнетавдинский район', value: 4886000, plan: 5000000, orgCount: 4 },
      { name: 'Упоровский район', value: 4500000, plan: 4700000, orgCount: 4 },
      { name: 'Армизонский район', value: 3909000, plan: 4000000, orgCount: 4 },
      { name: 'Аромашевский район', value: 3500000, plan: 3700000, orgCount: 4 },
      { name: 'Бердюжский район', value: 3421000, plan: 3500000, orgCount: 4 },
      { name: 'Вагайский район', value: 3200000, plan: 3400000, orgCount: 4 },
      { name: 'Викуловский район', value: 2932000, plan: 3000000, orgCount: 3 },
      { name: 'Абатский район', value: 2800000, plan: 3000000, orgCount: 3 },
      { name: 'Казанский район', value: 2443000, plan: 2600000, orgCount: 3 },
      { name: 'Омутинский район', value: 2200000, plan: 2400000, orgCount: 3 },
      { name: 'Сладковский район', value: 1954000, plan: 2100000, orgCount: 2 },
      { name: 'Сорокинский район', value: 1800000, plan: 2000000, orgCount: 2 },
      { name: 'Юргинский район', value: 1466000, plan: 1600000, orgCount: 3 },
      { name: 'Ярковский район', value: 977000, plan: 1100000, orgCount: 2 }
    ]
  },
  2023: {
    organizationCount: 274,
    factTotal: 420000000,
    planTotal: 410000000,
    budgetExecution: 102.4,
    dataQuality: 96,
    orgsWithData: 263,
    quarters: [
      { quarter: 'Q1', fact: 84000000, plan: 102500000 },
      { quarter: 'Q2', fact: 117600000, plan: 102500000 },
      { quarter: 'Q3', fact: 134400000, plan: 102500000 },
      { quarter: 'Q4', fact: 84000000, plan: 102500000 }
    ],
    districts: []
  },
  2024: {
    organizationCount: 274,
    factTotal: 450000000,
    planTotal: 440000000,
    budgetExecution: 102.3,
    dataQuality: 97,
    orgsWithData: 266,
    quarters: [
      { quarter: 'Q1', fact: 90000000, plan: 110000000 },
      { quarter: 'Q2', fact: 126000000, plan: 110000000 },
      { quarter: 'Q3', fact: 144000000, plan: 110000000 },
      { quarter: 'Q4', fact: 90000000, plan: 110000000 }
    ],
    districts: []
  },
  2025: {
    organizationCount: 274,
    factTotal: 480474000,
    planTotal: 470000000,
    budgetExecution: 122.1,
    dataQuality: 57,
    orgsWithData: 156,
    quarters: [
      { quarter: 'Q1', fact: 96095000, plan: 117500000 },
      { quarter: 'Q2', fact: 134533000, plan: 117500000 },
      { quarter: 'Q3', fact: 153752000, plan: 117500000 },
      { quarter: 'Q4', fact: 0, plan: 117500000 }  // Q4 пустой!
    ],
    districts: []
  }
};

// Данные по годам для графика
const allYearsData = [
  { year: 2022, fact: 390509000, plan: 393401000 },
  { year: 2023, fact: 420000000, plan: 410000000 },
  { year: 2024, fact: 450000000, plan: 440000000 },
  { year: 2025, fact: 480474000, plan: 470000000 }
];

// Форматирование
const formatMoney = (value) => {
  if (!value) return '0 ₽';
  const millions = value / 1000000;
  if (millions >= 1) {
    return millions.toFixed(1).replace(/\.0$/, '') + ' млн ₽';
  }
  const thousands = value / 1000;
  if (thousands >= 1) {
    return thousands.toFixed(1) + ' тыс ₽';
  }
  return value.toLocaleString('ru-RU') + ' ₽';
};

const formatMoneyShort = (value) => {
  if (!value) return '—';
  const millions = value / 1000000;
  if (millions >= 1) {
    return millions.toFixed(1) + 'М';
  }
  const thousands = value / 1000;
  return thousands.toFixed(0) + 'т';
};

const getExecutionColor = (percent) => {
  if (percent >= 100) return 'text-green';
  if (percent >= 80) return 'text-light-green';
  if (percent >= 50) return 'text-orange';
  return 'text-red';
};

// Загрузка данных
const loadStats = async () => {
  try {
    const [statsRes, mapRes] = await Promise.all([
      api.get('/analytics/stats', { params: { year: selectedYear.value } }),
      api.get('/analytics/map', { params: { year: selectedYear.value } })
    ]);

    stats.value = {
      organizationCount: statsRes.data.organizationCount || 274,
      factTotal: statsRes.data.factTotal || 0,
      planTotal: statsRes.data.forecastTotal || statsRes.data.planTotal || 0,
      budgetExecution: statsRes.data.budgetExecution || 0,
      dataQuality: statsRes.data.dataQuality || 0,
      orgsWithData: statsRes.data.orgsWithData || 0
    };

    mapData.value = mapRes.data || [];
    
    // Загружаем квартальные данные
    quarterlyData.value = mockDataByYear[selectedYear.value]?.quarters || [];
    
  } catch (error) {
    console.log('Using mock data');
    loadMockData();
  }

  buildChart();
};

const loadMockData = () => {
  const data = mockDataByYear[selectedYear.value] || mockDataByYear[2022];

  stats.value = {
    organizationCount: data.organizationCount,
    factTotal: data.factTotal,
    planTotal: data.planTotal,
    budgetExecution: data.budgetExecution,
    dataQuality: data.dataQuality,
    orgsWithData: data.orgsWithData
  };

  quarterlyData.value = data.quarters;

  // Для карты используем данные 2022 как базу (там есть все районы)
  mapData.value = mockDataByYear[2022].districts.map(d => ({
    name: d.name,
    value: d.value
  }));
};

// Построение графика
const buildChart = () => {
  if (chartMode.value === 'years') {
    barChartOption.value = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: (params) => {
          let result = `<strong>${params[0].name}</strong><br/>`;
          params.forEach(p => {
            const value = formatMoney(p.value);
            result += `${p.marker} ${p.seriesName}: ${value}<br/>`;
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
        data: allYearsData.map(d => d.year)
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: (val) => (val / 1000000).toFixed(0) + 'М'
        }
      },
      series: [
        {
          name: 'ФАКТ',
          type: 'bar',
          data: allYearsData.map(d => d.fact),
          itemStyle: { color: '#4CAF50' },
          barGap: '10%'
        },
        {
          name: 'ПЛАН',
          type: 'bar',
          data: allYearsData.map(d => d.plan),
          itemStyle: { color: '#F44336' }
        }
      ]
    };
  } else {
    // По кварталам
    const qData = quarterlyData.value;
    barChartOption.value = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: (params) => {
          let result = `<strong>${params[0].name} ${selectedYear.value}</strong><br/>`;
          params.forEach(p => {
            const value = formatMoney(p.value);
            result += `${p.marker} ${p.seriesName}: ${value}<br/>`;
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
        data: qData.map(d => d.quarter)
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: (val) => (val / 1000000).toFixed(0) + 'М'
        }
      },
      series: [
        {
          name: 'ФАКТ',
          type: 'bar',
          data: qData.map(d => d.fact),
          itemStyle: { color: '#4CAF50' },
          barGap: '10%'
        },
        {
          name: 'ПЛАН',
          type: 'bar',
          data: qData.map(d => d.plan),
          itemStyle: { color: '#F44336' }
        }
      ]
    };
  }
};

// Открытие диалога района
const openDistrictDialog = (districtName) => {
  const districtInfo = mockDataByYear[2022].districts.find(d => 
    d.name === districtName || 
    districtName.includes(d.name) ||
    d.name.includes(districtName.replace(' район', '').replace('ий', 'ий'))
  );

  if (districtInfo) {
    const execution = districtInfo.plan > 0
      ? Math.round((districtInfo.value / districtInfo.plan) * 100)
      : 0;

    selectedDistrict.value = {
      name: districtName,
      orgCount: districtInfo.orgCount,
      fact: districtInfo.value,
      plan: districtInfo.plan,
      execution: execution,
      quarters: [
        Math.round(districtInfo.value * 0.2),
        Math.round(districtInfo.value * 0.28),
        Math.round(districtInfo.value * 0.32),
        selectedYear.value === 2025 ? 0 : Math.round(districtInfo.value * 0.2)
      ]
    };
  } else {
    selectedDistrict.value = {
      name: districtName,
      orgCount: 5,
      fact: 2000000,
      plan: 2500000,
      execution: 80,
      quarters: [400000, 560000, 640000, selectedYear.value === 2025 ? 0 : 400000]
    };
  }

  districtDialog.value = true;
};

// Следим за изменением режима графика
watch(chartMode, () => {
  buildChart();
});

onMounted(() => {
  loadStats();
});
</script>

<style scoped>
.chart {
  height: 100%;
  width: 100%;
}
</style>
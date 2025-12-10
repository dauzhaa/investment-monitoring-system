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
        <v-card class="pa-4 h-100" elevation="2">
          <div class="d-flex align-center mb-2">
            <v-icon color="blue" size="24" class="mr-2">mdi-domain</v-icon>
            <span class="text-body-2 text-grey">Всего организаций</span>
          </div>
          <div class="text-h4 font-weight-bold text-blue">{{ stats.organizationCount }}</div>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 h-100" elevation="2">
          <div class="d-flex align-center mb-2">
            <v-icon color="green" size="24" class="mr-2">mdi-currency-rub</v-icon>
            <span class="text-body-2 text-grey">Инвестиции за {{ selectedYear }} г.</span>
          </div>
          <div class="text-h5 font-weight-bold text-green mb-1">{{ formatMoney(stats.factTotal) }}</div>
          <div class="text-caption text-grey">ФАКТ</div>
          <v-divider class="my-2"></v-divider>
          <div class="text-h6 text-red">{{ formatMoney(stats.forecastTotal) }}</div>
          <div class="text-caption text-grey">ПЛАН</div>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 h-100" elevation="2">
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
        <v-card class="pa-4 h-100" elevation="2">
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

    <!-- Основной контент -->
    <v-row>
      <!-- Карта -->
      <v-col cols="12" lg="7">
        <v-card class="rounded-lg fill-height" elevation="2">
          <v-card-title>Интерактивная карта области</v-card-title>
          <v-card-text style="height: 500px; padding: 8px;">
            <map-chart :data="mapData" :year="selectedYear" />
          </v-card-text>
        </v-card>
      </v-col>

      <!-- График -->
      <v-col cols="12" lg="5">
        <v-card class="rounded-lg fill-height" elevation="2">
          <v-card-title class="d-flex align-center">
            <span>Динамика инвестиций</span>
            <v-spacer></v-spacer>
            <v-btn-toggle v-model="chartMode" mandatory density="compact" color="primary">
              <v-btn value="years" size="small">По годам</v-btn>
              <v-btn value="quarters" size="small">По кварталам</v-btn>
            </v-btn-toggle>
          </v-card-title>
          <v-card-text style="height: 450px;">
            <v-chart class="chart" :option="chartOption" autoresize />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
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

const currentYear = new Date().getFullYear();
const selectedYear = ref(2022);
const availableYears = [2025, 2024, 2023, 2022];
const chartMode = ref('years');

const stats = ref({
  factTotal: 0,
  forecastTotal: 0,
  budgetExecution: 0,
  organizationCount: 274,
  dataQuality: 0,
  orgsWithData: 0
});

const mapData = ref([]);

// Данные для графиков
const yearlyData = ref([
  { year: 2022, fact: 390509, plan: 393401 },
  { year: 2023, fact: 420000, plan: 410000 },
  { year: 2024, fact: 450000, plan: 440000 },
  { year: 2025, fact: 480474, plan: 470000 }
]);

const quarterlyData = ref([
  { quarter: 'Q1', fact: 78102, plan: 98350 },
  { quarter: 'Q2', fact: 109342, plan: 98350 },
  { quarter: 'Q3', fact: 124982, plan: 98350 },
  { quarter: 'Q4', fact: 0, plan: 98351 }  // Q4 пустой
]);

const formatMoney = (value) => {
  if (!value) return '0 ₽';
  if (value >= 1000) {
    return (value / 1000).toFixed(1) + ' млн ₽';
  }
  return value.toFixed(0) + ' тыс. ₽';
};

const getExecutionColor = (percent) => {
  if (percent >= 100) return 'text-green';
  if (percent >= 80) return 'text-light-green';
  if (percent >= 50) return 'text-orange';
  return 'text-red';
};

// Вычисляемый option для графика
const chartOption = computed(() => {
  if (chartMode.value === 'years') {
    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: (params) => {
          let result = `<strong>${params[0].name}</strong><br/>`;
          params.forEach(p => {
            if (p.value !== null && p.value !== undefined) {
              result += `${p.marker} ${p.seriesName}: ${formatMoney(p.value)}<br/>`;
            }
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
    // По кварталам для выбранного года
    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: (params) => {
          let result = `<strong>${params[0].name} ${selectedYear.value}</strong><br/>`;
          params.forEach(p => {
            if (p.value !== null && p.value !== undefined && p.value !== 0) {
              result += `${p.marker} ${p.seriesName}: ${formatMoney(p.value)}<br/>`;
            } else if (p.seriesName === 'ФАКТ' && p.value === 0) {
              result += `${p.marker} ${p.seriesName}: нет данных<br/>`;
            }
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
          data: quarterlyData.value.map(d => d.fact || null),  // null для пустых
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
});

const loadStats = async () => {
  try {
    const [statsRes, mapRes] = await Promise.all([
      api.get('/analytics/stats', { params: { year: selectedYear.value } }),
      api.get('/analytics/map', { params: { year: selectedYear.value } })
    ]);
    
    stats.value = {
      ...statsRes.data,
      organizationCount: statsRes.data.organizationCount || 274
    };
    mapData.value = mapRes.data || [];
    
    // Загружаем квартальные данные
    try {
      const quartersRes = await api.get('/analytics/quarters', { params: { year: selectedYear.value } });
      if (quartersRes.data && quartersRes.data.length) {
        quarterlyData.value = quartersRes.data.map((q, i) => ({
          quarter: `Q${i + 1}`,
          fact: q.fact || 0,
          plan: q.plan || 0
        }));
      }
    } catch (e) {
      // Используем mock данные для кварталов
      loadQuarterlyMockData();
    }
    
  } catch (error) {
    console.error('Ошибка загрузки:', error);
    loadMockData();
  }
};

const loadMockData = () => {
  const mockByYear = {
    2022: {
      factTotal: 390509,
      forecastTotal: 393401,
      budgetExecution: 99.3,
      organizationCount: 274,
      dataQuality: 95,
      orgsWithData: 260
    },
    2023: {
      factTotal: 420000,
      forecastTotal: 410000,
      budgetExecution: 102.4,
      organizationCount: 274,
      dataQuality: 96,
      orgsWithData: 263
    },
    2024: {
      factTotal: 450000,
      forecastTotal: 440000,
      budgetExecution: 102.3,
      organizationCount: 274,
      dataQuality: 97,
      orgsWithData: 266
    },
    2025: {
      factTotal: 480474,
      forecastTotal: 470000,
      budgetExecution: 102.2,
      organizationCount: 274,
      dataQuality: 57,
      orgsWithData: 156
    }
  };

  stats.value = mockByYear[selectedYear.value] || mockByYear[2022];
  loadQuarterlyMockData();
};

const loadQuarterlyMockData = () => {
  const quartersByYear = {
    2022: [
      { quarter: 'Q1', fact: 78102, plan: 98350 },
      { quarter: 'Q2', fact: 109342, plan: 98350 },
      { quarter: 'Q3', fact: 124982, plan: 98350 },
      { quarter: 'Q4', fact: 78083, plan: 98351 }
    ],
    2023: [
      { quarter: 'Q1', fact: 84000, plan: 102500 },
      { quarter: 'Q2', fact: 117600, plan: 102500 },
      { quarter: 'Q3', fact: 134400, plan: 102500 },
      { quarter: 'Q4', fact: 84000, plan: 102500 }
    ],
    2024: [
      { quarter: 'Q1', fact: 90000, plan: 110000 },
      { quarter: 'Q2', fact: 126000, plan: 110000 },
      { quarter: 'Q3', fact: 144000, plan: 110000 },
      { quarter: 'Q4', fact: 90000, plan: 110000 }
    ],
    2025: [
      { quarter: 'Q1', fact: 96095, plan: 117500 },
      { quarter: 'Q2', fact: 134533, plan: 117500 },
      { quarter: 'Q3', fact: 153752, plan: 117500 },
      { quarter: 'Q4', fact: 0, plan: 117500 }  // Нет данных за Q4 2025
    ]
  };
  
  quarterlyData.value = quartersByYear[selectedYear.value] || quartersByYear[2022];
};

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
<template>
  <v-container fluid>
    <!-- KPI Cards -->
    <v-row>
      <v-col cols="12" md="3">
        <v-card color="primary" dark class="pa-4 rounded-lg">
          <div class="text-subtitle-2">Общие инвестиции ({{ selectedYear }})</div>
          <div class="text-h4 font-weight-bold">{{ formatMoney(stats.factTotal) }} млн ₽</div>
          <div class="text-caption">Прогноз: {{ formatMoney(stats.forecastTotal) }} млн ₽</div>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card color="green" dark class="pa-4 rounded-lg">
          <div class="text-subtitle-2">Кол-во организаций</div>
          <div class="text-h4 font-weight-bold">{{ stats.organizationCount }}</div>
          <div class="text-caption">Активных в системе</div>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card class="pa-4 rounded-lg" color="grey-lighten-4">
          <div class="text-subtitle-2">Качество данных</div>
          <div class="text-h4 font-weight-bold">{{ stats.dataQuality }}%</div>
          <div class="text-caption">Заполненность отчетов</div>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card color="orange" dark class="pa-4 rounded-lg">
          <div class="text-subtitle-2">Освоение бюджета</div>
          <div class="text-h4 font-weight-bold">{{ stats.budgetExecution }}%</div>
          <div class="text-caption">Факт / План × 100</div>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mt-4">
      <!-- Динамика по годам -->
      <v-col cols="12" md="6">
        <v-card class="rounded-lg fill-height">
          <v-card-title class="d-flex align-center">
            <span>Динамика (2022-{{ selectedYear }})</span>
            <v-spacer></v-spacer>
            <v-select
              v-model="selectedYear"
              :items="availableYears"
              density="compact"
              hide-details
              style="max-width: 100px"
              @update:model-value="loadStats"
            ></v-select>
          </v-card-title>
          <v-card-text style="height: 400px;">
            <v-chart class="chart" :option="barChartOption" autoresize />
          </v-card-text>
          <v-card-actions class="px-4 pb-4">
            <v-chip size="small" color="primary" variant="flat" class="mr-2">
              <v-icon start size="small">mdi-circle</v-icon>
              Факт
            </v-chip>
            <v-chip size="small" color="orange" variant="flat">
              <v-icon start size="small">mdi-circle</v-icon>
              Прогноз
            </v-chip>
          </v-card-actions>
        </v-card>
      </v-col>

      <!-- Карта районов -->
      <v-col cols="12" md="6">
        <v-card class="rounded-lg fill-height">
          <v-card-title>Интерактивная карта области</v-card-title>
          <v-card-text style="height: 400px; padding: 0;">
            <map-chart :data="mapData" />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import VChart from 'vue-echarts';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { BarChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components';
import MapChart from '@/components/MapChart.vue';
import api from '@/services/api';

use([CanvasRenderer, BarChart, GridComponent, TooltipComponent, LegendComponent]);

const currentYear = new Date().getFullYear();
const selectedYear = ref(currentYear);
const availableYears = computed(() => {
  const years = [];
  for (let y = 2022; y <= currentYear; y++) {
    years.push(y);
  }
  return years;
});

const stats = ref({
  factTotal: 0,
  forecastTotal: 0,
  budgetExecution: 0,
  organizationCount: 0,
  dataQuality: 0
});

const trendsData = ref({ history: [], forecast: [] });
const mapData = ref([]);
const barChartOption = ref({});

const formatMoney = (value) => {
  if (!value) return '0';
  const millions = value / 1000000;
  if (millions >= 1) {
    return millions.toFixed(1).replace(/\.0$/, '');
  }
  return value.toLocaleString('ru-RU');
};

const loadStats = async () => {
  try {
    const statsResponse = await api.get('/analytics/stats', {
      params: { year: selectedYear.value }
    });
    stats.value = statsResponse.data;

    const trendsResponse = await api.get('/analytics/trends');
    trendsData.value = trendsResponse.data;

    const mapResponse = await api.get('/analytics/map', {
      params: { year: selectedYear.value }
    });
    mapData.value = mapResponse.data;

    buildChart();
  } catch (error) {
    console.error('Ошибка загрузки данных:', error);
  }
};

const buildChart = () => {
  const history = trendsData.value.history || [];
  const forecast = trendsData.value.forecast || [];

  const years = [];
  const factData = [];
  const forecastData = [];

  history.forEach(item => {
    years.push(item.year);
    factData.push(item.amount / 1000000);
    forecastData.push(null);
  });

  forecast.forEach(item => {
    if (!years.includes(item.year)) {
      years.push(item.year);
      factData.push(null);
    }
    const idx = years.indexOf(item.year);
    forecastData[idx] = item.amount / 1000000;
  });

  barChartOption.value = {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        let result = `${params[0].axisValue}<br/>`;
        params.forEach(p => {
          if (p.value !== null && p.value !== undefined) {
            result += `${p.marker} ${p.seriesName}: ${p.value.toLocaleString('ru-RU')} млн ₽<br/>`;
          }
        });
        return result;
      }
    },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: years },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: (val) => `${val.toLocaleString('ru-RU')}` }
    },
    series: [
      { name: 'Факт', type: 'bar', data: factData, itemStyle: { color: '#1976D2' } },
      { name: 'Прогноз', type: 'bar', data: forecastData, itemStyle: { color: '#FF9800' } }
    ]
  };
};

onMounted(() => {
  loadStats();
});
</script>

<style scoped>
.chart { height: 100%; width: 100%; }
</style>
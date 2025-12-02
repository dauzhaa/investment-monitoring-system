<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12" md="3">
        <v-card color="primary" dark class="pa-4 rounded-lg">
          <div class="text-subtitle-1">Общие инвестиции ({{ currentYear }})</div>
          <div class="text-h4 font-weight-bold">{{ formatNumber(stats.total_annual) }} млн ₽</div>
          <div class="text-caption">Прогноз: {{ formatNumber(stats.forecast_total) }} млн ₽</div>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="3">
        <v-card color="success" dark class="pa-4 rounded-lg">
          <div class="text-subtitle-1">Кол-во организаций</div>
          <div class="text-h4 font-weight-bold">{{ stats.organizations_count }}</div>
          <div class="text-caption">Активных в системе</div>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="3">
        <v-card color="info" dark class="pa-4 rounded-lg">
          <div class="text-subtitle-1">Качество данных</div>
          <div class="text-h4 font-weight-bold">{{ stats.data_quality }}%</div>
          <div class="text-caption">Заполненность отчетов</div>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="3">
        <v-card color="warning" dark class="pa-4 rounded-lg">
          <div class="text-subtitle-1">Освоение бюджета</div>
          <div class="text-h4 font-weight-bold">{{ stats.execution_percent }}%</div>
          <div class="text-caption">Факт / План × 100</div>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mt-4">
      <v-col cols="12" md="4">
        <v-card class="rounded-lg fill-height" elevation="2">
          <v-card-title>Динамика (2022-2025)</v-card-title>
          <v-card-text style="height: 600px;">
             <v-chart class="chart" :option="barChartOption" autoresize />
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="8">
        <v-card class="rounded-lg fill-height" elevation="2">
          <v-card-title>Интерактивная карта области</v-card-title>
          <v-card-text style="height: 600px; padding: 0;">
            <map-chart 
              :mapData="mapData" 
              @district-click="goToDistrict" 
            />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import VChart from 'vue-echarts';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { BarChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components';
import MapChart from '@/components/MapChart.vue';
import axios from 'axios';

use([CanvasRenderer, BarChart, GridComponent, TooltipComponent, LegendComponent]);

const router = useRouter();
const currentYear = new Date().getFullYear();

const stats = ref({ 
  total_annual: 0, 
  forecast_total: 0, 
  execution_percent: 0,
  organizations_count: 0,
  data_quality: 0
});

const barChartOption = ref({});
const mapData = ref([]);

const formatNumber = (num) => {
  return num ? num.toLocaleString('ru-RU') : 0;
};

// Обработка клика по району на карте
const goToDistrict = (districtName) => {
  if (districtName) {
    router.push({ name: 'district', params: { name: districtName } });
  }
};

onMounted(async () => {
  try {
    const statsResponse = await axios.get('/api/v1/analytics/stats');
    stats.value = statsResponse.data;

    const trendsResponse = await axios.get('/api/v1/analytics/trends');
    const history = trendsResponse.data.history || [];
    
    const years = [];
    const factData = [];
    const forecastData = [];
    
    for (let year = 2022; year <= 2025; year++) {
      years.push(year.toString());
      const yearData = history.find(h => h.year === year);
      
      if (year <= 2024) {
        factData.push(yearData ? yearData.amount : 0);
        forecastData.push(null);
      } else {
        factData.push(null);
        forecastData.push(stats.value.forecast_total);
      }
    }

    barChartOption.value = {
      tooltip: { 
        trigger: 'axis',
        formatter: (params) => {
          let result = params[0].name + '<br/>';
          params.forEach(item => {
            if (item.value !== null) {
              result += `${item.seriesName}: ${formatNumber(item.value)} млн ₽<br/>`;
            }
          });
          return result;
        }
      },
      legend: { data: ['Факт', 'Прогноз'], bottom: 10 },
      xAxis: { type: 'category', data: years },
      yAxis: { type: 'value', axisLabel: { formatter: '{value}' } },
      series: [
        {
          name: 'Факт',
          data: factData,
          type: 'bar',
          itemStyle: { color: '#1976D2' },
          barWidth: '40%'
        },
        {
          name: 'Прогноз',
          data: forecastData,
          type: 'bar',
          itemStyle: { color: '#FFA726' },
          barWidth: '40%'
        }
      ]
    };

    const mapResponse = await axios.get('/api/v1/analytics/map');
    mapData.value = mapResponse.data || [];

  } catch (error) {
    console.error('Ошибка загрузки данных:', error);
  }
});
</script>

<style scoped>
.chart { height: 100%; width: 100%; }
</style>
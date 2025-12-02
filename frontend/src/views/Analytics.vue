<template>
  <v-container>
    <h1 class="text-h4 font-weight-bold mb-4">Аналитика</h1>
    
    <v-row>
      <v-col cols="12" md="5">
        <v-card class="rounded-lg">
          <v-card-title class="d-flex align-center">
            <v-icon color="primary" class="mr-2">mdi-podium</v-icon>
            Топ-3 Района по инвестициям (за все время)
          </v-card-title>
          <v-card-text>
            <v-list>
              <v-list-item v-for="(item, i) in topDistricts" :key="i" class="px-0">
                <template v-slot:prepend>
                  <v-avatar :color="getMedalColor(i)" size="36" class="mr-3">
                    <span class="text-white font-weight-bold">{{ i + 1 }}</span>
                  </v-avatar>
                </template>
                <v-list-item-title class="font-weight-medium">{{ item.name }}</v-list-item-title>
                <v-list-item-subtitle>{{ formatMoney(item.value) }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item v-if="topDistricts.length === 0">
                <v-list-item-title class="text-grey">Нет данных</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="7">
        <v-card class="rounded-lg">
          <v-card-title class="d-flex align-center">
            <v-icon color="success" class="mr-2">mdi-chart-line</v-icon>
            Динамика и AI Прогноз
          </v-card-title>
          <v-card-text style="height: 350px;">
            <v-chart class="chart" :option="chartOption" autoresize />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import VChart from 'vue-echarts';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components';
import api from '@/services/api';

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent]);

const topDistricts = ref([]);
const chartOption = ref({});

const formatMoney = (value) => {
  if (!value) return '0 ₽';
  if (value >= 1000000) {
    return (value / 1000000).toFixed(1) + ' млн ₽';
  }
  return value.toLocaleString('ru-RU') + ' ₽';
};

const getMedalColor = (index) => {
  const colors = ['#FFD700', '#C0C0C0', '#CD7F32'];
  return colors[index] || 'grey';
};

const loadData = async () => {
  try {
    const response = await api.get('/analytics/trends');
    const { history, rating, forecast } = response.data;
    
    topDistricts.value = rating || [];
    
    // Строим график
    const years = [];
    const factData = [];
    const forecastData = [];
    
    // История (факт)
    (history || []).forEach(item => {
      years.push(item.year);
      factData.push(item.amount);
    });
    
    // Прогноз
    (forecast || []).forEach(item => {
      if (!years.includes(item.year)) {
        years.push(item.year);
        factData.push(null);
      }
      const idx = years.indexOf(item.year);
      if (!forecastData[idx]) forecastData[idx] = item.amount;
    });
    
    // Заполняем пустые значения
    while (forecastData.length < years.length) {
      forecastData.push(null);
    }
    
    chartOption.value = {
      tooltip: {
        trigger: 'axis',
        formatter: (params) => {
          let result = `<b>${params[0].axisValue}</b><br/>`;
          params.forEach(p => {
            if (p.value !== null && p.value !== undefined) {
              result += `${p.marker} ${p.seriesName}: ${formatMoney(p.value)}<br/>`;
            }
          });
          return result;
        }
      },
      legend: { data: ['Факт', 'Прогноз'], bottom: 0 },
      grid: { left: '3%', right: '4%', bottom: '15%', top: '10%', containLabel: true },
      xAxis: { type: 'category', data: years, boundaryGap: false },
      yAxis: {
        type: 'value',
        axisLabel: { formatter: (val) => (val / 1000).toLocaleString('ru-RU') + 'к' }
      },
      series: [
        {
          name: 'Факт',
          type: 'line',
          data: factData,
          smooth: true,
          itemStyle: { color: '#4CAF50' },
          areaStyle: { opacity: 0.2 }
        },
        {
          name: 'Прогноз',
          type: 'line',
          data: forecastData,
          smooth: true,
          lineStyle: { type: 'dashed' },
          itemStyle: { color: '#FF9800' }
        }
      ]
    };
  } catch (error) {
    console.error('Ошибка загрузки аналитики:', error);
  }
};

onMounted(() => {
  loadData();
});
</script>

<style scoped>
.chart { height: 100%; width: 100%; }
</style>
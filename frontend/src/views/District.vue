<template>
  <v-container>
    <v-btn prepend-icon="mdi-arrow-left" variant="text" @click="$router.push('/')" class="mb-4">
      Назад к главной
    </v-btn>

    <v-card class="mb-4">
      <v-card-title class="text-h4 font-weight-bold" style="color: #1B3A5C;">
        {{ districtData.district?.name || 'Загрузка...' }}
      </v-card-title>
      <v-card-subtitle class="text-subtitle-1">
        Зарегистрировано организаций: {{ districtData.district?.organizations_count || 0 }}
      </v-card-subtitle>
    </v-card>

    <v-row>
      <v-col cols="12" md="4">
        <v-card color="#F57C00" dark class="pa-4 rounded-lg text-white">
          <div class="text-subtitle-1 font-weight-medium">План</div>
          <div class="text-h4 font-weight-bold">
            {{ formatNumber(districtData.stats?.forecast) }} <span class="text-h6">тыс. ₽</span>
          </div>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="4">
        <v-card color="#2E7D32" dark class="pa-4 rounded-lg text-white">
          <div class="text-subtitle-1 font-weight-medium">Факт</div>
          <div class="text-h4 font-weight-bold">
            {{ formatNumber(districtData.stats?.fact) }} <span class="text-h6">тыс. ₽</span>
          </div>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="4">
        <v-card color="#1B3A5C" dark class="pa-4 rounded-lg text-white">
          <div class="text-subtitle-1 font-weight-medium">Освоение бюджета</div>
          <div class="text-h4 font-weight-bold">
            {{ districtData.stats?.execution_percent || 0 }}%
          </div>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mt-4">
      <v-col cols="12">
        <v-card class="rounded-lg pa-4">
          <div class="text-h6 font-weight-bold mb-2" style="color: #1B3A5C;">История инвестиций</div>
          <v-card-text style="height: 400px; padding: 0;">
            <v-chart class="chart" :option="historyChartOption" autoresize />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title class="font-weight-bold" style="color: #1B3A5C;">Организации района</v-card-title>
          <v-data-table
            :headers="orgHeaders"
            :items="districtData.organizations"
            :items-per-page="10"
            hover
          >
            <template v-slot:item.forecast="{ item }">
              {{ formatNumber(item.forecast) }}
            </template>
            <template v-slot:item.fact="{ item }">
              <span class="font-weight-bold" style="color: #2E7D32;">{{ formatNumber(item.fact) }}</span>
            </template>
            <template v-slot:item.execution="{ item }">
              <v-chip :color="getExecutionColor(item)" size="small" variant="flat" class="font-weight-bold">
                {{ calculateExecution(item) }}%
              </v-chip>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import VChart from 'vue-echarts';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components';
import axios from 'axios';
import { BarChart } from 'echarts/charts';   // было: import { LineChart }
use([CanvasRenderer, BarChart, GridComponent, TooltipComponent, LegendComponent]);

const route = useRoute();

const districtData = ref({
  district: null,
  stats: null,
  history: [],
  organizations: []
});

const historyChartOption = ref({});

const orgHeaders = [
  { title: 'Организация', key: 'name', align: 'start' },
  { title: 'ИНН', key: 'inn' },
  { title: 'План (тыс. ₽)', key: 'forecast', align: 'end' },
  { title: 'Факт (тыс. ₽)', key: 'fact', align: 'end' },
  { title: 'Освоение', key: 'execution', align: 'center' }
];

const formatNumber = (num) => {
  return num ? new Intl.NumberFormat('ru-RU').format(Math.round(num)) : '0';
};

const calculateExecution = (item) => {
  if (!item.forecast || item.forecast === 0) return 0;
  return Math.round((item.fact / item.forecast) * 100);
};

const getExecutionColor = (item) => {
  const execution = calculateExecution(item);
  if (execution >= 80) return '#2E7D32';
  if (execution >= 50) return '#F57C00';
  return '#D32F2F';
};

// Внутри District.vue, самый низ скрипта
onMounted(async () => {
  try {
    const districtName = route.params.name;
    const response = await axios.get(`/api/v1/districts/${encodeURIComponent(districtName)}`);
    districtData.value = response.data;

    const years = districtData.value.history.map(h => h.year.toString());
    const factAmounts = districtData.value.history.map(h => h.amount);
    // Извлекаем План (forecast). Если его нет, ставим 0 или null
    const planAmounts = districtData.value.history.map(h => h.forecast || null); 

    historyChartOption.value = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: (params) => {
          let html = `${params[0].name}<br/>`;
          params.forEach(p => {
            const color = p.seriesName === 'Факт' ? '#2E7D32' : '#F57C00';
            const value = (p.value !== null && p.value !== undefined) ? formatNumber(p.value) : 'Н/Д';
            html += `<span style="color:${color};font-weight:bold;">${p.seriesName}:</span> ${value} тыс. ₽<br/>`;
          });
          return html;
        }
      },
      legend: { data: ['Факт', 'План'], top: 0, left: 'center' },
      grid: { left: '2%', right: '4%', bottom: '5%', top: '15%', containLabel: true },
      xAxis: { type: 'category', data: years },
      yAxis: { type: 'value', axisLabel: { formatter: (value) => formatNumber(value) } },
      series: [
        { name: 'Факт', type: 'bar', data: factAmounts, itemStyle: { color: '#2E7D32', borderRadius: [4, 4, 0, 0] } },
        { name: 'План', type: 'bar', data: planAmounts, itemStyle: { color: '#F57C00', borderRadius: [4, 4, 0, 0] } }
      ]
    };
  } catch (error) {
    console.error('Ошибка загрузки данных района:', error);
  }
});
</script>

<style scoped>
.chart { height: 100%; width: 100%; }
</style>
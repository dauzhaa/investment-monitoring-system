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
import { LineChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components';
import axios from 'axios';

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent]);

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

onMounted(async () => {
  try {
    const districtName = route.params.name;
    const response = await axios.get(`/api/v1/districts/${encodeURIComponent(districtName)}`);
    districtData.value = response.data;

    const years = districtData.value.history.map(h => h.year.toString());
    const amounts = districtData.value.history.map(h => h.amount);

    historyChartOption.value = {
      tooltip: {
        trigger: 'axis',
        formatter: (params) => {
          return `${params[0].name}<br/><span style="color:#2E7D32;font-weight:bold;">Факт:</span> ${formatNumber(params[0].value)} тыс. ₽`;
        }
      },
      grid: { left: '2%', right: '4%', bottom: '5%', top: '10%', containLabel: true },
      xAxis: { type: 'category', boundaryGap: false, data: years },
      yAxis: { type: 'value', axisLabel: { formatter: (value) => formatNumber(value) } },
      series: [
        {
          name: 'Инвестиции',
          type: 'line',
          data: amounts,
          smooth: true,
          itemStyle: { color: '#2E7D32' },
          areaStyle: { color: 'rgba(46, 125, 50, 0.2)' }
        }
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
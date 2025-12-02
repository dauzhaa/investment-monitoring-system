<template>
  <v-container>
    <v-btn
      prepend-icon="mdi-arrow-left"
      variant="text"
      @click="$router.push('/dashboard')"
      class="mb-4"
    >
      Назад к дашборду
    </v-btn>

    <v-card class="mb-4">
      <v-card-title class="text-h4">
        {{ districtData.district?.name }}
      </v-card-title>
      <v-card-subtitle>
        Организаций: {{ districtData.district?.organizations_count }}
      </v-card-subtitle>
    </v-card>

    <!-- Статистика -->
    <v-row>
      <v-col cols="12" md="4">
        <v-card color="primary" dark class="pa-4 rounded-lg">
          <div class="text-subtitle-1">Прогноз</div>
          <div class="text-h4 font-weight-bold">
            {{ formatNumber(districtData.stats?.forecast) }} млн ₽
          </div>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="4">
        <v-card color="success" dark class="pa-4 rounded-lg">
          <div class="text-subtitle-1">Факт</div>
          <div class="text-h4 font-weight-bold">
            {{ formatNumber(districtData.stats?.fact) }} млн ₽
          </div>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="4">
        <v-card color="info" dark class="pa-4 rounded-lg">
          <div class="text-subtitle-1">Освоение</div>
          <div class="text-h4 font-weight-bold">
            {{ districtData.stats?.execution_percent }}%
          </div>
        </v-card>
      </v-col>
    </v-row>

    <!-- График истории -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card class="rounded-lg">
          <v-card-title>История инвестиций</v-card-title>
          <v-card-text style="height: 400px;">
            <v-chart class="chart" :option="historyChartOption" autoresize />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Таблица организаций -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title>Организации района</v-card-title>
          <v-data-table
            :headers="orgHeaders"
            :items="districtData.organizations"
            :items-per-page="10"
          >
            <template v-slot:item.forecast="{ item }">
              {{ formatNumber(item.forecast) }}
            </template>
            <template v-slot:item.fact="{ item }">
              {{ formatNumber(item.fact) }}
            </template>
            <template v-slot:item.execution="{ item }">
              <v-chip 
                :color="getExecutionColor(item)"
                size="small"
              >
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
import { ref, onMounted, computed } from 'vue';
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
  { title: 'Прогноз (млн ₽)', key: 'forecast', align: 'end' },
  { title: 'Факт (млн ₽)', key: 'fact', align: 'end' },
  { title: 'Освоение', key: 'execution', align: 'center' }
];

const formatNumber = (num) => {
  return num ? num.toLocaleString('ru-RU') : 0;
};

const calculateExecution = (item) => {
  if (!item.forecast || item.forecast === 0) return 0;
  return Math.round((item.fact / item.forecast) * 100);
};

const getExecutionColor = (item) => {
  const execution = calculateExecution(item);
  if (execution >= 80) return 'success';
  if (execution >= 50) return 'warning';
  return 'error';
};

onMounted(async () => {
  try {
    const districtName = route.params.name;
    const response = await axios.get(`/api/v1/districts/${districtName}`);
    districtData.value = response.data;

    // Формируем график истории
    const years = districtData.value.history.map(h => h.year.toString());
    const amounts = districtData.value.history.map(h => h.amount);

    historyChartOption.value = {
      tooltip: {
        trigger: 'axis',
        formatter: (params) => {
          return `${params[0].name}<br/>Инвестиции: ${formatNumber(params[0].value)} млн ₽`;
        }
      },
      xAxis: {
        type: 'category',
        data: years
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: '{value} млн ₽'
        }
      },
      series: [
        {
          name: 'Инвестиции',
          type: 'line',
          data: amounts,
          smooth: true,
          itemStyle: { color: '#1976D2' },
          areaStyle: { opacity: 0.3 }
        }
      ]
    };
  } catch (error) {
    console.error('Ошибка загрузки данных района:', error);
  }
});
</script>

<style scoped>
.chart {
  height: 100%;
  width: 100%;
}
</style>
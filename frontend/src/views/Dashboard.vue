<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12" md="4">
        <v-card color="primary" dark class="pa-4 rounded-lg">
          <div class="text-subtitle-1">Инвестиции ({{ currentYear }})</div>
          <div class="text-h4 font-weight-bold">{{ stats.total_annual }} млн ₽</div>
          <div class="text-caption">Прогноз: {{ stats.forecast_total }} млн ₽</div>
        </v-card>
      </v-col>
      <v-col cols="12" md="4">
        <v-card class="pa-4 rounded-lg">
          <div class="text-subtitle-1">Освоение бюджета</div>
          <div class="d-flex align-center mt-2">
             <v-progress-linear
               :model-value="stats.execution_percent"
               color="success"
               height="25"
               striped
             >
               <strong>{{ stats.execution_percent }}%</strong>
             </v-progress-linear>
          </div>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mt-4">
      <v-col cols="12" md="8">
        <v-card class="rounded-lg fill-height">
          <v-card-title>Динамика инвестиций по годам</v-card-title>
          <v-card-text style="height: 400px;">
             <v-chart class="chart" :option="barChartOption" autoresize />
          </v-card-text>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="4">
        <v-card class="rounded-lg fill-height">
          <v-card-title>Карта районов</v-card-title>
          <v-card-text style="height: 400px; padding: 0;">
            <map-chart />
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
import { BarChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components';
import MapChart from '@/components/MapChart.vue';

use([CanvasRenderer, BarChart, GridComponent, TooltipComponent, LegendComponent]);

const currentYear = new Date().getFullYear();
const stats = ref({ total_annual: 0, forecast_total: 0, execution_percent: 0 });
const barChartOption = ref({});

// Фейковые данные для примера (пока не подтянем API), заменишь на вызов axios
onMounted(() => {
    // Здесь должен быть axios.get('/api/dashboard/stats')
    stats.value = {
        total_annual: 15400,
        forecast_total: 20000,
        execution_percent: 77
    };

    barChartOption.value = {
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: ['2023', '2024', '2025 (План)'] },
        yAxis: { type: 'value' },
        series: [{
            data: [12000, 15400, 20000],
            type: 'bar',
            itemStyle: { color: '#1976D2' }
        }]
    };
});
</script>

<style scoped>
.chart { height: 100%; width: 100%; }
</style>
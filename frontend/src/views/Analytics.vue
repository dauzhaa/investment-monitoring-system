<template>
  <v-container>
    <h1 class="text-h4 font-weight-bold mb-6">Аналитика</h1>
    
    <v-row>
       <v-col cols="12" md="6">
          <v-card class="rounded-lg h-100" elevation="2">
             <v-card-title class="d-flex align-center">
                <v-icon color="primary" class="mr-2">mdi-podium-gold</v-icon>
                Топ-3 Района по инвестициям (2025)
             </v-card-title>
             <v-card-text style="height: 350px;">
                <v-chart class="chart" :option="topDistrictsOption" autoresize />
             </v-card-text>
          </v-card>
       </v-col>

       <v-col cols="12" md="6">
           <v-card class="rounded-lg h-100" elevation="2">
               <v-card-title class="d-flex align-center">
                  <v-icon color="secondary" class="mr-2">mdi-chart-timeline-variant</v-icon>
                  Динамика и AI Прогноз
               </v-card-title>
               <v-card-text style="height: 350px;">
                   <v-chart class="chart" :option="forecastOption" autoresize />
               </v-card-text>
           </v-card>
       </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from '@/services/api';
import VChart from 'vue-echarts';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { BarChart, LineChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components';

use([CanvasRenderer, BarChart, LineChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent]);

const topDistrictsOption = ref({});
const forecastOption = ref({});

onMounted(async () => {
    try {
        const res = await axios.get('/analytics/trends');
        const data = res.data;

        // 1. Setup Top 3 Chart (Bar)
        if (data.rating) {
            topDistrictsOption.value = {
                tooltip: { trigger: 'axis' },
                grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
                xAxis: { type: 'value', axisLabel: { formatter: '{value} млн' } },
                yAxis: { type: 'category', data: data.rating.map(i => i.name).reverse() },
                series: [{
                    name: 'Инвестиции',
                    type: 'bar',
                    data: data.rating.map(i => i.value).reverse(),
                    itemStyle: { color: '#5C6BC0', borderRadius: [0, 4, 4, 0] },
                    label: { show: true, position: 'right' }
                }]
            };
        }

        // 2. Setup Forecast Chart (Line)
        if (data.history || data.forecast) {
            const years = [];
            const historyData = [];
            const forecastData = [];

            // Combine history and forecast for x-axis
            const allPoints = [...(data.history || []), ...(data.forecast || [])];
            // Unique sorted years
            const uniqueYears = [...new Set(allPoints.map(p => p.year))].sort();

            uniqueYears.forEach(year => {
                years.push(year);
                
                // Find history
                const histItem = data.history?.find(h => h.year === year);
                historyData.push(histItem ? histItem.amount : null);

                // Find forecast
                const foreItem = data.forecast?.find(f => f.year === year);
                // If we have history, we don't show forecast line overlap usually, 
                // OR we show forecast starting from the last history point.
                // Simplified:
                forecastData.push(foreItem ? foreItem.amount : null);
            });

            forecastOption.value = {
                tooltip: { trigger: 'axis' },
                legend: { data: ['Факт', 'Прогноз'], bottom: 0 },
                grid: { left: '3%', right: '4%', bottom: '10%', containLabel: true },
                xAxis: { type: 'category', boundaryGap: false, data: years },
                yAxis: { type: 'value' },
                series: [
                    {
                        name: 'Факт',
                        type: 'line',
                        data: historyData,
                        smooth: true,
                        itemStyle: { color: '#4CAF50' },
                        areaStyle: { opacity: 0.2, color: '#4CAF50' }
                    },
                    {
                        name: 'Прогноз',
                        type: 'line',
                        data: forecastData,
                        smooth: true,
                        itemStyle: { color: '#FF9800' },
                        lineStyle: { type: 'dashed' }
                    }
                ]
            };
        }

    } catch (e) {
        console.error("Ошибка загрузки аналитики:", e);
    }
});
</script>

<style scoped>
.chart { height: 100%; width: 100%; }
</style>
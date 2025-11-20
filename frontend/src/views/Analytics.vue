<template>
  <div>
    <h1 class="text-h4 font-weight-bold mb-6 text-primary">Анализ и Тенденции</h1>

    <v-card elevation="2" class="rounded-lg mb-6">
      <v-card-title>
        <v-icon start color="primary">mdi-chart-timeline-variant</v-icon>
        Прогноз развития региона (2022 - 2025)
      </v-card-title>
      <v-card-text style="height: 400px;">
        <div v-if="loading" class="d-flex fill-height align-center justify-center">
           <v-progress-circular indeterminate color="primary"></v-progress-circular>
        </div>
        <div v-else-if="!trendOption.series" class="d-flex fill-height align-center justify-center text-grey">
           Нет данных для отображения
        </div>
        <v-chart v-else class="chart" :option="trendOption" autoresize />
      </v-card-text>
    </v-card>

    <v-row>
      <v-col cols="12" md="8">
        <v-card elevation="2" class="rounded-lg h-100">
          <v-card-title>
            <v-icon start color="orange">mdi-trophy</v-icon>
            Топ-10 Районов по объему инвестиций
          </v-card-title>
          <v-card-text style="height: 400px;">
             <div v-if="!barOption.series" class="d-flex fill-height align-center justify-center text-grey">
                Нет данных
             </div>
             <v-chart v-else class="chart" :option="barOption" autoresize />
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="4">
        <v-card elevation="2" class="rounded-lg h-100 bg-blue-lighten-5">
          <v-card-title>
            <v-icon start color="blue">mdi-lightbulb-on</v-icon>
            Ключевые выводы
          </v-card-title>
          <v-card-text>
            <v-list bg-color="transparent">
               <v-list-item>
                 <template v-slot:prepend><v-icon color="green">mdi-arrow-up-bold</v-icon></template>
                 <v-list-item-title class="font-weight-bold">Рост +12%</v-list-item-title>
                 <v-list-item-subtitle>Прогнозируется рост инвестиций в Q3 2025 года.</v-list-item-subtitle>
               </v-list-item>
               
               <v-divider class="my-2"></v-divider>

               <v-list-item>
                 <template v-slot:prepend><v-icon color="orange">mdi-map-marker-alert</v-icon></template>
                 <v-list-item-title class="font-weight-bold">Дисбаланс</v-list-item-title>
                 <v-list-item-subtitle>80% инвестиций сосредоточены в Тюмени и Тобольске.</v-list-item-subtitle>
               </v-list-item>

               <v-divider class="my-2"></v-divider>

               <v-list-item>
                 <template v-slot:prepend><v-icon color="purple">mdi-calendar-clock</v-icon></template>
                 <v-list-item-title class="font-weight-bold">Сезонность</v-list-item-title>
                 <v-list-item-subtitle>Пик платежей традиционно приходится на Декабрь.</v-list-item-subtitle>
               </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart, BarChart } from 'echarts/charts';
import { TitleComponent, TooltipComponent, GridComponent, LegendComponent, ToolboxComponent } from 'echarts/components';
import VChart from 'vue-echarts';

use([CanvasRenderer, LineChart, BarChart, TitleComponent, TooltipComponent, GridComponent, LegendComponent, ToolboxComponent]);

const loading = ref(true);
const trendOption = ref({}); // Инициализируем пустыми объектами
const barOption = ref({});

const loadData = async () => {
  loading.value = true;
  try {
    const res = await axios.get('/api/v1/analytics/trends');
    const data = res.data;
    
    console.log("Trends Data:", data); // <-- ОТЛАДКА В КОНСОЛИ

    // 1. НАСТРОЙКА ГРАФИКА ТРЕНДА
    const historyDates = data.history.map(h => h.year.toString());
    const historyValues = data.history.map(h => h.amount);
    
    const forecastDates = data.forecast.map(f => f.date);
    const forecastValues = data.forecast.map(f => f.amount);
    
    // Склеиваем даты (убираем дубликаты)
    const allDates = [...new Set([...historyDates, ...forecastDates])].sort();

    // Подготавливаем серии (заполняем нулями/null где нет данных)
    // Для простоты рисуем две отдельные линии
    
    trendOption.value = {
      tooltip: { trigger: 'axis' },
      legend: { data: ['Исторические данные', 'AI Прогноз'] },
      xAxis: { type: 'category', data: allDates, boundaryGap: false },
      yAxis: { type: 'value', axisLabel: { formatter: (val) => `${(val / 1000000).toFixed(0)} млн` } },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      series: [
        {
          name: 'Исторические данные',
          type: 'line',
          // Мапим данные на общую ось дат
          data: allDates.map(d => {
              const found = data.history.find(h => h.year.toString() === d);
              return found ? found.amount : null;
          }),
          smooth: true,
          itemStyle: { color: '#1976D2' },
          areaStyle: { opacity: 0.1, color: '#1976D2' },
          connectNulls: true // Соединять точки
        },
        {
          name: 'AI Прогноз',
          type: 'line',
          data: allDates.map(d => {
              const found = data.forecast.find(f => f.date === d);
              return found ? found.amount : null;
          }),
          smooth: true,
          lineStyle: { type: 'dashed' },
          itemStyle: { color: '#FF5252' },
          connectNulls: true
        }
      ]
    };

    // 2. НАСТРОЙКА БАР-ЧАРТА (РЕЙТИНГ)
    barOption.value = {
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'value', axisLabel: { formatter: (val) => `${(val / 1000000).toFixed(0)} млн` } },
      yAxis: { 
        type: 'category', 
        data: data.rating.map(r => r.name).reverse(), 
        axisLabel: { width: 120, overflow: 'truncate' }
      },
      series: [
        {
          name: 'Объем инвестиций',
          type: 'bar',
          data: data.rating.map(r => r.value).reverse(),
          itemStyle: { borderRadius: [0, 4, 4, 0], color: '#4CAF50' },
          label: { show: true, position: 'right', formatter: (p) => `${(p.value / 1000000).toFixed(1)} млн` }
        }
      ]
    };

  } catch (e) {
    console.error("Ошибка загрузки трендов:", e);
  } finally {
    loading.value = false;
  }
};

onMounted(loadData);
</script>

<style scoped>
.chart { height: 100%; width: 100%; }
</style>
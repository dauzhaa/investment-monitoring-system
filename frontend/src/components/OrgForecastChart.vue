<template>
  <div style="height: 350px; width: 100%;">
    <v-chart class="chart" :option="option" autoresize />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart } from 'echarts/charts';
import { TitleComponent, TooltipComponent, GridComponent, LegendComponent } from 'echarts/components';
import VChart from 'vue-echarts';

use([CanvasRenderer, LineChart, TitleComponent, TooltipComponent, GridComponent, LegendComponent]);

const props = defineProps(['history', 'forecast']);

const option = ref({
  title: { text: 'Динамика и AI Прогноз', left: 'center', textStyle: { fontSize: 14 } },
  tooltip: { trigger: 'axis' },
  legend: { data: ['Факт', 'Прогноз'], bottom: 0 },
  grid: { left: '3%', right: '4%', bottom: '10%', containLabel: true },
  xAxis: { type: 'category', boundaryGap: false, data: [] },
  yAxis: { type: 'value', axisLabel: { formatter: (val) => `${val/1000}к` } },
  series: [
    {
      name: 'Факт',
      type: 'line',
      data: [],
      smooth: true,
      itemStyle: { color: '#1976D2' },
      areaStyle: { opacity: 0.1 }
    },
    {
      name: 'Прогноз',
      type: 'line',
      data: [], 
      smooth: true,
      lineStyle: { type: 'dashed', width: 2 },
      itemStyle: { color: '#FF5252' }
    }
  ]
});

watch(() => [props.history, props.forecast], () => {
  if (!props.history) return;

  const dates = [];
  const historyData = [];
  const forecastData = [];

  // 1. Заполняем исторические данные
  props.history.forEach(h => {
    const label = `${h.year} Q${h.quarter}`;
    dates.push(label);
    historyData.push(h.amount);
    forecastData.push(null); // В прошлом прогноза нет
  });

  // 2. Заполняем прогноз
  if (props.forecast && props.forecast.length > 0) {
      props.forecast.forEach((f) => {
         dates.push(f.date); 
         historyData.push(null); // В будущем факта нет
         forecastData.push(f.amount);
      });
  }

  option.value.xAxis.data = dates;
  option.value.series[0].data = historyData;
  option.value.series[1].data = forecastData;
  
}, { immediate: true, deep: true });
</script>

<style scoped>
.chart { height: 100%; width: 100%; }
</style>
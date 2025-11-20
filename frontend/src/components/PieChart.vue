<template>
  <div class="chart-wrapper">
    <v-chart class="chart" :option="option" autoresize />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { PieChart } from 'echarts/charts';
import { TooltipComponent, LegendComponent } from 'echarts/components';
import VChart from 'vue-echarts';

use([CanvasRenderer, PieChart, TooltipComponent, LegendComponent]);
const props = defineProps(['chartData']);

const option = ref({
  tooltip: { trigger: 'item', formatter: '{b}: {c} млн ({d}%)' },
  legend: { 
    bottom: '0%', 
    left: 'center', 
    itemWidth: 10, 
    itemHeight: 10,
    textStyle: { fontSize: 11 } // Уменьшили шрифт легенды
  },
  series: [
    {
      name: 'Источник',
      type: 'pie',
      radius: ['40%', '60%'], // Уменьшили внешний радиус, чтобы влезло
      center: ['50%', '45%'], // Чуть подняли вверх, чтобы освободить место легенде
      avoidLabelOverlap: true,
      itemStyle: { borderRadius: 5, borderColor: '#fff', borderWidth: 2 },
      label: { show: false }, // Скрыли выноски, чтобы не перекрывали
      data: []
    }
  ]
});

watch(() => props.chartData, (newData) => {
  if (newData) option.value.series[0].data = newData;
}, { deep: true });
</script>

<style scoped>
.chart-wrapper { height: 280px; width: 100%; }
.chart { height: 100%; width: 100%; }
</style>
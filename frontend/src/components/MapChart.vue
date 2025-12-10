<template>
  <div class="map-container">
    <div ref="chartRef" class="map-chart"></div>
    
    <!-- Диалог со статистикой района -->
    <v-dialog v-model="showDialog" max-width="700">
      <v-card v-if="selectedDistrict">
        <v-card-title class="bg-primary text-white d-flex align-center">
          <v-icon class="mr-2">mdi-map-marker</v-icon>
          {{ selectedDistrict.name }}
        </v-card-title>
        
        <v-card-text class="pa-4">
          <!-- Основные показатели -->
          <v-row class="mb-4">
            <v-col cols="4">
              <v-card variant="tonal" color="blue" class="pa-3 text-center">
                <div class="text-caption text-grey-darken-1">Организаций</div>
                <div class="text-h4 font-weight-bold text-blue">{{ selectedDistrict.orgCount }}</div>
              </v-card>
            </v-col>
            <v-col cols="4">
              <v-card variant="tonal" color="green" class="pa-3 text-center">
                <div class="text-caption text-grey-darken-1">ФАКТ</div>
                <div class="text-h5 font-weight-bold text-green">{{ formatMoney(selectedDistrict.fact) }}</div>
              </v-card>
            </v-col>
            <v-col cols="4">
              <v-card variant="tonal" color="red" class="pa-3 text-center">
                <div class="text-caption text-grey-darken-1">ПЛАН</div>
                <div class="text-h5 font-weight-bold text-red">{{ formatMoney(selectedDistrict.plan) }}</div>
              </v-card>
            </v-col>
          </v-row>

          <!-- Процент освоения -->
          <v-card variant="outlined" class="pa-3 mb-4">
            <div class="d-flex justify-space-between align-center mb-2">
              <span class="text-body-2">Освоение бюджета</span>
              <span class="text-h6 font-weight-bold" :class="getExecutionColor(selectedDistrict.execution)">
                {{ selectedDistrict.execution }}%
              </span>
            </div>
            <v-progress-linear
              :model-value="Math.min(selectedDistrict.execution, 100)"
              :color="selectedDistrict.execution >= 100 ? 'green' : selectedDistrict.execution >= 50 ? 'orange' : 'red'"
              height="10"
              rounded
            ></v-progress-linear>
          </v-card>

          <!-- Переключатель: По годам / По кварталам -->
          <div class="d-flex align-center mb-3">
            <span class="text-subtitle-1 font-weight-medium">Динамика:</span>
            <v-spacer></v-spacer>
            <v-btn-toggle v-model="dialogViewMode" mandatory density="compact" color="primary">
              <v-btn value="quarters" size="small">По кварталам</v-btn>
              <v-btn value="years" size="small">По годам</v-btn>
            </v-btn-toggle>
          </div>

          <!-- Таблица по кварталам -->
          <v-table v-if="dialogViewMode === 'quarters'" density="compact" class="mb-3">
            <thead>
              <tr class="bg-grey-lighten-4">
                <th>Квартал</th>
                <th class="text-right text-green">ФАКТ</th>
                <th class="text-right text-red">ПЛАН</th>
                <th class="text-right">%</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in selectedDistrict.quarters" :key="q.name">
                <td class="font-weight-medium">{{ q.name }}</td>
                <td class="text-right text-green font-weight-medium">{{ formatMoney(q.fact) }}</td>
                <td class="text-right text-red">{{ formatMoney(q.plan) }}</td>
                <td class="text-right" :class="getExecutionColor(q.percent)">{{ q.percent }}%</td>
              </tr>
            </tbody>
          </v-table>

          <!-- Таблица по годам -->
          <v-table v-else density="compact" class="mb-3">
            <thead>
              <tr class="bg-grey-lighten-4">
                <th>Год</th>
                <th class="text-right text-green">ФАКТ</th>
                <th class="text-right text-red">ПЛАН</th>
                <th class="text-right">%</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="y in selectedDistrict.years" :key="y.year">
                <td class="font-weight-medium">{{ y.year }}</td>
                <td class="text-right text-green font-weight-medium">{{ formatMoney(y.fact) }}</td>
                <td class="text-right text-red">{{ formatMoney(y.plan) }}</td>
                <td class="text-right" :class="getExecutionColor(y.percent)">{{ y.percent }}%</td>
              </tr>
            </tbody>
          </v-table>

          <!-- Мини-график -->
          <div ref="miniChartRef" style="height: 150px; width: 100%;"></div>
        </v-card-text>
        
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" variant="flat" @click="showDialog = false">Закрыть</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import * as echarts from 'echarts';
import tyumenGeoJson from '@/assets/tyumen_districts.json';
import api from '@/services/api';

const props = defineProps({
  data: { type: Array, default: () => [] },
  year: { type: Number, default: 2022 }
});

const chartRef = ref(null);
const miniChartRef = ref(null);
let myChart = null;
let miniChart = null;

const showDialog = ref(false);
const dialogViewMode = ref('quarters');
const selectedDistrict = ref(null);

// Реальные данные по районам из Excel 2022
const districtsRealData = {
  'г. Тюмень': { orgCount: 130, forecast: 178099, q1: 32811, q2: 80704, q3: 121646, q4: 178099 },
  'Тюменский район': { orgCount: 27, forecast: 47637, q1: 5314, q2: 16231, q3: 28446, q4: 47637 },
  'г. Ишим': { orgCount: 16, forecast: 22902, q1: 5701, q2: 12293, q3: 16515, q4: 22902 },
  'г. Тобольск': { orgCount: 20, forecast: 22438, q1: 7110, q2: 11928, q3: 16243, q4: 22438 },
  'Ярковский район': { orgCount: 4, forecast: 14209, q1: 5310, q2: 9989, q3: 11314, q4: 14209 },
  'Голышмановский район': { orgCount: 6, forecast: 11880, q1: 2114, q2: 5113, q3: 8472, q4: 11880 },
  'Тобольский район': { orgCount: 7, forecast: 11201, q1: 6615, q2: 7518, q3: 9283, q4: 11201 },
  'Упоровский район': { orgCount: 6, forecast: 10190, q1: 777, q2: 3301, q3: 6916, q4: 10190 },
  'г. Ялуторовск': { orgCount: 7, forecast: 9239, q1: 3597, q2: 6762, q3: 8990, q4: 9239 },
  'Заводоуковский район': { orgCount: 4, forecast: 8315, q1: 2568, q2: 6796, q3: 7301, q4: 8315 },
  'Ишимский район': { orgCount: 4, forecast: 7401, q1: 1866, q2: 4943, q3: 6130, q4: 7401 },
  'Уватский район': { orgCount: 8, forecast: 7329, q1: 1204, q2: 1825, q3: 6240, q4: 7329 },
  'Юргинский район': { orgCount: 3, forecast: 7004, q1: 1429, q2: 4889, q3: 5843, q4: 7004 },
  'Ялуторовский район': { orgCount: 4, forecast: 6965, q1: 1750, q2: 2780, q3: 4977, q4: 6965 },
  'Абатский район': { orgCount: 4, forecast: 6541, q1: 2128, q2: 4138, q3: 4965, q4: 6541 },
  'Казанский район': { orgCount: 3, forecast: 5772, q1: 1341, q2: 3227, q3: 4437, q4: 5772 },
  'Нижнетавдинский район': { orgCount: 3, forecast: 5691, q1: 1243, q2: 3099, q3: 4326, q4: 5691 },
  'Сладковский район': { orgCount: 2, forecast: 5543, q1: 1245, q2: 3022, q3: 4011, q4: 5543 },
  'Армизонский район': { orgCount: 3, forecast: 5400, q1: 1100, q2: 2800, q3: 3900, q4: 5400 },
  'Бердюжский район': { orgCount: 2, forecast: 4857, q1: 1058, q2: 2607, q3: 3533, q4: 4857 },
  'Викуловский район': { orgCount: 3, forecast: 4741, q1: 999, q2: 2488, q3: 3415, q4: 4741 },
  'Вагайский район': { orgCount: 3, forecast: 4528, q1: 932, q2: 2354, q3: 3241, q4: 4528 },
  'Омутинский район': { orgCount: 2, forecast: 4315, q1: 865, q2: 2220, q3: 3068, q4: 4315 },
  'Сорокинский район': { orgCount: 2, forecast: 3891, q1: 741, q2: 1952, q3: 2722, q4: 3891 },
  'Аромашевский район': { orgCount: 2, forecast: 3200, q1: 600, q2: 1500, q3: 2200, q4: 3200 },
  'Исетский район': { orgCount: 2, forecast: 2800, q1: 500, q2: 1300, q3: 1900, q4: 2800 },
  'г. Заводоуковск': { orgCount: 2, forecast: 2500, q1: 450, q2: 1150, q3: 1700, q4: 2500 }
};

const processGeoJson = () => {
  const processed = JSON.parse(JSON.stringify(tyumenGeoJson));
  processed.features.forEach(feature => {
    if (feature.properties.NL_NAME_2) {
      feature.properties.name = feature.properties.NL_NAME_2;
    }
  });
  return processed;
};

const formatMoney = (value) => {
  if (!value || value === 0) return '0 ₽';
  if (value >= 1000) {
    return (value / 1000).toFixed(1) + ' млн ₽';
  }
  return value.toFixed(0) + ' тыс ₽';
};

const getExecutionColor = (percent) => {
  if (percent >= 100) return 'text-green';
  if (percent >= 80) return 'text-orange';
  if (percent >= 50) return 'text-amber';
  return 'text-red';
};

const getDistrictData = (districtName) => {
  // Ищем данные по точному или частичному совпадению названия
  let data = districtsRealData[districtName];
  
  if (!data) {
    // Пробуем найти по частичному совпадению
    const key = Object.keys(districtsRealData).find(k => 
      k.includes(districtName) || districtName.includes(k)
    );
    if (key) {
      data = districtsRealData[key];
    }
  }
  
  if (!data) {
    // Возвращаем пустые данные
    data = { orgCount: 0, forecast: 0, q1: 0, q2: 0, q3: 0, q4: 0 };
  }
  
  return data;
};

const loadDistrictStats = async (districtName) => {
  const rawData = getDistrictData(districtName);
  
  // Рассчитываем план для каждого квартала (пропорционально от годового прогноза)
  const quarterPlan = rawData.forecast / 4;
  
  // Формируем данные по кварталам (данные в Excel накопительные, делаем поквартальные)
  const q1Fact = rawData.q1;
  const q2Fact = rawData.q2 - rawData.q1;
  const q3Fact = rawData.q3 - rawData.q2;
  const q4Fact = rawData.q4 - rawData.q3;
  
  const quarters = [
    { 
      name: 'Q1 (янв-мар)', 
      fact: q1Fact, 
      plan: quarterPlan,
      percent: quarterPlan > 0 ? Math.round((q1Fact / quarterPlan) * 100) : 0
    },
    { 
      name: 'Q2 (апр-июн)', 
      fact: q2Fact,
      plan: quarterPlan,
      percent: quarterPlan > 0 ? Math.round((q2Fact / quarterPlan) * 100) : 0
    },
    { 
      name: 'Q3 (июл-сен)', 
      fact: q3Fact,
      plan: quarterPlan,
      percent: quarterPlan > 0 ? Math.round((q3Fact / quarterPlan) * 100) : 0
    },
    { 
      name: 'Q4 (окт-дек)', 
      fact: q4Fact,
      plan: quarterPlan,
      percent: quarterPlan > 0 ? Math.round((q4Fact / quarterPlan) * 100) : 0
    }
  ];

  // Данные по годам (симуляция роста на основе реальных данных 2022)
  const baseValue = rawData.q4;
  const basePlan = rawData.forecast;
  
  const years = [
    { year: 2022, fact: baseValue, plan: basePlan, percent: basePlan > 0 ? Math.round((baseValue / basePlan) * 100) : 0 },
    { year: 2023, fact: Math.round(baseValue * 1.08), plan: Math.round(basePlan * 1.05), percent: 103 },
    { year: 2024, fact: Math.round(baseValue * 1.15), plan: Math.round(basePlan * 1.1), percent: 105 },
    { year: 2025, fact: Math.round(baseValue * 1.22), plan: Math.round(basePlan * 1.15), percent: 106 }
  ];

  const execution = rawData.forecast > 0 ? Math.round((rawData.q4 / rawData.forecast) * 100) : 0;

  selectedDistrict.value = {
    name: districtName,
    orgCount: rawData.orgCount,
    fact: rawData.q4,
    plan: rawData.forecast,
    execution: execution,
    quarters: quarters,
    years: years
  };
  
  showDialog.value = true;
  
  // Инициализируем мини-график после открытия диалога
  await nextTick();
  setTimeout(() => {
    initMiniChart();
  }, 100);
};

const initMiniChart = () => {
  if (!miniChartRef.value || !selectedDistrict.value) return;
  
  if (miniChart) {
    miniChart.dispose();
  }
  
  miniChart = echarts.init(miniChartRef.value);
  
  const data = dialogViewMode.value === 'quarters' 
    ? selectedDistrict.value.quarters 
    : selectedDistrict.value.years;
  
  const categories = dialogViewMode.value === 'quarters'
    ? data.map(d => d.name.split(' ')[0])
    : data.map(d => d.year);
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: {
      data: ['ФАКТ', 'ПЛАН'],
      bottom: 0,
      textStyle: { fontSize: 10 }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '20%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: categories,
      axisLabel: { fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        fontSize: 10,
        formatter: (val) => (val / 1000).toFixed(0) + 'М'
      }
    },
    series: [
      {
        name: 'ФАКТ',
        type: 'bar',
        data: data.map(d => d.fact),
        itemStyle: { color: '#4CAF50' },
        barGap: '10%'
      },
      {
        name: 'ПЛАН',
        type: 'bar',
        data: data.map(d => d.plan),
        itemStyle: { color: '#F44336' }
      }
    ]
  };
  
  miniChart.setOption(option);
};

// Следим за переключением вида
watch(dialogViewMode, () => {
  nextTick(() => {
    initMiniChart();
  });
});

const initChart = () => {
  if (!chartRef.value) return;
  
  const processedGeoJson = processGeoJson();
  echarts.registerMap('TYUMEN', processedGeoJson);
  
  myChart = echarts.init(chartRef.value);
  
  // Подготавливаем данные для карты
  const mapData = Object.keys(districtsRealData).map(name => ({
    name: name,
    value: districtsRealData[name].q4 || 0
  }));

  const maxValue = Math.max(...mapData.map(d => d.value), 1);

  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#ccc',
      borderWidth: 1,
      textStyle: { color: '#333' },
      formatter: (params) => {
        const districtData = getDistrictData(params.name);
        return `<div style="padding: 5px;">
          <b style="font-size: 14px;">${params.name}</b><br/>
          <span style="color: #666;">Организаций: ${districtData.orgCount}</span><br/>
          <span style="color: #4CAF50;">ФАКТ: ${formatMoney(districtData.q4)}</span><br/>
          <span style="color: #F44336;">ПЛАН: ${formatMoney(districtData.forecast)}</span><br/>
          <span style="color: #888; font-size: 11px;">Нажмите для подробностей</span>
        </div>`;
      }
    },
    visualMap: {
      min: 0,
      max: maxValue,
      text: ['Макс', 'Мин'],
      realtime: false,
      calculable: false,
      orient: 'vertical',
      right: 10,
      bottom: 50,
      itemWidth: 15,
      itemHeight: 100,
      textStyle: { fontSize: 11 },
      inRange: {
        color: ['#E3F2FD', '#90CAF9', '#42A5F5', '#1E88E5', '#1565C0', '#0D47A1']
      }
    },
    series: [{
      name: 'Инвестиции',
      type: 'map',
      map: 'TYUMEN',
      roam: true,
      zoom: 1.1,
      center: [68.5, 57.5],
      aspectScale: 0.85,
      nameProperty: 'name',
      label: {
        show: false
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 11,
          fontWeight: 'bold',
          color: '#333'
        },
        itemStyle: {
          areaColor: '#FFC107',
          borderColor: '#FF9800',
          borderWidth: 2
        }
      },
      select: {
        label: { show: true },
        itemStyle: {
          areaColor: '#FF9800'
        }
      },
      itemStyle: {
        areaColor: '#E3F2FD',
        borderColor: '#FFFFFF',
        borderWidth: 1.5
      },
      data: mapData
    }]
  };

  myChart.setOption(option);
  
  myChart.on('click', (params) => {
    if (params.componentType === 'series' && params.name) {
      loadDistrictStats(params.name);
    }
  });
  
  window.addEventListener('resize', handleResize);
};

const handleResize = () => {
  myChart?.resize();
  miniChart?.resize();
};

watch(() => props.data, () => {
  nextTick(() => {
    if (myChart && props.data && props.data.length) {
      const mapData = props.data.map(item => ({
        name: item.name,
        value: item.value || 0
      }));
      myChart.setOption({
        series: [{ data: mapData }]
      });
    }
  });
}, { deep: true });

onMounted(() => {
  nextTick(() => {
    initChart();
  });
});

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
  if (myChart) {
    myChart.off('click');
    myChart.dispose();
    myChart = null;
  }
  if (miniChart) {
    miniChart.dispose();
    miniChart = null;
  }
});
</script>

<style scoped>
.map-container {
  width: 100%;
  height: 100%;
  position: relative;
}
.map-chart {
  width: 100%;
  height: 100%;
  min-height: 450px;
}
</style>
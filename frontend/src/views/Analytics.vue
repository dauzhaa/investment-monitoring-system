<template>
  <v-container>
    <h1 class="text-h4 font-weight-bold mb-4">Аналитика</h1>

    <!-- Выбор года -->
    <v-row class="mb-4">
      <v-col cols="12" md="3">
        <v-select
          v-model="selectedYear"
          :items="availableYears"
          label="Год"
          variant="outlined"
          density="comfortable"
          prepend-inner-icon="mdi-calendar"
        ></v-select>
      </v-col>
    </v-row>

    <v-row>
      <!-- Топ районов -->
      <v-col cols="12" md="6">
        <v-card class="fill-height">
          <v-card-title>Топ-5 районов по инвестициям ({{ selectedYear }})</v-card-title>
          <v-list>
            <v-list-item v-for="(item, i) in topDistricts" :key="i">
              <template v-slot:prepend>
                <v-avatar :color="getRankColor(i)" class="text-white" size="36">
                  {{ i + 1 }}
                </v-avatar>
              </template>
              <v-list-item-title class="font-weight-medium">{{ item.name }}</v-list-item-title>
              <v-list-item-subtitle>
                <span class="text-green font-weight-bold">{{ formatMoney(item.value) }} млн ₽</span>
              </v-list-item-subtitle>
              <template v-slot:append>
                <v-progress-linear
                  :model-value="(item.value / maxDistrictValue) * 100"
                  :color="getRankColor(i)"
                  height="8"
                  rounded
                  style="width: 100px;"
                ></v-progress-linear>
              </template>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>

      <!-- График по годам (кликабельный) -->
      <v-col cols="12" md="6">
        <v-card class="fill-height">
          <v-card-title>
            Динамика инвестиций по годам
            <v-chip class="ml-2" size="small" color="info">Кликните на год</v-chip>
          </v-card-title>
          <v-card-text style="height: 300px;">
            <v-chart class="chart" :option="yearlyChartOption" autoresize @click="onYearClick" />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Квартальная диаграмма -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title>
            Инвестиции по кварталам за {{ selectedYear }} год
            <v-spacer></v-spacer>
            <v-chip color="green" size="small" class="mr-2">
              <v-icon start size="small">mdi-circle</v-icon>
              ФАКТ
            </v-chip>
            <v-chip color="red" size="small">
              <v-icon start size="small">mdi-circle</v-icon>
              ПЛАН
            </v-chip>
          </v-card-title>
          <v-card-text style="height: 350px;">
            <v-chart class="chart" :option="quarterlyChartOption" autoresize />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Сравнительная таблица по годам -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title>Сравнение показателей по годам</v-card-title>
          <v-data-table
            :headers="comparisonHeaders"
            :items="yearlyComparison"
            :items-per-page="5"
            class="elevation-0"
          >
            <template v-slot:item.fact="{ item }">
              <span class="text-green font-weight-bold">{{ formatMoney(item.fact) }} млн ₽</span>
            </template>
            <template v-slot:item.plan="{ item }">
              <span class="text-red">{{ formatMoney(item.plan) }} млн ₽</span>
            </template>
            <template v-slot:item.execution="{ item }">
              <v-chip :color="item.execution >= 80 ? 'green' : item.execution >= 50 ? 'orange' : 'red'" size="small">
                {{ item.execution }}%
              </v-chip>
            </template>
            <template v-slot:item.growth="{ item }">
              <span :class="item.growth >= 0 ? 'text-green' : 'text-red'">
                {{ item.growth >= 0 ? '+' : '' }}{{ item.growth }}%
              </span>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import VChart from 'vue-echarts';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { BarChart, LineChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components';
import axios from 'axios';

use([CanvasRenderer, BarChart, LineChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent]);

// Состояние
const currentYear = new Date().getFullYear();
const selectedYear = ref(currentYear);

// Данные
const topDistricts = ref([]);
const yearlyData = ref([]);
const quarterlyData = ref([]);

const availableYears = computed(() => {
  const years = [];
  for (let y = currentYear; y >= 2022; y--) {
    years.push(y);
  }
  return years;
});

// Максимальное значение для прогресс-бара
const maxDistrictValue = computed(() => {
  if (topDistricts.value.length === 0) return 1;
  return Math.max(...topDistricts.value.map(d => d.value));
});

// Заголовки сравнительной таблицы
const comparisonHeaders = [
  { title: 'Год', key: 'year', sortable: true },
  { title: 'ФАКТ', key: 'fact', sortable: true },
  { title: 'ПЛАН', key: 'plan', sortable: true },
  { title: 'Выполнение', key: 'execution', sortable: true },
  { title: 'Рост к пред. году', key: 'growth', sortable: true }
];

// Сравнение по годам
const yearlyComparison = computed(() => {
  return yearlyData.value.map((item, index) => {
    const prev = index > 0 ? yearlyData.value[index - 1].fact : item.fact;
    const growth = prev > 0 ? Math.round(((item.fact - prev) / prev) * 100) : 0;
    return {
      year: item.year,
      fact: item.fact,
      plan: item.plan,
      execution: item.plan > 0 ? Math.round((item.fact / item.plan) * 100) : 0,
      growth: growth
    };
  });
});

// График по годам
const yearlyChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['ФАКТ', 'ПЛАН'], bottom: 0 },
  grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
  xAxis: {
    type: 'category',
    data: yearlyData.value.map(y => y.year.toString()),
    axisLabel: {
      formatter: (val) => val,
      fontWeight: 'bold'
    }
  },
  yAxis: { 
    type: 'value',
    axisLabel: { formatter: (val) => `${(val / 1000).toFixed(0)} млн` }
  },
  series: [
    {
      name: 'ФАКТ',
      type: 'bar',
      data: yearlyData.value.map(y => y.fact),
      itemStyle: { color: '#4CAF50' },
      barWidth: '25%'
    },
    {
      name: 'ПЛАН',
      type: 'bar',
      data: yearlyData.value.map(y => y.plan),
      itemStyle: { color: '#F44336' },
      barWidth: '25%'
    }
  ]
}));

// График по кварталам
const quarterlyChartOption = computed(() => ({
  title: { 
    text: `Квартальные данные за ${selectedYear.value} год`,
    left: 'center',
    textStyle: { fontSize: 14 }
  },
  tooltip: { trigger: 'axis' },
  legend: { data: ['ФАКТ', 'ПЛАН'], bottom: 0 },
  grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
  xAxis: {
    type: 'category',
    data: [
      '1 квартал\n(янв-мар)',
      '2 квартал\n(апр-июн)',
      '3 квартал\n(июл-сен)',
      '4 квартал\n(окт-дек)'
    ]
  },
  yAxis: { 
    type: 'value',
    axisLabel: { formatter: (val) => `${(val / 1000).toFixed(0)} млн` }
  },
  series: [
    {
      name: 'ФАКТ',
      type: 'bar',
      data: quarterlyData.value.map(q => q.fact),
      itemStyle: { color: '#4CAF50' },
      barWidth: '30%',
      label: {
        show: true,
        position: 'top',
        formatter: (params) => `${(params.value / 1000).toFixed(1)}м`
      }
    },
    {
      name: 'ПЛАН',
      type: 'bar',
      data: quarterlyData.value.map(q => q.plan),
      itemStyle: { color: '#F44336' },
      barWidth: '30%'
    }
  ]
}));

// Методы
const formatMoney = (value) => {
  if (!value) return '0';
  return (value / 1000).toFixed(1);
};

const getRankColor = (index) => {
  const colors = ['amber-darken-2', 'grey', 'brown', 'blue-grey', 'blue-grey-lighten-2'];
  return colors[index] || 'grey';
};

const onYearClick = (params) => {
  if (params.name) {
    const clickedYear = parseInt(params.name);
    if (!isNaN(clickedYear)) {
      selectedYear.value = clickedYear;
    }
  }
};

const fetchData = async () => {
  // Загрузка топ районов
  try {
    const trendsRes = await axios.get(`/api/v1/analytics/trends?year=${selectedYear.value}`);
    if (trendsRes.data) {
      topDistricts.value = trendsRes.data.rating || [];
      
      // Данные по годам
      if (trendsRes.data.history) {
        yearlyData.value = trendsRes.data.history.map(h => ({
          year: h.year,
          fact: h.amount || 0,
          plan: h.forecast || h.amount * 1.2 || 0
        }));
      }
    }
  } catch (e) {
    console.log('Using mock analytics data');
    topDistricts.value = [
      { name: 'г. Тюмень', value: 8500 },
      { name: 'Тюменский район', value: 4500 },
      { name: 'Тобольский район', value: 3200 },
      { name: 'г. Тобольск', value: 2800 },
      { name: 'Ишимский район', value: 2100 }
    ];
    
    yearlyData.value = [
      { year: 2022, fact: 120000, plan: 150000 },
      { year: 2023, fact: 135000, plan: 160000 },
      { year: 2024, fact: 154000, plan: 180000 },
      { year: 2025, fact: 80000, plan: 200000 }
    ];
  }

  // Загрузка квартальных данных
  try {
    const quarterRes = await axios.get(`/api/v1/analytics/quarters?year=${selectedYear.value}`);
    if (quarterRes.data) {
      quarterlyData.value = quarterRes.data;
    }
  } catch (e) {
    console.log('Using mock quarterly data');
    // Заглушка для квартальных данных
    const yearData = yearlyData.value.find(y => y.year === selectedYear.value);
    const totalFact = yearData?.fact || 100000;
    const totalPlan = yearData?.plan || 120000;
    
    quarterlyData.value = [
      { quarter: 1, fact: totalFact * 0.2, plan: totalPlan * 0.25 },
      { quarter: 2, fact: totalFact * 0.28, plan: totalPlan * 0.25 },
      { quarter: 3, fact: totalFact * 0.32, plan: totalPlan * 0.25 },
      { quarter: 4, fact: totalFact * 0.2, plan: totalPlan * 0.25 }
    ];
  }
};

onMounted(() => {
  fetchData();
});

watch(selectedYear, () => {
  fetchData();
});
</script>

<style scoped>
.chart {
  height: 100%;
  width: 100%;
}
</style>
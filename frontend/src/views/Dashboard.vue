<template>
  <v-container fluid>
    <!-- Заголовок с количеством организаций и датой -->
    <v-row class="mb-4">
      <v-col cols="12">
        <div class="text-h5 font-weight-bold text-grey-darken-2">
          {{ organizationsCount }} организаций на текущую дату ({{ currentDateFormatted }})
        </div>
      </v-col>
    </v-row>

    <!-- Выбор года с сортировкой по убыванию -->
    <v-row class="mb-4">
      <v-col cols="12" md="3">
        <v-select
          v-model="selectedYear"
          :items="availableYears"
          label="Год"
          variant="outlined"
          density="comfortable"
          prepend-inner-icon="mdi-calendar"
          @update:model-value="fetchData"
        ></v-select>
      </v-col>
      <v-col cols="12" md="3">
        <v-btn-toggle v-model="sortOrder" mandatory color="primary" variant="outlined">
          <v-btn value="asc" size="small">
            <v-icon start>mdi-sort-ascending</v-icon>
            сорт ↑
          </v-btn>
          <v-btn value="desc" size="small">
            <v-icon start>mdi-sort-descending</v-icon>
            сорт ↓
          </v-btn>
        </v-btn-toggle>
      </v-col>
    </v-row>

    <!-- Карточки статистики -->
    <v-row>
      <v-col cols="12" md="4">
        <v-card color="primary" dark class="pa-4 rounded-lg">
          <div class="text-subtitle-1">Инвестиции ФАКТ ({{ selectedYear }})</div>
          <div class="text-h4 font-weight-bold">{{ formatMoney(stats.fact_total) }} млн ₽</div>
          <div class="text-caption">ПЛАН: {{ formatMoney(stats.plan_total) }} млн ₽</div>
        </v-card>
      </v-col>
      <v-col cols="12" md="4">
        <v-card class="pa-4 rounded-lg">
          <div class="text-subtitle-1">Освоение бюджета (ФАКТ/ПЛАН)</div>
          <div class="d-flex align-center mt-2">
            <v-progress-linear
              :model-value="stats.execution_percent"
              :color="stats.execution_percent >= 80 ? 'green' : stats.execution_percent >= 50 ? 'orange' : 'red'"
              height="25"
              striped
            >
              <strong>{{ stats.execution_percent }}%</strong>
            </v-progress-linear>
          </div>
        </v-card>
      </v-col>
      <v-col cols="12" md="4">
        <v-card class="pa-4 rounded-lg">
          <div class="text-subtitle-1">Организаций с инвестициями</div>
          <div class="text-h4 font-weight-bold text-green">{{ stats.orgs_with_investments }}</div>
          <div class="text-caption text-red">Без инвестиций: {{ stats.orgs_without_investments }}</div>
        </v-card>
      </v-col>
    </v-row>

    <!-- Графики -->
    <v-row class="mt-4">
      <!-- Столбчатая диаграмма по годам -->
      <v-col cols="12" md="8">
        <v-card class="rounded-lg fill-height">
          <v-card-title class="d-flex align-center">
            <span>Количество инвестиций за {{ selectedYear }} год</span>
            <v-spacer></v-spacer>
            <v-btn-toggle v-model="chartView" mandatory color="primary" density="compact">
              <v-btn value="years" size="small">По годам</v-btn>
              <v-btn value="quarters" size="small">По кварталам</v-btn>
            </v-btn-toggle>
          </v-card-title>
          <v-card-text style="height: 400px;">
            <v-chart class="chart" :option="mainChartOption" autoresize @click="onChartClick" />
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Карта районов -->
      <v-col cols="12" md="4">
        <v-card class="rounded-lg fill-height">
          <v-card-title class="text-center">
            <div class="text-subtitle-1 font-weight-bold">Тюменская область</div>
            <div class="text-caption text-grey">Карта районов</div>
          </v-card-title>
          <v-card-text style="height: 380px; padding: 0;">
            <map-chart :year="selectedYear" />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Таблица инвестиций с сортировкой -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card class="rounded-lg">
          <v-card-title>
            Инвестиции по организациям ({{ selectedYear }})
            <v-spacer></v-spacer>
            <v-text-field
              v-model="search"
              append-inner-icon="mdi-magnify"
              label="Поиск"
              single-line
              hide-details
              density="compact"
              variant="outlined"
              style="max-width: 300px;"
            ></v-text-field>
          </v-card-title>
          <v-data-table
            :headers="tableHeaders"
            :items="sortedInvestments"
            :search="search"
            :items-per-page="10"
            class="elevation-0"
          >
            <template v-slot:item.fact_amount="{ item }">
              <span :class="item.fact_amount > 0 ? 'text-green' : 'text-red'">
                {{ formatMoney(item.fact_amount) }}
              </span>
            </template>
            <template v-slot:item.plan_amount="{ item }">
              {{ formatMoney(item.plan_amount) }}
            </template>
            <template v-slot:item.execution="{ item }">
              <v-chip 
                :color="item.execution >= 80 ? 'green' : item.execution >= 50 ? 'orange' : 'red'" 
                size="small"
              >
                {{ item.execution }}%
              </v-chip>
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
import MapChart from '@/components/MapChart.vue';
import axios from 'axios';

use([CanvasRenderer, BarChart, LineChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent]);

// Состояние
const currentYear = new Date().getFullYear();
const selectedYear = ref(currentYear);
const sortOrder = ref('desc');
const chartView = ref('years');
const search = ref('');
const organizationsCount = ref(274);

// Данные
const stats = ref({
  fact_total: 0,
  plan_total: 0,
  execution_percent: 0,
  orgs_with_investments: 0,
  orgs_without_investments: 0
});

const yearlyData = ref([]);
const quarterlyData = ref([]);
const investments = ref([]);

// Годы по убыванию (последний год сверху)
const availableYears = computed(() => {
  const years = [];
  for (let y = currentYear; y >= 2022; y--) {
    years.push(y);
  }
  return years;
});

// Текущая дата в формате ДД.ММ.ГГГГ
const currentDateFormatted = computed(() => {
  const now = new Date();
  return now.toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });
});

// Заголовки таблицы
const tableHeaders = [
  { title: 'Организация', key: 'name', sortable: true },
  { title: 'Район', key: 'district', sortable: true },
  { title: 'ФАКТ (тыс. ₽)', key: 'fact_amount', sortable: true },
  { title: 'ПЛАН (тыс. ₽)', key: 'plan_amount', sortable: true },
  { title: 'Выполнение', key: 'execution', sortable: true }
];

// Сортированные инвестиции
const sortedInvestments = computed(() => {
  const data = [...investments.value];
  if (sortOrder.value === 'asc') {
    return data.sort((a, b) => a.fact_amount - b.fact_amount);
  } else {
    return data.sort((a, b) => b.fact_amount - a.fact_amount);
  }
});

// Опции графика
const mainChartOption = computed(() => {
  if (chartView.value === 'quarters') {
    // График по кварталам
    return {
      title: { text: `Инвестиции по кварталам ${selectedYear.value}`, left: 'center', textStyle: { fontSize: 14 } },
      tooltip: { trigger: 'axis' },
      legend: { data: ['ФАКТ', 'ПЛАН'], bottom: 0 },
      grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
      xAxis: {
        type: 'category',
        data: ['1 квартал\n(янв-мар)', '2 квартал\n(апр-июн)', '3 квартал\n(июл-сен)', '4 квартал\n(окт-дек)']
      },
      yAxis: { type: 'value', axisLabel: { formatter: (val) => `${(val / 1000).toFixed(0)} млн` } },
      series: [
        {
          name: 'ФАКТ',
          type: 'bar',
          data: quarterlyData.value.map(q => q.fact),
          itemStyle: { color: '#4CAF50' }, // Зеленый
          barWidth: '30%'
        },
        {
          name: 'ПЛАН',
          type: 'bar',
          data: quarterlyData.value.map(q => q.plan),
          itemStyle: { color: '#F44336' }, // Красный
          barWidth: '30%'
        }
      ]
    };
  } else {
    // График по годам (слева направо столбики)
    return {
      title: { text: 'Динамика инвестиций по годам', left: 'center', textStyle: { fontSize: 14 } },
      tooltip: { trigger: 'axis' },
      legend: { data: ['ФАКТ', 'ПЛАН'], bottom: 0 },
      grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
      xAxis: {
        type: 'category',
        data: yearlyData.value.map(y => y.year.toString())
      },
      yAxis: { type: 'value', axisLabel: { formatter: (val) => `${(val / 1000).toFixed(0)} млн` } },
      series: [
        {
          name: 'ФАКТ',
          type: 'bar',
          data: yearlyData.value.map(y => y.fact),
          itemStyle: { color: '#4CAF50' }, // Зеленый
          barWidth: '30%'
        },
        {
          name: 'ПЛАН',
          type: 'bar',
          data: yearlyData.value.map(y => y.plan),
          itemStyle: { color: '#F44336' }, // Красный  
          barWidth: '30%'
        }
      ]
    };
  }
});

// Форматирование денег
const formatMoney = (value) => {
  if (!value) return '0';
  return (value / 1000).toFixed(1);
};

// Обработка клика по графику годов
const onChartClick = (params) => {
  if (chartView.value === 'years' && params.name) {
    const clickedYear = parseInt(params.name);
    if (!isNaN(clickedYear)) {
      selectedYear.value = clickedYear;
      chartView.value = 'quarters';
    }
  }
};

// Загрузка данных
const fetchData = async () => {
  try {
    // Получение статистики
    const statsRes = await axios.get(`/api/v1/analytics/dashboard?year=${selectedYear.value}`);
    if (statsRes.data) {
      stats.value = {
        fact_total: statsRes.data.factTotal || 0,
        plan_total: statsRes.data.planTotal || statsRes.data.forecastTotal || 0,
        execution_percent: statsRes.data.executionPercent || statsRes.data.budgetExecution || 0,
        orgs_with_investments: statsRes.data.orgsWithInvestments || 0,
        orgs_without_investments: statsRes.data.orgsWithoutInvestments || 0
      };
    }
  } catch (e) {
    console.log('Using mock data for stats');
    // Заглушка
    stats.value = {
      fact_total: 15400000,
      plan_total: 20000000,
      execution_percent: 77,
      orgs_with_investments: 180,
      orgs_without_investments: 94
    };
  }

  try {
    // Получение данных по годам
    const trendsRes = await axios.get('/api/v1/analytics/trends');
    if (trendsRes.data && trendsRes.data.history) {
      yearlyData.value = trendsRes.data.history.map(h => ({
        year: h.year,
        fact: h.amount || 0,
        plan: h.forecast || h.amount * 1.2 || 0
      }));
    }
  } catch (e) {
    console.log('Using mock data for trends');
    yearlyData.value = [
      { year: 2022, fact: 120000, plan: 150000 },
      { year: 2023, fact: 135000, plan: 160000 },
      { year: 2024, fact: 154000, plan: 180000 },
      { year: 2025, fact: 80000, plan: 200000 }
    ];
  }

  // Данные по кварталам (заглушка, надо добавить endpoint)
  quarterlyData.value = [
    { quarter: 1, fact: stats.value.fact_total * 0.2, plan: stats.value.plan_total * 0.25 },
    { quarter: 2, fact: stats.value.fact_total * 0.3, plan: stats.value.plan_total * 0.25 },
    { quarter: 3, fact: stats.value.fact_total * 0.35, plan: stats.value.plan_total * 0.25 },
    { quarter: 4, fact: stats.value.fact_total * 0.15, plan: stats.value.plan_total * 0.25 }
  ];

  // Данные для таблицы (заглушка)
  try {
    const orgsRes = await axios.get(`/api/v1/organizations?year=${selectedYear.value}`);
    if (orgsRes.data) {
      investments.value = orgsRes.data.map(org => ({
        name: org.name,
        district: org.district || org.municipality || 'Не указан',
        fact_amount: org.fact_amount || org.total_investment || 0,
        plan_amount: org.plan_amount || org.forecast || 0,
        execution: org.plan_amount > 0 ? Math.round((org.fact_amount / org.plan_amount) * 100) : 0
      }));
    }
  } catch (e) {
    console.log('Using mock data for investments');
    investments.value = [
      { name: 'ГАОУ ТО "ФМШ"', district: 'г. Тюмень', fact_amount: 3891, plan_amount: 4000, execution: 97 },
      { name: 'ГАПОУ ТО "ГОЛЫШМАНОВСКИЙ АГРОПЕДКОЛЛЕДЖ"', district: 'Голышмановский район', fact_amount: 4978, plan_amount: 5000, execution: 100 },
      { name: 'АНО УМЦ ДПО "СТАТУС"', district: 'г. Тюмень', fact_amount: 2563, plan_amount: 3000, execution: 85 }
    ];
  }

  // Обновление счетчика организаций
  try {
    const countRes = await axios.get('/api/v1/organizations/count');
    if (countRes.data && countRes.data.count) {
      organizationsCount.value = countRes.data.count;
    }
  } catch (e) {
    organizationsCount.value = 274;
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
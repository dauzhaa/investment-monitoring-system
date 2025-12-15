<template>
  <v-container fluid>
    <!-- Заголовок и выбор года -->
    <div class="d-flex align-center mb-6">
      <h1 class="text-h4 font-weight-bold">Главная</h1>
      <v-spacer></v-spacer>
      <v-select
        v-model="selectedYear"
        :items="availableYears"
        label="Год"
        variant="outlined"
        density="compact"
        hide-details
        style="max-width: 120px;"
      ></v-select>
    </div>

    <!-- KPI Cards -->
    <v-row class="mb-4">
      <v-col cols="12" sm="6" lg="3">
        <v-card class="pa-4 rounded-lg kpi-card" elevation="2" height="140">
          <div class="d-flex align-center mb-2">
            <v-icon :color="colors.primary" size="24" class="mr-2">mdi-domain</v-icon>
            <span class="text-body-2 text-grey-darken-1">Всего организаций</span>
          </div>
          <div class="text-h4 font-weight-bold" :style="{ color: colors.primary }">
            {{ currentYearData.organizationCount }}
          </div>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" lg="3">
        <v-card class="pa-4 rounded-lg kpi-card" elevation="2" height="140">
          <div class="d-flex align-center mb-2">
            <v-icon :color="colors.success" size="24" class="mr-2">mdi-currency-rub</v-icon>
            <span class="text-body-2 text-grey-darken-1">Инвестиции за {{ selectedYear }} г.</span>
          </div>
          <div class="text-h5 font-weight-bold mb-1" :style="{ color: colors.success }">
            {{ formatMoney(currentYearData.factTotal) }}
          </div>
          <div class="text-caption text-grey">ФАКТ</div>
          <div class="text-body-2 mt-1" :style="{ color: colors.planText }">
            {{ formatMoney(currentYearData.planTotal) }} <span class="text-grey">ПЛАН</span>
          </div>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" lg="3">
        <v-card class="pa-4 rounded-lg kpi-card" elevation="2" height="140">
          <div class="d-flex align-center mb-2">
            <v-icon :color="colors.accent" size="24" class="mr-2">mdi-chart-pie</v-icon>
            <span class="text-body-2 text-grey-darken-1">Освоение бюджета</span>
          </div>
          <div class="text-h4 font-weight-bold" :style="{ color: getExecutionColor(currentYearData.budgetExecution) }">
            {{ currentYearData.budgetExecution }}%
          </div>
          <v-progress-linear
            :model-value="Math.min(currentYearData.budgetExecution, 100)"
            :color="currentYearData.budgetExecution >= 100 ? colors.success : colors.accent"
            height="6"
            rounded
            class="mt-2"
          ></v-progress-linear>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" lg="3">
        <v-card class="pa-4 rounded-lg kpi-card" elevation="2" height="140">
          <div class="d-flex align-center mb-2">
            <v-icon :color="colors.info" size="24" class="mr-2">mdi-check-decagram</v-icon>
            <span class="text-body-2 text-grey-darken-1">Сдача отчётов</span>
          </div>
          <div class="d-flex align-center">
            <v-progress-circular
              :model-value="currentYearData.dataQuality"
              :size="60"
              :width="6"
              :color="colors.info"
            >
              <span class="text-body-1 font-weight-bold">{{ currentYearData.dataQuality }}%</span>
            </v-progress-circular>
            <div class="ml-3">
              <div class="text-caption text-grey-darken-1">
                {{ currentYearData.orgsWithData }} из {{ currentYearData.organizationCount }}
              </div>
              <div class="text-caption text-grey">отчитались</div>
            </div>
          </div>
        </v-card>
      </v-col>
    </v-row>

    <!-- Динамика по годам -->
    <v-row class="mb-4">
      <v-col cols="12">
        <v-card class="rounded-lg" elevation="2">
          <v-card-title class="d-flex align-center">
            <span>Динамика инвестиций по годам (2022–2025)</span>
            <v-spacer></v-spacer>
            <v-btn variant="outlined" size="small" :color="colors.primary" @click="exportYearlyReport">
              <v-icon size="18" class="mr-1">mdi-download</v-icon>
              Выгрузить
            </v-btn>
          </v-card-title>
          <v-card-text style="height: 300px;">
            <v-chart class="chart" :option="yearlyChartOption" autoresize />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Кварталы + Карта -->
    <v-row>
      <v-col cols="12" md="6">
        <v-card class="rounded-lg fill-height" elevation="2">
          <v-card-title>Инвестиции по кварталам {{ selectedYear }} г.</v-card-title>
          <v-card-text style="height: 380px;">
            <v-chart class="chart" :option="quarterlyChartOption" autoresize />
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card class="rounded-lg fill-height" elevation="2">
          <v-card-title class="d-flex align-center">
            <span>Интерактивная карта Тюменской области</span>
            <v-spacer></v-spacer>
            <v-btn variant="outlined" size="small" :color="colors.primary" @click="exportDistrictsReport">
              <v-icon size="18" class="mr-1">mdi-download</v-icon>
              По районам
            </v-btn>
          </v-card-title>
          <v-card-text style="height: 420px; padding: 8px;">
            <map-chart 
              :data="currentMapData" 
              :selected-year="selectedYear"
              @district-click="openDistrictDialog" 
            />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Диалог района -->
    <v-dialog v-model="districtDialog" max-width="650">
      <v-card class="rounded-lg">
        <v-card-title class="py-4 px-6" :style="{ backgroundColor: colors.primary }">
          <div class="d-flex align-center justify-space-between w-100">
            <div class="d-flex align-center">
              <v-icon color="white" class="mr-3" size="28">mdi-map-marker</v-icon>
              <div>
                <div class="text-h6 text-white font-weight-bold">{{ selectedDistrict.name }}</div>
                <div class="text-caption text-white" style="opacity: 0.8;">{{ selectedYear }} год</div>
              </div>
            </div>
            <v-btn icon variant="text" color="white" @click="districtDialog = false">
              <v-icon>mdi-close</v-icon>
            </v-btn>
          </div>
        </v-card-title>
        
        <v-card-text class="pa-6">
          <!-- Основная статистика -->
          <v-row class="mb-4">
            <v-col cols="4">
              <div class="text-center pa-3 rounded-lg" style="background: #E8F5E9;">
                <div class="text-h5 font-weight-bold" style="color: #2E7D32;">
                  {{ formatMoneyShort(selectedDistrict.fact) }}
                </div>
                <div class="text-caption text-grey-darken-1">ФАКТ</div>
              </div>
            </v-col>
            <v-col cols="4">
              <div class="text-center pa-3 rounded-lg" style="background: #E3F2FD;">
                <div class="text-h5 font-weight-bold" style="color: #1565C0;">
                  {{ formatMoneyShort(selectedDistrict.plan) }}
                </div>
                <div class="text-caption text-grey-darken-1">ПЛАН</div>
              </div>
            </v-col>
            <v-col cols="4">
              <div class="text-center pa-3 rounded-lg" style="background: #FFF3E0;">
                <div class="text-h5 font-weight-bold" style="color: #E65100;">
                  {{ selectedDistrict.orgCount }}
                </div>
                <div class="text-caption text-grey-darken-1">Организаций</div>
              </div>
            </v-col>
          </v-row>

          <!-- Освоение -->
          <div class="mb-4">
            <div class="d-flex justify-space-between mb-1">
              <span class="text-body-2">Освоение бюджета</span>
              <span class="text-body-2 font-weight-bold" :style="{ color: getExecutionColor(selectedDistrict.execution) }">
                {{ selectedDistrict.execution }}%
              </span>
            </div>
            <v-progress-linear
              :model-value="Math.min(selectedDistrict.execution, 100)"
              :color="getExecutionColor(selectedDistrict.execution)"
              height="8"
              rounded
            ></v-progress-linear>
          </div>

          <!-- По кварталам -->
          <div class="text-subtitle-2 mb-2 font-weight-bold">По кварталам</div>
          <v-row dense>
            <v-col v-for="q in 4" :key="q" cols="3">
              <div 
                class="text-center pa-2 rounded" 
                :style="{ 
                  background: getQuarterBg(q),
                  border: '1px solid ' + getQuarterBorder(q)
                }"
              >
                <div class="text-caption font-weight-bold mb-1">Q{{ q }}</div>
                <div class="text-caption" style="color: #2E7D32;">
                  {{ formatMoneyShort(getQuarterFact(q)) }}
                </div>
                <div class="text-caption text-grey">
                  {{ formatMoneyShort(getQuarterPlan(q)) }}
                </div>
              </div>
            </v-col>
          </v-row>
        </v-card-text>

        <v-card-actions class="px-6 pb-4">
          <v-btn variant="outlined" :color="colors.primary" @click="exportDistrictReport(selectedDistrict.name)">
            <v-icon class="mr-1">mdi-download</v-icon>
            Скачать отчёт
          </v-btn>
          <v-spacer></v-spacer>
          <v-btn color="grey" variant="text" @click="districtDialog = false">Закрыть</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { BarChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components';
import VChart from 'vue-echarts';
import MapChart from '@/components/MapChart.vue';
import api from '@/services/api';

use([CanvasRenderer, BarChart, GridComponent, TooltipComponent, LegendComponent]);

// НОВЫЕ ЦВЕТА - СОЧЕТАЮТСЯ С СИНИМ, БЕЛЫМ, ЗЕЛЁНЫМ
const colors = {
  primary: '#5C6BC0',    // Сине-фиолетовый (основной)
  success: '#26A69A',    // Бирюзовый/зелёный для ФАКТ
  plan: '#90CAF9',       // Светло-голубой для ПЛАН (сочетается с синим!)
  planText: '#1976D2',   // Синий для текста ПЛАН
  accent: '#FFCA28',     // Жёлтый
  info: '#42A5F5',       // Голубой
  warning: '#FF8A65'     // Оранжевый
};

const selectedYear = ref(2025);
const availableYears = [2025, 2024, 2023, 2022];

const districtDialog = ref(false);
const selectedDistrict = ref({});
const snackbar = ref({ show: false, text: '', color: 'success' });

// Mock данные по годам
const mockDataByYear = {
  2022: {
    organizationCount: 274,
    factTotal: 390509000,
    planTotal: 393401000,
    budgetExecution: 99.3,
    dataQuality: 95,
    orgsWithData: 260,
    quarters: [
      { quarter: 'Q1', fact: 78102000, plan: 98350000 },
      { quarter: 'Q2', fact: 109342000, plan: 98350000 },
      { quarter: 'Q3', fact: 124982000, plan: 98350000 },
      { quarter: 'Q4', fact: 78083000, plan: 98351000 }
    ]
  },
  2023: {
    organizationCount: 274,
    factTotal: 420000000,
    planTotal: 410000000,
    budgetExecution: 102.4,
    dataQuality: 96,
    orgsWithData: 263,
    quarters: [
      { quarter: 'Q1', fact: 84000000, plan: 102500000 },
      { quarter: 'Q2', fact: 117600000, plan: 102500000 },
      { quarter: 'Q3', fact: 134400000, plan: 102500000 },
      { quarter: 'Q4', fact: 84000000, plan: 102500000 }
    ]
  },
  2024: {
    organizationCount: 274,
    factTotal: 450000000,
    planTotal: 440000000,
    budgetExecution: 102.3,
    dataQuality: 97,
    orgsWithData: 266,
    quarters: [
      { quarter: 'Q1', fact: 90000000, plan: 110000000 },
      { quarter: 'Q2', fact: 126000000, plan: 110000000 },
      { quarter: 'Q3', fact: 144000000, plan: 110000000 },
      { quarter: 'Q4', fact: 90000000, plan: 110000000 }
    ]
  },
  2025: {
    organizationCount: 274,
    factTotal: 384379000,
    planTotal: 470000000,
    budgetExecution: 81.8,
    dataQuality: 57,
    orgsWithData: 156,
    quarters: [
      { quarter: 'Q1', fact: 96095000, plan: 117500000 },
      { quarter: 'Q2', fact: 134533000, plan: 117500000 },
      { quarter: 'Q3', fact: 153751000, plan: 117500000 },
      { quarter: 'Q4', fact: 0, plan: 117500000 }
    ]
  }
};

const districtsByYear = {
  2022: [
    { name: 'Тюмень', fact: 169154000, plan: 170000000, orgCount: 89 },
    { name: 'Тюменский район', fact: 51465000, plan: 52000000, orgCount: 28 },
    { name: 'Ишим', fact: 22902000, plan: 23000000, orgCount: 12 },
    { name: 'Тобольск', fact: 19551000, plan: 20000000, orgCount: 18 },
    { name: 'Тобольский район', fact: 15641000, plan: 16000000, orgCount: 14 },
    { name: 'Ишимский район', fact: 14500000, plan: 15000000, orgCount: 15 },
    { name: 'Ялуторовск', fact: 11731000, plan: 12000000, orgCount: 8 },
    { name: 'Ялуторовский район', fact: 9773000, plan: 10000000, orgCount: 7 },
    { name: 'Заводоуковск', fact: 8500000, plan: 9000000, orgCount: 6 },
    { name: 'Голышмановский район', fact: 6500000, plan: 7000000, orgCount: 5 },
    { name: 'Исетский район', fact: 5864000, plan: 6000000, orgCount: 5 },
    { name: 'Уватский район', fact: 5500000, plan: 5800000, orgCount: 5 },
    { name: 'Нижнетавдинский район', fact: 4886000, plan: 5000000, orgCount: 4 },
    { name: 'Упоровский район', fact: 4500000, plan: 4700000, orgCount: 4 },
    { name: 'Армизонский район', fact: 3909000, plan: 4000000, orgCount: 4 },
    { name: 'Аромашевский район', fact: 3500000, plan: 3700000, orgCount: 4 },
    { name: 'Бердюжский район', fact: 3421000, plan: 3500000, orgCount: 4 },
    { name: 'Вагайский район', fact: 3200000, plan: 3400000, orgCount: 4 },
    { name: 'Викуловский район', fact: 2932000, plan: 3000000, orgCount: 3 },
    { name: 'Абатский район', fact: 2800000, plan: 3000000, orgCount: 3 },
    { name: 'Казанский район', fact: 2443000, plan: 2600000, orgCount: 3 },
    { name: 'Омутинский район', fact: 2200000, plan: 2400000, orgCount: 3 },
    { name: 'Сладковский район', fact: 1954000, plan: 2100000, orgCount: 2 },
    { name: 'Сорокинский район', fact: 1800000, plan: 2000000, orgCount: 2 },
    { name: 'Юргинский район', fact: 1466000, plan: 1600000, orgCount: 3 },
    { name: 'Ярковский район', fact: 977000, plan: 1100000, orgCount: 2 }
  ],
  2023: [],
  2024: [],
  2025: []
};

[2023, 2024, 2025].forEach(year => {
  const coef = year === 2023 ? 1.08 : year === 2024 ? 1.15 : 0.98;
  districtsByYear[year] = districtsByYear[2022].map(d => ({
    ...d,
    fact: Math.round(d.fact * coef * (year === 2025 ? 0.75 : 1)),
    plan: Math.round(d.plan * coef)
  }));
});

const allYearsData = [
  { year: 2022, fact: 390509000, plan: 393401000 },
  { year: 2023, fact: 420000000, plan: 410000000 },
  { year: 2024, fact: 450000000, plan: 440000000 },
  { year: 2025, fact: 384379000, plan: 470000000 }
];

const currentYearData = computed(() => mockDataByYear[selectedYear.value] || mockDataByYear[2022]);

const currentMapData = computed(() => {
  const districts = districtsByYear[selectedYear.value] || districtsByYear[2022];
  return districts.map(d => ({ name: d.name, value: d.fact }));
});

// КВАРТАЛЬНЫЙ ГРАФИК - НОВЫЕ ЦВЕТА (ЗЕЛЁНЫЙ + ГОЛУБОЙ)
const quarterlyChartOption = computed(() => {
  const qData = currentYearData.value.quarters;
  return {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        let result = `<strong>${params[0].name} ${selectedYear.value}</strong><br/>`;
        params.forEach(p => {
          result += `${p.marker} ${p.seriesName}: ${formatMoney(p.value)}<br/>`;
        });
        return result;
      }
    },
    legend: { data: ['ФАКТ', 'ПЛАН'], bottom: 0 },
    grid: { left: '3%', right: '4%', bottom: '15%', top: '10%', containLabel: true },
    xAxis: { type: 'category', data: qData.map(d => d.quarter) },
    yAxis: { type: 'value', axisLabel: { formatter: v => (v / 1000000).toFixed(0) + 'М' } },
    series: [
      { 
        name: 'ФАКТ', 
        type: 'bar', 
        data: qData.map(d => d.fact), 
        itemStyle: { color: '#26A69A', borderRadius: [4, 4, 0, 0] },  // Бирюзовый/зелёный
        barGap: '20%' 
      },
      { 
        name: 'ПЛАН', 
        type: 'bar', 
        data: qData.map(d => d.plan), 
        itemStyle: { color: '#90CAF9', borderRadius: [4, 4, 0, 0] }  // Светло-голубой!
      }
    ]
  };
});

// ГОДОВОЙ ГРАФИК - НОВЫЕ ЦВЕТА (ЗЕЛЁНЫЙ + ГОЛУБОЙ)
const yearlyChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    formatter: (params) => {
      let result = `<strong>${params[0].name} год</strong><br/>`;
      params.forEach(p => {
        result += `${p.marker} ${p.seriesName}: ${formatMoney(p.value)}<br/>`;
      });
      return result;
    }
  },
  legend: { data: ['ФАКТ', 'ПЛАН'], bottom: 0 },
  grid: { left: '3%', right: '4%', bottom: '15%', top: '10%', containLabel: true },
  xAxis: { type: 'category', data: allYearsData.map(d => d.year) },
  yAxis: { type: 'value', axisLabel: { formatter: v => (v / 1000000).toFixed(0) + 'М' } },
  series: [
    { 
      name: 'ФАКТ', 
      type: 'bar', 
      data: allYearsData.map(d => d.fact), 
      itemStyle: { color: '#26A69A', borderRadius: [4, 4, 0, 0] },  // Бирюзовый/зелёный
      barGap: '20%' 
    },
    { 
      name: 'ПЛАН', 
      type: 'bar', 
      data: allYearsData.map(d => d.plan), 
      itemStyle: { color: '#90CAF9', borderRadius: [4, 4, 0, 0] }  // Светло-голубой!
    }
  ]
}));

const formatMoney = (value) => {
  if (!value) return '0 ₽';
  const millions = value / 1000000;
  if (millions >= 1) return millions.toFixed(1).replace(/\.0$/, '') + ' млн ₽';
  const thousands = value / 1000;
  if (thousands >= 1) return thousands.toFixed(1) + ' тыс ₽';
  return value.toLocaleString('ru-RU') + ' ₽';
};

const formatMoneyShort = (value) => {
  if (!value) return '—';
  const millions = value / 1000000;
  if (millions >= 1) return millions.toFixed(1) + 'М';
  return (value / 1000).toFixed(0) + 'т';
};

const getExecutionColor = (pct) => {
  if (pct >= 100) return colors.success;
  if (pct >= 80) return colors.accent;
  return colors.warning;
};

const getQuarterBg = (q) => {
  if (selectedYear.value === 2025 && q === 4) return '#F5F5F5';
  return '#FAFAFA';
};

const getQuarterBorder = (q) => {
  if (selectedYear.value === 2025 && q === 4) return '#E0E0E0';
  return '#E8E8E8';
};

const openDistrictDialog = (districtName) => {
  const districts = districtsByYear[selectedYear.value] || districtsByYear[2022];
  const d = districts.find(x => x.name === districtName);
  if (d) {
    selectedDistrict.value = {
      ...d,
      execution: d.plan > 0 ? Math.round((d.fact / d.plan) * 100) : 0
    };
    districtDialog.value = true;
  }
};

const getQuarterFact = (q) => {
  const qData = currentYearData.value.quarters;
  return qData[q - 1]?.fact || 0;
};

const getQuarterPlan = (q) => {
  const qData = currentYearData.value.quarters;
  return qData[q - 1]?.plan || 0;
};

const exportYearlyReport = async () => {
  try {
    const response = await api.get('/reports/export/yearly', { responseType: 'blob' });
    downloadFile(response.data, `yearly_2022-2025.xlsx`);
    showSnackbar('Отчёт выгружен');
  } catch (e) {
    showSnackbar('Ошибка выгрузки', 'error');
  }
};

const exportDistrictsReport = async () => {
  try {
    const response = await api.get('/reports/export/districts', { params: { year: selectedYear.value }, responseType: 'blob' });
    downloadFile(response.data, `districts_${selectedYear.value}.xlsx`);
    showSnackbar('Отчёт выгружен');
  } catch (e) {
    showSnackbar('Ошибка выгрузки', 'error');
  }
};

const exportDistrictReport = async (name) => {
  try {
    const response = await api.get('/reports/export/district', { params: { year: selectedYear.value, district: name }, responseType: 'blob' });
    downloadFile(response.data, `${name}_${selectedYear.value}.xlsx`);
    showSnackbar('Отчёт выгружен');
  } catch (e) {
    showSnackbar('Ошибка выгрузки', 'error');
  }
};

const downloadFile = (data, filename) => {
  const url = window.URL.createObjectURL(new Blob([data]));
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
};

const showSnackbar = (text, color = 'success') => {
  snackbar.value = { show: true, text, color };
};

onMounted(() => {});
</script>

<style scoped>
.chart { height: 100%; width: 100%; }
.kpi-card { transition: transform 0.2s, box-shadow 0.2s; }
.kpi-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important; }
.w-100 { width: 100%; }
</style>
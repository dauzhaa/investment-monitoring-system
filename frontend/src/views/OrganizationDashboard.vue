<template>
  <v-container fluid>
    <!-- Заголовок -->
    <div class="d-flex align-center mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold">{{ organization.name }}</h1>
        <div class="text-body-2 text-grey">ИНН: {{ organization.inn }} | {{ organization.district }}</div>
      </div>
      <v-spacer></v-spacer>
      <v-select
        v-model="selectedYear"
        :items="availableYears"
        label="Год"
        variant="outlined"
        density="compact"
        hide-details
        style="max-width: 120px;"
        @update:model-value="loadData"
      ></v-select>
    </div>

    <!-- KPI для организации -->
    <v-row class="mb-4">
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 rounded-lg" elevation="2" height="130">
          <div class="d-flex align-center mb-2">
            <v-icon color="#26A69A" size="24" class="mr-2">mdi-currency-rub</v-icon>
            <span class="text-body-2 text-grey-darken-1">Инвестиции ФАКТ</span>
          </div>
          <div class="text-h4 font-weight-bold" style="color: #26A69A;">
            {{ formatMoney(orgStats.fact) }}
          </div>
          <div class="text-caption text-grey">за {{ selectedYear }} год</div>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 rounded-lg" elevation="2" height="130">
          <div class="d-flex align-center mb-2">
            <v-icon color="#FF8A65" size="24" class="mr-2">mdi-target</v-icon>
            <span class="text-body-2 text-grey-darken-1">Инвестиции ПЛАН</span>
          </div>
          <div class="text-h4 font-weight-bold" style="color: #FF8A65;">
            {{ formatMoney(orgStats.plan) }}
          </div>
          <div class="text-caption text-grey">за {{ selectedYear }} год</div>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 rounded-lg" elevation="2" height="130">
          <div class="d-flex align-center mb-2">
            <v-icon color="#FFCA28" size="24" class="mr-2">mdi-percent</v-icon>
            <span class="text-body-2 text-grey-darken-1">Освоение бюджета</span>
          </div>
          <div class="text-h4 font-weight-bold" :style="{ color: getExecutionColor(orgStats.execution) }">
            {{ orgStats.execution }}%
          </div>
          <v-progress-linear
            :model-value="Math.min(orgStats.execution, 100)"
            :color="orgStats.execution >= 100 ? '#26A69A' : '#FFCA28'"
            height="6"
            rounded
            class="mt-2"
          ></v-progress-linear>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 rounded-lg" elevation="2" height="130">
          <div class="d-flex align-center mb-2">
            <v-icon color="#42A5F5" size="24" class="mr-2">mdi-file-document-check</v-icon>
            <span class="text-body-2 text-grey-darken-1">Статус отчётности</span>
          </div>
          <v-chip
            :color="orgStats.status === 'submitted' ? 'success' : orgStats.status === 'overdue' ? 'error' : 'grey'"
            size="large"
            class="mt-2"
          >
            {{ getStatusText(orgStats.status) }}
          </v-chip>
        </v-card>
      </v-col>
    </v-row>

    <!-- Графики -->
    <v-row>
      <!-- Инвестиции по кварталам -->
      <v-col cols="12" md="6">
        <v-card class="rounded-lg" elevation="2">
          <v-card-title>Инвестиции по кварталам {{ selectedYear }} г.</v-card-title>
          <v-card-text style="height: 300px;">
            <v-chart class="chart" :option="quarterlyChartOption" autoresize />
          </v-card-text>
        </v-card>
      </v-col>

      <!-- История по годам -->
      <v-col cols="12" md="6">
        <v-card class="rounded-lg" elevation="2">
          <v-card-title>История инвестиций</v-card-title>
          <v-card-text style="height: 300px;">
            <v-chart class="chart" :option="yearlyChartOption" autoresize />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Таблица отчётов -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card class="rounded-lg" elevation="2">
          <v-card-title class="d-flex align-center">
            <span>История отчётов</span>
            <v-spacer></v-spacer>
            <v-btn color="#5C6BC0" variant="flat" @click="uploadDialog = true">
              <v-icon class="mr-2">mdi-upload</v-icon>
              Загрузить отчёт
            </v-btn>
          </v-card-title>
          <v-data-table
            :headers="tableHeaders"
            :items="reports"
            class="elevation-0"
          >
            <template v-slot:item.status="{ item }">
              <v-chip
                :color="item.status === 'accepted' ? 'success' : item.status === 'pending' ? 'warning' : 'error'"
                size="small"
              >
                {{ item.status === 'accepted' ? 'Принят' : item.status === 'pending' ? 'На проверке' : 'Отклонён' }}
              </v-chip>
            </template>
            <template v-slot:item.actions="{ item }">
              <v-btn icon size="small" variant="text" @click="downloadReport(item)">
                <v-icon>mdi-download</v-icon>
              </v-btn>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>

    <!-- Диалог загрузки -->
    <v-dialog v-model="uploadDialog" max-width="500">
      <v-card>
        <v-card-title class="bg-primary text-white">
          Загрузка отчёта
        </v-card-title>
        <v-card-text class="pa-4">
          <v-select
            v-model="uploadQuarter"
            :items="quarters"
            label="Квартал"
            variant="outlined"
            class="mb-4"
          ></v-select>
          <v-file-input
            v-model="uploadFile"
            label="Выберите файл"
            accept=".xlsx,.xls,.pdf"
            variant="outlined"
            prepend-icon="mdi-file-upload"
          ></v-file-input>
          <v-alert v-if="uploadFile && uploadFile.name?.endsWith('.pdf')" type="info" variant="tonal" class="mt-2">
            PDF файлы проверяются на наличие печати и подписи
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="uploadDialog = false">Отмена</v-btn>
          <v-btn color="primary" variant="flat" @click="submitReport" :loading="uploading">
            Загрузить
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import VChart from 'vue-echarts';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { BarChart, LineChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components';

use([CanvasRenderer, BarChart, LineChart, GridComponent, TooltipComponent, LegendComponent]);

const selectedYear = ref(2022);
const availableYears = [2025, 2024, 2023, 2022];

// Данные организации (пример - МАОУ СОШ №1 г. Тюмень)
const organization = ref({
  id: 1,
  name: 'МАОУ СОШ №1 г. Тюмени',
  inn: '7203123456',
  district: 'г. Тюмень',
  okved: '85.14',
  is_smp: false
});

const orgStats = ref({
  fact: 2500000,
  plan: 2800000,
  execution: 89.3,
  status: 'submitted'
});

const quarterlyChartOption = ref({});
const yearlyChartOption = ref({});

const tableHeaders = [
  { title: 'Период', key: 'period' },
  { title: 'Дата загрузки', key: 'date' },
  { title: 'Статус', key: 'status' },
  { title: 'Сумма, тыс. ₽', key: 'amount' },
  { title: '', key: 'actions', sortable: false }
];

const reports = ref([
  { id: 1, period: 'Q1 2022', date: '15.04.2022', status: 'accepted', amount: 500 },
  { id: 2, period: 'Q2 2022', date: '18.07.2022', status: 'accepted', amount: 700 },
  { id: 3, period: 'Q3 2022', date: '12.10.2022', status: 'accepted', amount: 800 },
  { id: 4, period: 'Q4 2022', date: '20.01.2023', status: 'accepted', amount: 500 },
]);

const uploadDialog = ref(false);
const uploadQuarter = ref('Q1');
const uploadFile = ref(null);
const uploading = ref(false);
const quarters = ['Q1', 'Q2', 'Q3', 'Q4', 'Годовой'];

const formatMoney = (value) => {
  if (!value) return '0 ₽';
  if (value >= 1000000) return (value / 1000000).toFixed(1) + ' млн ₽';
  if (value >= 1000) return (value / 1000).toFixed(0) + ' тыс ₽';
  return value + ' ₽';
};

const getExecutionColor = (pct) => {
  if (pct >= 100) return '#26A69A';
  if (pct >= 80) return '#FFCA28';
  return '#FF8A65';
};

const getStatusText = (status) => {
  const map = { submitted: 'Сдан', overdue: 'Просрочен', not_planned: 'Не запланировано' };
  return map[status] || status;
};

const loadData = () => {
  // Квартальный график
  quarterlyChartOption.value = {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: ['Q1', 'Q2', 'Q3', 'Q4'] },
    yAxis: { type: 'value', axisLabel: { formatter: v => (v/1000) + 'т' } },
    series: [
      { name: 'ФАКТ', type: 'bar', data: [500000, 700000, 800000, 500000], itemStyle: { color: '#26A69A' } },
      { name: 'ПЛАН', type: 'bar', data: [700000, 700000, 700000, 700000], itemStyle: { color: '#FF8A65' } }
    ]
  };

  // Годовой график
  yearlyChartOption.value = {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: ['2022', '2023', '2024', '2025'] },
    yAxis: { type: 'value', axisLabel: { formatter: v => (v/1000000).toFixed(1) + 'М' } },
    series: [
      { name: 'Инвестиции', type: 'line', data: [2500000, 2800000, 3100000, 2400000], 
        itemStyle: { color: '#5C6BC0' }, areaStyle: { color: 'rgba(92,107,192,0.2)' } }
    ]
  };
};

const submitReport = async () => {
  uploading.value = true;
  // Имитация загрузки
  setTimeout(() => {
    uploading.value = false;
    uploadDialog.value = false;
    reports.value.unshift({
      id: reports.value.length + 1,
      period: `${uploadQuarter.value} ${selectedYear.value}`,
      date: new Date().toLocaleDateString('ru-RU'),
      status: 'pending',
      amount: 0
    });
  }, 1500);
};

const downloadReport = (item) => {
  console.log('Download:', item);
};

onMounted(() => {
  loadData();
});
</script>

<style scoped>
.chart { height: 100%; width: 100%; }
</style>
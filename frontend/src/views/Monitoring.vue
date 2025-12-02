<template>
  <v-container>
    <h1 class="text-h4 font-weight-bold mb-4">Мониторинг сдачи</h1>

    <v-card class="mb-4 pa-4">
      <v-row align="center">
        <v-col cols="12" md="2">
          <v-select
            v-model="selectedYear"
            :items="availableYears"
            label="Год"
            hide-details
            density="compact"
            @update:model-value="loadData"
          ></v-select>
        </v-col>
        <v-col cols="12" md="2">
          <v-select
            v-model="selectedPeriod"
            :items="periodItems"
            item-title="title"
            item-value="value"
            label="Период"
            hide-details
            density="compact"
            @update:model-value="loadData"
          ></v-select>
        </v-col>
        <v-col cols="12" md="3">
          <v-btn
            color="primary"
            prepend-icon="mdi-download"
            @click="downloadReport"
            :loading="downloading"
          >
            СКАЧАТЬ СВОД (EXCEL)
          </v-btn>
        </v-col>
        <v-spacer></v-spacer>
        <v-col cols="12" md="3" class="text-right">
          <v-chip color="primary" variant="outlined" class="mr-2">
            Всего: {{ summary.total }}
          </v-chip>
          <v-chip color="success" variant="flat">
            Сдано: {{ summary.submitted }} ({{ summary.percent }}%)
          </v-chip>
        </v-col>
      </v-row>
    </v-card>

    <v-data-table
      :headers="headers"
      :items="organizations"
      :loading="loading"
      :search="search"
      items-per-page="15"
      class="elevation-1"
    >
      <template v-slot:top>
        <v-text-field
          v-model="search"
          label="Поиск организации..."
          prepend-inner-icon="mdi-magnify"
          variant="outlined"
          density="compact"
          hide-details
          class="ma-4"
          style="max-width: 400px"
        ></v-text-field>
      </template>

      <template v-slot:item.status="{ item }">
        <v-chip :color="getStatusColor(item.status)" size="small" variant="flat">
          {{ getStatusText(item.status) }}
        </v-chip>
      </template>

      <template v-slot:item.actions="{ item }">
        <v-btn
          v-if="isSubmitted(item.status)"
          icon size="small" color="primary" variant="text"
          @click="viewReport(item)" title="Просмотреть отчет"
        >
          <v-icon>mdi-eye</v-icon>
        </v-btn>
        <v-btn
          v-else
          icon size="small" color="warning" variant="text"
          @click="remindOrg(item)" title="Напомнить"
        >
          <v-icon>mdi-bell-ring</v-icon>
        </v-btn>
      </template>
    </v-data-table>

    <v-dialog v-model="remindDialog" max-width="500">
      <v-card>
        <v-card-title>Отправить напоминание</v-card-title>
        <v-card-text>
          Отправить напоминание о необходимости сдать отчет для организации
          <strong>{{ selectedOrg?.name }}</strong>?
          <br><br>
          Email: {{ selectedOrg?.email || 'Не указан' }}
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="remindDialog = false">Отмена</v-btn>
          <v-btn color="warning" @click="sendReminder" :loading="sending">Отправить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar" :color="snackbarColor" timeout="3000">
      {{ snackbarText }}
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import api from '@/services/api';

const loading = ref(false);
const downloading = ref(false);
const sending = ref(false);
const search = ref('');
const organizations = ref([]);
const summary = ref({ total: 0, submitted: 0, percent: 0 });

const currentYear = new Date().getFullYear();
const selectedYear = ref(currentYear);
const selectedPeriod = ref('year');

const availableYears = computed(() => {
  const years = [];
  for (let y = 2022; y <= currentYear; y++) years.push(y);
  return years;
});

const periodItems = [
  { title: 'Весь год', value: 'year' },
  { title: '1 квартал', value: 1 },
  { title: '2 квартал', value: 2 },
  { title: '3 квартал', value: 3 },
  { title: '4 квартал', value: 4 }
];

const remindDialog = ref(false);
const selectedOrg = ref(null);
const snackbar = ref(false);
const snackbarText = ref('');
const snackbarColor = ref('success');

const headers = [
  { title: 'Организация', key: 'name', sortable: true },
  { title: 'ИНН', key: 'inn', sortable: true },
  { title: 'Район', key: 'municipality', sortable: true },
  { title: 'Статус', key: 'status', sortable: true },
  { title: 'Действия', key: 'actions', sortable: false, align: 'center' }
];

const getStatusColor = (status) => {
  const s = status?.toLowerCase();
  if (s === 'submitted' || s === 'сдан') return 'success';
  if (s === 'overdue' || s === 'просрочен') return 'error';
  return 'grey';
};

const getStatusText = (status) => {
  const s = status?.toLowerCase();
  if (s === 'submitted' || s === 'сдан') return 'Сдан';
  if (s === 'overdue' || s === 'просрочен') return 'Просрочен';
  return status || 'Неизвестно';
};

const isSubmitted = (status) => {
  const s = status?.toLowerCase();
  return s === 'submitted' || s === 'сдан';
};

const loadData = async () => {
  loading.value = true;
  try {
    const params = { year: selectedYear.value };
    if (selectedPeriod.value !== 'year') params.quarter = selectedPeriod.value;

    const response = await api.get('/monitoring/status', { params });
    organizations.value = response.data.items || [];
    summary.value = {
      total: response.data.total || 0,
      submitted: response.data.submitted || 0,
      percent: response.data.percent || 0
    };
  } catch (error) {
    console.error('Ошибка загрузки:', error);
    showMessage('Ошибка загрузки данных', 'error');
  } finally {
    loading.value = false;
  }
};

const downloadReport = async () => {
  downloading.value = true;
  try {
    const params = { year: selectedYear.value };
    params.quarter = selectedPeriod.value === 'year' ? 0 : selectedPeriod.value;

    const response = await api.get('/monitoring/export', { params, responseType: 'blob' });

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    const periodName = selectedPeriod.value === 'year' ? 'год' : `Q${selectedPeriod.value}`;
    link.setAttribute('download', `monitoring_${selectedYear.value}_${periodName}.xlsx`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);

    showMessage('Отчет успешно скачан', 'success');
  } catch (error) {
    console.error('Ошибка скачивания:', error);
    showMessage('Ошибка скачивания отчета', 'error');
  } finally {
    downloading.value = false;
  }
};

const viewReport = (item) => {
  showMessage(`Просмотр отчета: ${item.name}`, 'info');
};

const remindOrg = (item) => {
  selectedOrg.value = item;
  remindDialog.value = true;
};

const sendReminder = async () => {
  sending.value = true;
  try {
    await api.post('/monitoring/remind', null, {
      params: {
        year: selectedYear.value,
        quarter: selectedPeriod.value === 'year' ? null : selectedPeriod.value,
        organization_id: selectedOrg.value.id
      }
    });
    remindDialog.value = false;
    showMessage(`Напоминание отправлено для ${selectedOrg.value.name}`, 'success');
  } catch (error) {
    console.error('Ошибка:', error);
    showMessage('Ошибка отправки напоминания', 'error');
  } finally {
    sending.value = false;
  }
};

const showMessage = (text, color = 'success') => {
  snackbarText.value = text;
  snackbarColor.value = color;
  snackbar.value = true;
};

onMounted(() => { loadData(); });
</script>
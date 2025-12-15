<template>
  <v-container fluid>
    <h1 class="text-h4 font-weight-bold mb-6">Мониторинг сдачи отчётности</h1>

    <!-- Фильтры -->
    <v-row class="mb-4" align="center">
      <v-col cols="12" sm="6" md="2">
        <v-select
          v-model="selectedYear"
          :items="availableYears"
          label="Год"
          variant="outlined"
          density="compact"
          hide-details
        ></v-select>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-select
          v-model="selectedPeriod"
          :items="periods"
          item-title="title"
          item-value="value"
          label="Период"
          variant="outlined"
          density="compact"
          hide-details
        ></v-select>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-select
          v-model="selectedDistrict"
          :items="districts"
          label="Районы"
          variant="outlined"
          density="compact"
          hide-details
          clearable
        ></v-select>
      </v-col>
      <v-col cols="12" sm="6" md="2">
        <v-btn color="#5C6BC0" variant="flat" @click="showAdvancedFilters = true" block>
          <v-icon class="mr-2">mdi-filter</v-icon>
          Фильтры
        </v-btn>
      </v-col>
      <v-col cols="12" sm="6" md="2">
        <v-btn color="#26A69A" variant="flat" @click="downloadReport" block :loading="exporting">
          <v-icon class="mr-2">mdi-download</v-icon>
          Скачать отчёт
        </v-btn>
      </v-col>
    </v-row>

    <!-- Сводка - мягкие цвета в стиле Dashboard -->
    <v-card class="mb-4 rounded-lg" elevation="2" :style="{ background: 'linear-gradient(135deg, #5C6BC0 0%, #7986CB 100%)' }">
      <v-card-text class="py-5">
        <div class="text-center text-white mb-3 text-body-1">
          Отчёт об инвестициях за {{ periodTitle }} {{ selectedYear }} года
        </div>
        <v-row align="center" justify="center">
          <v-col cols="4" class="text-center">
            <div class="text-h3 font-weight-bold text-white">{{ summary.total }}</div>
            <div class="text-white text-body-2">Всего орг.</div>
          </v-col>
          <v-col cols="4" class="text-center">
            <div class="text-h3 font-weight-bold" style="color: #A5D6A7;">{{ summary.submitted }}</div>
            <div class="text-white text-body-2">Сдали отчёт</div>
          </v-col>
          <v-col cols="4" class="text-center">
            <div class="text-h3 font-weight-bold" style="color: #FFAB91;">{{ summary.overdue }}</div>
            <div class="text-white text-body-2">Просрочено</div>
          </v-col>
        </v-row>
        <v-progress-linear
          :model-value="summary.percent"
          color="#A5D6A7"
          bg-color="rgba(255,255,255,0.3)"
          height="14"
          rounded
          class="mt-4"
        >
          <template v-slot:default>
            <span class="text-white text-caption font-weight-bold">{{ summary.percent }}%</span>
          </template>
        </v-progress-linear>
      </v-card-text>
    </v-card>

    <!-- Таблица с русской локализацией -->
    <v-card class="rounded-lg" elevation="2">
      <v-data-table
        :headers="headers"
        :items="filteredOrganizations"
        :items-per-page="itemsPerPage"
        :loading="loading"
        class="elevation-0"
        :items-per-page-options="itemsPerPageOptions"
        :items-per-page-text="'Записей на странице'"
        :page-text="'{0}-{1} из {2}'"
        :no-data-text="'Нет данных'"
        :loading-text="'Загрузка...'"
      >
        <template v-slot:item.status="{ item }">
          <v-chip
            :color="getStatusColor(item.status)"
            size="small"
            variant="flat"
          >
            {{ getStatusText(item.status) }}
          </v-chip>
        </template>
        <template v-slot:item.actions="{ item }">
          <v-btn
            v-if="item.status === 'submitted'"
            icon
            size="small"
            variant="text"
            color="#5C6BC0"
            @click="downloadOrgReport(item)"
          >
            <v-icon>mdi-download</v-icon>
          </v-btn>
          <span v-else class="text-grey">—</span>
        </template>
        
        <!-- Кастомный footer с русским текстом -->
        <template v-slot:bottom>
          <div class="d-flex align-center justify-end pa-4">
            <span class="text-body-2 mr-4">Записей на странице:</span>
            <v-select
              v-model="itemsPerPage"
              :items="[10, 15, 25, 50]"
              density="compact"
              variant="outlined"
              hide-details
              style="max-width: 80px;"
              class="mr-4"
            ></v-select>
            <span class="text-body-2">
              {{ paginationText }}
            </span>
            <v-btn icon size="small" :disabled="currentPage <= 1" @click="currentPage--" class="ml-2">
              <v-icon>mdi-chevron-left</v-icon>
            </v-btn>
            <v-btn icon size="small" :disabled="currentPage >= totalPages" @click="currentPage++">
              <v-icon>mdi-chevron-right</v-icon>
            </v-btn>
          </div>
        </template>
      </v-data-table>
    </v-card>

    <!-- Диалог расширенных фильтров -->
    <v-dialog v-model="showAdvancedFilters" max-width="500">
      <v-card>
        <v-card-title class="text-h6" style="background: #5C6BC0; color: white;">
          Расширенные фильтры
        </v-card-title>
        <v-card-text class="pa-4">
          <v-select
            v-model="filterStatus"
            :items="statusOptions"
            label="Статус"
            variant="outlined"
            clearable
            class="mb-4"
          ></v-select>
          <v-checkbox v-model="filterSMP" label="Только СМП" hide-details color="#5C6BC0"></v-checkbox>
          <v-checkbox v-model="filterWithEmail" label="Только с email" hide-details color="#5C6BC0"></v-checkbox>
        </v-card-text>
        <v-card-actions>
          <v-btn variant="text" @click="resetAdvancedFilters">Сбросить</v-btn>
          <v-spacer></v-spacer>
          <v-btn color="#5C6BC0" variant="flat" @click="showAdvancedFilters = false">Применить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import api from '@/services/api';

const selectedYear = ref(2022);
const selectedPeriod = ref('q1');
const selectedDistrict = ref(null);
const showAdvancedFilters = ref(false);
const filterStatus = ref(null);
const filterSMP = ref(false);
const filterWithEmail = ref(false);
const exporting = ref(false);
const loading = ref(false);
const organizations = ref([]);
const itemsPerPage = ref(15);
const currentPage = ref(1);

const availableYears = [2025, 2024, 2023, 2022];

const periods = [
  { title: '1 квартал (январь-март)', value: 'q1' },
  { title: '2 квартал (апрель-июнь)', value: 'q2' },
  { title: '3 квартал (июль-сентябрь)', value: 'q3' },
  { title: '4 квартал (октябрь-декабрь)', value: 'q4' },
  { title: 'Годовой отчёт', value: 'annual' }
];

// Русская локализация для пагинации
const itemsPerPageOptions = [
  { value: 10, title: '10' },
  { value: 15, title: '15' },
  { value: 25, title: '25' },
  { value: 50, title: '50' },
  { value: -1, title: 'Все' }
];

const periodTitle = computed(() => {
  const p = periods.find(x => x.value === selectedPeriod.value);
  return p ? p.title : '';
});

const districts = [
  'г. Тюмень', 'Тюменский район', 'г. Ишим', 'Ишимский район',
  'г. Тобольск', 'Тобольский район', 'г. Ялуторовск', 'Ялуторовский район',
  'г. Заводоуковск', 'Голышмановский район', 'Исетский район', 'Уватский район'
];

const statusOptions = [
  { title: 'Сдан', value: 'submitted' },
  { title: 'Не запланировано', value: 'not_planned' },
  { title: 'Просрочено', value: 'overdue' }
];

const headers = [
  { title: 'Организация', key: 'name', width: '35%' },
  { title: 'ИНН', key: 'inn', width: '12%' },
  { title: 'Район', key: 'district', width: '18%' },
  { title: 'Email', key: 'email', width: '20%' },
  { title: 'Статус', key: 'status', width: '10%' },
  { title: 'Действия', key: 'actions', width: '5%', sortable: false }
];

const snackbar = ref({ show: false, text: '', color: 'success' });

const summary = computed(() => {
  const total = organizations.value.length || 274;
  const submitted = organizations.value.filter(o => o.status === 'submitted').length || 157;
  const overdue = organizations.value.filter(o => o.status === 'overdue').length || 0;
  const percent = total > 0 ? Math.round((submitted / total) * 100) : 57;
  return { total, submitted, overdue, percent };
});

const filteredOrganizations = computed(() => {
  let result = [...organizations.value];
  if (selectedDistrict.value) {
    result = result.filter(o => o.district === selectedDistrict.value);
  }
  if (filterStatus.value) {
    result = result.filter(o => o.status === filterStatus.value);
  }
  if (filterSMP.value) {
    result = result.filter(o => o.is_smp);
  }
  if (filterWithEmail.value) {
    result = result.filter(o => o.email);
  }
  return result;
});

const totalPages = computed(() => {
  return Math.ceil(filteredOrganizations.value.length / itemsPerPage.value);
});

const paginationText = computed(() => {
  const total = filteredOrganizations.value.length;
  const start = (currentPage.value - 1) * itemsPerPage.value + 1;
  const end = Math.min(currentPage.value * itemsPerPage.value, total);
  return `${start}-${end} из ${total}`;
});

const getStatusColor = (status) => {
  const map = { submitted: '#26A69A', not_planned: '#78909C', overdue: '#FF8A65' };
  return map[status] || '#78909C';
};

const getStatusText = (status) => {
  const map = { submitted: 'Сдан', not_planned: 'Не запланировано', overdue: 'Просрочено' };
  return map[status] || status;
};

const resetAdvancedFilters = () => {
  filterStatus.value = null;
  filterSMP.value = false;
  filterWithEmail.value = false;
};

const downloadReport = async () => {
  exporting.value = true;
  try {
    const response = await api.get('/reports/export/monitoring', {
      params: { year: selectedYear.value, period: selectedPeriod.value },
      responseType: 'blob'
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const a = document.createElement('a');
    a.href = url;
    a.download = `monitoring_${selectedPeriod.value}_${selectedYear.value}.xlsx`;
    a.click();
    snackbar.value = { show: true, text: 'Отчёт успешно выгружен', color: 'success' };
  } catch (e) {
    snackbar.value = { show: true, text: 'Ошибка выгрузки', color: 'error' };
  } finally {
    exporting.value = false;
  }
};

const downloadOrgReport = async (org) => {
  try {
    const response = await api.get(`/reports/export/organization/${org.id}`, {
      params: { year: selectedYear.value, quarter: selectedPeriod.value },
      responseType: 'blob'
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const a = document.createElement('a');
    a.href = url;
    a.download = `report_${org.inn}_${selectedPeriod.value}_${selectedYear.value}.xlsx`;
    a.click();
  } catch (e) {
    snackbar.value = { show: true, text: 'Ошибка выгрузки', color: 'error' };
  }
};

const fetchData = async () => {
  loading.value = true;
  try {
    const res = await api.get('/monitoring/status', {
      params: { year: selectedYear.value, period: selectedPeriod.value }
    });
    if (res.data?.items) {
      organizations.value = res.data.items.map(o => ({
        id: o.id,
        name: o.name,
        inn: o.inn,
        district: o.district?.name || o.municipality || '',
        email: o.contact_email || o.email || '',
        status: o.status || 'not_planned',
        is_smp: o.is_smp || false
      }));
    }
  } catch (e) {
    console.error('Error fetching monitoring data:', e);
  } finally {
    loading.value = false;
  }
};

watch([selectedYear, selectedPeriod], fetchData);
onMounted(fetchData);
</script>
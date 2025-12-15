<template>
  <v-container fluid>
    <h1 class="text-h4 font-weight-bold mb-6">Реестр организаций</h1>

    <!-- Панель фильтров -->
    <v-row class="mb-4" align="center">
      <v-col cols="12" md="5">
        <v-text-field
          v-model="search"
          label="Поиск (ИНН, Название)"
          prepend-inner-icon="mdi-magnify"
          variant="outlined"
          density="compact"
          hide-details
          clearable
        ></v-text-field>
      </v-col>
      <v-col cols="12" md="2">
        <v-select
          v-model="selectedYear"
          :items="availableYears"
          label="Год"
          variant="outlined"
          density="compact"
          hide-details
        ></v-select>
      </v-col>
      <v-col cols="12" md="2">
        <v-btn color="#5C6BC0" variant="flat" @click="showFilters = true" block>
          <v-icon class="mr-2">mdi-filter</v-icon>
          Фильтры
        </v-btn>
      </v-col>
      <v-col cols="12" md="2">
        <v-btn variant="text" color="grey" @click="resetFilters">
          <v-icon class="mr-1">mdi-filter-off</v-icon>
          Сбросить
        </v-btn>
      </v-col>
    </v-row>

    <!-- Таблица -->
    <v-card class="rounded-lg" elevation="2">
      <v-toolbar flat color="white">
        <v-toolbar-title class="text-body-1">
          Найдено: <strong>{{ filteredItems.length }}</strong> организаций
        </v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn-toggle v-model="sortOrder" mandatory variant="outlined" density="compact" class="mr-2">
          <v-btn value="desc" size="small">
            <v-icon size="18">mdi-sort-descending</v-icon>
            СОРТ ↓
          </v-btn>
          <v-btn value="asc" size="small">
            <v-icon size="18">mdi-sort-ascending</v-icon>
            СОРТ ↑
          </v-btn>
        </v-btn-toggle>
      </v-toolbar>

      <v-data-table
        :headers="headers"
        :items="filteredItems"
        :search="search"
        :items-per-page="itemsPerPage"
        :loading="loading"
        class="elevation-0"
      >
        <!-- Наименование с подсветкой СМП -->
        <template v-slot:item.name="{ item }">
          <div class="d-flex align-center">
            <span :class="{ 'text-success font-weight-medium': item.is_smp }">
              {{ item.name }}
            </span>
            <v-chip v-if="item.is_smp" color="success" size="x-small" class="ml-2" variant="flat">
              СМП
            </v-chip>
          </div>
        </template>

        <!-- Район - нормальное отображение -->
        <template v-slot:item.district="{ item }">
          <span>{{ item.district || '—' }}</span>
        </template>

        <!-- ОКВЭД - нормальное отображение -->
        <template v-slot:item.okved="{ item }">
          <span class="text-grey-darken-1">{{ item.okved || '—' }}</span>
        </template>

        <!-- ФАКТ - правильные единицы (тыс. руб, не тыс*1000) -->
        <template v-slot:item.fact_amount="{ item }">
          <span class="text-success font-weight-bold">
            {{ formatMoney(item.fact_amount) }}
          </span>
        </template>

        <!-- ПЛАН -->
        <template v-slot:item.plan_amount="{ item }">
          <span class="text-grey-darken-1">
            {{ formatMoney(item.plan_amount) }}
          </span>
        </template>

        <template v-slot:item.status="{ item }">
          <v-chip :color="getStatusColor(item.status)" size="small" variant="flat">
            {{ getStatusText(item.status) }}
          </v-chip>
        </template>

        <template v-slot:item.actions="{ item }">
          <v-btn icon size="small" variant="text" color="#5C6BC0" @click="viewDetails(item)">
            <v-icon>mdi-eye</v-icon>
          </v-btn>
        </template>
        
        <!-- Кастомный footer с русским текстом -->
        <template v-slot:bottom>
          <div class="d-flex align-center justify-end pa-4">
            <span class="text-body-2 mr-4">Записей на странице:</span>
            <v-select
              v-model="itemsPerPage"
              :items="[10, 15, 25, 50, 100]"
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

    <!-- Диалог расширенных фильтров (без ОКВЭД) -->
    <v-dialog v-model="showFilters" max-width="700">
      <v-card>
        <v-card-title class="text-h6" style="background: #5C6BC0; color: white;">
          Расширенные фильтры
        </v-card-title>
        <v-card-text class="pa-4">
          <!-- Районы (чипсы) -->
          <div class="text-subtitle-2 mb-2">Районы</div>
          <div class="d-flex flex-wrap ga-2 mb-4">
            <v-chip
              v-for="d in allDistricts"
              :key="d"
              :color="selectedDistricts.includes(d) ? '#5C6BC0' : 'grey-lighten-2'"
              :variant="selectedDistricts.includes(d) ? 'flat' : 'outlined'"
              size="small"
              @click="toggleDistrict(d)"
            >
              {{ d }}
            </v-chip>
          </div>

          <v-row>
            <v-col cols="6">
              <v-select
                v-model="filterSMP"
                :items="smpOptions"
                label="Статус СМП"
                variant="outlined"
                density="compact"
                clearable
              ></v-select>
            </v-col>
            <v-col cols="6">
              <v-select
                v-model="filterStatus"
                :items="statusOptions"
                label="Статус отчёта"
                variant="outlined"
                density="compact"
                clearable
              ></v-select>
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="6">
              <v-text-field
                v-model.number="filterMinInvest"
                label="Мин. инвестиции (тыс. ₽)"
                type="number"
                variant="outlined"
                density="compact"
              ></v-text-field>
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model.number="filterMaxInvest"
                label="Макс. инвестиции (тыс. ₽)"
                type="number"
                variant="outlined"
                density="compact"
              ></v-text-field>
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="6">
              <v-select
                v-model="filterEmail"
                :items="emailOptions"
                label="Наличие email"
                variant="outlined"
                density="compact"
                clearable
              ></v-select>
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-btn variant="text" @click="resetAllFilters">Сбросить фильтры</v-btn>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="showFilters = false">Отмена</v-btn>
          <v-btn color="#5C6BC0" variant="flat" @click="applyFilters">Применить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Диалог деталей -->
    <v-dialog v-model="detailsDialog" max-width="600">
      <v-card v-if="selectedOrg">
        <v-card-title class="text-white" style="background: #5C6BC0;">{{ selectedOrg.name }}</v-card-title>
        <v-card-text class="pa-4">
          <v-row>
            <v-col cols="6">
              <p><strong>ИНН:</strong> {{ selectedOrg.inn }}</p>
              <p><strong>Район:</strong> {{ selectedOrg.district || '—' }}</p>
              <p><strong>ОКВЭД:</strong> {{ selectedOrg.okved || '—' }}</p>
            </v-col>
            <v-col cols="6">
              <p><strong>СМП:</strong> {{ selectedOrg.is_smp ? 'Да' : 'Нет' }}</p>
              <p><strong>Email:</strong> {{ selectedOrg.email || 'Не указан' }}</p>
            </v-col>
          </v-row>
          <v-divider class="my-3"></v-divider>
          <v-row>
            <v-col cols="6">
              <p><strong>ФАКТ ({{ selectedYear }}):</strong> 
                <span class="text-success font-weight-bold">{{ formatMoney(selectedOrg.fact_amount) }}</span>
              </p>
            </v-col>
            <v-col cols="6">
              <p><strong>ПЛАН ({{ selectedYear }}):</strong> {{ formatMoney(selectedOrg.plan_amount) }}</p>
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="#5C6BC0" variant="flat" @click="detailsDialog = false">Закрыть</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import api from '@/services/api';

const search = ref('');
const selectedYear = ref(2022);
const sortOrder = ref('desc');
const loading = ref(false);
const items = ref([]);
const showFilters = ref(false);
const detailsDialog = ref(false);
const selectedOrg = ref(null);
const itemsPerPage = ref(15);
const currentPage = ref(1);

// Фильтры
const selectedDistricts = ref([]);
const filterSMP = ref(null);
const filterStatus = ref(null);
const filterMinInvest = ref(null);
const filterMaxInvest = ref(null);
const filterEmail = ref(null);

const availableYears = [2025, 2024, 2023, 2022];

const smpOptions = [
  { title: 'Все организации', value: null },
  { title: 'Только СМП', value: true },
  { title: 'Не СМП', value: false }
];

const statusOptions = [
  { title: 'Все', value: null },
  { title: 'Сдан', value: 'submitted' },
  { title: 'Нет данных', value: 'no_data' },
  { title: 'Просрочено', value: 'overdue' }
];

const emailOptions = [
  { title: 'Все', value: null },
  { title: 'С email', value: true },
  { title: 'Без email', value: false }
];

const allDistricts = ref([
  'г. Тюмень', 'г. Тобольск', 'г. Ишим', 'г. Ялуторовск', 'г. Заводоуковск', 'Абатский район',
  'Армизонский район', 'Аромашевский район', 'Бердюжский район', 'Вагайский район',
  'Викуловский район', 'Голышмановский район', 'Заводоуковский район', 'Исетский район',
  'Ишимский район', 'Казанский район', 'Нижнетавдинский район', 'Омутинский район',
  'Сладковский район', 'Сорокинский район', 'Тобольский район', 'Тюменский район',
  'Уватский район', 'Упоровский район', 'Юргинский район', 'Ярковский район'
]);

// Заголовки таблицы (без СМП столбца!)
const headers = [
  { title: 'Наименование', key: 'name', sortable: true, width: '32%' },
  { title: 'ИНН', key: 'inn', sortable: true, width: '11%' },
  { title: 'Район', key: 'district', sortable: true, width: '15%' },
  { title: 'ОКВЭД', key: 'okved', sortable: true, width: '8%' },
  { title: 'ФАКТ', key: 'fact_amount', sortable: true, width: '12%' },
  { title: 'ПЛАН', key: 'plan_amount', sortable: true, width: '11%' },
  { title: 'Статус', key: 'status', sortable: true, width: '9%' },
  { title: '', key: 'actions', sortable: false, width: '2%' }
];

const filteredItems = computed(() => {
  let result = [...items.value];

  // Фильтр по районам
  if (selectedDistricts.value.length > 0) {
    result = result.filter(item => selectedDistricts.value.includes(item.district));
  }

  // Фильтр по СМП
  if (filterSMP.value !== null) {
    result = result.filter(item => item.is_smp === filterSMP.value);
  }

  // Фильтр по статусу
  if (filterStatus.value) {
    result = result.filter(item => item.status === filterStatus.value);
  }

  // Фильтр по инвестициям
  if (filterMinInvest.value) {
    result = result.filter(item => item.fact_amount >= filterMinInvest.value);
  }
  if (filterMaxInvest.value) {
    result = result.filter(item => item.fact_amount <= filterMaxInvest.value);
  }

  // Фильтр по email
  if (filterEmail.value === true) {
    result = result.filter(item => item.email);
  } else if (filterEmail.value === false) {
    result = result.filter(item => !item.email);
  }

  // Сортировка
  result.sort((a, b) => sortOrder.value === 'asc' ? a.fact_amount - b.fact_amount : b.fact_amount - a.fact_amount);

  return result;
});

const totalPages = computed(() => {
  return Math.ceil(filteredItems.value.length / itemsPerPage.value);
});

const paginationText = computed(() => {
  const total = filteredItems.value.length;
  const start = (currentPage.value - 1) * itemsPerPage.value + 1;
  const end = Math.min(currentPage.value * itemsPerPage.value, total);
  return `${start}-${end} из ${total}`;
});

// ИСПРАВЛЕНО: Правильное форматирование - данные уже в тысячах!
const formatMoney = (value) => {
  if (!value || value === 0) return '0 тыс. ₽';
  // Данные УЖЕ в тысячах рублей, просто форматируем с пробелами
  return value.toLocaleString('ru-RU') + ' тыс. ₽';
};

const getStatusColor = (status) => {
  const map = { 
    submitted: '#26A69A', 
    no_data: '#78909C', 
    overdue: '#FF8A65' 
  };
  return map[status] || '#78909C';
};

const getStatusText = (status) => {
  const map = { 
    submitted: 'Сдан', 
    no_data: 'Нет данных', 
    overdue: 'Просрочено' 
  };
  return map[status] || 'Нет данных';
};

const toggleDistrict = (d) => {
  const idx = selectedDistricts.value.indexOf(d);
  if (idx >= 0) selectedDistricts.value.splice(idx, 1);
  else selectedDistricts.value.push(d);
};

const resetFilters = () => {
  search.value = '';
  selectedDistricts.value = [];
  filterSMP.value = null;
  filterStatus.value = null;
  filterMinInvest.value = null;
  filterMaxInvest.value = null;
  filterEmail.value = null;
};

const resetAllFilters = () => {
  resetFilters();
};

const applyFilters = () => {
  showFilters.value = false;
};

const viewDetails = (item) => {
  selectedOrg.value = item;
  detailsDialog.value = true;
};

// Загрузка данных из БД
const fetchData = async () => {
  loading.value = true;
  try {
    const res = await api.get(`/organizations`, { params: { year: selectedYear.value } });
    if (res.data && Array.isArray(res.data)) {
      items.value = res.data.map(org => ({
        id: org.id,
        name: org.name,
        inn: org.inn,
        district: org.district?.name || org.municipality || '',
        okved: org.okved?.code || org.okved || '',
        is_smp: org.is_smp || false,
        email: org.contact_email || org.email || '',
        // Данные уже приходят в тысячах, не умножаем!
        fact_amount: org.fact_amount || org.total_investment || 0,
        plan_amount: org.plan_amount || org.forecast || 0,
        status: org.status || (org.fact_amount > 0 ? 'submitted' : 'no_data')
      }));
    }
  } catch (e) {
    console.error('Error fetching organizations:', e);
  } finally {
    loading.value = false;
  }
};

watch(selectedYear, fetchData);

onMounted(() => {
  fetchData();
});
</script>

<style scoped>
.v-data-table :deep(th) {
  font-weight: 600 !important;
  color: #555 !important;
}
</style>
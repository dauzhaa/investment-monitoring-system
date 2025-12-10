<template>
  <div>
    <h1 class="text-h4 font-weight-bold mb-6">Реестр организаций</h1>

    <!-- Панель фильтров -->
    <v-card class="mb-4 pa-4" elevation="2">
      <v-row align="center">
        <v-col cols="12" sm="6" md="4">
          <v-text-field
            v-model="search"
            label="Поиск (ИНН, Название)"
            variant="outlined"
            density="compact"
            hide-details
            prepend-inner-icon="mdi-magnify"
            clearable
          ></v-text-field>
        </v-col>
        <v-col cols="12" sm="6" md="2">
          <v-select
            v-model="selectedYear"
            :items="availableYears"
            label="Год"
            variant="outlined"
            density="compact"
            hide-details
            @update:model-value="loadData"
          ></v-select>
        </v-col>
        <v-col cols="auto">
          <v-btn color="primary" variant="outlined" @click="showFilterDialog = true">
            <v-icon start>mdi-filter-variant</v-icon>
            Фильтры
            <v-badge
              v-if="activeFiltersCount > 0"
              :content="activeFiltersCount"
              color="red"
              inline
              class="ml-2"
            quier></v-badge>
          </v-btn>
        </v-col>
        <v-col cols="auto">
          <v-btn variant="text" @click="resetAllFilters" :disabled="activeFiltersCount === 0">
            <v-icon start>mdi-filter-off</v-icon>
            Сбросить
          </v-btn>
        </v-col>
      </v-row>
    </v-card>

    <!-- Результаты -->
    <v-card elevation="2">
      <v-card-title class="d-flex align-center">
        <span>Найдено: {{ filteredOrganizations.length }} организаций</span>
        <v-spacer></v-spacer>
        <v-btn-toggle v-model="sortDirection" mandatory density="compact" color="primary">
          <v-btn value="desc" size="small">
            <v-icon start size="small">mdi-sort-descending</v-icon>
            СОРТ ↓
          </v-btn>
          <v-btn value="asc" size="small">
            <v-icon start size="small">mdi-sort-ascending</v-icon>
            СОРТ ↑
          </v-btn>
        </v-btn-toggle>
      </v-card-title>

      <v-data-table
        :headers="headers"
        :items="filteredOrganizations"
        :items-per-page="10"
        :search="search"
        class="elevation-0"
      >
        <!-- ФАКТ -->
        <template v-slot:item.fact_amount="{ item }">
          <span class="text-green font-weight-medium">
            {{ formatMoney(item.fact_amount) }}
          </span>
        </template>

        <!-- ПЛАН -->
        <template v-slot:item.plan_amount="{ item }">
          <span class="text-grey">
            {{ formatMoney(item.plan_amount) }}
          </span>
        </template>

        <!-- СМП -->
        <template v-slot:item.is_smp="{ item }">
          <v-chip :color="item.is_smp ? 'blue' : 'grey'" size="small" label>
            {{ item.is_smp ? 'Да' : 'Нет' }}
          </v-chip>
        </template>

        <!-- Статус -->
        <template v-slot:item.status="{ item }">
          <v-chip
            :color="item.status === 'submitted' ? 'green' : 'grey'"
            size="small"
            label
          >
            {{ item.status === 'submitted' ? 'Сдан' : 'Нет' }}
          </v-chip>
        </template>

        <!-- Действия -->
        <template v-slot:item.actions="{ item }">
          <v-btn
            icon
            size="small"
            color="primary"
            variant="text"
            @click="showOrgDetails(item)"
          >
            <v-icon>mdi-eye</v-icon>
          </v-btn>
        </template>
      </v-data-table>
    </v-card>

    <!-- Диалог расширенных фильтров -->
    <v-dialog v-model="showFilterDialog" max-width="700">
      <v-card>
        <v-card-title>Расширенные фильтры</v-card-title>
        <v-card-text>
          <v-row>
            <!-- Районы -->
            <v-col cols="12">
              <div class="text-subtitle-2 mb-2">Районы</div>
              <v-chip-group v-model="filters.districts" multiple column>
                <v-chip
                  v-for="district in allDistricts"
                  :key="district"
                  :value="district"
                  filter
                  variant="outlined"
                  size="small"
                >
                  {{ district }}
                </v-chip>
              </v-chip-group>
            </v-col>

            <v-divider class="my-4"></v-divider>

            <!-- Статус СМП -->
            <v-col cols="12" sm="6">
              <v-select
                v-model="filters.smp"
                :items="[
                  { title: 'Все организации', value: null },
                  { title: 'Только СМП', value: true },
                  { title: 'Только не СМП', value: false }
                ]"
                item-title="title"
                item-value="value"
                label="Статус СМП"
                variant="outlined"
                density="compact"
              ></v-select>
            </v-col>

            <!-- Статус отчёта -->
            <v-col cols="12" sm="6">
              <v-select
                v-model="filters.reportStatus"
                :items="[
                  { title: 'Все', value: null },
                  { title: 'Сдали отчёт', value: 'submitted' },
                  { title: 'Не сдали', value: 'not_submitted' }
                ]"
                item-title="title"
                item-value="value"
                label="Статус отчёта"
                variant="outlined"
                density="compact"
              ></v-select>
            </v-col>

            <!-- Диапазон инвестиций -->
            <v-col cols="12" sm="6">
              <v-text-field
                v-model.number="filters.minInvestment"
                label="Мин. инвестиции (тыс. ₽)"
                variant="outlined"
                density="compact"
                type="number"
              ></v-text-field>
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model.number="filters.maxInvestment"
                label="Макс. инвестиции (тыс. ₽)"
                variant="outlined"
                density="compact"
                type="number"
              ></v-text-field>
            </v-col>

            <!-- ОКВЭД -->
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="filters.okved"
                label="ОКВЭД (начинается с)"
                variant="outlined"
                density="compact"
                placeholder="85"
              ></v-text-field>
            </v-col>

            <!-- Наличие email -->
            <v-col cols="12" sm="6">
              <v-select
                v-model="filters.hasEmail"
                :items="[
                  { title: 'Все', value: null },
                  { title: 'С email', value: true },
                  { title: 'Без email', value: false }
                ]"
                item-title="title"
                item-value="value"
                label="Наличие email"
                variant="outlined"
                density="compact"
              ></v-select>
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-btn @click="resetFilters">Сбросить фильтры</v-btn>
          <v-spacer></v-spacer>
          <v-btn variant="text" @click="showFilterDialog = false">Отмена</v-btn>
          <v-btn color="primary" @click="applyFilters">Применить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Диалог деталей организации -->
    <v-dialog v-model="detailsDialog" max-width="600">
      <v-card v-if="selectedOrg">
        <v-card-title>{{ selectedOrg.name }}</v-card-title>
        <v-card-text>
          <v-list>
            <v-list-item>
              <v-list-item-title>ИНН</v-list-item-title>
              <v-list-item-subtitle>{{ selectedOrg.inn }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title>ОКПО</v-list-item-title>
              <v-list-item-subtitle>{{ selectedOrg.okpo || '—' }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title>ОКВЭД</v-list-item-title>
              <v-list-item-subtitle>{{ selectedOrg.okved || '—' }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title>Район</v-list-item-title>
              <v-list-item-subtitle>{{ selectedOrg.district }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title>СМП</v-list-item-title>
              <v-list-item-subtitle>{{ selectedOrg.is_smp ? 'Да' : 'Нет' }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title>Email</v-list-item-title>
              <v-list-item-subtitle>{{ selectedOrg.email || '—' }}</v-list-item-subtitle>
            </v-list-item>
            <v-divider class="my-2"></v-divider>
            <v-list-item>
              <v-list-item-title class="text-green">Инвестиции ФАКТ</v-list-item-title>
              <v-list-item-subtitle class="text-h6 text-green">{{ formatMoney(selectedOrg.fact_amount) }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title class="text-red">Инвестиции ПЛАН</v-list-item-title>
              <v-list-item-subtitle class="text-h6 text-red">{{ formatMoney(selectedOrg.plan_amount) }}</v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="detailsDialog = false">Закрыть</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';

// Состояние
const search = ref('');
const selectedYear = ref(2022);
const sortDirection = ref('desc');
const showFilterDialog = ref(false);
const detailsDialog = ref(false);
const selectedOrg = ref(null);

const availableYears = [2025, 2024, 2023, 2022];

const allDistricts = [
  'г. Тюмень', 'г. Тобольск', 'г. Ишим', 'г. Ялуторовск', 'г. Заводоуковск',
  'Абатский район', 'Армизонский район', 'Аромашевский район', 'Бердюжский район',
  'Вагайский район', 'Викуловский район', 'Голышмановский район', 'Заводоуковский район',
  'Исетский район', 'Ишимский район', 'Казанский район', 'Нижнетавдинский район',
  'Омутинский район', 'Сладковский район', 'Сорокинский район', 'Тобольский район',
  'Тюменский район', 'Уватский район', 'Упоровский район', 'Юргинский район', 'Ярковский район'
];

// Фильтры
const filters = ref({
  districts: [],
  smp: null,
  reportStatus: null,
  minInvestment: null,
  maxInvestment: null,
  okved: '',
  hasEmail: null
});

// Данные
const organizations = ref([]);

// Заголовки таблицы
const headers = [
  { title: 'Наименование', key: 'name', width: '30%' },
  { title: 'ИНН', key: 'inn', width: '12%' },
  { title: 'Район', key: 'district', width: '15%' },
  { title: 'ОКВЭД', key: 'okved', width: '8%' },
  { title: 'СМП', key: 'is_smp', width: '7%', align: 'center' },
  { title: 'ФАКТ', key: 'fact_amount', width: '12%', align: 'end' },
  { title: 'ПЛАН', key: 'plan_amount', width: '10%', align: 'end' },
  { title: 'Статус', key: 'status', width: '8%', align: 'center' },
  { title: '', key: 'actions', width: '5%', sortable: false }
];

// Количество активных фильтров
const activeFiltersCount = computed(() => {
  let count = 0;
  if (filters.value.districts.length > 0) count++;
  if (filters.value.smp !== null) count++;
  if (filters.value.reportStatus !== null) count++;
  if (filters.value.minInvestment) count++;
  if (filters.value.maxInvestment) count++;
  if (filters.value.okved) count++;
  if (filters.value.hasEmail !== null) count++;
  return count;
});

// Отфильтрованные организации
const filteredOrganizations = computed(() => {
  let result = [...organizations.value];
  
  // Фильтр по районам
  if (filters.value.districts.length > 0) {
    result = result.filter(org => filters.value.districts.includes(org.district));
  }
  
  // Фильтр по СМП
  if (filters.value.smp !== null) {
    result = result.filter(org => org.is_smp === filters.value.smp);
  }
  
  // Фильтр по статусу отчёта
  if (filters.value.reportStatus !== null) {
    if (filters.value.reportStatus === 'submitted') {
      result = result.filter(org => org.status === 'submitted');
    } else {
      result = result.filter(org => org.status !== 'submitted');
    }
  }
  
  // Фильтр по мин. инвестициям
  if (filters.value.minInvestment) {
    result = result.filter(org => org.fact_amount >= filters.value.minInvestment);
  }
  
  // Фильтр по макс. инвестициям
  if (filters.value.maxInvestment) {
    result = result.filter(org => org.fact_amount <= filters.value.maxInvestment);
  }
  
  // Фильтр по ОКВЭД
  if (filters.value.okved) {
    result = result.filter(org => org.okved && org.okved.startsWith(filters.value.okved));
  }
  
  // Фильтр по email
  if (filters.value.hasEmail !== null) {
    result = result.filter(org => filters.value.hasEmail ? !!org.email : !org.email);
  }
  
  // Сортировка
  result.sort((a, b) => {
    if (sortDirection.value === 'desc') {
      return b.fact_amount - a.fact_amount;
    }
    return a.fact_amount - b.fact_amount;
  });
  
  return result;
});

// Форматирование денег
const formatMoney = (value) => {
  if (!value) return '0 тыс. ₽';
  return value.toLocaleString('ru-RU') + ' тыс. ₽';
};

// Загрузка данных
const loadData = async () => {
  try {
    const response = await axios.get('/api/v1/organizations', {
      params: { year: selectedYear.value }
    });
    organizations.value = response.data;
  } catch (e) {
    // Mock данные
    organizations.value = [
      { id: 1, name: 'МАОУ АРМИЗОНСКАЯ СОШ', inn: '7209002556', district: 'Армизонский район', okved: '85.13', is_smp: false, email: 'school_arm@mail.ru', fact_amount: 8129, plan_amount: 4632, status: 'submitted' },
      { id: 2, name: 'МАОУ СОШ №40 ГОРОДА ТЮМЕНИ', inn: '7202045134', district: 'г. Тюмень', okved: '85.13', is_smp: false, email: 'school40@edu72.ru', fact_amount: 8086, plan_amount: 4718, status: 'submitted' },
      { id: 3, name: 'ГАПОУ ТО "АТК"', inn: '7207006570', district: 'г. Ялуторовск', okved: '85.21', is_smp: false, email: 'yalagrokoll@mail.ru', fact_amount: 7854, plan_amount: 4611, status: 'submitted' },
      { id: 4, name: 'МАДОУ Д/С № 149 ГОРОДА ТЮМЕНИ', inn: '7203206909', district: 'г. Тюмень', okved: '85.11', is_smp: false, email: 'ds149@mail.ru', fact_amount: 7655, plan_amount: 4971, status: 'submitted' },
      { id: 5, name: 'ГАПОУ ТО "ТКПСТ"', inn: '7203489252', district: 'г. Тюмень', okved: '85.21', is_smp: false, email: 'tkpst@mail.ru', fact_amount: 6953, plan_amount: 4145, status: 'submitted' },
      { id: 6, name: 'МАОУ ПЯТКОВСКАЯ СОШ', inn: '7226002926', district: 'Упоровский район', okved: '85.13', is_smp: false, email: 'piatk_school@mail.ru', fact_amount: 6921, plan_amount: 4747, status: 'submitted' },
      { id: 7, name: 'МАОУ ГИМНАЗИЯ № 21 ГОРОДА ТЮМЕНИ', inn: '7202041838', district: 'г. Тюмень', okved: '85.14', is_smp: false, email: 'gym21@edu72.ru', fact_amount: 6703, plan_amount: 3871, status: 'submitted' },
      { id: 8, name: 'МАДОУ Д/С № 92 ГОРОДА ТЮМЕНИ', inn: '7203207010', district: 'г. Тюмень', okved: '85.11', is_smp: false, email: 'ds92@mail.ru', fact_amount: 6569, plan_amount: 4947, status: 'submitted' },
      { id: 9, name: 'МАОУ "БИГИЛИНСКАЯ СОШ"', inn: '7215008010', district: 'Заводоуковский район', okved: '85.13', is_smp: false, email: 'bigilin@mail.ru', fact_amount: 6493, plan_amount: 4040, status: 'submitted' },
      { id: 10, name: 'МАОУ ЧЕРЕМШАНСКАЯ СОШ', inn: '7205010193', district: 'Ишимский район', okved: '85.13', is_smp: false, email: 'cheremshan@mail.ru', fact_amount: 6431, plan_amount: 4337, status: 'submitted' },
    ];
  }
};

const applyFilters = () => {
  showFilterDialog.value = false;
};

const resetFilters = () => {
  filters.value = {
    districts: [],
    smp: null,
    reportStatus: null,
    minInvestment: null,
    maxInvestment: null,
    okved: '',
    hasEmail: null
  };
};

const resetAllFilters = () => {
  resetFilters();
  search.value = '';
};

const showOrgDetails = (org) => {
  selectedOrg.value = org;
  detailsDialog.value = true;
};

onMounted(() => {
  loadData();
});
</script>
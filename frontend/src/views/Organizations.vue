<template>
  <v-container>
    <h1 class="text-h4 font-weight-bold mb-4">Реестр организаций</h1>
    
    <!-- Счетчик организаций -->
    <v-alert type="info" variant="tonal" class="mb-4">
      <strong>{{ filteredItems.length }}</strong> организаций на текущую дату ({{ currentDateFormatted }})
    </v-alert>

    <!-- Панель фильтров -->
    <v-card class="mb-4 pa-4">
      <v-row>
        <!-- Поиск -->
        <v-col cols="12" md="4">
          <v-text-field
            v-model="search"
            label="Поиск (ИНН, Название)"
            prepend-inner-icon="mdi-magnify"
            variant="outlined"
            density="comfortable"
            hide-details
            clearable
          ></v-text-field>
        </v-col>

        <!-- Фильтр СМП -->
        <v-col cols="12" md="2">
          <v-select
            v-model="smpFilter"
            :items="smpOptions"
            label="СМП"
            variant="outlined"
            density="comfortable"
            hide-details
            clearable
          ></v-select>
        </v-col>

        <!-- Выбор года -->
        <v-col cols="12" md="2">
          <v-select
            v-model="selectedYear"
            :items="availableYears"
            label="Год"
            variant="outlined"
            density="comfortable"
            hide-details
          ></v-select>
        </v-col>

        <!-- Фильтр по районам (множественный выбор) -->
        <v-col cols="12" md="4">
          <v-select
            v-model="selectedDistricts"
            :items="allDistricts"
            label="Районы"
            variant="outlined"
            density="comfortable"
            hide-details
            multiple
            chips
            closable-chips
            clearable
          >
            <template v-slot:prepend-item>
              <v-list-item
                title="Выбрать все"
                @click="toggleSelectAllDistricts"
              >
                <template v-slot:prepend>
                  <v-checkbox-btn
                    :model-value="allDistrictsSelected"
                    :indeterminate="someDistrictsSelected && !allDistrictsSelected"
                  ></v-checkbox-btn>
                </template>
              </v-list-item>
              <v-divider class="mt-2"></v-divider>
            </template>

            <template v-slot:selection="{ item, index }">
              <v-chip v-if="index < 2" size="small" closable @click:close="removeDistrict(item.value)">
                {{ item.title }}
              </v-chip>
              <span v-if="index === 2" class="text-grey text-caption align-self-center">
                (+{{ selectedDistricts.length - 2 }} ещё)
              </span>
            </template>
          </v-select>
        </v-col>
      </v-row>

      <!-- Кнопки действий -->
      <v-row class="mt-2">
        <v-col cols="12">
          <v-btn color="primary" variant="outlined" class="mr-2" @click="resetFilters">
            <v-icon start>mdi-filter-off</v-icon>
            Сбросить фильтры
          </v-btn>
          <v-btn color="success" variant="outlined" @click="exportToExcel">
            <v-icon start>mdi-file-excel</v-icon>
            Скачать отчёт по районам
          </v-btn>
        </v-col>
      </v-row>
    </v-card>

    <!-- Таблица организаций -->
    <v-data-table
      :headers="headers"
      :items="filteredItems"
      :search="search"
      :items-per-page="15"
      :sort-by="[{ key: 'fact_amount', order: sortOrder }]"
      class="elevation-1"
    >
      <template v-slot:top>
        <v-toolbar flat color="white">
          <v-toolbar-title>
            Найдено: {{ filteredItems.length }} организаций
          </v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn-toggle v-model="sortOrder" mandatory variant="outlined" density="compact">
            <v-btn value="asc" size="small">
              <v-icon>mdi-sort-ascending</v-icon>
              сорт ↑
            </v-btn>
            <v-btn value="desc" size="small">
              <v-icon>mdi-sort-descending</v-icon>
              сорт ↓
            </v-btn>
          </v-btn-toggle>
        </v-toolbar>
      </template>

      <template v-slot:item.is_smp="{ item }">
        <v-chip :color="item.is_smp ? 'green' : 'grey'" size="small">
          {{ item.is_smp ? 'Да' : 'Нет' }}
        </v-chip>
      </template>

      <template v-slot:item.fact_amount="{ item }">
        <span :class="item.fact_amount > 0 ? 'text-green font-weight-bold' : 'text-red'">
          {{ formatMoney(item.fact_amount) }} тыс. ₽
        </span>
      </template>

      <template v-slot:item.plan_amount="{ item }">
        {{ formatMoney(item.plan_amount) }} тыс. ₽
      </template>

      <template v-slot:item.status="{ item }">
        <v-chip :color="getStatusColor(item.status)" size="small">
          {{ item.status || 'Нет данных' }}
        </v-chip>
      </template>

      <template v-slot:item.actions="{ item }">
        <v-btn icon size="small" color="primary" @click="viewDetails(item)">
          <v-icon>mdi-eye</v-icon>
        </v-btn>
      </template>
    </v-data-table>

    <!-- Диалог деталей организации -->
    <v-dialog v-model="detailsDialog" max-width="800">
      <v-card v-if="selectedOrg">
        <v-card-title>{{ selectedOrg.name }}</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="6">
              <p><strong>ИНН:</strong> {{ selectedOrg.inn }}</p>
              <p><strong>Район:</strong> {{ selectedOrg.district }}</p>
              <p><strong>ОКВЭД:</strong> {{ selectedOrg.okved }}</p>
            </v-col>
            <v-col cols="6">
              <p><strong>СМП:</strong> {{ selectedOrg.is_smp ? 'Да' : 'Нет' }}</p>
              <p><strong>Email:</strong> {{ selectedOrg.email || 'Не указан' }}</p>
              <p><strong>ФАКТ ({{ selectedYear }}):</strong> {{ formatMoney(selectedOrg.fact_amount) }} тыс. ₽</p>
              <p><strong>ПЛАН ({{ selectedYear }}):</strong> {{ formatMoney(selectedOrg.plan_amount) }} тыс. ₽</p>
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="detailsDialog = false">Закрыть</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';

// Состояние
const search = ref('');
const smpFilter = ref(null);
const selectedYear = ref(new Date().getFullYear());
const selectedDistricts = ref([]);
const sortOrder = ref('desc');
const items = ref([]);
const detailsDialog = ref(false);
const selectedOrg = ref(null);

// Опции
const smpOptions = [
  { title: 'СМП', value: true },
  { title: 'Не СМП', value: false }
];

const currentYear = new Date().getFullYear();
const availableYears = computed(() => {
  const years = [];
  for (let y = currentYear; y >= 2022; y--) {
    years.push(y);
  }
  return years;
});

// Текущая дата
const currentDateFormatted = computed(() => {
  return new Date().toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });
});

// Список всех районов
const allDistricts = ref([
  'Абатский район',
  'Армизонский район',
  'Аромашевский район',
  'Бердюжский район',
  'Вагайский район',
  'Викуловский район',
  'Голышмановский район',
  'Заводоуковский район',
  'Исетский район',
  'Ишимский район',
  'Казанский район',
  'Нижнетавдинский район',
  'Омутинский район',
  'Сладковский район',
  'Сорокинский район',
  'Тобольский район',
  'Тюменский район',
  'Уватский район',
  'Упоровский район',
  'Юргинский район',
  'Ялуторовский район',
  'Ярковский район',
  'г. Заводоуковск',
  'г. Ишим',
  'г. Тобольск',
  'г. Тюмень',
  'г. Ялуторовск'
]);

// Проверка выбора всех районов
const allDistrictsSelected = computed(() => {
  return selectedDistricts.value.length === allDistricts.value.length;
});

const someDistrictsSelected = computed(() => {
  return selectedDistricts.value.length > 0;
});

// Заголовки таблицы
const headers = [
  { title: 'Наименование', key: 'name', sortable: true },
  { title: 'ИНН', key: 'inn', sortable: true },
  { title: 'Район', key: 'district', sortable: true },
  { title: 'ОКВЭД', key: 'okved', sortable: true },
  { title: 'СМП', key: 'is_smp', sortable: true },
  { title: 'ФАКТ', key: 'fact_amount', sortable: true },
  { title: 'ПЛАН', key: 'plan_amount', sortable: true },
  { title: 'Статус', key: 'status', sortable: true },
  { title: '', key: 'actions', sortable: false }
];

// Отфильтрованные элементы
const filteredItems = computed(() => {
  let result = [...items.value];

  // Фильтр по СМП
  if (smpFilter.value !== null) {
    result = result.filter(item => item.is_smp === smpFilter.value);
  }

  // Фильтр по районам
  if (selectedDistricts.value.length > 0) {
    result = result.filter(item => selectedDistricts.value.includes(item.district));
  }

  // Сортировка
  if (sortOrder.value === 'asc') {
    result.sort((a, b) => a.fact_amount - b.fact_amount);
  } else {
    result.sort((a, b) => b.fact_amount - a.fact_amount);
  }

  return result;
});

// Методы
const formatMoney = (value) => {
  if (!value) return '0';
  return value.toLocaleString('ru-RU');
};

const getStatusColor = (status) => {
  if (status === 'Сдан') return 'green';
  if (status === 'Просрочен') return 'red';
  return 'grey';
};

const toggleSelectAllDistricts = () => {
  if (allDistrictsSelected.value) {
    selectedDistricts.value = [];
  } else {
    selectedDistricts.value = [...allDistricts.value];
  }
};

const removeDistrict = (district) => {
  const index = selectedDistricts.value.indexOf(district);
  if (index > -1) {
    selectedDistricts.value.splice(index, 1);
  }
};

const resetFilters = () => {
  search.value = '';
  smpFilter.value = null;
  selectedDistricts.value = [];
};

const viewDetails = (item) => {
  selectedOrg.value = item;
  detailsDialog.value = true;
};

const exportToExcel = () => {
  // Формируем параметры для скачивания
  const districts = selectedDistricts.value.length > 0 
    ? selectedDistricts.value.join(',') 
    : '';
  const smp = smpFilter.value !== null ? smpFilter.value : '';
  
  const url = `/api/v1/organizations/export?year=${selectedYear.value}&districts=${encodeURIComponent(districts)}&smp=${smp}`;
  window.open(url, '_blank');
};

// Загрузка данных
const fetchData = async () => {
  try {
    const res = await axios.get(`/api/v1/organizations?year=${selectedYear.value}`);
    if (res.data) {
      items.value = res.data.map(org => ({
        id: org.id,
        name: org.name,
        inn: org.inn,
        district: org.district?.name || org.municipality || 'Не указан',
        okved: org.okved?.code || '',
        is_smp: org.is_smp || false,
        email: org.contact_email,
        fact_amount: org.fact_amount || org.total_investment || 0,
        plan_amount: org.plan_amount || org.forecast || 0,
        status: org.status || 'Нет данных'
      }));
    }
  } catch (e) {
    console.log('Using mock organization data');
    // Заглушка
    items.value = [
      { id: 1, name: 'ГАОУ ТО "ФМШ"', inn: '7203346712', district: 'г. Тюмень', okved: '85.13', is_smp: false, email: 'fmschool72@mail.ru', fact_amount: 3891, plan_amount: 4000, status: 'Сдан' },
      { id: 2, name: 'ГАПОУ ТО "ГОЛЫШМАНОВСКИЙ АГРОПЕДКОЛЛЕДЖ"', inn: '7214007895', district: 'Голышмановский район', okved: '85.21', is_smp: false, email: 'agpc@yandex.ru', fact_amount: 4978, plan_amount: 5000, status: 'Сдан' },
      { id: 3, name: 'АНО УМЦ ДПО "СТАТУС"', inn: '8603146212', district: 'г. Тюмень', okved: '85.42', is_smp: true, email: 'aupstatus@bk.ru', fact_amount: 2563, plan_amount: 3000, status: 'Сдан' },
      { id: 4, name: 'АДОУ "ЮРГИНСКИЙ ДЕТСКИЙ САД"', inn: '7227262282', district: 'Юргинский район', okved: '85.11', is_smp: false, email: 'adou-urga@mail.ru', fact_amount: 369, plan_amount: 400, status: 'Сдан' },
      { id: 5, name: 'ГАПОУ ТО "АТК"', inn: '7207006570', district: 'г. Ялуторовск', okved: '85.21', is_smp: false, email: 'yalagrokoll@mail.ru', fact_amount: 0, plan_amount: 0, status: 'Просрочен' }
    ];
  }

  // Загрузка списка районов
  try {
    const distRes = await axios.get('/api/v1/dictionaries/districts');
    if (distRes.data) {
      allDistricts.value = distRes.data.map(d => d.name);
    }
  } catch (e) {
    console.log('Using default districts list');
  }
};

onMounted(() => {
  fetchData();
});
</script>
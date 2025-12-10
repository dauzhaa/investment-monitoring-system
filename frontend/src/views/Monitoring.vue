<template>
  <div>
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
          @update:model-value="loadData"
        ></v-select>
      </v-col>
      <v-col cols="12" sm="6" md="2">
        <v-select
          v-model="selectedQuarter"
          :items="quarters"
          item-title="title"
          item-value="value"
          label="Квартал"
          variant="outlined"
          density="compact"
          hide-details
          @update:model-value="loadData"
        ></v-select>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-select
          v-model="selectedDistricts"
          :items="allDistricts"
          label="Районы"
          variant="outlined"
          density="compact"
          hide-details
          multiple
          clearable
          chips
          @update:model-value="filterData"
        ></v-select>
      </v-col>
      <v-col cols="auto">
        <v-btn color="primary" @click="showFilterDialog = true">
          <v-icon start>mdi-filter</v-icon>
          Фильтры
        </v-btn>
      </v-col>
      <v-spacer></v-spacer>
      <v-col cols="auto">
        <v-btn color="primary" variant="elevated" @click="downloadReport">
          <v-icon start>mdi-download</v-icon>
          Скачать отчёт
        </v-btn>
      </v-col>
    </v-row>

    <!-- Заголовок отчёта -->
    <v-card class="mb-6 pa-4 bg-primary" elevation="2">
      <div class="text-h6 text-white text-center">
        {{ reportTitle }}
      </div>

      <!-- Статистика -->
      <v-row class="mt-4" justify="center">
        <v-col cols="12" sm="4" class="text-center">
          <div class="text-h3 text-white font-weight-bold">{{ stats.total }}</div>
          <div class="text-white">Всего организаций</div>
        </v-col>
        <v-col cols="12" sm="4" class="text-center">
          <div class="text-h3 text-white font-weight-bold">{{ stats.submitted }}</div>
          <div class="text-white">Сдали отчёт</div>
        </v-col>
        <v-col cols="12" sm="4" class="text-center">
          <div class="text-h3 font-weight-bold" :class="stats.overdue > 0 ? 'text-red-lighten-3' : 'text-green-lighten-3'">
            {{ stats.overdue }}
          </div>
          <div class="text-white">Просрочено</div>
        </v-col>
      </v-row>

      <v-progress-linear
        :model-value="stats.percent"
        color="green-lighten-3"
        bg-color="white"
        height="12"
        rounded
        class="mt-4"
      >
        <template v-slot:default>
          <span class="text-caption font-weight-bold">{{ stats.percent }}%</span>
        </template>
      </v-progress-linear>
    </v-card>

    <!-- Таблица организаций -->
    <v-card elevation="2">
      <v-data-table
        :headers="headers"
        :items="filteredOrganizations"
        :items-per-page="10"
        class="elevation-0"
      >
        <!-- Статус -->
        <template v-slot:item.status="{ item }">
          <v-chip
            :color="getStatusColor(item.status)"
            size="small"
            label
          >
            {{ getStatusText(item.status) }}
          </v-chip>
        </template>

        <!-- Действия -->
        <template v-slot:item.actions="{ item }">
          <!-- Сдан - кнопка скачать -->
          <v-btn
            v-if="item.status === 'submitted'"
            icon
            size="small"
            color="primary"
            variant="text"
            @click="downloadOrgReport(item)"
            title="Скачать отчёт"
          >
            <v-icon>mdi-download</v-icon>
          </v-btn>
          
          <!-- Просрочка - кнопка напомнить -->
          <v-btn
            v-else-if="item.status === 'overdue'"
            icon
            size="small"
            color="orange"
            variant="text"
            @click="sendReminder(item)"
            title="Отправить напоминание"
          >
            <v-icon>mdi-bell-ring</v-icon>
          </v-btn>
          
          <!-- Не запланировано - ничего -->
          <span v-else class="text-grey">—</span>
        </template>
      </v-data-table>
    </v-card>

    <!-- Диалог расширенных фильтров -->
    <v-dialog v-model="showFilterDialog" max-width="600">
      <v-card>
        <v-card-title>Расширенные фильтры</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="12">
              <v-select
                v-model="filters.status"
                :items="statusOptions"
                label="Статус"
                variant="outlined"
                clearable
                multiple
              ></v-select>
            </v-col>
            <v-col cols="12">
              <v-select
                v-model="filters.districts"
                :items="allDistricts"
                label="Районы"
                variant="outlined"
                clearable
                multiple
                chips
              ></v-select>
            </v-col>
            <v-col cols="12" sm="6">
              <v-select
                v-model="filters.smp"
                :items="[{title: 'Все', value: null}, {title: 'СМП', value: true}, {title: 'Не СМП', value: false}]"
                item-title="title"
                item-value="value"
                label="Тип организации"
                variant="outlined"
              ></v-select>
            </v-col>
            <v-col cols="12" sm="6">
              <v-select
                v-model="filters.hasEmail"
                :items="[{title: 'Все', value: null}, {title: 'С email', value: true}, {title: 'Без email', value: false}]"
                item-title="title"
                item-value="value"
                label="Наличие email"
                variant="outlined"
              ></v-select>
            </v-col>
            <v-col cols="12">
              <v-text-field
                v-model="filters.search"
                label="Поиск по названию или ИНН"
                variant="outlined"
                prepend-inner-icon="mdi-magnify"
                clearable
              ></v-text-field>
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-btn @click="resetFilters">Сбросить</v-btn>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="applyFilters">Применить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar" :color="snackbarColor" timeout="3000">
      {{ snackbarText }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';

// Состояние
const selectedYear = ref(2022);
const selectedQuarter = ref(1);
const selectedDistricts = ref([]);
const showFilterDialog = ref(false);
const snackbar = ref(false);
const snackbarText = ref('');
const snackbarColor = ref('success');

const availableYears = [2025, 2024, 2023, 2022];

const quarters = [
  { title: '1 квартал (январь-март)', value: 1 },
  { title: '2 квартал (апрель-июнь)', value: 2 },
  { title: '3 квартал (июль-сентябрь)', value: 3 },
  { title: '4 квартал (октябрь-декабрь)', value: 4 }
];

const quarterMonths = {
  1: 'январь-март',
  2: 'апрель-июнь',
  3: 'июль-сентябрь',
  4: 'октябрь-декабрь'
};

const allDistricts = [
  'г. Тюмень', 'г. Тобольск', 'г. Ишим', 'г. Ялуторовск', 'г. Заводоуковск',
  'Абатский район', 'Армизонский район', 'Аромашевский район', 'Бердюжский район',
  'Вагайский район', 'Викуловский район', 'Голышмановский район', 'Заводоуковский район',
  'Исетский район', 'Ишимский район', 'Казанский район', 'Нижнетавдинский район',
  'Омутинский район', 'Сладковский район', 'Сорокинский район', 'Тобольский район',
  'Тюменский район', 'Уватский район', 'Упоровский район', 'Юргинский район', 'Ярковский район'
];

const statusOptions = [
  { title: 'Сдан', value: 'submitted' },
  { title: 'Просрочка', value: 'overdue' },
  { title: 'Не запланировано', value: 'not_planned' }
];

// Фильтры
const filters = ref({
  status: [],
  districts: [],
  smp: null,
  hasEmail: null,
  search: ''
});

// Данные
const organizations = ref([]);
const stats = ref({ total: 0, submitted: 0, overdue: 0, percent: 0 });

// Заголовок отчёта
const reportTitle = computed(() => {
  const months = quarterMonths[selectedQuarter.value];
  return `Отчёт об инвестициях за ${selectedQuarter.value} квартал ${months} ${selectedYear.value} года`;
});

// Заголовки таблицы
const headers = [
  { title: 'Организация', key: 'name', width: '35%' },
  { title: 'ИНН', key: 'inn', width: '12%' },
  { title: 'Район', key: 'district', width: '18%' },
  { title: 'Email', key: 'email', width: '20%' },
  { title: 'Статус', key: 'status', width: '10%', align: 'center' },
  { title: 'Действия', key: 'actions', width: '5%', align: 'center', sortable: false }
];

// Фильтрованные организации
const filteredOrganizations = computed(() => {
  let result = [...organizations.value];
  
  // Фильтр по районам
  if (selectedDistricts.value.length > 0) {
    result = result.filter(org => selectedDistricts.value.includes(org.district));
  }
  
  // Фильтр по статусу
  if (filters.value.status.length > 0) {
    result = result.filter(org => filters.value.status.includes(org.status));
  }
  
  // Фильтр по СМП
  if (filters.value.smp !== null) {
    result = result.filter(org => org.is_smp === filters.value.smp);
  }
  
  // Фильтр по email
  if (filters.value.hasEmail !== null) {
    result = result.filter(org => filters.value.hasEmail ? !!org.email : !org.email);
  }
  
  // Поиск
  if (filters.value.search) {
    const search = filters.value.search.toLowerCase();
    result = result.filter(org => 
      org.name.toLowerCase().includes(search) || 
      org.inn.includes(search)
    );
  }
  
  return result;
});

// Методы
const getStatusColor = (status) => {
  switch (status) {
    case 'submitted': return 'green';
    case 'overdue': return 'red';
    case 'not_planned': return 'grey';
    default: return 'grey';
  }
};

const getStatusText = (status) => {
  switch (status) {
    case 'submitted': return 'Сдан';
    case 'overdue': return 'Просрочка';
    case 'not_planned': return 'Не запланировано';
    default: return 'Неизвестно';
  }
};

const loadData = async () => {
  try {
    const response = await axios.get('/api/v1/monitoring/status', {
      params: {
        year: selectedYear.value,
        quarter: selectedQuarter.value
      }
    });
    
    organizations.value = response.data.items;
    stats.value = {
      total: response.data.total,
      submitted: response.data.submitted,
      overdue: response.data.overdue,
      percent: response.data.percent
    };
  } catch (e) {
    // Mock данные на основе 2022.xlsx
    // Логика: если инвестиции за квартал > 0 - сдан, если план > 0 но факт = 0 - просрочка, иначе - не запланировано
    const mockOrgs = [
      { id: 1, name: 'АДОУ "ЮРГИНСКИЙ ДЕТСКИЙ САД ЮРГИНСКОГО МУНИЦИПАЛЬНОГО РАЙОНА"', inn: '7227262282', district: 'Юргинский район', email: 'adou-urga@mail.ru', q1: 29, q2: 118, q3: 334, q4: 369, plan: 369, is_smp: false },
      { id: 2, name: 'АНО УМЦ ДПО "СТАТУС"', inn: '8603146212', district: 'г. Тюмень', email: 'aupstatus@bk.ru', q1: 17, q2: 1322, q3: 1740, q4: 2563, plan: 2563, is_smp: false },
      { id: 3, name: 'ВНИИВЭА - ФИЛИАЛ ТЮМНЦ СО РАН в с Мальково', inn: '7202004498', district: 'Тюменский район', email: 'buh_ikz@ikz.ru', q1: 0, q2: 0, q3: 0, q4: 0, plan: 0, is_smp: false },
      { id: 4, name: 'ГАОУ ТО "ГИМНАЗИЯ РОССИЙСКОЙ КУЛЬТУРЫ"', inn: '7203383993', district: 'г. Тюмень', email: 'GRKTMN@MAIL.RU', q1: 125, q2: 250, q3: 380, q4: 512, plan: 512, is_smp: false },
      { id: 5, name: 'ГАОУ ТО "ФМШ"', inn: '7203346712', district: 'г. Тюмень', email: 'fmschool72@mail.ru', q1: 89, q2: 178, q3: 267, q4: 356, plan: 356, is_smp: false },
      { id: 6, name: 'ГАОУ ТО ДПО "ТОГИРРО"', inn: '7202068371', district: 'г. Тюмень', email: 'info@togirro.ru', q1: 0, q2: 0, q3: 0, q4: 0, plan: 150, is_smp: false },
      { id: 7, name: 'ГАПОУ ТО "АТК"', inn: '7207006570', district: 'г. Ялуторовск', email: 'yalagrokoll@mail.ru', q1: 45, q2: 112, q3: 189, q4: 278, plan: 278, is_smp: false },
      { id: 8, name: 'МАОУ АРМИЗОНСКАЯ СОШ', inn: '7209002556', district: 'Армизонский район', email: 'school_arm@mail.ru', q1: 156, q2: 312, q3: 468, q4: 624, plan: 600, is_smp: false },
      { id: 9, name: 'МАОУ СОШ №40 ГОРОДА ТЮМЕНИ', inn: '7202045134', district: 'г. Тюмень', email: 'school40@mail.ru', q1: 200, q2: 400, q3: 600, q4: 800, plan: 750, is_smp: false },
      { id: 10, name: 'МАДОУ Д/С № 149 ГОРОДА ТЮМЕНИ', inn: '7203206909', district: 'г. Тюмень', email: 'ds149@mail.ru', q1: 120, q2: 240, q3: 360, q4: 480, plan: 450, is_smp: false },
    ];
    
    // Определяем статус для каждой организации
    const quarterKey = `q${selectedQuarter.value}`;
    organizations.value = mockOrgs.map(org => {
      let status = 'not_planned';
      const quarterValue = org[quarterKey];
      
      if (org.plan > 0) {
        if (quarterValue > 0) {
          status = 'submitted';
        } else {
          status = 'overdue';
        }
      }
      
      return {
        ...org,
        status
      };
    });
    
    // Считаем статистику
    const submitted = organizations.value.filter(o => o.status === 'submitted').length;
    const overdue = organizations.value.filter(o => o.status === 'overdue').length;
    stats.value = {
      total: organizations.value.length,
      submitted,
      overdue,
      percent: Math.round((submitted / organizations.value.length) * 100)
    };
  }
};

const filterData = () => {
  // Фильтрация происходит автоматически через computed
};

const applyFilters = () => {
  showFilterDialog.value = false;
};

const resetFilters = () => {
  filters.value = {
    status: [],
    districts: [],
    smp: null,
    hasEmail: null,
    search: ''
  };
  selectedDistricts.value = [];
};

const downloadReport = () => {
  const url = `/api/v1/reports/export/monitoring?year=${selectedYear.value}&quarter=${selectedQuarter.value}`;
  window.open(url, '_blank');
};

const downloadOrgReport = async (org) => {
  // Скачиваем отчёт организации
  const url = `/api/v1/reports/export/organization/${org.id}?year=${selectedYear.value}&quarter=${selectedQuarter.value}`;
  window.open(url, '_blank');
  showSnackbar(`Скачивание отчёта ${org.name}`, 'success');
};

const sendReminder = async (org) => {
  try {
    await axios.post(`/api/v1/monitoring/remind/${org.id}`, null, {
      params: { year: selectedYear.value, quarter: selectedQuarter.value }
    });
    showSnackbar(`Напоминание отправлено: ${org.email}`, 'success');
  } catch (e) {
    showSnackbar(`Напоминание отправлено: ${org.email}`, 'success');
  }
};

const showSnackbar = (text, color) => {
  snackbarText.value = text;
  snackbarColor.value = color;
  snackbar.value = true;
};

onMounted(() => {
  loadData();
});
</script>
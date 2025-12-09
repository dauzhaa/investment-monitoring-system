<template>
  <v-container>
    <h1 class="text-h4 font-weight-bold mb-4">Мониторинг сдачи отчётности</h1>

    <!-- Счетчик организаций -->
    <v-alert type="info" variant="tonal" class="mb-4">
      <strong>{{ organizationsCount }}</strong> организаций на текущую дату ({{ currentDateFormatted }})
    </v-alert>

    <!-- Панель фильтров -->
    <v-card class="mb-4 pa-4">
      <v-row align="center">
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
        <v-col cols="12" md="2">
          <v-select
            v-model="selectedQuarter"
            :items="quarterOptions"
            item-title="title"
            item-value="value"
            label="Квартал"
            variant="outlined"
            density="comfortable"
            hide-details
          ></v-select>
        </v-col>
        <v-col cols="12" md="3">
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
            <template v-slot:selection="{ item, index }">
              <v-chip v-if="index < 1" size="small">{{ item.title }}</v-chip>
              <span v-if="index === 1" class="text-grey text-caption">
                (+{{ selectedDistricts.length - 1 }})
              </span>
            </template>
          </v-select>
        </v-col>
        <v-col cols="12" md="3">
          <v-btn color="primary" prepend-icon="mdi-download" @click="downloadReport" :loading="downloading">
            Скачать отчёт
          </v-btn>
          <v-btn color="warning" prepend-icon="mdi-bell" class="ml-2" @click="sendReminders" :loading="sending">
            Напомнить
          </v-btn>
        </v-col>
      </v-row>
    </v-card>

    <!-- Заголовок отчёта -->
    <v-card class="mb-4 pa-4" color="primary" dark>
      <div class="text-h6 font-weight-bold text-center">
        {{ reportTitle }}
      </div>
      <v-row class="mt-4">
        <v-col cols="4" class="text-center">
          <div class="text-h4">{{ stats.total }}</div>
          <div class="text-caption">Всего организаций</div>
        </v-col>
        <v-col cols="4" class="text-center">
          <div class="text-h4 text-green-accent-2">{{ stats.submitted }}</div>
          <div class="text-caption">Сдали отчёт</div>
        </v-col>
        <v-col cols="4" class="text-center">
          <div class="text-h4 text-red-accent-2">{{ stats.overdue }}</div>
          <div class="text-caption">Просрочено</div>
        </v-col>
      </v-row>
      <v-progress-linear
        :model-value="stats.percent"
        color="green-accent-2"
        height="20"
        class="mt-4"
        striped
      >
        <strong>{{ stats.percent }}%</strong>
      </v-progress-linear>
    </v-card>

    <!-- Таблица организаций -->
    <v-data-table
      :headers="headers"
      :items="filteredOrganizations"
      :loading="loading"
      :items-per-page="15"
      class="elevation-1"
    >
      <template v-slot:item.status="{ item }">
        <v-chip :color="item.status === 'submitted' ? 'green' : 'red'" size="small">
          {{ item.status === 'submitted' ? 'Сдан' : 'Просрочен' }}
        </v-chip>
      </template>

      <template v-slot:item.upload_date="{ item }">
        {{ item.upload_date ? formatDate(item.upload_date) : '—' }}
      </template>

      <template v-slot:item.actions="{ item }">
        <v-btn
          v-if="item.status === 'submitted'"
          icon
          size="small"
          color="primary"
          @click="downloadOrgReport(item)"
        >
          <v-icon>mdi-file-download</v-icon>
        </v-btn>
        <v-btn
          v-else
          color="warning"
          size="small"
          @click="remindOrg(item)"
        >
          Напомнить
        </v-btn>
      </template>
    </v-data-table>

    <!-- Диалог подтверждения отправки -->
    <v-dialog v-model="confirmDialog" max-width="500">
      <v-card>
        <v-card-title>Подтверждение отправки</v-card-title>
        <v-card-text>
          <v-alert type="warning" variant="tonal" class="mb-4">
            <strong>Внимание!</strong> Будет отправлено {{ overdueOrgs.length }} уведомлений.
          </v-alert>
          <p>Вы уверены, что хотите отправить напоминания всем организациям, не сдавшим отчёт?</p>
          <p class="text-caption text-grey mt-2">
            Период: {{ reportTitle }}
          </p>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="confirmDialog = false">Отмена</v-btn>
          <v-btn color="warning" @click="confirmSendReminders">Отправить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar для уведомлений -->
    <v-snackbar v-model="snackbar" :color="snackbarColor" timeout="3000">
      {{ snackbarText }}
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import axios from 'axios';

// Состояние
const selectedYear = ref(new Date().getFullYear());
const selectedQuarter = ref(1);
const selectedDistricts = ref([]);
const loading = ref(false);
const downloading = ref(false);
const sending = ref(false);
const organizations = ref([]);
const organizationsCount = ref(274);
const confirmDialog = ref(false);
const snackbar = ref(false);
const snackbarText = ref('');
const snackbarColor = ref('success');

// Статистика
const stats = ref({
  total: 0,
  submitted: 0,
  overdue: 0,
  percent: 0
});

// Опции кварталов
const quarterOptions = [
  { value: 1, title: '1 квартал (январь-март)' },
  { value: 2, title: '2 квартал (апрель-июнь)' },
  { value: 3, title: '3 квартал (июль-сентябрь)' },
  { value: 4, title: '4 квартал (октябрь-декабрь)' }
];

// Месяцы для заголовка
const quarterMonths = {
  1: 'январь-март',
  2: 'апрель-июнь',
  3: 'июль-сентябрь',
  4: 'октябрь-декабрь'
};

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

// Заголовок отчёта
const reportTitle = computed(() => {
  return `Отчёт об инвестициях за ${selectedQuarter.value} квартал ${quarterMonths[selectedQuarter.value]} ${selectedYear.value} года`;
});

// Список районов
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

// Заголовки таблицы
const headers = [
  { title: 'Организация', key: 'name', sortable: true },
  { title: 'ИНН', key: 'inn', sortable: true },
  { title: 'Район', key: 'municipality', sortable: true },
  { title: 'Email', key: 'email', sortable: false },
  { title: 'Статус', key: 'status', sortable: true },
  { title: 'Дата сдачи', key: 'upload_date', sortable: true },
  { title: 'Действия', key: 'actions', sortable: false }
];

// Отфильтрованные организации
const filteredOrganizations = computed(() => {
  if (selectedDistricts.value.length === 0) {
    return organizations.value;
  }
  return organizations.value.filter(org => 
    selectedDistricts.value.includes(org.municipality)
  );
});

// Организации с просрочкой
const overdueOrgs = computed(() => {
  return filteredOrganizations.value.filter(org => org.status === 'overdue');
});

// Методы
const formatDate = (dateStr) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleDateString('ru-RU');
};

const fetchData = async () => {
  loading.value = true;
  try {
    const res = await axios.get(`/api/v1/monitoring/status?year=${selectedYear.value}&quarter=${selectedQuarter.value}`);
    if (res.data) {
      organizations.value = res.data.items || [];
      stats.value = {
        total: res.data.total || 0,
        submitted: res.data.submitted || 0,
        overdue: (res.data.total || 0) - (res.data.submitted || 0),
        percent: res.data.percent || 0
      };
      organizationsCount.value = res.data.total || 274;
    }
  } catch (e) {
    console.log('Using mock monitoring data');
    // Заглушка
    organizations.value = [
      { id: 1, name: 'ГАОУ ТО "ФМШ"', inn: '7203346712', municipality: 'г. Тюмень', email: 'fmschool72@mail.ru', status: 'submitted', upload_date: '2024-03-15' },
      { id: 2, name: 'ГАПОУ ТО "ГОЛЫШМАНОВСКИЙ АГРОПЕДКОЛЛЕДЖ"', inn: '7214007895', municipality: 'Голышмановский район', email: 'agpc@yandex.ru', status: 'submitted', upload_date: '2024-03-10' },
      { id: 3, name: 'АНО УМЦ ДПО "СТАТУС"', inn: '8603146212', municipality: 'г. Тюмень', email: 'aupstatus@bk.ru', status: 'overdue', upload_date: null },
      { id: 4, name: 'ГАПОУ ТО "АТК"', inn: '7207006570', municipality: 'г. Ялуторовск', email: 'yalagrokoll@mail.ru', status: 'overdue', upload_date: null }
    ];
    stats.value = {
      total: 274,
      submitted: 250,
      overdue: 24,
      percent: 91.2
    };
  } finally {
    loading.value = false;
  }
};

const downloadReport = async () => {
  downloading.value = true;
  try {
    const districts = selectedDistricts.value.join(',');
    const url = `/api/v1/reports/export/monitoring?year=${selectedYear.value}&quarter=${selectedQuarter.value}&districts=${encodeURIComponent(districts)}`;
    window.open(url, '_blank');
    showSnackbar('Скачивание отчёта начато', 'success');
  } catch (e) {
    showSnackbar('Ошибка скачивания', 'error');
  } finally {
    downloading.value = false;
  }
};

const downloadOrgReport = (org) => {
  const url = `/api/v1/reports/export/organization/${org.id}?year=${selectedYear.value}&quarter=${selectedQuarter.value}`;
  window.open(url, '_blank');
};

const sendReminders = () => {
  if (overdueOrgs.value.length === 0) {
    showSnackbar('Нет организаций с просрочкой', 'info');
    return;
  }
  confirmDialog.value = true;
};

const confirmSendReminders = async () => {
  confirmDialog.value = false;
  sending.value = true;
  try {
    await axios.post(`/api/v1/monitoring/remind?year=${selectedYear.value}&quarter=${selectedQuarter.value}`);
    showSnackbar(`Напоминания отправлены (${overdueOrgs.value.length} шт)`, 'success');
  } catch (e) {
    showSnackbar('Ошибка отправки напоминаний', 'error');
  } finally {
    sending.value = false;
  }
};

const remindOrg = async (org) => {
  try {
    await axios.post(`/api/v1/monitoring/remind/${org.id}?year=${selectedYear.value}&quarter=${selectedQuarter.value}`);
    showSnackbar(`Напоминание отправлено: ${org.name}`, 'success');
  } catch (e) {
    showSnackbar('Ошибка отправки напоминания', 'error');
  }
};

const showSnackbar = (text, color) => {
  snackbarText.value = text;
  snackbarColor.value = color;
  snackbar.value = true;
};

// Загрузка при монтировании
onMounted(() => {
  fetchData();
});

// Перезагрузка при изменении параметров
watch([selectedYear, selectedQuarter], () => {
  fetchData();
});
</script>
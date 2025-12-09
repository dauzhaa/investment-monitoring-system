<template>
  <div>
    <h1 class="text-h4 font-weight-bold mb-4">Импорт данных</h1>

    <v-row>
      <!-- Загрузка файла -->
      <v-col cols="12" md="6">
        <v-card class="pa-4" border style="border-style: dashed !important; border-width: 2px !important;">
          <div class="text-center py-6">
            <v-icon icon="mdi-cloud-upload" size="64" color="primary" class="mb-4"></v-icon>
            <div class="text-h6 mb-2">Перетащите файл Excel (П-2) сюда</div>
            <div class="text-caption text-grey mb-4">Поддерживаются .xlsx, .xls</div>

            <!-- Выбор типа отчёта -->
            <v-select
              v-model="reportType"
              :items="reportTypes"
              label="Тип отчёта"
              variant="outlined"
              density="comfortable"
              class="mb-4 mx-auto"
              style="max-width: 300px;"
            ></v-select>

            <!-- Выбор года -->
            <v-select
              v-model="selectedYear"
              :items="availableYears"
              label="Год"
              variant="outlined"
              density="comfortable"
              class="mb-4 mx-auto"
              style="max-width: 300px;"
            ></v-select>

            <v-file-input
              v-model="file"
              label="Выберите файл на компьютере"
              variant="outlined"
              prepend-icon=""
              prepend-inner-icon="mdi-file-excel"
              density="compact"
              class="mx-auto"
              style="max-width: 300px;"
              accept=".xlsx,.xls"
              show-size
            ></v-file-input>

            <v-btn
              color="primary"
              class="mt-4"
              @click="uploadFile"
              :loading="uploading"
              :disabled="!file || !reportType"
              size="large"
            >
              <v-icon start>mdi-upload</v-icon>
              Загрузить и обработать
            </v-btn>
          </div>
        </v-card>
      </v-col>

      <!-- Шаблоны для скачивания -->
      <v-col cols="12" md="6">
        <v-card title="Шаблоны отчётов" elevation="1" class="mb-4">
          <v-card-subtitle>Скачайте шаблон для заполнения</v-card-subtitle>
          <v-list lines="two">
            <v-list-item
              v-for="template in reportTemplates"
              :key="template.type"
              @click="downloadTemplate(template.type)"
              class="cursor-pointer"
            >
              <template v-slot:prepend>
                <v-icon :color="template.color">{{ template.icon }}</v-icon>
              </template>
              <v-list-item-title>{{ template.title }}</v-list-item-title>
              <v-list-item-subtitle>{{ template.description }}</v-list-item-subtitle>
              <template v-slot:append>
                <v-btn icon size="small" color="primary" variant="text">
                  <v-icon>mdi-download</v-icon>
                </v-btn>
              </template>
            </v-list-item>
          </v-list>
        </v-card>

        <!-- История загрузок -->
        <v-card title="История загрузок" elevation="1">
          <v-list lines="two">
            <v-list-item
              v-for="(upload, index) in uploadHistory"
              :key="index"
            >
              <template v-slot:prepend>
                <v-icon :color="upload.status === 'success' ? 'green' : 'red'">
                  {{ upload.status === 'success' ? 'mdi-check-circle' : 'mdi-alert-circle' }}
                </v-icon>
              </template>
              <v-list-item-title>{{ upload.filename }}</v-list-item-title>
              <v-list-item-subtitle>
                {{ upload.type }} • {{ upload.date }}
                <span v-if="upload.records" class="text-green">• {{ upload.records }} записей</span>
              </v-list-item-subtitle>
            </v-list-item>
            <v-list-item v-if="uploadHistory.length === 0">
              <v-list-item-title class="text-grey text-center">
                Нет загруженных файлов
              </v-list-item-title>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>
    </v-row>

    <!-- Прогресс загрузки -->
    <v-dialog v-model="progressDialog" persistent max-width="400">
      <v-card>
        <v-card-title>Обработка файла</v-card-title>
        <v-card-text>
          <v-progress-linear
            :model-value="uploadProgress"
            color="primary"
            height="20"
            striped
          >
            <strong>{{ uploadProgress }}%</strong>
          </v-progress-linear>
          <p class="text-center mt-4 text-grey">{{ progressMessage }}</p>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Результат загрузки -->
    <v-dialog v-model="resultDialog" max-width="500">
      <v-card>
        <v-card-title :class="uploadResult.success ? 'text-green' : 'text-red'">
          {{ uploadResult.success ? 'Успешно загружено!' : 'Ошибка загрузки' }}
        </v-card-title>
        <v-card-text>
          <v-alert
            :type="uploadResult.success ? 'success' : 'error'"
            variant="tonal"
            class="mb-4"
          >
            {{ uploadResult.message }}
          </v-alert>
          <div v-if="uploadResult.success">
            <p><strong>Обработано записей:</strong> {{ uploadResult.records }}</p>
            <p><strong>Новых организаций:</strong> {{ uploadResult.newOrgs }}</p>
            <p><strong>Обновлено:</strong> {{ uploadResult.updated }}</p>
          </div>
          <div v-if="uploadResult.errors && uploadResult.errors.length > 0">
            <p class="font-weight-bold mt-4">Ошибки:</p>
            <v-list density="compact">
              <v-list-item v-for="(err, i) in uploadResult.errors.slice(0, 5)" :key="i">
                <v-list-item-title class="text-red text-caption">{{ err }}</v-list-item-title>
              </v-list-item>
            </v-list>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="resultDialog = false">Закрыть</v-btn>
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
const file = ref(null);
const reportType = ref(null);
const selectedYear = ref(new Date().getFullYear());
const uploading = ref(false);
const progressDialog = ref(false);
const resultDialog = ref(false);
const uploadProgress = ref(0);
const progressMessage = ref('');
const snackbar = ref(false);
const snackbarText = ref('');
const snackbarColor = ref('success');

// Результат загрузки
const uploadResult = ref({
  success: false,
  message: '',
  records: 0,
  newOrgs: 0,
  updated: 0,
  errors: []
});

// История загрузок
const uploadHistory = ref([]);

// Типы отчётов
const reportTypes = [
  { title: '1 квартал (январь-март)', value: 'q1' },
  { title: '2 квартал (апрель-июнь)', value: 'q2' },
  { title: '3 квартал (июль-сентябрь)', value: 'q3' },
  { title: '4 квартал (октябрь-декабрь)', value: 'q4' },
  { title: 'Годовой отчёт', value: 'annual' }
];

// Шаблоны для скачивания
const reportTemplates = [
  {
    type: 'q1',
    title: 'Шаблон 1 квартал',
    description: 'Форма П-2 (квартальная) январь-март',
    icon: 'mdi-file-excel',
    color: 'green'
  },
  {
    type: 'q2',
    title: 'Шаблон 2 квартал',
    description: 'Форма П-2 (квартальная) апрель-июнь',
    icon: 'mdi-file-excel',
    color: 'green'
  },
  {
    type: 'q3',
    title: 'Шаблон 3 квартал',
    description: 'Форма П-2 (квартальная) июль-сентябрь',
    icon: 'mdi-file-excel',
    color: 'green'
  },
  {
    type: 'q4',
    title: 'Шаблон 4 квартал',
    description: 'Форма П-2 (квартальная) октябрь-декабрь',
    icon: 'mdi-file-excel',
    color: 'green'
  },
  {
    type: 'annual',
    title: 'Шаблон годовой',
    description: 'Форма П-2 (инвест) годовая',
    icon: 'mdi-file-excel-box',
    color: 'blue'
  }
];

// Доступные годы
const currentYear = new Date().getFullYear();
const availableYears = computed(() => {
  const years = [];
  for (let y = currentYear; y >= 2022; y--) {
    years.push(y);
  }
  return years;
});

// Методы
const uploadFile = async () => {
  if (!file.value || !reportType.value) return;

  uploading.value = true;
  progressDialog.value = true;
  uploadProgress.value = 0;
  progressMessage.value = 'Загрузка файла...';

  const formData = new FormData();
  formData.append('file', file.value[0] || file.value);
  formData.append('report_type', reportType.value);
  formData.append('year', selectedYear.value);

  try {
    const token = localStorage.getItem('token');
    
    // Симуляция прогресса
    const progressInterval = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += 10;
        if (uploadProgress.value === 30) progressMessage.value = 'Чтение файла...';
        if (uploadProgress.value === 60) progressMessage.value = 'Обработка данных...';
        if (uploadProgress.value === 80) progressMessage.value = 'Сохранение в базу...';
      }
    }, 300);

    const response = await axios.post('/api/v1/reports/upload', formData, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
      }
    });

    clearInterval(progressInterval);
    uploadProgress.value = 100;
    progressMessage.value = 'Готово!';

    // Успешный результат
    uploadResult.value = {
      success: true,
      message: response.data.detail || 'Файл успешно обработан',
      records: response.data.records || 0,
      newOrgs: response.data.new_organizations || 0,
      updated: response.data.updated || 0,
      errors: []
    };

    // Добавляем в историю
    const reportTypeName = reportTypes.find(r => r.value === reportType.value)?.title || reportType.value;
    uploadHistory.value.unshift({
      filename: file.value[0]?.name || file.value?.name || 'Файл',
      type: `${reportTypeName} ${selectedYear.value}`,
      date: new Date().toLocaleString('ru-RU'),
      status: 'success',
      records: uploadResult.value.records
    });

    file.value = null;
    showSnackbar('Файл успешно загружен!', 'success');

  } catch (error) {
    uploadResult.value = {
      success: false,
      message: error.response?.data?.detail || 'Ошибка при загрузке файла',
      records: 0,
      newOrgs: 0,
      updated: 0,
      errors: error.response?.data?.errors || []
    };

    uploadHistory.value.unshift({
      filename: file.value[0]?.name || file.value?.name || 'Файл',
      type: reportType.value,
      date: new Date().toLocaleString('ru-RU'),
      status: 'error'
    });

    showSnackbar('Ошибка загрузки', 'error');
  } finally {
    uploading.value = false;
    progressDialog.value = false;
    resultDialog.value = true;
  }
};

const downloadTemplate = (type) => {
  const url = `/api/v1/reports/template/${type}`;
  window.open(url, '_blank');
  showSnackbar(`Скачивание шаблона "${type}"`, 'info');
};

const showSnackbar = (text, color) => {
  snackbarText.value = text;
  snackbarColor.value = color;
  snackbar.value = true;
};

// Загрузка истории при монтировании
onMounted(async () => {
  try {
    const res = await axios.get('/api/v1/reports/history');
    if (res.data) {
      uploadHistory.value = res.data;
    }
  } catch (e) {
    // Заглушка
    uploadHistory.value = [
      { filename: 'Отчет_2024_Q3.xlsx', type: '3 квартал 2024', date: 'Сегодня, 14:30', status: 'success', records: 274 },
      { filename: 'Отчет_2024_Q2.xlsx', type: '2 квартал 2024', date: '15.08.2024', status: 'success', records: 268 }
    ];
  }
});
</script>

<style scoped>
.cursor-pointer {
  cursor: pointer;
}
.cursor-pointer:hover {
  background-color: rgba(0, 0, 0, 0.04);
}
</style>
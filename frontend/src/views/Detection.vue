<template>
  <v-container>
    <v-row justify="center">
      <v-col cols="12" md="10">
        <h1 class="text-h4 mb-6 font-weight-bold text-primary">
          <v-icon size="large" class="mr-2">mdi-stamper</v-icon>
          Детекция документов
        </h1>

        <v-card elevation="2" class="mb-6 rounded-lg">
          <v-card-title class="text-h6 px-6 pt-6">Загрузка файла</v-card-title>
          <v-card-text class="px-6 pb-6">
            <v-file-input
              v-model="file"
              label="Выберите PDF или изображение"
              accept=".pdf, .jpg, .jpeg, .png"
              prepend-icon="mdi-cloud-upload"
              variant="outlined"
              color="primary"
              show-size
              :error-messages="errorMessage"
              @update:model-value="errorMessage = ''"
            >
              <template v-slot:selection="{ fileNames }">
                <v-chip size="small" color="primary" class="mr-2">
                  {{ fileNames[0] }}
                </v-chip>
              </template>
            </v-file-input>

            <div class="d-flex justify-end mt-4">
              <v-btn
                color="primary"
                size="large"
                :loading="loading"
                :disabled="!file"
                @click="uploadFile"
                prepend-icon="mdi-magnify"
              >
                Начать анализ
              </v-btn>
            </div>
          </v-card-text>
        </v-card>

        <v-expand-transition>
          <div v-if="result">
            <v-row>
              <v-col cols="12" md="4">
                <v-card class="h-100 rounded-lg" color="blue-lighten-5" variant="flat">
                  <v-card-item>
                    <div class="text-overline mb-1">Всего найдено</div>
                    <div class="text-h3 font-weight-bold text-primary">
                      {{ totalDetections }}
                    </div>
                    <div class="d-flex gap-2 mt-2">
                      <v-chip size="small" color="success">
                        Печатей: {{ countType('stamp') }}
                      </v-chip>
                      <v-chip size="small" color="info">
                        Подписей: {{ countType('signature') }}
                      </v-chip>
                    </div>
                  </v-card-item>
                </v-card>
              </v-col>

              <v-col cols="12" md="8">
                <v-card class="rounded-lg" title="Детализация по страницам">
                  <v-list lines="two">
                    <v-list-group v-for="(page, index) in parsedResult" :key="index" :value="page.page">
                      <template v-slot:activator="{ props }">
                        <v-list-item v-bind="props" prepend-icon="mdi-file-document-outline">
                          <v-list-item-title>Страница {{ page.page }}</v-list-item-title>
                          <v-list-item-subtitle>
                            Найдено объектов: {{ page.detections.length }}
                          </v-list-item-subtitle>
                        </v-list-item>
                      </template>

                      <v-list-item
                        v-for="(det, i) in page.detections"
                        :key="i"
                        :prepend-icon="det.name === 'stamp' ? 'mdi-check-decagram' : 'mdi-draw'"
                      >
                        <v-list-item-title class="text-capitalize">
                          {{ det.name === 'stamp' ? 'Печать' : 'Подпись' }}
                        </v-list-item-title>
                        <v-list-item-subtitle>
                          Уверенность: {{ (det.confidence * 100).toFixed(1) }}%
                          <br />
                          Координаты: [{{ det.box.x1.toFixed(0) }}, {{ det.box.y1.toFixed(0) }}]
                        </v-list-item-subtitle>
                      </v-list-item>
                    </v-list-group>
                  </v-list>
                </v-card>
              </v-col>
            </v-row>

            <v-expansion-panels class="mt-6">
              <v-expansion-panel title="Показать технические данные (JSON)">
                <v-expansion-panel-text>
                  <pre class="json-code">{{ JSON.stringify(parsedResult, null, 2) }}</pre>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </div>
        </v-expand-transition>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed } from 'vue';
import api from '@/services/api';

const file = ref(null);
const result = ref(null);
const loading = ref(false);
const errorMessage = ref('');

// Парсим результат, так как бэк может вернуть строку JSON внутри поля
const parsedResult = computed(() => {
  if (!result.value) return [];
  
  return result.value.map(page => {
    let detections = page.detections;
    // Если пришла строка, парсим её
    if (typeof detections === 'string') {
      try {
        detections = JSON.parse(detections);
      } catch (e) {
        console.error("Ошибка парсинга JSON детекции", e);
        detections = [];
      }
    }
    return { ...page, detections };
  });
});

const totalDetections = computed(() => {
  return parsedResult.value.reduce((acc, page) => acc + page.detections.length, 0);
});

const countType = (type) => {
  return parsedResult.value.reduce((acc, page) => {
    return acc + page.detections.filter(d => d.name === type).length;
  }, 0);
};

const uploadFile = async () => {
  if (!file.value) return;

  loading.value = true;
  result.value = null;
  errorMessage.value = '';

  const formData = new FormData();
  // Vuetify 3 иногда возвращает массив файлов, берем первый
  const fileToSend = Array.isArray(file.value) ? file.value[0] : file.value;
  formData.append('file', fileToSend);

  try {
    const response = await api.post('/detection/predict', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000 // Увеличиваем таймаут до 30 секунд для тяжелых PDF
    });
    result.value = response.data.results;
  } catch (error) {
    console.error('Ошибка:', error);
    errorMessage.value = 'Не удалось обработать файл. Попробуйте другой или повторите позже.';
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.json-code {
  background: #f5f5f5;
  padding: 15px;
  border-radius: 8px;
  overflow-x: auto;
  font-size: 0.85rem;
  font-family: monospace;
}
.gap-2 {
  gap: 8px;
}
</style>
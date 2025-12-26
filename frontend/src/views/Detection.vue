<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-6 text-primary font-weight-bold">
          <v-icon class="mr-2">mdi-stamper</v-icon>
          Анализ документов
        </h1>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="4">
        <v-card elevation="2" class="rounded-lg">
          <v-card-title>Загрузка файла</v-card-title>
          <v-card-text>
            <v-file-input
              v-model="file"
              label="Выберите документ (PDF, JPG)"
              accept=".pdf, .jpg, .jpeg, .png"
              prepend-icon=""
              prepend-inner-icon="mdi-file-document-outline"
              variant="outlined"
              color="primary"
              :show-size="1000"
              @update:model-value="result = null"
            ></v-file-input>

            <v-btn
              block
              color="primary"
              size="large"
              class="mt-4"
              :loading="loading"
              :disabled="!file"
              @click="uploadFile"
            >
              <v-icon left>mdi-magnify</v-icon>
              Найти печати и подписи
            </v-btn>

            <v-alert
              v-if="errorMessage"
              type="error"
              variant="tonal"
              class="mt-4"
              closable
            >
              {{ errorMessage }}
            </v-alert>
          </v-card-text>
        </v-card>

        <v-slide-y-transition>
          <v-card v-if="result" class="mt-4 rounded-lg bg-blue-lighten-5" variant="flat">
            <v-card-text>
              <div class="text-overline mb-1">Результат</div>
              <div class="text-h3 font-weight-bold text-primary mb-2">
                {{ totalItems }}
              </div>
              <div class="d-flex flex-wrap gap-2">
                <v-chip color="success" label>
                  <v-icon start size="small">mdi-check-decagram</v-icon>
                  Печатей: {{ countType('stamp') }}
                </v-chip>
                <v-chip color="info" label>
                  <v-icon start size="small">mdi-draw</v-icon>
                  Подписей: {{ countType('signature') }}
                </v-chip>
              </div>
            </v-card-text>
          </v-card>
        </v-slide-y-transition>
      </v-col>

      <v-col cols="12" md="8">
        <v-fade-transition mode="out-in">
          <v-card v-if="!result && !loading" variant="outlined" class="d-flex align-center justify-center pa-12" style="height: 300px; border-style: dashed;">
            <div class="text-center text-grey">
              <v-icon size="64" color="grey-lighten-2">mdi-file-find-outline</v-icon>
              <div class="mt-4 text-h6">Загрузите файл для проверки</div>
              <div class="text-body-2">Нейросеть найдет все печати и подписи</div>
            </div>
          </v-card>

          <div v-else-if="result">
            <v-card class="rounded-lg" elevation="2">
              <v-list lines="three">
                <template v-for="(page, i) in result" :key="i">
                  <v-list-subheader class="font-weight-bold text-uppercase bg-grey-lighten-4">
                    Страница {{ page.page }}
                  </v-list-subheader>
                  
                  <template v-if="page.detections && page.detections.length">
                    <v-list-item
                      v-for="(item, k) in page.detections"
                      :key="k"
                      :prepend-icon="item.name === 'stamp' ? 'mdi-check-decagram' : 'mdi-draw'"
                    >
                      <v-list-item-title class="text-capitalize font-weight-bold">
                        {{ item.name === 'stamp' ? 'Печать' : 'Подпись' }}
                      </v-list-item-title>
                      
                      <v-list-item-subtitle>
                        <span class="text-green-darken-1">
                          Точность: {{ (item.confidence * 100).toFixed(1) }}%
                        </span>
                        <span class="mx-2">•</span>
                        Координаты: x={{ item.box.x1.toFixed(0) }}, y={{ item.box.y1.toFixed(0) }}
                      </v-list-item-subtitle>
                    </v-list-item>
                  </template>
                  
                  <v-list-item v-else>
                    <v-list-item-title class="text-grey font-italic">
                      Объектов не найдено
                    </v-list-item-title>
                  </v-list-item>
                  
                  <v-divider v-if="i < result.length - 1"></v-divider>
                </template>
              </v-list>
            </v-card>

            <v-expansion-panels class="mt-4" variant="popout">
              <v-expansion-panel title="Показать JSON данные">
                <v-expansion-panel-text>
                  <pre class="code-block">{{ JSON.stringify(result, null, 2) }}</pre>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </div>
        </v-fade-transition>
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

// Подсчет общего количества
const totalItems = computed(() => {
  if (!result.value) return 0;
  return result.value.reduce((acc, page) => acc + (page.detections?.length || 0), 0);
});

// Подсчет по типам
const countType = (type) => {
  if (!result.value) return 0;
  return result.value.reduce((acc, page) => {
    return acc + (page.detections?.filter(d => d.name === type).length || 0);
  }, 0);
};

const uploadFile = async () => {
  if (!file.value) return;

  loading.value = true;
  result.value = null;
  errorMessage.value = '';

  const formData = new FormData();
  // Vuetify 3 возвращает массив файлов
  const fileToSend = Array.isArray(file.value) ? file.value[0] : file.value;
  formData.append('file', fileToSend);

  try {
    const response = await api.post('/detection/predict', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000 // Таймаут 60 секунд (для больших PDF)
    });
    
    result.value = response.data.results;
  } catch (error) {
    console.error('Ошибка:', error);
    errorMessage.value = 'Ошибка при обработке. Проверьте консоль или повторите попытку.';
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.gap-2 {
  gap: 8px;
}
.code-block {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  overflow-x: auto;
  max-height: 300px;
}
</style>
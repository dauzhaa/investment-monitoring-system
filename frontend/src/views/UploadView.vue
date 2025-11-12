<template>
  <v-app>
    <v-main>
      <v-container>
        <v-row justify="center">
          <v-col cols="12" md="8">
            <v-sheet class="pa-6" rounded="lg" elevation="4">
              <div class="d-flex justify-space-between align-center mb-4">
                <h2>Загрузить отчет</h2>
                <v-btn @click="handleLogout" color="grey" variant="text">
                  Выйти
                </v-btn>
              </div>

              <v-file-input
                v-model="file"
                label="Выберите Excel-файл (.xlsx)"
                variant="outlined"
                accept=".xlsx, .xls"
                @update:modelValue="clearMessages"
              ></v-file-input>

              <v-alert
                v-if="message"
                type="success"
                variant="tonal"
                class="mb-4"
              >
                {{ message }}
              </v-alert>

              <v-alert v-if="error" type="error" variant="tonal" class="mb-4">
                {{ error }}
              </v-alert>

              <v-btn
                @click="handleUpload"
                :loading="loading"
                :disabled="!file"
                color="primary"
                block
                size="large"
              >
                Загрузить и отправить на проверку
              </v-btn>
            </v-sheet>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import api from '@/services/api';

// v-model="file" будет хранить здесь один File-объект, или null
const file = ref(null);
const loading = ref(false);
const message = ref(null);
const error = ref(null);

const router = useRouter();

const clearMessages = () => {
  message.value = null;
  error.value = null;
};

const handleLogout = () => {
  localStorage.removeItem('token');
  router.push('/login');
};

const handleUpload = async () => {
  // --- vvv --- ИСПРАВЛЕНИЕ 1 --- vvv ---
  // Было: if (!file.value[0]) return;
  // Стало: Проверяем сам 'file.value'
  if (!file.value) return;
  // --- ^^^ --- ИСПРАВЛЕНИЕ 1 --- ^^^ ---

  loading.value = true;
  clearMessages();

  const formData = new FormData();
  
  // --- vvv --- ИСПРАВЛЕНИЕ 2 --- vvv ---
  // Было: formData.append('file', file.value[0]);
  // Стало: 'file.value' - это и есть сам файл
  formData.append('file', file.value);
  // --- ^^^ --- ИСПРАВЛЕНИЕ 2 --- ^^^ ---

  try {
    // Наш 'api.js' (перехватчик) автоматически добавит токен
    const response = await api.post('/reports/upload', formData);

    // Успех! API вернул ответ от Celery "File accepted"
    message.value = response.data.detail || 'Файл принят в обработку!';
    file.value = null; // Очищаем поле файла
  } catch (err) {
    // Ошибка (Например, "ИНН не совпадает" от excel_processor)
    error.value =
      err.response?.data?.detail || 'Произошла неизвестная ошибка.';
  } finally {
    loading.value = false;
  }
};
</script>
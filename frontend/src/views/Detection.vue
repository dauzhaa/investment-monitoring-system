<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">Детекция подписей и печатей</h1>
        <v-card class="pa-4">
          
          <v-file-input
            v-model="file"
            label="Загрузите PDF или изображение"
            accept=".pdf, .jpg, .jpeg, .png"
            prepend-icon="mdi-file-document-outline"
            outlined
            dense
          ></v-file-input>

          <v-btn 
            color="primary" 
            @click="uploadFile" 
            :loading="loading"
            :disabled="!file"
          >
            Обработать
          </v-btn>
        </v-card>
      </v-col>
    </v-row>

    <v-row v-if="result">
      <v-col cols="12">
        <v-card class="mt-4 pa-4">
          <h2 class="text-h6">Результаты:</h2>
          <pre style="background: #f5f5f5; padding: 10px; overflow: auto;">{{ JSON.parse(result) }}</pre>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue';
import api from '@/services/api';

const file = ref(null);
const result = ref(null);
const loading = ref(false);

const uploadFile = async () => {
  if (!file.value) return;

  loading.value = true;
  const formData = new FormData();
  formData.append('file', file.value);

  try {
    const fileToSend = Array.isArray(file.value) ? file.value[0] : file.value;
    formData.set('file', fileToSend);

    const response = await api.post('/detection/predict', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });

    result.value = response.data.results;
  } catch (error) {
    console.error('Ошибка загрузки:', error);
    alert('Ошибка при обработке файла');
  } finally {
    loading.value = false;
  }
};
</script>
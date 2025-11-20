<template>
  <div>
    <h1 class="text-h4 font-weight-bold mb-4">Импорт данных</h1>
    
    <v-row>
      <v-col cols="12" md="6">
        <v-card class="pa-4" border style="border-style: dashed !important; border-width: 2px !important;">
          <div class="text-center py-8">
            <v-icon icon="mdi-cloud-upload" size="64" color="primary" class="mb-4"></v-icon>
            <div class="text-h6 mb-2">Перетащите файл Excel (П-2) сюда</div>
            <div class="text-caption text-grey mb-6">Поддерживаются .xlsx, .xls</div>
            
            <v-file-input
              v-model="file"
              label="Выберите файл на компьютере"
              variant="outlined"
              prepend-icon=""
              density="compact"
              class="mx-auto"
              style="max-width: 300px;"
            ></v-file-input>
            
            <v-btn color="primary" class="mt-4" @click="uploadFile" :loading="uploading" :disabled="!file">
              Загрузить и обработать
            </v-btn>
          </div>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="6">
        <v-card title="История загрузок" elevation="1">
          <v-list lines="two">
             <v-list-item title="Отчет_2024_Q3.xlsx" subtitle="Загружено: Сегодня, 14:30">
               <template v-slot:prepend><v-icon color="green">mdi-check-circle</v-icon></template>
             </v-list-item>
             <v-list-item title="Отчет_2024_Q2.xlsx" subtitle="Загружено: 15.08.2024">
               <template v-slot:prepend><v-icon color="green">mdi-check-circle</v-icon></template>
             </v-list-item>
          </v-list>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';

const file = ref(null);
const uploading = ref(false);

const uploadFile = async () => {
  if (!file.value) return;
  uploading.value = true;
  
  const formData = new FormData();
  formData.append('file', file.value[0]); // Vuetify возвращает массив

  try {
    // Используем токен из localStorage
    const token = localStorage.getItem('token');
    await axios.post('/upload', formData, {
      headers: { Authorization: `Bearer ${token}` }
    });
    alert('Файл успешно загружен и отправлен в обработку!');
    file.value = null;
  } catch (e) {
    alert('Ошибка загрузки');
  } finally {
    uploading.value = false;
  }
};
</script>
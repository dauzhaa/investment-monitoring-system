<template>
  <div>
    <h1 class="text-h4 font-weight-bold mb-4">Импорт данных</h1>
    
    <v-row>
      <v-col cols="12" md="6">
        <v-card class="pa-4" border style="border-style: dashed !important; border-width: 2px !important;">
          <div class="text-center py-8">
            <v-icon icon="mdi-cloud-upload" size="64" color="primary" class="mb-4"></v-icon>
            <div class="text-h6 mb-2">Перетащите файл Excel (П-2) сюда</div>
            <div class="text-caption text-grey mb-4">Поддерживаются .xlsx, .xls</div>
            
            <v-file-input
              v-model="file"
              label="Выберите файл на компьютере"
              variant="outlined"
              prepend-icon=""
              density="compact"
              accept=".xlsx,.xls"
              class="mx-auto"
              style="max-width: 300px;"
            ></v-file-input>
            
            <v-text-field
              v-model="year"
              label="Год отчетности"
              type="number"
              variant="outlined"
              density="compact"
              class="mx-auto mt-2"
              style="max-width: 150px;"
              hint="Оставьте пустым для автоопределения"
              persistent-hint
            ></v-text-field>
            
            <v-btn color="primary" class="mt-4" @click="uploadFile" :loading="uploading" :disabled="!file">
              Загрузить и обработать
            </v-btn>
            
            <v-alert v-if="uploadResult" :type="uploadResult.type" class="mt-4 text-left" density="compact">
              {{ uploadResult.message }}
            </v-alert>
          </div>
        </v-card>
      </v-col>
      
      <v-col cols="12" md="6">
        <v-card title="История загрузок" elevation="1">
          <v-list lines="two">
            <v-list-item v-for="item in uploadHistory" :key="item.id" :title="item.filename" :subtitle="`Загружено: ${item.date}`">
              <template v-slot:prepend>
                <v-icon :color="item.status === 'success' ? 'green' : 'red'">
                  {{ item.status === 'success' ? 'mdi-check-circle' : 'mdi-alert-circle' }}
                </v-icon>
              </template>
            </v-list-item>
            <v-list-item v-if="uploadHistory.length === 0">
              <v-list-item-title class="text-grey">Нет загрузок</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import api from '@/services/api';

const file = ref(null);
const year = ref('');
const uploading = ref(false);
const uploadResult = ref(null);
const uploadHistory = ref([]);

const uploadFile = async () => {
  if (!file.value || !file.value.length) return;
  
  uploading.value = true;
  uploadResult.value = null;
  
  const formData = new FormData();
  formData.append('file', file.value[0]);
  
  // Добавляем год если указан
  if (year.value) {
    formData.append('year', year.value);
  }

  try {
    const response = await api.post('/reports/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    
    uploadResult.value = {
      type: 'success',
      message: `Файл успешно загружен! Обработано записей: ${response.data.processed || 'в процессе'}`
    };
    
    // Добавляем в историю
    uploadHistory.value.unshift({
      id: Date.now(),
      filename: file.value[0].name,
      date: new Date().toLocaleString('ru-RU'),
      status: 'success'
    });
    
    file.value = null;
    year.value = '';
    
  } catch (e) {
    console.error('Ошибка загрузки:', e);
    uploadResult.value = {
      type: 'error',
      message: e.response?.data?.detail || 'Ошибка загрузки файла'
    };
    
    uploadHistory.value.unshift({
      id: Date.now(),
      filename: file.value[0]?.name || 'Неизвестный файл',
      date: new Date().toLocaleString('ru-RU'),
      status: 'error'
    });
  } finally {
    uploading.value = false;
  }
};
</script>
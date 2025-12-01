<template>
  <v-container>
    <h1 class="text-h4 font-weight-bold mb-4">Мониторинг сдачи</h1>

    <v-card class="mb-4 pa-4">
      <v-row align="center">
        <v-col cols="3">
          <v-select 
            v-model="selectedQuarter" 
            :items="[1,2,3,4]" 
            label="Квартал" 
            hide-details
          ></v-select>
        </v-col>
        <v-col cols="3">
          <v-btn color="primary" prepend-icon="mdi-download" @click="downloadReport">
            Скачать отчет за квартал
          </v-btn>
        </v-col>
      </v-row>
    </v-card>

    <v-data-table :headers="headers" :items="organizations" :loading="loading">
      <template v-slot:item.status="{ item }">
        <v-chip :color="item.status === 'Сдан' ? 'green' : 'red'">
          {{ item.status }}
        </v-chip>
      </template>

      <template v-slot:item.actions="{ item }">
        <v-btn v-if="item.status === 'Сдан'" icon size="small" color="primary" @click="downloadOrgReport(item.id)">
           <v-icon>mdi-file-download</v-icon>
        </v-btn>
        <v-btn v-else color="warning" size="small" @click="remindOrg(item)">
           Напомнить
        </v-btn>
      </template>
    </v-data-table>
  </v-container>
</template>

<script setup>
import { ref } from 'vue';

const selectedQuarter = ref(1);
const loading = ref(false);
const headers = [
    { title: 'Организация', key: 'name' },
    { title: 'ИНН', key: 'inn' },
    { title: 'Статус', key: 'status' },
    { title: 'Действия', key: 'actions' }
];
// Пример данных (замени на API call)
const organizations = ref([
    { id: 1, name: 'ООО Пример', inn: '7200001', status: 'Сдан' },
    { id: 2, name: 'ЗАО Тест', inn: '7200002', status: 'Просрочен' }
]);

const downloadReport = () => {
    alert(`Скачивание сводного отчета за ${selectedQuarter.value} квартал...`);
    // window.open(`/api/reports/export/summary?quarter=${selectedQuarter.value}`)
};

const downloadOrgReport = (id) => {
    alert(`Скачивание отчета организации ID: ${id}`);
};

const remindOrg = (item) => {
    alert(`Напоминание отправлено на email для ${item.name}. (В системе это происходит автоматически по Celery)`);
};
</script>
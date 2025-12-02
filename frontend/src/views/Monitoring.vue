<template>
  <v-container>
    <h1 class="text-h4 font-weight-bold mb-4">Мониторинг сдачи</h1>

    <v-card class="mb-4 pa-4">
      <v-row align="center">
        <v-col cols="12" md="3">
          <v-select 
            v-model="selectedYear" 
            :items="[2022, 2023, 2024, 2025]" 
            label="Год" 
            variant="outlined"
            density="compact"
            hide-details
            @update:model-value="loadData"
          ></v-select>
        </v-col>

        <v-col cols="12" md="3">
          <v-select 
            v-model="selectedQuarter" 
            :items="quarters" 
            item-title="title"
            item-value="value"
            label="Период" 
            variant="outlined"
            density="compact"
            hide-details
            @update:model-value="loadData"
          ></v-select>
        </v-col>

        <v-col cols="12" md="3">
          <v-btn 
            block 
            color="success" 
            prepend-icon="mdi-file-excel" 
            @click="downloadSummary"
            :loading="downloading"
          >
            Скачать свод (Excel)
          </v-btn>
        </v-col>
      </v-row>
    </v-card>

    <v-data-table 
        :headers="headers" 
        :items="organizations" 
        :loading="loading"
        class="elevation-1"
        items-per-page="15"
    >
      <template v-slot:item.status="{ item }">
        <v-chip 
          :color="getStatusColor(item.status)" 
          size="small"
          class="font-weight-bold"
        >
          {{ item.status }}
        </v-chip>
      </template>

      <template v-slot:item.actions="{ item }">
        <div class="d-flex gap-2 justify-end">
            <v-btn v-if="item.status === 'Сдан'" 
                   icon="mdi-download" 
                   size="small" 
                   color="primary" 
                   variant="text"
                   title="Скачать отчет организации"
                   @click="downloadOrgReport(item.id)">
            </v-btn>

            <v-btn v-else 
                   prepend-icon="mdi-bell-ring" 
                   size="small" 
                   color="warning" 
                   variant="tonal"
                   @click="remindOrg(item)">
               Напомнить
            </v-btn>
        </div>
      </template>
    </v-data-table>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from '@/services/api'; // Use configured api instance

const selectedYear = ref(2025);
const selectedQuarter = ref(0); 
const loading = ref(false);
const downloading = ref(false);
const organizations = ref([]);

const quarters = [
    { title: 'Весь год', value: 0 },
    { title: '1 Квартал', value: 1 },
    { title: '2 Квартал', value: 2 },
    { title: '3 Квартал', value: 3 },
    { title: '4 Квартал', value: 4 },
];

const headers = [
    { title: 'Организация', key: 'name', width: '40%' },
    { title: 'ИНН', key: 'inn' },
    { title: 'Район', key: 'district' },
    { title: 'Статус', key: 'status', align: 'center' },
    { title: 'Действия', key: 'actions', align: 'end', sortable: false }
];

const getStatusColor = (status) => {
    if (status === 'Сдан') return 'green-lighten-4 text-green-darken-3';
    if (status === 'Не запланировано') return 'grey-lighten-2 text-grey-darken-2';
    return 'red-lighten-4 text-red-darken-3';
};

const loadData = async () => {
    loading.value = true;
    try {
        const res = await axios.get('/monitoring/status', {
            params: { year: selectedYear.value, quarter: selectedQuarter.value }
        });
        organizations.value = res.data.items;
    } catch (e) {
        console.error("Ошибка загрузки:", e);
    } finally {
        loading.value = false;
    }
};

const downloadSummary = async () => {
    downloading.value = true;
    try {
        const response = await axios.get('/monitoring/export/quarterly', {
            params: { year: selectedYear.value, quarter: selectedQuarter.value },
            responseType: 'blob' // Important for binary files
        });
        
        // Create link to download
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `report_${selectedYear.value}_q${selectedQuarter.value}.xlsx`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    } catch (e) {
        console.error('Ошибка скачивания:', e);
        alert('Не удалось скачать файл');
    } finally {
        downloading.value = false;
    }
};

const downloadOrgReport = async (orgId) => {
    // Similar logic for individual reports if needed
    alert('Функция скачивания индивидуального отчета в разработке');
};

const remindOrg = async (item) => {
    if(!item.email) return alert('У этой организации нет Email!');
    try {
        await axios.post('/monitoring/remind', {
            organization_id: item.id,
            year: selectedYear.value,
            quarter: selectedQuarter.value,
            email: item.email
        });
        alert(`Напоминание успешно отправлено на ${item.email}`);
    } catch(e) {
        alert('Ошибка отправки напоминания');
    }
};

onMounted(loadData);
</script>
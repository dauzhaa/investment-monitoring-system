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
          <v-btn block color="success" prepend-icon="mdi-file-excel" @click="downloadSummary">
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
          :color="item.status === 'submitted' ? 'green-lighten-4' : 'red-lighten-4'" 
          :class="item.status === 'submitted' ? 'text-green-darken-3' : 'text-red-darken-3'"
          size="small"
          class="font-weight-bold"
        >
          {{ item.status === 'submitted' ? 'Сдан' : 'Не сдан' }}
        </v-chip>
      </template>

      <template v-slot:item.actions="{ item }">
        <div class="d-flex gap-2">
            <v-btn v-if="item.status === 'submitted'" 
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
import axios from 'axios';

const selectedYear = ref(2025);
const selectedQuarter = ref(0); // 0 = Весь год по умолчанию
const loading = ref(false);
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

const loadData = async () => {
    loading.value = true;
    try {
        const res = await axios.get('/api/v1/monitoring/status', {
            params: { year: selectedYear.value, quarter: selectedQuarter.value }
        });
        organizations.value = res.data.items;
    } catch (e) {
        console.error("Ошибка загрузки:", e);
    } finally {
        loading.value = false;
    }
};

const downloadSummary = () => {
    const url = `/api/v1/monitoring/export/quarterly?year=${selectedYear.value}&quarter=${selectedQuarter.value}`;
    // Открываем в новой вкладке, чтобы браузер начал скачивание
    window.open(axios.defaults.baseURL + url, '_blank');
};

const downloadOrgReport = (orgId) => {
    const url = `/api/v1/monitoring/export/organization/${orgId}?year=${selectedYear.value}&quarter=${selectedQuarter.value}`;
    window.open(axios.defaults.baseURL + url, '_blank');
};

const remindOrg = async (item) => {
    if(!item.email) return alert('У этой организации нет Email!');
    
    try {
        await axios.post('/api/v1/monitoring/remind', {
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
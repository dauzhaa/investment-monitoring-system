<template>
  <div>
    <h1 class="text-h4 font-weight-bold mb-4 text-primary">Реестр организаций</h1>

    <v-card elevation="2" class="rounded-lg mb-4">
      <v-card-text>
        <v-row align="center">
          <v-col cols="12" md="4">
            <v-text-field
              v-model="search"
              prepend-inner-icon="mdi-magnify"
              label="Поиск по названию или ИНН"
              single-line
              hide-details
              variant="outlined"
              density="compact"
              color="primary"
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="4">
            <v-select
              v-model="filterMunicipality"
              :items="municipalities"
              label="Фильтр по району"
              clearable
              hide-details
              variant="outlined"
              density="compact"
              color="primary"
            ></v-select>
          </v-col>
          <v-col cols="12" md="4" class="text-right">
             <v-chip color="primary" variant="tonal" size="large" label>
                Всего: {{ filteredOrgs.length }}
             </v-chip>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <v-card elevation="2" class="rounded-lg">
      <v-data-table
        :headers="headers"
        :items="filteredOrgs"
        :search="search"
        :loading="loading"
        hover
        class="elevation-0"
        items-per-page="10"
      >
        <template v-slot:item.cluster_group="{ item }">
          <v-chip :color="getClusterColor(item.cluster_group)" size="small" variant="flat" class="font-weight-bold">
            {{ getClusterName(item.cluster_group) }}
          </v-chip>
        </template>

        <template v-slot:item.total_investment="{ item }">
          <span class="font-weight-medium">{{ formatMoney(item.total_investment) }}</span>
        </template>

        <template v-slot:item.actions="{ item }">
          <v-btn icon="mdi-chart-box-outline" size="small" color="primary" variant="text" @click="openDetails(item)"></v-btn>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="dialog" max-width="900px">
      <v-card v-if="selectedOrg" class="rounded-lg">
        <v-toolbar color="primary" density="compact">
           <v-toolbar-title class="text-body-1 font-weight-bold">{{ selectedOrg.info.name }}</v-toolbar-title>
           <v-btn icon="mdi-close" @click="dialog = false"></v-btn>
        </v-toolbar>
        
        <v-card-text class="pa-4 bg-grey-lighten-5">
          <v-row>
            <v-col cols="12" md="4">
              <v-card class="mb-4 pa-3" elevation="1">
                  <div class="text-caption text-grey">ИНН</div>
                  <div class="text-body-2 font-weight-bold mb-2">{{ selectedOrg.info.inn }}</div>
                  
                  <div class="text-caption text-grey">Район</div>
                  <div class="text-body-2 mb-2">{{ selectedOrg.info.municipality }}</div>

                  <div class="text-caption text-grey">Контакты</div>
                  <div class="text-body-2">{{ selectedOrg.info.email || 'Не указан' }}</div>
              </v-card>
              
              <v-btn block color="success" prepend-icon="mdi-file-excel" variant="outlined">
                 Скачать справку
              </v-btn>
            </v-col>
            
            <v-col cols="12" md="8">
               <v-card elevation="1" class="pa-2">
                   <org-forecast-chart :history="selectedOrg.reports" :forecast="selectedOrg.forecast" />
               </v-card>
            </v-col>
          </v-row>

          <v-row class="mt-1">
             <v-col cols="12">
                <h3 class="text-h6 mb-2">История отчетов</h3>
                <v-table density="compact">
                   <thead>
                     <tr>
                       <th>Год</th>
                       <th>Квартал</th>
                       <th>Сумма</th>
                       <th>Фед. бюджет</th>
                       <th>Рег. бюджет</th>
                     </tr>
                   </thead>
                   <tbody>
                     <tr v-for="(rep, i) in selectedOrg.reports" :key="i">
                        <td>{{ rep.year }}</td>
                        <td>{{ rep.quarter }}</td>
                        <td class="font-weight-bold">{{ formatMoney(rep.amount) }}</td>
                        <td class="text-grey">{{ formatMoney(rep.source_fed) }}</td>
                        <td class="text-grey">{{ formatMoney(rep.source_reg) }}</td>
                     </tr>
                   </tbody>
                </v-table>
             </v-col>
          </v-row>

        </v-card-text>
      </v-card>
    </v-dialog>

  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';
import OrgForecastChart from '@/components/OrgForecastChart.vue';

const loading = ref(true);
const search = ref('');
const filterMunicipality = ref(null);
const orgs = ref([]);
const municipalities = ref([]);
const dialog = ref(false);
const selectedOrg = ref(null);

const headers = [
  { title: 'Наименование', key: 'name', width: '40%' },
  { title: 'ИНН', key: 'inn' },
  { title: 'Район', key: 'municipality' },
  { title: 'Статус', key: 'cluster_group' },
  { title: 'Инвестиции', key: 'total_investment', align: 'end' },
  { title: 'Действия', key: 'actions', sortable: false, align: 'center' },
];

const fetchData = async () => {
  loading.value = true;
  try {
    const res = await axios.get('/api/v1/organizations/');
    orgs.value = res.data;
    // Уникальные районы для фильтра
    municipalities.value = [...new Set(orgs.value.map(o => o.municipality))].sort();
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
};

const filteredOrgs = computed(() => {
  let data = orgs.value;
  if (filterMunicipality.value) {
    data = data.filter(o => o.municipality === filterMunicipality.value);
  }
  return data;
});

const getClusterColor = (id) => {
  if (id === 2) return 'green-lighten-4 text-green-darken-4';
  if (id === 1) return 'orange-lighten-4 text-orange-darken-4';
  return 'red-lighten-4 text-red-darken-4';
};
const getClusterName = (id) => {
  if (id === 2) return 'Лидер';
  if (id === 1) return 'Средний';
  return 'Отстающий';
};

const formatMoney = (val) => {
  if (!val) return '0 ₽';
  return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 }).format(val);
};

const openDetails = async (item) => {
  try {
    const res = await axios.get(`/api/v1/organizations/${item.id}`);
    selectedOrg.value = res.data;
    dialog.value = true;
  } catch (e) {
    alert("Ошибка загрузки данных организации");
  }
};

onMounted(fetchData);
</script>
<template>
  <v-container>
    <h1 class="text-h4 font-weight-bold mb-4">Реестр организаций</h1>
    
    <v-card class="elevation-1">
      <v-data-table
        :headers="headers"
        :items="items"
        :search="search"
        :loading="loading"
        items-per-page="15"
      >
         <template v-slot:top>
           <v-toolbar flat color="white" class="px-4">
             <v-text-field
                v-model="search"
                prepend-inner-icon="mdi-magnify"
                label="Поиск (ИНН, Название)"
                single-line
                hide-details
                variant="outlined"
                density="compact"
                class="mr-4"
                style="max-width: 400px;"
             ></v-text-field>
             <v-spacer></v-spacer>
             <v-chip color="primary" variant="tonal">
               Всего: {{ items.length }}
             </v-chip>
           </v-toolbar>
         </template>
         
         <template v-slot:item.is_smp="{ item }">
            <v-icon :color="item.is_smp ? 'success' : 'grey-lighten-2'">
              {{ item.is_smp ? 'mdi-check-circle' : 'mdi-minus-circle' }}
            </v-icon>
         </template>
         
         <template v-slot:item.total_investment="{ item }">
            {{ formatMoney(item.total_investment) }}
         </template>
      </v-data-table>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from '@/services/api';

const search = ref('');
const loading = ref(false);
const items = ref([]);

const headers = [
    { title: 'Наименование', key: 'name', width: '35%' },
    { title: 'ИНН', key: 'inn' },
    { title: 'Район', key: 'municipality' }, // Note: backend returns district name as 'municipality' currently
    { title: 'СМП', key: 'is_smp', align: 'center' },
    { title: 'Инвестиции (всего)', key: 'total_investment', align: 'end' }
];

const formatMoney = (val) => {
  if (!val) return '0 ₽';
  return val.toLocaleString('ru-RU') + ' тыс. ₽';
};

const loadOrgs = async () => {
    loading.value = true;
    try {
        const res = await axios.get('/organizations/');
        items.value = res.data;
    } catch (e) {
        console.error("Ошибка загрузки:", e);
    } finally {
        loading.value = false;
    }
};

onMounted(loadOrgs);
</script>
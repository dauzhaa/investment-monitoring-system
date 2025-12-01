<template>
  <v-container>
    <h1 class="text-h4 font-weight-bold mb-4">Реестр организаций</h1>
    
    <v-data-table
      :headers="headers"
      :items="items"
      :search="search"
    >
       <template v-slot:top>
         <v-text-field v-model="search" label="Поиск (ИНН, Название)" class="mx-4"></v-text-field>
       </template>
       
       <template v-slot:item.is_smp="{ item }">
          {{ item.is_smp ? 'Да' : 'Нет' }}
       </template>
       
       <template v-slot:item.status="{ item }">
          <v-chip color="blue-grey">{{ item.status || 'Нет данных' }}</v-chip>
       </template>
    </v-data-table>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

const search = ref('');
const items = ref([]);
const headers = [
    { title: 'Наименование', key: 'name' },
    { title: 'ИНН', key: 'inn' },
    { title: 'ОКВЭД', key: 'okved.code' }, // Access nested object if backend sends it
    { title: 'СМП', key: 'is_smp' },
    { title: 'Статус', key: 'status' }
];

onMounted(async () => {
    // const res = await axios.get('/api/organizations');
    // items.value = res.data;
    // Пока заглушка чтобы ты видел структуру
    items.value = [
        { name: 'Тюменский ГУ', inn: '7202010861', okved: {code: '85.22'}, is_smp: false, status: 'Сдан' }
    ];
});
</script>
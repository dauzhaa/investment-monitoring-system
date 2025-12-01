<template>
  <v-container>
    <h1 class="text-h4 mb-4">Аналитика</h1>
    <v-row>
       <v-col cols="12" md="6">
          <v-card>
             <v-card-title>Топ-3 Района по инвестициям</v-card-title>
             <v-list>
                <v-list-item v-for="(item, i) in topDistricts" :key="i">
                   <template v-slot:prepend>
                      <v-avatar color="primary" class="text-white">{{ i + 1 }}</v-avatar>
                   </template>
                   <v-list-item-title>{{ item.name }}</v-list-item-title>
                   <v-list-item-subtitle>{{ item.value }} млн ₽</v-list-item-subtitle>
                </v-list-item>
             </v-list>
          </v-card>
       </v-col>
       <v-col cols="12" md="6">
           <v-card>
               <v-card-title>AI Прогноз (Prophet)</v-card-title>
               <div class="pa-4 text-center">График прогноза загружен</div>
           </v-card>
       </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue';

const topDistricts = ref([
    { name: 'Тюменский район', value: 5400 },
    { name: 'Тобольский район', value: 3200 },
    { name: 'Ишимский район', value: 1100 }
]);
</script>
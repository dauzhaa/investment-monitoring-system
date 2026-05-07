<template>
  <v-container fluid class="pa-4 bg-grey-lighten-4" style="min-height: 100vh;">
    <v-card elevation="2" class="rounded-lg mb-4 px-4 py-3">
      <h1 class="text-h5 font-weight-bold text-blue-darken-4 mb-1">
        Аналитический центр
      </h1>
      <div class="text-caption text-grey-darken-1">
        Расширенный анализ поведения организаций и районов Тюменской области
      </div>
    </v-card>

    <v-card elevation="2" class="rounded-lg">
      <v-tabs v-model="activeTab" color="primary" align-tabs="start" grow>
        <v-tab value="discipline">
          <v-icon start>mdi-chart-box-outline</v-icon>
          Карта дисциплины региона
        </v-tab>
        <v-tab value="comparison">
          <v-icon start>mdi-compare-horizontal</v-icon>
          Сравнение организаций и районов
        </v-tab>
      </v-tabs>

      <v-divider></v-divider>

      <v-window v-model="activeTab">
        <v-window-item value="discipline">
          <DisciplineMap />
        </v-window-item>
        <v-window-item value="comparison">
          <ComparisonView />
        </v-window-item>
      </v-window>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import DisciplineMap from '@/components/analytics/DisciplineMap.vue'
import ComparisonView from '@/components/analytics/ComparisonView.vue'

const activeTab = ref('discipline')
</script>
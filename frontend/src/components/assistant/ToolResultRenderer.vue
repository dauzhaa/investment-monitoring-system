<template>
  <component :is="rendererComponent" :data="result" class="mb-4" />
</template>

<script setup>
import { computed } from 'vue'
import RankingChart from './renderers/RankingChart.vue'
// Импортируем новый график для презентации
import DisciplineChart from './renderers/DisciplineChart.vue' 

const props = defineProps({
  toolName: String,
  result: Object
})

const RENDERERS = {
  get_top_organizations: RankingChart,
  // Временно (или постоянно) привязываем этот вызов к нашему новому графику
  compare_discipline: DisciplineChart 
}

const rendererComponent = computed(() => {
  return RENDERERS[props.toolName] || null 
})
</script>
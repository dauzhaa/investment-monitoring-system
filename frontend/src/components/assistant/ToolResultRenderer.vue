<template>
  <component :is="rendererComponent" :data="result" class="mb-4" />
</template>

<script setup>
import { computed } from 'vue'
import RankingChart from './renderers/RankingChart.vue'

const props = defineProps({
  toolName: String,
  result: Object
})

const RENDERERS = {
  get_top_organizations: RankingChart,
  // get_bottom_organizations: RankingChart,
  // get_district_summary: DistrictsTable,
}

const rendererComponent = computed(() => {
  // Возвращаем специфичный компонент, если нет — можно вернуть заглушку GenericTable
  return RENDERERS[props.toolName] || null 
})
</script>
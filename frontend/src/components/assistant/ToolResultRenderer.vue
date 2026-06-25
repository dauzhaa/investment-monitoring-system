<template>
  <component :is="rendererComponent" :data="result" class="mb-4" />
</template>

<script setup>
import { computed } from 'vue'
import RankingChart from './renderers/RankingChart.vue' // <--- ТВОЙ НОВЫЙ ГРАФИК

const props = defineProps({
  toolName: String,
  result: Object
})

const RENDERERS = {
  get_top_organizations: RankingChart // <--- СВЯЗКА
}

const rendererComponent = computed(() => {
  return RENDERERS[props.toolName] || null 
})
</script>
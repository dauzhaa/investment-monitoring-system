<template>
  <div class="d-flex flex-wrap gap-2 mt-2">
    <v-chip
      v-for="sug in suggestions"
      :key="sug"
      variant="outlined"
      color="primary"
      class="bg-white"
      link
      @click="$emit('select', sug)"
    >
      <v-icon start size="16">mdi-sparkles</v-icon> {{ sug }}
    </v-chip>
  </div>
</template>

<script setup>
defineProps({ suggestions: Array })
defineEmits(['select'])
</script>
<style scoped>.gap-2 { gap: 8px; }</style>
<template>
  <div class="pa-4">
    <v-btn-toggle
      v-model="mode"
      mandatory
      color="primary"
      class="mb-4"
      density="comfortable"
    >
      <v-btn value="organizations" prepend-icon="mdi-account-group">
        Организации
      </v-btn>
      <v-btn value="districts" prepend-icon="mdi-map">
        Районы
      </v-btn>
    </v-btn-toggle>

    <PeerComparison v-if="mode === 'organizations'" />
    <DistrictsClusters v-else />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import PeerComparison from './PeerComparison.vue'
import DistrictsClusters from './DistrictsClusters.vue'

const mode = ref('organizations')
</script>
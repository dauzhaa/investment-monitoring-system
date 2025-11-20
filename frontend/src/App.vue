<template>
  <v-app v-if="$route.path === '/login'">
    <router-view />
  </v-app>

  <MainLayout v-else />
</template>

<script setup>
import MainLayout from '@/layouts/MainLayout.vue';
</script>
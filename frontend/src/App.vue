<template>
  <v-app>
    <!-- Navigation Drawer -->
    <v-navigation-drawer
      v-if="isAuthenticated"
      v-model="drawer"
      :rail="rail"
      permanent
      color="#F5F7FA"
    >
      <!-- Logo -->
      <v-list-item
        :prepend-icon="rail ? 'mdi-chart-line' : undefined"
        class="py-4"
        @click="rail = !rail"
      >
        <template v-slot:prepend v-if="!rail">
          <div class="d-flex align-center">
            <v-avatar color="#5C6BC0" size="36" class="mr-3">
              <span class="text-white font-weight-bold">72</span>
            </v-avatar>
          </div>
        </template>
        <v-list-item-title v-if="!rail" class="text-h6 font-weight-bold" style="color: #5C6BC0;">
          ИнвестМонитор
        </v-list-item-title>
        <v-list-item-subtitle v-if="!rail" class="text-caption">
          Тюменская область
        </v-list-item-subtitle>
      </v-list-item>

      <v-divider></v-divider>

      <!-- Menu Items -->
      <v-list density="compact" nav>
        <v-list-item
          v-for="item in menuItems"
          :key="item.title"
          :to="item.to"
          :prepend-icon="item.icon"
          :title="item.title"
          rounded="lg"
          class="my-1"
          color="#5C6BC0"
        ></v-list-item>
      </v-list>

      <!-- Убрана кнопка Выход из sidebar -->
    </v-navigation-drawer>

    <!-- App Bar -->
    <v-app-bar v-if="isAuthenticated" elevation="1" color="white">
      <v-app-bar-nav-icon @click="rail = !rail"></v-app-bar-nav-icon>
      
      <v-toolbar-title class="text-grey-darken-2">
        Департамент образования и науки
      </v-toolbar-title>

      <v-spacer></v-spacer>

      <!-- User Menu -->
      <v-menu>
        <template v-slot:activator="{ props }">
          <v-btn
            v-bind="props"
            variant="outlined"
            color="#5C6BC0"
            class="mr-4"
          >
            <v-icon class="mr-2">mdi-account</v-icon>
            {{ currentUser?.name || 'Администратор' }}
          </v-btn>
        </template>
        <v-list>
          <v-list-item prepend-icon="mdi-account-circle">
            <v-list-item-title>{{ currentUser?.email || 'admin@obr72.ru' }}</v-list-item-title>
            <v-list-item-subtitle>{{ currentUser?.role || 'Администратор' }}</v-list-item-subtitle>
          </v-list-item>
          <v-divider></v-divider>
          <v-list-item prepend-icon="mdi-cog" @click="openSettings">
            <v-list-item-title>Настройки</v-list-item-title>
          </v-list-item>
          <v-list-item prepend-icon="mdi-logout" @click="logout" color="error">
            <v-list-item-title>Выход</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>
    </v-app-bar>

    <!-- Main Content -->
    <v-main :class="{ 'bg-grey-lighten-4': isAuthenticated }">
      <router-view />
    </v-main>

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000" location="top right">
      {{ snackbar.text }}
      <template v-slot:actions>
        <v-btn variant="text" @click="snackbar.show = false">Закрыть</v-btn>
      </template>
    </v-snackbar>
  </v-app>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const drawer = ref(true);
const rail = ref(false);
const snackbar = ref({ show: false, text: '', color: 'success' });
const currentUser = ref(null);

const isAuthenticated = computed(() => !!localStorage.getItem('token'));

const menuItems = [
  { title: 'Главная', icon: 'mdi-view-dashboard-outline', to: '/dashboard' },
  { title: 'Мониторинг сдачи', icon: 'mdi-clipboard-check-outline', to: '/monitoring' },
  { title: 'Загрузка данных', icon: 'mdi-upload-outline', to: '/upload' },
  { title: 'Организации', icon: 'mdi-domain', to: '/organizations' },
  { title: 'Аналитика', icon: 'mdi-chart-bar', to: '/analytics' },
  { title: 'Детекция', icon: 'mdi-file-search-outline', to: '/detection' },
];

const logout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  router.push('/login');
};

const openSettings = () => {};

onMounted(() => {
  const userStr = localStorage.getItem('user');
  if (userStr) {
    try {
      currentUser.value = JSON.parse(userStr);
    } catch (e) {
      currentUser.value = { name: 'Администратор', email: 'admin@obr72.ru', role: 'admin' };
    }
  }
});
</script>

<style>
:root {
  --primary-color: #5C6BC0;
  --success-color: #26A69A;
  --warning-color: #FF8A65;
  --accent-color: #FFCA28;
  --info-color: #42A5F5;
}
</style>
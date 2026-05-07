<template>
  <v-app>
    <v-navigation-drawer v-model="drawer" app color="grey-lighten-4">
      <div class="d-flex align-center pa-4">
        <v-avatar color="primary" size="40" class="mr-3">
          <span class="text-h6 text-white">72</span>
        </v-avatar>
        <div>
          <div class="text-subtitle-2 font-weight-bold">Мониторинг</div>
          <div class="text-caption">Тюменская область</div>
        </div>
      </div>

      <v-divider></v-divider>

      <v-list density="compact" nav>
        <v-list-item to="/dashboard" prepend-icon="mdi-view-dashboard" title="Дашборд" value="dash"></v-list-item>
        <v-list-item 
          to="/monitoring" 
          prepend-icon="mdi-monitor-dashboard" 
          title="Мониторинг сдачи" 
          value="monitoring"
        ></v-list-item>
        <v-list-item to="/upload" prepend-icon="mdi-file-excel" title="Загрузка данных" value="upload"></v-list-item>
        <v-list-item 
          to="/organizations" 
          prepend-icon="mdi-domain" 
          title="Организации" 
          value="orgs"
        ></v-list-item>
        <v-list-item 
          to="/ipo-analytics" 
          title="Центр ИПО" 
          prepend-icon="mdi-radar" 
          value="ipo-analytics"
          class="text-blue-darken-3 font-weight-medium"
        ></v-list-item>
        <v-list-item to="/analytics" title="Аналитика" prepend-icon="mdi-chart-bar" value="analytics"></v-list-item>
        <v-list-item
          prepend-icon="mdi-stamper" 
          title="Детекция"
          to="/detection"
        ></v-list-item>
      </v-list>

      
      <template v-slot:append>
        <div class="pa-2">
          <v-btn block color="error" variant="outlined" @click="logout">
            Выход
          </v-btn>
        </div>
      </template>
    </v-navigation-drawer>

    <v-app-bar app elevation="1" color="white">
      <v-app-bar-nav-icon @click="drawer = !drawer"></v-app-bar-nav-icon>
      <v-app-bar-title class="text-body-1 text-grey-darken-2">
        Департамент образования и науки
      </v-app-bar-title>
      <v-spacer></v-spacer>
      <v-chip class="mr-4" color="primary" variant="outlined">
        <v-icon start>mdi-account</v-icon>
        Администратор
      </v-chip>
    </v-app-bar>

    <v-main class="bg-grey-lighten-5">
      <v-container fluid class="pa-6">
        <router-view />
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const drawer = ref(true);
const router = useRouter();

const logout = () => {
  localStorage.removeItem('token');
  router.push('/login');
};
</script>
<template>
  <div>
    <v-row class="mb-4 align-center">
      <v-col>
        <h1 class="text-h4 font-weight-bold text-primary">InvestMonitor72</h1>
        <div class="text-subtitle-1 text-grey">Система мониторинга и прогнозирования</div>
      </v-col>
      <v-col class="text-right">
        <v-btn 
          prepend-icon="mdi-refresh" 
          color="primary" 
          variant="tonal" 
          @click="loadData" 
          :loading="loading"
        >
          Обновить данные
        </v-btn>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 pt-6" elevation="2" rounded="lg">
          <div class="text-overline text-grey mb-1">Общий объем инвестиций</div>
          <div class="text-h4 font-weight-bold text-primary">
            {{ stats.total_investment }} <span class="text-h6 text-grey">млн ₽</span>
          </div>
          <div class="text-caption text-green mt-2">
            <v-icon icon="mdi-arrow-up" size="x-small"></v-icon> Данные из БД
          </div>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 pt-6" elevation="2" rounded="lg">
          <div class="text-overline text-grey mb-1">Организаций в базе</div>
          <div class="text-h4 font-weight-bold">{{ stats.org_count }}</div>
          <div class="text-caption text-grey mt-2">Активных субъектов</div>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 pt-6" elevation="2" rounded="lg">
          <div class="text-overline text-grey mb-1">Качество данных</div>
          <div class="text-h4 font-weight-bold text-teal">{{ stats.data_quality }}%</div>
          <div class="text-caption text-teal mt-2">
             Заполненность отчетов
          </div>
        </v-card>
      </v-col>
      
      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 pt-6" elevation="2" rounded="lg">
          <div class="text-overline text-grey mb-1">Исполнение бюджета</div>
          <div class="text-h4 font-weight-bold">{{ stats.execution_rate }}%</div>
          <div class="text-caption text-orange mt-2">
            <v-icon icon="mdi-alert-circle-outline" size="x-small"></v-icon> Риск неосвоения
          </div>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mt-4">
      
      <v-col cols="12" md="8">
        <v-card elevation="2" class="h-100 rounded-lg">
          <v-card-title class="d-flex align-center">
            Инвестиционная активность районов
            <v-spacer></v-spacer>
            <v-chip size="small" color="green" variant="text">Лидеры</v-chip>
            <v-chip size="small" color="orange" variant="text">Стабильные</v-chip>
            <v-chip size="small" color="red" variant="text">Низкая активность</v-chip>
          </v-card-title>
          <v-divider></v-divider>
          
          <v-card-text style="height: 500px; padding: 0;">
             <div v-if="loading" class="d-flex fill-height align-center justify-center">
               <v-progress-circular indeterminate color="primary"></v-progress-circular>
             </div>
             <map-chart v-else :clusteringData="clusterData" @region-click="handleRegionClick"/>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="4">
        
        <v-card elevation="2" class="mb-4 rounded-lg">
          <v-card-title>Структура финансирования</v-card-title>
          <v-divider></v-divider>
          <v-card-text>
             <pie-chart :chartData="stats.pie_chart" />
          </v-card-text>
        </v-card>

        <v-card elevation="2" class="rounded-lg">
          <v-card-title>Выявленные аномалии</v-card-title>
          <v-divider></v-divider>
          
          <v-list density="compact" v-if="stats.anomalies && stats.anomalies.length > 0">
            <v-list-item 
                v-for="(item, i) in stats.anomalies" 
                :key="i"
                :title="item.org_name"
            >
              <v-list-item-subtitle>
                  <span class="text-red font-weight-bold">{{ item.reason }}</span>
                  <span class="text-grey ms-2">({{ item.period }})</span>
              </v-list-item-subtitle>

              <template v-slot:prepend>
                <v-icon :color="item.type === 'critical' ? 'red' : 'orange'">
                    {{ item.type === 'critical' ? 'mdi-fire' : 'mdi-trending-up' }}
                </v-icon>
              </template>
              <template v-slot:append>
                  <span class="font-weight-bold">{{ item.amount }} ₽</span>
              </template>
            </v-list-item>
          </v-list>
          
          <div v-else class="pa-4 text-center text-grey">
              Аномалий не найдено
          </div>
        </v-card>

      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import MapChart from '@/components/MapChart.vue';
import PieChart from '@/components/PieChart.vue'; 

const loading = ref(true);
const clusterData = ref(null);

// Начальное состояние статистики
const stats = ref({
  total_investment: 0,
  org_count: 0,
  execution_rate: 0,
  data_quality: 0,
  pie_chart: [],
  anomalies: []
});

const loadData = async () => {
  loading.value = true;
  try {
    // 1. Запускаем пересчет кластеров
    await axios.post('http://localhost:8000/api/v1/analytics/calculate/clustering');
    
    // 2. Загружаем карту
    const mapRes = await axios.get('http://localhost:8000/api/v1/analytics/map');
    clusterData.value = mapRes.data;
    
    // 3. Загружаем статистику (включая диаграмму и аномалии)
    const statsRes = await axios.get('http://localhost:8000/api/v1/analytics/stats');
    stats.value = statsRes.data;
    
  } catch (e) {
    console.error("Ошибка загрузки:", e);
  } finally {
    loading.value = false;
  }
};

const handleRegionClick = (regionName) => {
  alert(`Выбран район: ${regionName}. Здесь можно открыть детальный отчет.`);
};

onMounted(() => {
  loadData();
});
</script>
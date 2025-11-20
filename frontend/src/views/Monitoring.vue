<template>
  <div>
    <h1 class="text-h4 font-weight-bold mb-4 text-primary">Мониторинг отчетности</h1>

    <v-card elevation="2" class="rounded-lg mb-4">
      <v-card-text>
        <v-row align="center">
          <v-col cols="12" md="2">
            <v-select
              v-model="selectedYear"
              :items="[2023, 2024, 2025]"
              label="Год"
              variant="outlined"
              density="compact"
              hide-details
              color="primary"
              @update:model-value="loadData"
            ></v-select>
          </v-col>
          <v-col cols="12" md="2">
            <v-select
              v-model="selectedQuarter"
              :items="[1, 2, 3, 4]"
              label="Квартал"
              variant="outlined"
              density="compact"
              hide-details
              color="primary"
              @update:model-value="loadData"
            ></v-select>
          </v-col>
          
          <v-col cols="12" md="5">
            <div class="d-flex justify-space-between mb-1">
               <span class="text-caption text-grey">Прогресс сбора</span>
               <span class="font-weight-bold">
                 {{ monitorStats?.submitted || 0 }} / {{ monitorStats?.total || 0 }}
               </span>
            </div>
            <v-progress-linear
              :model-value="monitorStats?.percent || 0"
              color="success"
              height="10"
              striped
              rounded
            ></v-progress-linear>
            <div class="text-right text-caption mt-1">
              {{ monitorStats?.percent || 0 }}% сдано
            </div>
          </v-col>

          <v-col cols="12" md="3" class="text-right">
             <v-btn 
               color="error" 
               variant="flat" 
               prepend-icon="mdi-email-alert"
               @click="sendReminders"
               :loading="reminding"
               :disabled="!monitorStats?.overdue || monitorStats.overdue === 0"
             >
               Напомнить всем
             </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <v-card elevation="2" class="rounded-lg">
      <v-data-table
        :headers="headers"
        :items="items"
        :loading="loading"
        :search="search"
        items-per-page="10"
      >
        <template v-slot:top>
           <v-toolbar flat density="compact" color="white">
              <v-text-field
                v-model="search"
                prepend-inner-icon="mdi-magnify"
                label="Поиск организации..."
                single-line
                hide-details
                variant="plain"
                class="mx-4"
              ></v-text-field>
              
              <v-spacer></v-spacer>
              
              <v-btn 
                color="primary" 
                variant="tonal" 
                prepend-icon="mdi-microsoft-excel" 
                title="Скачать свод"
                @click="downloadReport"
                :loading="downloading"
              >
                Скачать Excel
              </v-btn>
           </v-toolbar>
        </template>

        <template v-slot:item.status="{ item }">
          <v-chip 
            :color="item.status === 'submitted' ? 'green' : 'red'" 
            size="small" 
            label
            class="font-weight-bold"
          >
            <v-icon start size="small" :icon="item.status === 'submitted' ? 'mdi-check-circle' : 'mdi-alert-circle'"></v-icon>
            {{ item.status === 'submitted' ? 'Сдано' : 'Просрочено' }}
          </v-chip>
        </template>

        <template v-slot:item.actions="{ item }">
          <v-btn 
            v-if="item.status === 'overdue'"
            size="small" 
            color="orange" 
            variant="text" 
            icon="mdi-bell-ring"
            title="Напомнить лично"
            @click="remindOne(item)"
          ></v-btn>
          <v-btn 
             v-else
             size="small"
             color="blue"
             variant="text"
             icon="mdi-eye"
             title="Посмотреть отчет"
          ></v-btn>
        </template>
      </v-data-table>
    </v-card>

    <v-snackbar v-model="snackbar" :color="snackbarColor" timeout="3000">
      {{ snackbarText }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';

const loading = ref(false);
const reminding = ref(false); 
const downloading = ref(false);
const search = ref('');

const selectedYear = ref(2024);
const selectedQuarter = ref(1);

const rawItems = ref([]);
// Инициализируем явно, чтобы не было undefined
const monitorStats = ref({ total: 0, submitted: 0, overdue: 0, percent: 0 });

const snackbar = ref(false);
const snackbarText = ref('');
const snackbarColor = ref('success');

const headers = [
  { title: 'Наименование', key: 'name', width: '40%' },
  { title: 'Район', key: 'municipality' },
  { title: 'Email', key: 'email' },
  { title: 'Статус', key: 'status', align: 'center' },
  { title: '', key: 'actions', sortable: false, align: 'end' },
];

const loadData = async () => {
  loading.value = true;
  try {
    const res = await axios.get('http://localhost:8000/api/v1/monitoring/status', {
        params: { year: selectedYear.value, quarter: selectedQuarter.value }
    });
    
    // Защита от пустых данных
    if (res.data) {
      rawItems.value = res.data.items || [];
      // Важно: берем meta из ответа и кладем в monitorStats
      monitorStats.value = res.data.meta || { total: 0, submitted: 0, overdue: 0, percent: 0 };
    }
  } catch (e) {
    console.error("Ошибка загрузки:", e);
  } finally {
    loading.value = false;
  }
};

const items = computed(() => {
   return rawItems.value;
});

const sendReminders = async () => {
  if (!confirm(`Вы уверены, что хотите отправить письма ${monitorStats.value.overdue} организациям?`)) return;
  
  reminding.value = true;
  try {
     await axios.post('/api/v1/monitoring/remind/all', null, {
        params: { year: selectedYear.value, quarter: selectedQuarter.value }
     });
     showMsg('Рассылка запущена успешно!', 'success');
  } catch (e) {
     showMsg('Ошибка запуска рассылки', 'error');
  } finally {
     reminding.value = false;
  }
};

const remindOne = (item) => {
    showMsg(`Письмо отправлено на ${item.email || 'нет почты'}`, 'info');
};

const downloadReport = async () => {
  downloading.value = true;
  try {
    const response = await axios.get('/api/v1/monitoring/export/summary', {
      params: { year: selectedYear.value, quarter: selectedQuarter.value },
      responseType: 'blob',
    });
    
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `report_${selectedYear.value}_q${selectedQuarter.value}.xlsx`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
  } catch (e) {
    showMsg("Ошибка скачивания отчета", "error");
  } finally {
    downloading.value = false;
  }
};

const showMsg = (text, color) => {
    snackbarText.value = text;
    snackbarColor.value = color;
    snackbar.value = true;
};

onMounted(loadData);
</script>
<template>
  <div class="monitoring">
    <v-card class="stat-card pa-4 mb-4">
      <v-row align="center" dense>
        <v-col cols="12" sm="3">
          <v-select v-model="selectedYear" :items="[2022, 2023, 2024, 2025]" label="Год" variant="outlined" density="compact" hide-details />
        </v-col>
        <v-col cols="12" sm="3">
          <v-select v-model="selectedQuarter" :items="quarterOptions" item-title="title" item-value="value" label="Период" variant="outlined" density="compact" hide-details />
        </v-col>
        <v-col cols="12" sm="3">
          <v-select v-model="selectedDistricts" :items="districts" item-title="name" item-value="name" label="Район" variant="outlined" density="compact" hide-details clearable multiple chips />
        </v-col>
        <v-col cols="12" sm="3" class="d-flex gap-2">
          <v-btn color="#1B3A5C" variant="flat" @click="loadStatus" :loading="loading" block>
            <v-icon start>mdi-magnify</v-icon>
            Показать
          </v-btn>
        </v-col>
      </v-row>
    </v-card>

    <div class="d-flex justify-end gap-2 mb-4">
      <v-btn
        variant="flat"
        color="#D32F2F"
        size="default"
        prepend-icon="mdi-email-alert-outline"
        @click="sendAllReminders"
        :disabled="statusData.overdue === 0"
        class="text-white font-weight-bold"
        :class="{ 'btn-pulse': statusData.overdue > 0 }"
      >
        Напомнить всем ({{ statusData.overdue }})
      </v-btn>
      <v-btn variant="flat" color="#1B3A5C" size="default" class="text-white font-weight-bold" prepend-icon="mdi-download" @click="exportData">
        Экспорт в Excel
      </v-btn>
    </div>

    <v-row class="mb-4">
      <v-col cols="12" md="5">
        <v-card class="stat-card pa-4 h-100 d-flex flex-column align-center justify-center relative">
          <div class="text-h6 font-weight-bold align-self-start w-100 mb-2" style="color: #1B3A5C">Прогресс сдачи отчетности</div>
          <div style="height: 250px; width: 100%;">
            <v-chart v-if="!loading" class="chart" :option="donutOption" autoresize />
            <div v-else class="d-flex align-center justify-center h-100 text-grey text-h6">Загрузка данных...</div>
          </div>
        </v-card>
      </v-col>

      <v-col cols="12" md="7">
        <v-row class="h-100" dense>
          <v-col cols="6">
            <v-card class="stat-card pa-4 text-center h-100 d-flex flex-column justify-center border-left-total">
              <div class="text-h3 font-weight-bold" style="color: #1B3A5C">{{ statusData.total }}</div>
              <div class="text-subtitle-1 font-weight-bold text-grey-darken-3 mt-1">Всего организаций</div>
            </v-card>
          </v-col>
          <v-col cols="6">
            <v-card class="stat-card pa-4 text-center h-100 d-flex flex-column justify-center border-left-submitted">
              <div class="text-h3 font-weight-bold" style="color: #2E7D32">{{ statusData.submitted }}</div>
              <div class="text-subtitle-1 font-weight-bold text-grey-darken-3 mt-1">Сдано вовремя</div>
            </v-card>
          </v-col>
          <v-col cols="6">
            <v-card class="stat-card pa-4 text-center h-100 d-flex flex-column justify-center border-left-overdue">
              <div class="text-h3 font-weight-bold" style="color: #D32F2F">{{ statusData.overdue }}</div>
              <div class="text-subtitle-1 font-weight-bold text-grey-darken-3 mt-1">Просрочено</div>
            </v-card>
          </v-col>
          <v-col cols="6">
            <v-card class="stat-card pa-4 text-center h-100 d-flex flex-column justify-center border-left-unplanned">
              <div class="text-h3 font-weight-bold" style="color: #757575">{{ statusData.not_planned }}</div>
              <div class="text-subtitle-1 font-weight-bold text-grey-darken-3 mt-1">Не запланировано</div>
            </v-card>
          </v-col>
        </v-row>
      </v-col>
    </v-row>

    <v-card class="stat-card">
      <v-row class="pa-3" align="center" dense>
        <v-col cols="12" sm="7">
          <v-text-field v-model="search" prepend-inner-icon="mdi-magnify" placeholder="Поиск по наименованию учреждения или ИНН..." variant="solo-filled" density="compact" flat hide-details />
        </v-col>
        <v-col cols="12" sm="5" class="d-flex align-center justify-end">
          <span class="text-subtitle-2 text-grey-darken-2 mr-3 font-weight-bold">Показывать записей:</span>
          <v-select v-model="itemsPerPage" :items="[10, 25, 50, 100, { title: 'Все', value: -1 }]" density="compact" variant="outlined" hide-details style="max-width: 130px;" />
        </v-col>
      </v-row>

      <v-data-table
        :headers="headers"
        :items="filteredItems"
        :search="search"
        :items-per-page="itemsPerPage"
        :row-props="getRowProps"
        density="default"
        hover
        class="monitoring-table"
      >
        <template #item.status="{ item }">
          <div class="d-flex align-center gap-2">
            <v-icon size="12" :color="statusColor(item.status)">mdi-circle</v-icon>
            <span class="text-subtitle-2 font-weight-bold" :style="{ color: statusColor(item.status) }">{{ statusText(item.status) }}</span>
          </div>
        </template>

        <template #item.is_smp="{ item }">
          <v-icon v-if="item.is_smp" size="22" color="#2E7D32">mdi-check-circle</v-icon>
          <span v-else class="text-grey">—</span>
        </template>

        <template #item.actions="{ item }">
          <v-btn v-if="item.status === 'overdue'" icon size="small" variant="text" color="#F57C00" @click="sendReminder(item)">
            <v-icon size="22">mdi-email-outline</v-icon>
            <v-tooltip activator="parent" location="top">Отправить уведомление</v-tooltip>
          </v-btn>
          <v-btn v-if="item.status === 'submitted'" icon size="small" variant="text" color="#1B3A5C">
            <v-icon size="22">mdi-download</v-icon>
            <v-tooltip activator="parent" location="top">Скачать архив отчёта</v-tooltip>
          </v-btn>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="reminderDialog" max-width="550">
      <v-card class="stat-card pa-2">
        <v-card-title class="text-h6 font-weight-bold pt-4 px-4" style="color: #1B3A5C;">Отправка уведомления</v-card-title>
        <v-card-text class="px-4 pb-0">
          <p class="mb-4 text-subtitle-1 text-grey-darken-3">Кому: <strong style="color: #1A1A2E;">{{ selectedOrgForReminder?.name }}</strong></p>
          <v-textarea v-model="reminderMessage" label="Текст официального уведомления" variant="outlined" auto-grow rows="4" color="#1B3A5C"></v-textarea>
        </v-card-text>
        <v-card-actions class="px-4 pb-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" class="font-weight-bold" color="grey-darken-2" @click="reminderDialog = false" :disabled="isSendingReminder">Отмена</v-btn>
          <v-btn color="#1B3A5C" class="font-weight-bold" variant="flat" :loading="isSendingReminder" @click="confirmSendReminder">Отправить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar" :color="snackbarColor" timeout="3000" class="font-weight-bold">{{ snackbarText }}</v-snackbar>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { monitoringAPI, dictionariesAPI, organizationsAPI, notificationsAPI } from '@/services/api'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components'
import VChart from 'vue-echarts'

use([CanvasRenderer, PieChart, TooltipComponent, LegendComponent, TitleComponent])

const selectedYear = ref(2025)
const selectedQuarter = ref(1)
const selectedDistricts = ref([])
const loading = ref(false)
const search = ref('')
const districts = ref([])
const itemsPerPage = ref(25)

const snackbar = ref(false)
const snackbarText = ref('')
const snackbarColor = ref('success')

const quarterOptions = [
  { title: '1 кв (январь–март)', value: 1 },
  { title: '2 кв (январь–июнь)', value: 2 },
  { title: '3 кв (январь–сентябрь)', value: 3 },
  { title: '4 кв (январь–декабрь)', value: 4 },
]

const statusData = ref({ total: 0, submitted: 0, overdue: 0, not_planned: 0, percent: 0, items: [] })

// Конфигурация Пай-чарта адаптирована под экран проектора
const donutOption = computed(() => ({
  title: {
    text: `${statusData.value.percent}%`,
    left: '40%',
    top: 'center',
    textAlign: 'center',
    textVerticalAlign: 'middle',
    textStyle: { fontSize: 32, fontWeight: 'bold', color: statusData.value.percent >= 80 ? '#2E7D32' : '#F57C00' }
  },
  tooltip: { 
    trigger: 'item', 
    formatter: '{b}: <b>{c}</b> ({d}%)',
    textStyle: { fontSize: 14 }
  },
  legend: { 
    right: '5%', 
    top: 'center', 
    orient: 'vertical',
    itemGap: 16, 
    itemWidth: 14, 
    itemHeight: 14,
    textStyle: { fontSize: 14, fontWeight: 'bold', color: '#333' }
  },
  series: [
    {
      type: 'pie',
      radius: ['55%', '82%'],
      center: ['35%', '50%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 5, borderColor: '#fff', borderWidth: 2 },
      label: { show: false },
      data: [
        { value: statusData.value.submitted, name: 'Сдано', itemStyle: { color: '#2E7D32' } },
        { value: statusData.value.overdue, name: 'Просрочено', itemStyle: { color: '#D32F2F' } },
        { value: statusData.value.not_planned, name: 'Не запланировано', itemStyle: { color: '#9E9E9E' } }
      ]
    }
  ]
}))

const headers = [
  { title: '№', key: 'index', width: '60px', sortable: false },
  { title: 'Организация', key: 'name', width: '40%' },
  { title: 'ИНН', key: 'inn', width: '130px' },
  { title: 'Район', key: 'district' },
  { title: 'СМП', key: 'is_smp', width: '70px', align: 'center' },
  { title: 'Статус сдачи', key: 'status', width: '150px' },
  { title: 'Действия', key: 'actions', width: '100px', sortable: false, align: 'center' },
]

const filteredItems = computed(() => (statusData.value.items || []).map((item, i) => ({ ...item, index: i + 1 })))

function statusColor(s) { return { submitted: '#2E7D32', overdue: '#D32F2F', not_planned: '#757575' }[s] || '#757575' }
function statusText(s) { return { submitted: 'Сдан', overdue: 'Просрочен', not_planned: 'Не запл.' }[s] || s }

function getRowProps({ item }) {
  return { class: `row-status-${item.status} text-body-1` }
}

async function loadDistricts() {
  try {
    const { data } = await dictionariesAPI.getDistricts()
    districts.value = data
  } catch { /* ignore */ }
}

async function loadStatus() {
  loading.value = true
  try {
    const params = { year: selectedYear.value, quarter: selectedQuarter.value }
    if (selectedDistricts.value.length) params.districts = selectedDistricts.value.join(',')
    const { data } = await monitoringAPI.getStatus(params)
    statusData.value = data
  } catch (e) { console.error(e) } finally { loading.value = false }
}

const reminderDialog = ref(false)
const selectedOrgForReminder = ref(null)
const reminderMessage = ref('')
const isSendingReminder = ref(false)

function sendReminder(item) {
  selectedOrgForReminder.value = item
  const quarterText = quarterOptions.find(q => q.value === selectedQuarter.value)?.title || ''
  reminderMessage.value = `Уважаемый руководитель! Напоминаем о необходимости срочно сдать отчетность формы П-2 за ${quarterText} ${selectedYear.value} года.`
  reminderDialog.value = true
}

async function confirmSendReminder() {
  if (!selectedOrgForReminder.value || !reminderMessage.value) return
  isSendingReminder.value = true
  try {
    await notificationsAPI.send({ organization_id: selectedOrgForReminder.value.id, message: reminderMessage.value })
    snackbarText.value = 'Уведомление успешно отправлено'
    snackbarColor.value = 'success'
    snackbar.value = true
    reminderDialog.value = false
  } catch (e) {
    snackbarText.value = 'Ошибка отправки уведомления'
    snackbarColor.value = 'error'
    snackbar.value = true
  } finally { isSendingReminder.value = false }
}

async function sendAllReminders() {
  try {
    const { data } = await monitoringAPI.sendReminders(selectedYear.value, selectedQuarter.value)
    snackbarText.value = data.message
    snackbarColor.value = 'success'
    snackbar.value = true
  } catch {
    snackbarText.value = 'Ошибка при массовой рассылке'
    snackbarColor.value = 'error'
    snackbar.value = true
  }
}

async function exportData() {
  try {
    const { data } = await organizationsAPI.exportExcel({ year: selectedYear.value, districts: selectedDistricts.value.join(',') })
    const url = URL.createObjectURL(data)
    const a = document.createElement('a')
    a.href = url
    a.download = `monitoring_${selectedYear.value}_Q${selectedQuarter.value}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) { console.error(e) }
}

onMounted(() => { loadDistricts(); loadStatus() })
</script>

<style scoped>
.gap-2 { gap: 8px; }
.chart { width: 100%; height: 100%; }

/* Левые цветные маркеры на карточках KPI для лучшей считываемости */
.border-left-total { border-left: 6px solid #1B3A5C !important; }
.border-left-submitted { border-left: 6px solid #2E7D32 !important; }
.border-left-overdue { border-left: 6px solid #D32F2F !important; }
.border-left-unplanned { border-left: 6px solid #757575 !important; }

.monitoring-table :deep(.v-data-table-header th) {
  font-size: 14px !important;
  font-weight: bold !important;
  background-color: #F8F9FA !important;
}

.monitoring-table :deep(.v-data-table__tr) {
  font-size: 14px !important;
}

.monitoring-table :deep(.row-status-submitted:hover) { background-color: rgba(46, 125, 50, 0.07) !important; }
.monitoring-table :deep(.row-status-overdue:hover) { background-color: rgba(211, 47, 47, 0.07) !important; }
.monitoring-table :deep(.row-status-not_planned:hover) { background-color: rgba(117, 117, 117, 0.07) !important; }

.btn-pulse {
  animation: pulse-red 2s infinite;
}
@keyframes pulse-red {
  0% { box-shadow: 0 0 0 0 rgba(211, 47, 47, 0.6); }
  70% { box-shadow: 0 0 0 10px rgba(211, 47, 47, 0); }
  100% { box-shadow: 0 0 0 0 rgba(211, 47, 47, 0); }
}
</style>
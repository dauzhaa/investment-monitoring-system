<template>
  <div class="monitoring">
    <v-card class="stat-card pa-4 mb-5">
      <v-row align="center" dense>
        <v-col cols="12" sm="3">
          <v-select
            v-model="selectedYear"
            :items="[2022, 2023, 2024, 2025]"
            label="Год"
            variant="outlined"
            density="compact"
            hide-details
          />
        </v-col>
        <v-col cols="12" sm="3">
          <v-select
            v-model="selectedQuarter"
            :items="quarterOptions"
            item-title="title"
            item-value="value"
            label="Период"
            variant="outlined"
            density="compact"
            hide-details
          />
        </v-col>
        <v-col cols="12" sm="3">
          <v-select
            v-model="selectedDistricts"
            :items="districts"
            item-title="name"
            item-value="name"
            label="Район"
            variant="outlined"
            density="compact"
            hide-details
            clearable
            multiple
            chips
          />
        </v-col>
        <v-col cols="12" sm="3" class="d-flex gap-2">
          <v-btn color="#1B3A5C" variant="flat" @click="loadStatus" :loading="loading" block>
            <v-icon start>mdi-magnify</v-icon>
            Показать
          </v-btn>
        </v-col>
      </v-row>
    </v-card>

    <v-row class="mb-4">
      <v-col cols="6" sm="3">
        <v-card class="stat-card pa-4 text-center">
          <div class="kpi-value" style="color: #1B3A5C">{{ statusData.total }}</div>
          <div class="kpi-label">Всего</div>
        </v-card>
      </v-col>
      <v-col cols="6" sm="3">
        <v-card class="stat-card pa-4 text-center">
          <div class="kpi-value" style="color: #2E7D32">{{ statusData.submitted }}</div>
          <div class="kpi-label">Сдано</div>
        </v-card>
      </v-col>
      <v-col cols="6" sm="3">
        <v-card class="stat-card pa-4 text-center">
          <div class="kpi-value" style="color: #D32F2F">{{ statusData.overdue }}</div>
          <div class="kpi-label">Просрочено</div>
        </v-card>
      </v-col>
      <v-col cols="6" sm="3">
        <v-card class="stat-card pa-4 text-center">
          <div class="kpi-value" style="color: #9E9E9E">{{ statusData.not_planned }}</div>
          <div class="kpi-label">Не запланировано</div>
        </v-card>
      </v-col>
    </v-row>

    <v-card class="stat-card pa-4 mb-5">
      <div class="d-flex align-center justify-space-between mb-2">
        <span class="text-body-2 font-weight-bold">Прогресс сдачи</span>
        <span class="text-h6 font-weight-black" :style="{ color: statusData.percent >= 80 ? '#2E7D32' : '#F57C00' }">
          {{ statusData.percent }}%
        </span>
      </div>
      <v-progress-linear
        :model-value="statusData.percent"
        :color="statusData.percent >= 80 ? '#2E7D32' : statusData.percent >= 50 ? '#F57C00' : '#D32F2F'"
        height="10"
        rounded
      />
    </v-card>

    <div class="d-flex justify-end gap-2 mb-3">
      <v-btn
        variant="tonal"
        color="#D32F2F"
        size="small"
        prepend-icon="mdi-email-alert-outline"
        @click="sendAllReminders"
        :disabled="statusData.overdue === 0"
      >
        Напомнить всем ({{ statusData.overdue }})
      </v-btn>
      <v-btn
        variant="tonal"
        color="#1B3A5C"
        size="small"
        prepend-icon="mdi-download"
        @click="exportData"
      >
        Экспорт в Excel
      </v-btn>
    </div>

    <v-card class="stat-card">
      <v-text-field
        v-model="search"
        prepend-inner-icon="mdi-magnify"
        placeholder="Поиск по названию или ИНН..."
        variant="solo-filled"
        density="compact"
        flat
        hide-details
        class="ma-2"
      />
      <v-data-table
        :headers="headers"
        :items="filteredItems"
        :search="search"
        :items-per-page="25"
        density="compact"
        hover
        class="monitoring-table"
      >
        <template #item.status="{ item }">
          <v-chip
            :color="statusColor(item.status)"
            size="small"
            variant="tonal"
            label
          >
            {{ statusText(item.status) }}
          </v-chip>
        </template>

        <template #item.is_smp="{ item }">
          <v-icon v-if="item.is_smp" size="18" color="#2E7D32">mdi-check-circle</v-icon>
          <span v-else class="text-grey">—</span>
        </template>

        <template #item.actions="{ item }">
          <v-btn
            v-if="item.status === 'overdue'"
            icon
            size="x-small"
            variant="text"
            color="#F57C00"
            @click="sendReminder(item)"
          >
            <v-icon>mdi-email-outline</v-icon>
            <v-tooltip activator="parent" location="top">Напомнить</v-tooltip>
          </v-btn>
          <v-btn
            v-if="item.status === 'submitted'"
            icon
            size="x-small"
            variant="text"
            color="#1B3A5C"
          >
            <v-icon>mdi-download</v-icon>
            <v-tooltip activator="parent" location="top">Скачать отчёт</v-tooltip>
          </v-btn>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="reminderDialog" max-width="500">
      <v-card class="stat-card pa-2">
        <v-card-title class="text-h6 font-weight-bold pt-4 px-4" style="color: #1B3A5C;">
          Отправка уведомления
        </v-card-title>
        <v-card-text class="px-4 pb-0">
          <p class="mb-4 text-body-2 text-grey-darken-1">
            Кому: <strong style="color: #1A1A2E;">{{ selectedOrgForReminder?.name }}</strong>
          </p>
          <v-textarea
            v-model="reminderMessage"
            label="Текст уведомления"
            variant="outlined"
            auto-grow
            rows="4"
            color="#1B3A5C"
          ></v-textarea>
        </v-card-text>
        <v-card-actions class="px-4 pb-4">
          <v-spacer></v-spacer>
          <v-btn variant="text" color="grey-darken-1" @click="reminderDialog = false" :disabled="isSendingReminder">Отмена</v-btn>
          <v-btn color="#1B3A5C" variant="flat" :loading="isSendingReminder" @click="confirmSendReminder">Отправить</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar" :color="snackbarColor" timeout="3000">
      {{ snackbarText }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
// ИМПОРТ НОВОГО API notificationsAPI
import { monitoringAPI, dictionariesAPI, organizationsAPI, notificationsAPI } from '@/services/api'

const selectedYear = ref(2025)
const selectedQuarter = ref(1)
const selectedDistricts = ref([])
const loading = ref(false)
const search = ref('')
const districts = ref([])

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

const headers = [
  { title: '№', key: 'index', width: '50px', sortable: false },
  { title: 'Организация', key: 'name', width: '35%' },
  { title: 'ИНН', key: 'inn', width: '120px' },
  { title: 'Район', key: 'district' },
  { title: 'СМП', key: 'is_smp', width: '60px', align: 'center' },
  { title: 'Статус', key: 'status', width: '140px' },
  { title: '', key: 'actions', width: '80px', sortable: false },
]

const filteredItems = computed(() => {
  return (statusData.value.items || []).map((item, i) => ({
    ...item,
    index: i + 1
  }))
})

function statusColor(s) {
  return { submitted: '#2E7D32', overdue: '#D32F2F', not_planned: '#9E9E9E' }[s] || '#9E9E9E'
}
function statusText(s) {
  return { submitted: 'Сдан', overdue: 'Просрочен', not_planned: 'Не запл.' }[s] || s
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
    if (selectedDistricts.value.length) {
      params.districts = selectedDistricts.value.join(',')
    }
    const { data } = await monitoringAPI.getStatus(params)
    statusData.value = data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

// --- ЛОГИКА ОТПРАВКИ УВЕДОМЛЕНИЙ ---
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
    // ВЫЗЫВАЕМ НАШ НОВЫЙ БЭКЕНД
    await notificationsAPI.send({
      organization_id: selectedOrgForReminder.value.id,
      message: reminderMessage.value
    })
    snackbarText.value = 'Уведомление успешно отправлено'
    snackbarColor.value = 'success'
    snackbar.value = true
    reminderDialog.value = false
  } catch (e) {
    snackbarText.value = 'Ошибка отправки уведомления'
    snackbarColor.value = 'error'
    snackbar.value = true
  } finally {
    isSendingReminder.value = false
  }
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
    const { data } = await organizationsAPI.exportExcel({
      year: selectedYear.value,
      districts: selectedDistricts.value.join(',')
    })
    const url = URL.createObjectURL(data)
    const a = document.createElement('a')
    a.href = url
    a.download = `monitoring_${selectedYear.value}_Q${selectedQuarter.value}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => {
  loadDistricts()
  loadStatus()
})
</script>

<style scoped>
.monitoring-table :deep(.v-data-table__tr:hover) {
  background: #F8F9FB !important;
}
.gap-2 { gap: 8px; }
</style>
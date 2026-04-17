<template>
  <div class="org-dashboard">
    <div v-if="loadingStats" class="text-center pa-10">
      <v-progress-circular indeterminate color="#1B3A5C" />
    </div>

    <template v-else>
      <v-card class="stat-card pa-6 mb-5" style="background: linear-gradient(135deg, #0F2439, #1B3A5C)">
        <div class="text-white">
          <h2 class="text-h5 font-weight-bold mb-1">Добро пожаловать, {{ authStore.user?.email }}!</h2>
          <p class="text-body-2" style="color: rgba(255,255,255,0.7)">Личный кабинет организации</p>
        </div>
      </v-card>

      <v-row>
        <v-col cols="12" md="6">
          <v-card class="stat-card pa-5" style="height: 100%;">
            <div class="section-title mb-4 font-weight-bold text-h6">Ваши показатели ({{ stats?.year || currentYear }} год)</div>
            
            <div v-if="!hasData" class="text-center text-grey pa-6 mt-4">
              <v-icon size="48" color="grey-lighten-1" class="mb-4">mdi-inbox-remove-outline</v-icon>
              <p class="text-body-1" style="color: var(--text-primary);">Нет данных об инвестициях</p>
              <p class="text-caption mt-2">Департамент пока не загрузил плановые или фактические показатели по вашей организации.</p>
            </div>

            <div v-else>
              <div class="mb-4 pa-4 bg-grey-lighten-4 rounded-lg">
                <div class="text-caption text-uppercase text-grey font-weight-bold mb-1">План на год</div>
                <div class="text-h5 font-weight-black text-primary">{{ formatMoney(stats.plan) }} тыс. ₽</div>
              </div>

              <div class="mb-4 pa-4 bg-blue-grey-lighten-5 rounded-lg border">
                <div class="text-caption text-uppercase text-grey font-weight-bold mb-1">Фактическое освоение</div>
                <div class="text-h5 font-weight-black text-success">{{ formatMoney(totalFact) }} тыс. ₽</div>
                <v-progress-linear :model-value="progress" color="success" height="8" rounded class="mt-2"></v-progress-linear>
                <div class="text-caption text-end mt-1">{{ progress }}% от плана</div>
              </div>

              <div v-if="stats.submissions?.length > 0">
                <div class="text-caption text-uppercase text-grey font-weight-bold mb-2">Статус отчетов</div>
                <v-list density="compact" class="pa-0">
                  <v-list-item v-for="sub in stats.submissions" :key="sub.quarter" class="px-0 border-b">
                    <v-list-item-title>{{ sub.quarter ? sub.quarter + ' квартал' : 'Годовой' }}</v-list-item-title>
                    <template v-slot:append>
                      <v-chip :color="getStatusColor(sub.status)" size="small" variant="flat" class="font-weight-bold">
                        {{ getStatusText(sub.status) }}
                      </v-chip>
                    </template>
                  </v-list-item>
                </v-list>
              </div>
            </div>
          </v-card>
        </v-col>

        <v-col cols="12" md="6">
          <v-card class="stat-card pa-5" style="height: 100%;">
            <div class="section-title mb-4 font-weight-bold text-h6">Загрузить отчёт</div>
            
            <v-select
              v-model="reportType"
              :items="reportTypes"
              item-title="title"
              item-value="value"
              label="Тип отчёта"
              variant="outlined"
              density="compact"
              class="mb-3"
              color="#1B3A5C"
              hide-details
            />

            <v-text-field
              v-model.number="selectedYear"
              label="Год"
              variant="outlined"
              density="compact"
              type="number"
              class="mb-3"
              color="#1B3A5C"
              hide-details
            />

            <v-file-input
              v-model="file"
              label="Выберите файл Excel"
              variant="outlined"
              density="compact"
              accept=".xlsx,.xls"
              prepend-icon=""
              prepend-inner-icon="mdi-file-excel"
              class="mb-4"
              color="#1B3A5C"
              hide-details
            />

            <v-btn
              color="#2E7D32"
              block
              size="large"
              class="text-white font-weight-bold"
              @click="uploadFile"
              :loading="uploading"
              :disabled="!file"
            >
              <v-icon start>mdi-upload</v-icon>
              Отправить отчёт
            </v-btn>

            <v-alert
              v-if="result"
              :type="result.status === 'success' ? 'success' : 'error'"
              variant="tonal"
              class="mt-4"
              closable
              @click:close="result = null"
            >
              <template v-if="result.status === 'success'">
                Отчёт успешно загружен в систему!
              </template>
              <template v-else>
                Ошибка: {{ result.detail }}
              </template>
            </v-alert>

            <div class="mt-6 pa-4 bg-grey-lighten-4 rounded text-center">
              <v-icon size="24" color="#1B3A5C" class="mb-2">mdi-information-outline</v-icon>
              <p class="text-caption text-grey-darken-1 mb-0">
                Пожалуйста, загружайте форму П-2 своевременно. В случае просрочки вам будет направлено уведомление.
              </p>
            </div>
          </v-card>
        </v-col>
      </v-row>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { reportsAPI } from '@/services/api'
import api from '@/services/api' // Базовый инстанс для get запросов
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// --- ЛОГИКА СТАТИСТИКИ ---
const stats = ref(null)
const loadingStats = ref(true)
const currentYear = new Date().getFullYear()

const hasData = computed(() => {
  if (!stats.value) return false
  return stats.value.plan > 0 || (stats.value.facts && stats.value.facts.length > 0)
})

const totalFact = computed(() => {
  if (!stats.value || !stats.value.facts) return 0
  return stats.value.facts.reduce((sum, f) => sum + f.amount, 0)
})

const progress = computed(() => {
  if (!stats.value || stats.value.plan === 0) return 0
  return Math.min(Math.round((totalFact.value / stats.value.plan) * 100), 100)
})

const formatMoney = (val) => new Intl.NumberFormat('ru-RU').format(val || 0)

const getStatusColor = (status) => {
  const colors = { 'submitted': 'success', 'overdue': 'error', 'pending': 'warning' }
  return colors[status] || 'grey'
}

const getStatusText = (status) => {
  const texts = { 'submitted': 'Сдан', 'overdue': 'Просрочен', 'pending': 'Ожидается' }
  return texts[status] || status
}

const fetchStats = async () => {
  try {
    const response = await api.get('/reports/my-stats')
    stats.value = response.data
  } catch (e) {
    console.error("Данные статистики не найдены или ошибка:", e)
  } finally {
    loadingStats.value = false
  }
}

// --- ЛОГИКА ЗАГРУЗКИ ---
const file = ref(null)
const reportType = ref('quarterly')
const selectedYear = ref(currentYear)
const uploading = ref(false)
const result = ref(null)

const reportTypes = [
  { title: 'Квартальный П-2', value: 'quarterly' },
  { title: 'Годовой отчёт', value: 'annual' },
]

async function uploadFile() {
  if (!file.value) return
  uploading.value = true
  result.value = null
  try {
    const { data } = await reportsAPI.upload(file.value, reportType.value, selectedYear.value)
    result.value = { status: 'success', records: data.records_processed || data.records || 0 }
    file.value = null
    // Обновляем статистику после успешной загрузки отчета
    await fetchStats()
  } catch (e) {
    result.value = { status: 'error', detail: e.response?.data?.detail || 'Ошибка при загрузке файла. Проверьте формат.' }
  } finally {
    uploading.value = false
  }
}

onMounted(() => {
  fetchStats()
})
</script>
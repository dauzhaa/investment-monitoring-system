<template>
  <div class="org-dashboard">
    <div v-if="loading" class="text-center pa-10">
      <v-progress-circular indeterminate color="#1B3A5C" />
    </div>

    <template v-else>
      <v-card class="stat-card pa-6 mb-5" style="background: linear-gradient(135deg, #0F2439, #1B3A5C)">
        <div class="text-white">
          <h2 class="text-h5 font-weight-bold mb-1">Добро пожаловать, {{ authStore.user?.email }}!</h2>
          <p class="text-body-2" style="color: rgba(255,255,255,0.7)">
            Личный кабинет организации
          </p>
        </div>
      </v-card>

      <v-row>
        <v-col cols="12" md="6">
          <v-card class="stat-card pa-5" style="height: 100%;">
            <div class="section-title">Памятка</div>
            <div class="text-center text-grey pa-6">
              <v-icon size="48" color="#1B3A5C" class="mb-4">mdi-information-outline</v-icon>
              <p class="text-body-1" style="color: var(--text-primary);">
                Обязательная сдача формы П-2
              </p>
              <p class="text-caption mt-2">
                Пожалуйста, загружайте отчёты своевременно. В случае просрочки вам будет направлено уведомление от Администратора системы.
              </p>
            </div>
          </v-card>
        </v-col>

        <v-col cols="12" md="6">
          <v-card class="stat-card pa-5" style="height: 100%;">
            <div class="section-title">Загрузить отчёт</div>
            
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

          </v-card>
        </v-col>
      </v-row>
    </template>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { reportsAPI } from '@/services/api'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const loading = ref(false)

// Логика загрузки файла
const file = ref(null)
const reportType = ref('quarterly')
const selectedYear = ref(new Date().getFullYear())
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
  } catch (e) {
    result.value = { status: 'error', detail: e.response?.data?.detail || 'Ошибка при загрузке файла. Проверьте формат.' }
  } finally {
    uploading.value = false
  }
}
</script>
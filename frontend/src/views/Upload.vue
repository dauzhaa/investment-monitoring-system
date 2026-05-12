<template>
  <div class="upload-page">
    <v-row>
      <v-col cols="12" md="7">
        <v-card class="stat-card pa-6">
          <div class="section-title">Загрузка файла Excel (форма П-2)</div>

          <div
            class="upload-dropzone"
            :class="{ 'upload-dropzone--active': isDragging }"
            @dragover.prevent="isDragging = true"
            @dragleave="isDragging = false"
            @drop.prevent="handleDrop"
            @click="triggerFileInput"
          >
            <v-icon size="64" class="upload-icon" :color="isDragging ? '#2E7D32' : '#9E9E9E'">
              mdi-cloud-upload-outline
            </v-icon>
            <p class="mt-4 text-h6 font-weight-bold" :class="isDragging ? 'text-success' : 'text-primary'">
              {{ file ? file.name : 'Перетащите файл сюда' }}
            </p>
            <p class="text-body-2 text-grey-darken-1">
              или нажмите, чтобы выбрать файл вручную (XLSX, XLS)
            </p>
            <v-file-input
              ref="hiddenFileInput"
              v-model="file"
              accept=".xlsx,.xls"
              class="d-none"
            />
          </div>

          <v-row class="mt-6" dense>
            <v-col cols="12" sm="6">
              <v-select v-model="reportType" :items="reportTypes" item-title="title" item-value="value" label="Тип отчёта" variant="outlined" density="compact" hide-details color="#1B3A5C" />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model.number="selectedYear" label="Год" variant="outlined" density="compact" type="number" hide-details color="#1B3A5C" />
            </v-col>
          </v-row>

          <v-btn color="#2E7D32" block class="mt-6 text-white text-subtitle-1 font-weight-bold" size="large" @click="uploadFile" :loading="uploading" :disabled="!file || !reportType">
            <v-icon start>mdi-upload</v-icon>
            Загрузить и обработать
          </v-btn>

          <v-expand-transition>
            <div v-if="result">
              <v-card v-if="result.status === 'success' && (!result.errors || result.errors.length === 0)" class="mt-6 pa-5 bg-green-lighten-5 border rounded-lg" elevation="0" style="border-color: #2E7D32 !important;">
                <div class="d-flex align-center mb-4">
                  <v-icon color="success" size="36" class="mr-3">mdi-check-circle</v-icon>
                  <div>
                    <div class="text-h6 text-success font-weight-bold">Файл успешно загружен</div>
                    <div class="text-caption text-grey-darken-3">Система обработала и сохранила данные без ошибок.</div>
                  </div>
                  <v-spacer></v-spacer>
                  <v-btn icon size="small" variant="text" @click="result = null"><v-icon>mdi-close</v-icon></v-btn>
                </div>
                <div class="d-flex flex-wrap gap-2">
                  <v-chip color="success" variant="flat" size="small" class="font-weight-bold">
                    Обработано записей: {{ result.records }}
                  </v-chip>
                  <v-chip color="#1B3A5C" variant="tonal" size="small">Новые / Обновлены</v-chip>
                </div>
              </v-card>

              <v-card v-else-if="result.status === 'success' && result.errors && result.errors.length > 0" class="mt-6 pa-5 bg-red-lighten-5 border rounded-lg" elevation="0" style="border-color: #D32F2F !important;">
                <div class="d-flex align-start mb-4">
                  <v-icon color="error" size="36" class="mr-3 mt-1">mdi-alert-circle</v-icon>
                  <div class="w-100">
                    <div class="d-flex justify-space-between align-center mb-1">
                      <div class="text-h6 text-error font-weight-bold">В файле найдены ошибки</div>
                      <v-btn icon size="small" variant="text" @click="result = null"><v-icon>mdi-close</v-icon></v-btn>
                    </div>
                    <div class="text-caption text-grey-darken-3 mb-3">
                      Успешно загружено записей: {{ result.records }}. Пожалуйста, исправьте следующие строки и загрузите их заново:
                    </div>
                    
                    <v-table density="compact" class="bg-transparent text-caption border rounded">
                      <thead class="bg-red-lighten-4">
                        <tr>
                          <th class="text-left font-weight-bold text-black">Строка</th>
                          <th class="text-left font-weight-bold text-black">Организация</th>
                          <th class="text-left font-weight-bold text-black">Описание проблемы</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="(err, idx) in result.errors" :key="idx">
                          <td class="font-weight-bold">{{ err.row }}</td>
                          <td>{{ err.organization || '—' }}</td>
                          <td class="text-red-darken-2">{{ Array.isArray(err.issues) ? err.issues.join(', ') : err.issues || err }}</td>
                        </tr>
                      </tbody>
                    </v-table>
                  </div>
                </div>
              </v-card>

              <v-card v-else class="mt-6 pa-5 bg-red-lighten-5 border rounded-lg" elevation="0" style="border-color: #D32F2F !important;">
                <div class="d-flex align-center">
                  <v-icon color="error" size="36" class="mr-3">mdi-alert-circle</v-icon>
                  <div>
                    <div class="text-h6 text-error font-weight-bold">Критическая ошибка файла</div>
                    <div class="text-caption text-grey-darken-3">{{ result.detail }}</div>
                  </div>
                  <v-spacer></v-spacer>
                  <v-btn icon size="small" variant="text" @click="result = null"><v-icon>mdi-close</v-icon></v-btn>
                </div>
              </v-card>
            </div>
          </v-expand-transition>
        </v-card>
      </v-col>

      <v-col cols="12" md="5">
        <v-card class="stat-card pa-5 mb-4">
          <div class="section-title">Шаблоны для заполнения</div>
          <v-list density="compact">
            <v-list-item v-for="t in templates" :key="t.type" @click="downloadTemplate(t.type)" prepend-icon="mdi-file-download-outline" :title="t.title" :subtitle="t.desc" class="rounded-lg mb-1" />
          </v-list>
        </v-card>

        <v-card class="stat-card pa-5">
          <div class="section-title">Экспорт данных (База)</div>
          <v-list density="compact">
            <v-list-item prepend-icon="mdi-calendar-range" title="Динамика 2022–2025" subtitle="ФАКТ / ПЛАН по годам" @click="exportYearly" class="rounded-lg mb-1" />
            <v-list-item prepend-icon="mdi-map-marker-multiple" title="По районам" subtitle="Все районы за выбранный год" @click="exportDistricts" class="rounded-lg mb-1" />
          </v-list>
        </v-card>
      </v-col>
    </v-row>

    <v-snackbar v-model="snackbar" :color="snackbarColor" timeout="3000">{{ snackbarText }}</v-snackbar>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { reportsAPI } from '@/services/api'

const hiddenFileInput = ref(null)
const file = ref(null)
const reportType = ref('annual')
const selectedYear = ref(new Date().getFullYear())
const uploading = ref(false)
const isDragging = ref(false)
const result = ref(null)

const snackbar = ref(false)
const snackbarText = ref('')
const snackbarColor = ref('success')

const reportTypes = [
  { title: 'Годовой отчёт', value: 'annual' },
  { title: 'Квартальный П-2', value: 'quarterly' },
]

const templates = [
  { type: 'annual', title: 'Шаблон годового отчёта', desc: 'Excel с колонками П-2' },
  { type: 'quarterly', title: 'Шаблон квартального', desc: 'Для квартальной сдачи' },
]

function triggerFileInput() {
  hiddenFileInput.value.$el.querySelector('input').click()
}

function handleDrop(e) {
  isDragging.value = false
  const dropped = e.dataTransfer.files[0]
  if (dropped) file.value = dropped
}

async function uploadFile() {
  if (!file.value) return
  uploading.value = true
  result.value = null
  try {
    const { data } = await reportsAPI.upload(file.value, reportType.value, selectedYear.value)
    result.value = { 
      status: 'success', 
      records: data.records_processed || data.records || 0, 
      errors: data.errors || [] // Теперь это всегда массив
    }
    file.value = null
  } catch (e) {
    result.value = { status: 'error', detail: e.response?.data?.detail || 'Произошла системная ошибка при парсинге файла' }
  } finally {
    uploading.value = false
  }
}

async function downloadTemplate(type) {
  try {
    const { data } = await reportsAPI.downloadTemplate(type)
    downloadBlob(data, `template_${type}.xlsx`)
  } catch (e) { showError('Ошибка скачивания шаблона') }
}

async function exportYearly() {
  try {
    const { data } = await reportsAPI.exportYearly()
    downloadBlob(data, 'yearly_2022-2025.xlsx')
  } catch (e) { showError('Ошибка экспорта данных') }
}

async function exportDistricts() {
  try {
    const { data } = await reportsAPI.exportDistricts(selectedYear.value)
    downloadBlob(data, `districts_${selectedYear.value}.xlsx`)
  } catch (e) { showError('Ошибка экспорта данных') }
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

function showError(msg) {
  snackbarText.value = msg
  snackbarColor.value = 'error'
  snackbar.value = true
}
</script>

<style scoped>
.upload-dropzone {
  border: 2px dashed #CFD8DC;
  border-radius: 16px;
  padding: 64px 24px;
  text-align: center;
  transition: all 0.3s ease;
  cursor: pointer;
  background-color: #F8F9FA;
}

.upload-dropzone:hover {
  background-color: #F1F3F5;
  border-color: #1B3A5C;
}

.upload-dropzone--active {
  border: 2px solid #2E7D32 !important;
  background-color: rgba(46, 125, 50, 0.05) !important;
}

.upload-dropzone--active .upload-icon {
  animation: bounceCloud 1s infinite;
}

@keyframes bounceCloud {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-12px); }
}

.gap-2 { gap: 8px; }
</style>
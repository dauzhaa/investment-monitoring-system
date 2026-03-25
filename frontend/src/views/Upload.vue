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
          >
            <v-icon size="56" :color="isDragging ? '#2E7D32' : '#BDBDBD'">
              mdi-cloud-upload-outline
            </v-icon>
            <p class="mt-3 text-body-1 font-weight-medium">
              Перетащите файл сюда
            </p>
            <p class="text-caption text-grey">или нажмите кнопку ниже</p>
          </div>

          <v-row class="mt-4" dense>
            <v-col cols="12" sm="4">
              <v-select
                v-model="reportType"
                :items="reportTypes"
                item-title="title"
                item-value="value"
                label="Тип отчёта"
                variant="outlined"
                density="compact"
                hide-details
                color="#1B3A5C"
              />
            </v-col>
            <v-col cols="12" sm="4">
              <v-text-field
                v-model.number="selectedYear"
                label="Год"
                variant="outlined"
                density="compact"
                type="number"
                hide-details
                color="#1B3A5C"
              />
            </v-col>
            <v-col cols="12" sm="4">
              <v-file-input
                v-model="file"
                label="Выберите файл"
                variant="outlined"
                density="compact"
                accept=".xlsx,.xls"
                prepend-icon=""
                prepend-inner-icon="mdi-file-excel"
                show-size
                hide-details
                color="#1B3A5C"
              />
            </v-col>
          </v-row>

          <v-btn
            color="#2E7D32"
            block
            class="mt-4 text-white"
            size="large"
            @click="uploadFile"
            :loading="uploading"
            :disabled="!file || !reportType"
          >
            <v-icon start>mdi-upload</v-icon>
            Загрузить и обработать
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
              Файл успешно обработан. Загружено записей: <strong>{{ result.records || 0 }}</strong>
            </template>
            <template v-else>
              Ошибка обработки: {{ result.detail }}
            </template>
          </v-alert>
        </v-card>
      </v-col>

      <v-col cols="12" md="5">
        <v-card class="stat-card pa-5 mb-4">
          <div class="section-title">Шаблоны для заполнения</div>
          <v-list density="compact">
            <v-list-item
              v-for="t in templates"
              :key="t.type"
              @click="downloadTemplate(t.type)"
              prepend-icon="mdi-file-download-outline"
              :title="t.title"
              :subtitle="t.desc"
              class="rounded-lg mb-1"
            />
          </v-list>
        </v-card>

        <v-card class="stat-card pa-5">
          <div class="section-title">Экспорт данных (База)</div>
          <v-list density="compact">
            <v-list-item
              prepend-icon="mdi-calendar-range"
              title="Динамика 2022–2025"
              subtitle="ФАКТ / ПЛАН по годам"
              @click="exportYearly"
              class="rounded-lg mb-1"
            />
            <v-list-item
              prepend-icon="mdi-map-marker-multiple"
              title="По районам"
              subtitle="Все районы за выбранный год"
              @click="exportDistricts"
              class="rounded-lg mb-1"
            />
          </v-list>
        </v-card>
      </v-col>
    </v-row>

    <v-snackbar v-model="snackbar" :color="snackbarColor" timeout="3000">
      {{ snackbarText }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { reportsAPI } from '@/services/api'

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
    result.value = { status: 'success', records: data.records_processed || data.records || 0 }
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
  } catch (e) {
    showError('Ошибка скачивания шаблона')
  }
}

async function exportYearly() {
  try {
    const { data } = await reportsAPI.exportYearly()
    downloadBlob(data, 'yearly_2022-2025.xlsx')
  } catch (e) {
    showError('Ошибка экспорта данных')
  }
}

async function exportDistricts() {
  try {
    const { data } = await reportsAPI.exportDistricts(selectedYear.value)
    downloadBlob(data, `districts_${selectedYear.value}.xlsx`)
  } catch (e) {
    showError('Ошибка экспорта данных')
  }
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
  border: 2px dashed #D0D5DD;
  border-radius: 12px;
  padding: 48px;
  text-align: center;
  transition: all 0.2s;
  cursor: pointer;
}
.upload-dropzone--active {
  border-color: #2E7D32;
  background: rgba(46, 125, 50, 0.04);
}
</style>
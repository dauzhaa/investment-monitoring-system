<template>
  <div class="organizations">
    <v-card class="stat-card pa-4 mb-5">
      <v-row align="center" dense>
        <v-col cols="12" sm="3">
          <v-text-field v-model="search" prepend-inner-icon="mdi-magnify" placeholder="Поиск по названию / ИНН" variant="outlined" density="compact" hide-details clearable color="#1B3A5C" />
        </v-col>
        <v-col cols="12" sm="3">
          <v-select v-model="filterDistricts" :items="districts" item-title="name" item-value="name" label="Район" variant="outlined" density="compact" hide-details clearable multiple chips color="#1B3A5C" />
        </v-col>
        <v-col cols="12" sm="2">
          <v-select v-model="filterSmp" :items="[{ title: 'Все', value: null }, { title: 'Да', value: true }, { title: 'Нет', value: false }]" item-title="title" item-value="value" label="СМП" variant="outlined" density="compact" hide-details color="#1B3A5C" />
        </v-col>
        <v-col cols="12" sm="2">
          <v-select v-model="selectedYear" :items="[2022, 2023, 2024, 2025]" label="Год" variant="outlined" density="compact" hide-details color="#1B3A5C" />
        </v-col>
        <v-col cols="12" sm="2" class="d-flex gap-2">
          <v-btn color="#1B3A5C" variant="flat" @click="loadOrgs" :loading="loading" block>Найти</v-btn>
        </v-col>
      </v-row>
    </v-card>

    <div class="d-flex justify-space-between align-center mb-4">
      <div class="d-flex align-center gap-4">
        <span class="text-body-2 font-weight-medium text-grey-darken-1">Найдено: {{ organizations.length }}</span>
        
        <v-btn-toggle v-model="viewMode" mandatory density="compact" color="#1B3A5C" class="rounded-lg border">
          <v-btn value="table" icon="mdi-table" size="small"></v-btn>
          <v-btn value="cards" icon="mdi-view-grid" size="small"></v-btn>
        </v-btn-toggle>
      </div>

      <v-btn variant="tonal" color="#1B3A5C" size="small" prepend-icon="mdi-microsoft-excel" @click="exportToExcel" :loading="exporting">
        Экспорт в Excel
      </v-btn>
    </div>

    <v-card v-if="viewMode === 'table'" class="stat-card">
      <v-data-table :headers="headers" :items="organizations" :items-per-page="25" density="compact" hover class="orgs-table" @click:row="(e, { item }) => navigateToDetail(item.id)">
        <template #item.name="{ item }">
          <div class="org-name">{{ item.name }}</div>
        </template>
        <template #item.district="{ item }">
          {{ item.district?.name || item.district || '—' }}
        </template>
        <template #item.is_smp="{ item }">
          <v-chip v-if="item.is_smp" size="x-small" color="#2E7D32" variant="tonal">СМП</v-chip>
        </template>
        <template #item.fact_amount="{ item }">
          <span class="font-weight-bold" style="color: #2E7D32;">{{ formatMoney(item.fact_amount) }}</span>
        </template>
        <template #item.plan_amount="{ item }">
          <span style="color: #F57C00;">{{ formatMoney(item.plan_amount) }}</span>
        </template>
      </v-data-table>
    </v-card>

    <v-row v-else dense>
      <v-col v-for="org in organizations" :key="org.id" cols="12" sm="6" md="4" lg="3">
        <v-card class="stat-card h-100 pa-4 d-flex flex-column cursor-pointer" hover @click="navigateToDetail(org.id)">
          <div class="d-flex justify-space-between align-start mb-2">
            <v-chip size="x-small" :color="org.is_smp ? '#2E7D32' : 'grey'" variant="tonal" class="font-weight-bold">
              {{ org.is_smp ? 'СМП' : 'Крупный бизнес' }}
            </v-chip>
            <div class="text-caption text-grey">ИНН: {{ org.inn }}</div>
          </div>
          <div class="text-subtitle-2 font-weight-bold mb-1" style="color: #1B3A5C; line-height: 1.3;">
            {{ org.name }}
          </div>
          <div class="text-caption text-grey-darken-1 mb-3">
            <v-icon size="14" class="mr-1">mdi-map-marker-outline</v-icon>
            {{ org.district?.name || org.district || 'Не указан' }}
          </div>
          <v-spacer></v-spacer>
          <v-divider class="mb-2"></v-divider>
          <div class="d-flex justify-space-between align-center">
            <div>
              <div class="text-caption text-grey">Факт (тыс. ₽)</div>
              <div class="text-body-2 font-weight-bold" style="color: #2E7D32;">{{ formatMoney(org.fact_amount) }}</div>
            </div>
            <div class="text-right">
              <div class="text-caption text-grey">План (тыс. ₽)</div>
              <div class="text-body-2 font-weight-bold" style="color: #F57C00;">{{ formatMoney(org.plan_amount) }}</div>
            </div>
          </div>
        </v-card>
      </v-col>
    </v-row>

    <v-snackbar v-model="snackbar" :color="snackbarColor" timeout="3000">{{ snackbarText }}</v-snackbar>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { organizationsAPI, dictionariesAPI } from '@/services/api'

const router = useRouter()

const viewMode = ref('table') // Режим отображения: table или cards
const loading = ref(false)
const exporting = ref(false)
const search = ref('')
const selectedYear = ref(2025)
const filterDistricts = ref([])
const filterSmp = ref(null)
const districts = ref([])
const organizations = ref([])

const snackbar = ref(false)
const snackbarText = ref('')
const snackbarColor = ref('success')

const headers = [
  { title: '№', key: 'index', width: '50px', sortable: false },
  { title: 'Наименование', key: 'name', width: '35%' },
  { title: 'ИНН', key: 'inn', width: '130px' },
  { title: 'Район', key: 'district' },
  { title: 'СМП', key: 'is_smp', width: '70px', align: 'center' },
  { title: 'ФАКТ, тыс. ₽', key: 'fact_amount', width: '130px', align: 'end' },
  { title: 'ПЛАН, тыс. ₽', key: 'plan_amount', width: '130px', align: 'end' },
]

function formatMoney(val) {
  if (!val) return '0'
  const thousands = val > 100000 ? Math.round(val / 1000) : val
  return new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 }).format(thousands)
}

function navigateToDetail(id) {
  router.push(`/organizations/${id}`)
}

async function loadOrgs() {
  loading.value = true
  try {
    const params = { year: selectedYear.value }
    if (search.value) params.search = search.value
    if (filterDistricts.value.length) params.districts = filterDistricts.value.join(',')
    if (filterSmp.value !== null) params.smp = filterSmp.value

    const { data } = await organizationsAPI.getAll(params)
    organizations.value = data.map((org, i) => ({ ...org, index: i + 1 }))
  } catch (e) {
    snackbarText.value = 'Ошибка загрузки данных'
    snackbarColor.value = 'error'
    snackbar.value = true
  } finally {
    loading.value = false
  }
}

async function exportToExcel() {
  exporting.value = true
  try {
    const params = { year: selectedYear.value }
    if (filterDistricts.value.length) params.districts = filterDistricts.value.join(',')
    if (filterSmp.value !== null) params.smp = String(filterSmp.value)

    const { data } = await organizationsAPI.exportExcel(params)
    const url = URL.createObjectURL(data)
    const a = document.createElement('a')
    a.href = url
    a.download = `organizations_${selectedYear.value}.xlsx`
    a.click()
    URL.revokeObjectURL(url)
    
    snackbarText.value = 'Отчет успешно выгружен'
    snackbarColor.value = 'success'
    snackbar.value = true
  } catch (e) {
    snackbarText.value = 'Ошибка экспорта'
    snackbarColor.value = 'error'
    snackbar.value = true
  } finally {
    exporting.value = false
  }
}

watch(selectedYear, loadOrgs)

onMounted(async () => {
  try {
    const { data } = await dictionariesAPI.getDistricts()
    districts.value = data
  } catch { /* ignore */ }
  loadOrgs()
})
</script>

<style scoped>
.orgs-table :deep(.v-data-table__tr) { cursor: pointer; }
.orgs-table :deep(.v-data-table__tr:hover) { background: #F8F9FB !important; }
.org-name { font-weight: 500; font-size: 13px; max-width: 400px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.gap-2 { gap: 8px; }
.gap-4 { gap: 16px; }
.cursor-pointer { cursor: pointer; }
</style>
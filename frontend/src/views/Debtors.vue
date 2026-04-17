<template>
  <v-container fluid>
    <div class="d-flex justify-space-between align-center mb-6">
      <h1 class="text-h4 font-weight-bold">
        <v-icon color="error" class="mr-2" size="large">mdi-alert-circle-outline</v-icon>
        Контроль сроков (Должники)
      </h1>
      <v-btn color="primary" prepend-icon="mdi-refresh" @click="fetchDebtors" :loading="loading">
        Обновить данные
      </v-btn>
    </div>

    <v-card class="elevation-2 rounded-lg">
      <v-data-table
        :headers="headers"
        :items="debtors"
        :loading="loading"
        hover
      >
        <template v-slot:item.report="{ item }">
          <span class="font-weight-medium">
            {{ item.quarter ? `${item.quarter} квартал ${item.year}` : `Годовой П-2 (${item.year})` }}
          </span>
        </template>

        <template v-slot:item.deadline_date="{ item }">
          {{ formatDate(item.deadline_date) }}
        </template>

        <template v-slot:item.days_overdue="{ item }">
          <v-chip color="error" variant="flat" size="small" class="font-weight-bold">
            {{ item.days_overdue }} дн.
          </v-chip>
        </template>

        <template v-slot:item.actions="{ item }">
          <v-btn
            size="small"
            color="warning"
            variant="tonal"
            prepend-icon="mdi-email-fast-outline"
            @click="sendReminder(item)"
            :loading="notifyingId === item.id"
          >
            Напомнить
          </v-btn>
        </template>

        <template v-slot:no-data>
          <v-alert type="success" variant="tonal" class="ma-4">
            Отлично! Все организации сдали отчетность вовремя.
          </v-alert>
        </template>
      </v-data-table>
    </v-card>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000">
      {{ snackbar.text }}
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api' // Твой настроенный axios

const debtors = ref([])
const loading = ref(false)
const notifyingId = ref(null)

const snackbar = ref({ show: false, text: '', color: 'success' })

const headers = [
  { title: 'Организация', key: 'organization_name', sortable: true },
  { title: 'ИНН', key: 'inn', sortable: false },
  { title: 'Отчет', key: 'report', sortable: true },
  { title: 'Дедлайн', key: 'deadline_date', sortable: true },
  { title: 'Просрочка', key: 'days_overdue', sortable: true, align: 'center' },
  { title: 'Действия', key: 'actions', sortable: false, align: 'end' },
]

const formatDate = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleDateString('ru-RU')
}

const fetchDebtors = async () => {
  loading.value = true
  try {
    const response = await api.get('/reports/overdue')
    debtors.value = response.data
  } catch (error) {
    console.error('Ошибка загрузки должников:', error)
    showSnackbar('Ошибка загрузки данных', 'error')
  } finally {
    loading.value = false
  }
}

const sendReminder = async (item) => {
  notifyingId.value = item.id
  try {
    // Дергаем тот самый роутер, который мы написали
    await api.post('/notifications/send', {
      organization_id: item.id, // ВАЖНО: убедись, что бэкенд возвращает organization_id должника
      message: `Напоминаем о необходимости сдать отчет за ${item.quarter ? item.quarter + ' кв.' : 'год'} ${item.year}!`
    })
    showSnackbar(`Уведомление отправлено в ${item.organization_name}`, 'success')
  } catch (error) {
    console.error('Ошибка отправки:', error)
    showSnackbar('Не удалось отправить уведомление', 'error')
  } finally {
    notifyingId.value = null
  }
}

const showSnackbar = (text, color) => {
  snackbar.value = { show: true, text, color }
}

onMounted(() => {
  fetchDebtors()
})
</script>
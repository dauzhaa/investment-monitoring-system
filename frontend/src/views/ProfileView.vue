<template>
  <div class="profile-view">
    <v-card class="stat-card" elevation="0">
      <v-tabs v-model="activeTab" color="#1B3A5C" align-tabs="start">
        <v-tab value="profile">Данные профиля</v-tab>
        <v-tab value="audit">Журнал аудита</v-tab>
      </v-tabs>

      <v-card-text class="pt-6">
        <v-window v-model="activeTab">
          <v-window-item value="profile">
            <v-row>
              <v-col cols="12" md="6">
                <div class="text-subtitle-2 text-grey-darken-1 mb-1">Email пользователя</div>
                <div class="text-body-1 font-weight-medium mb-4">{{ authStore.user?.email }}</div>

                <div class="text-subtitle-2 text-grey-darken-1 mb-1">Роль в системе</div>
                <div class="text-body-1 font-weight-medium mb-4">
                  <v-chip :color="authStore.isAdmin ? 'primary' : 'success'" size="small">
                    {{ authStore.isAdmin ? 'Администратор' : 'Организация' }}
                  </v-chip>
                </div>

                <div class="text-subtitle-2 text-grey-darken-1 mb-1">Статус верификации Email</div>
                <div class="text-body-1 font-weight-medium">
                  <v-icon :color="authStore.user?.is_email_verified ? 'success' : 'warning'" class="mr-1">
                    {{ authStore.user?.is_email_verified ? 'mdi-check-circle' : 'mdi-alert-circle' }}
                  </v-icon>
                  {{ authStore.user?.is_email_verified ? 'Подтвержден' : 'Требуется подтверждение' }}
                </div>
              </v-col>
            </v-row>
          </v-window-item>

          <v-window-item value="audit">
            <v-data-table :headers="auditHeaders" :items="auditLogs" :loading="loadingAudit" hover class="border rounded">
              <template #[`item.created_at`]="{ item }">
                {{ new Date(item.created_at).toLocaleString('ru-RU') }}
              </template>
              <template #[`item.details`]="{ item }">
                <pre class="text-caption bg-grey-lighten-4 pa-2 rounded" style="max-height: 100px; overflow-y: auto;">{{ JSON.stringify(item.details, null, 2) }}</pre>
              </template>
            </v-data-table>
          </v-window-item>
        </v-window>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
// Убедись, что импортируешь правильный инстанс axios
import api from '@/services/api' 

const authStore = useAuthStore()
const activeTab = ref('profile')

const auditLogs = ref([])
const loadingAudit = ref(false)
const auditHeaders = [
  { title: 'Дата и Время', key: 'created_at', width: '200px' },
  { title: 'Пользователь (ID)', key: 'user_id', width: '150px' },
  { title: 'Действие', key: 'action', width: '250px' },
  { title: 'Детали (JSON)', key: 'details' }
]

async function loadAudit() {
  loadingAudit.value = true
  try {
    const { data } = await api.get('/audit/')
    auditLogs.value = data
  } catch (e) {
    console.error('Ошибка загрузки аудита', e)
  } finally {
    loadingAudit.value = false
  }
}

watch(activeTab, (newVal) => {
  if (newVal === 'audit' && auditLogs.value.length === 0) loadAudit()
})
</script>
<template>
  <div class="profile-view">
    <v-card class="stat-card" elevation="0">
      <v-tabs v-model="activeTab" color="#1B3A5C" align-tabs="start">
        <v-tab value="profile">Данные профиля</v-tab>
        <v-tab value="organizations" v-if="authStore.isAdmin">Организации</v-tab>
        <v-tab value="audit" v-if="authStore.isAdmin">Журнал аудита</v-tab>
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

          <v-window-item value="organizations" v-if="authStore.isAdmin">
            <v-row>
              <v-col cols="12" md="8" lg="6">
                <h3 class="text-h6 mb-4">Регистрация новой организации</h3>
                <v-form @submit.prevent="createOrganization" v-model="isFormValid" ref="orgForm">
                  <v-text-field
                    v-model="newOrg.name"
                    label="Официальное наименование организации"
                    variant="outlined"
                    density="comfortable"
                    :rules="[v => !!v || 'Наименование обязательно']"
                    required
                    class="mb-2"
                  ></v-text-field>
                  
                  <v-text-field
                    v-model="newOrg.inn"
                    label="ИНН"
                    variant="outlined"
                    density="comfortable"
                    :rules="[
                      v => !!v || 'ИНН обязателен',
                      v => /^\d{10}$|^\d{12}$/.test(v) || 'ИНН должен содержать 10 или 12 цифр'
                    ]"
                    required
                    class="mb-2"
                  ></v-text-field>

                  <v-checkbox
                    v-model="newOrg.is_smp"
                    label="Субъект малого предпринимательства (СМП)"
                    color="primary"
                    hide-details
                    class="mb-4"
                  ></v-checkbox>

                  <v-btn
                    type="submit"
                    color="#1B3A5C"
                    :loading="isLoading"
                    :disabled="!isFormValid"
                    class="text-none"
                  >
                    Зарегистрировать организацию
                  </v-btn>
                </v-form>
              </v-col>
            </v-row>
          </v-window-item>

          <v-window-item value="audit" v-if="authStore.isAdmin">
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

    <v-dialog v-model="successDialog" max-width="450">
      <v-card rounded="lg">
        <v-card-title class="bg-success text-white d-flex align-center py-3">
          <v-icon class="mr-2">mdi-check-circle-outline</v-icon>
          Успешная регистрация
        </v-card-title>
        <v-card-text class="pt-5 pb-4">
          <p class="text-body-1 mb-4 text-center">Передайте эти данные представителю организации для входа в систему:</p>
          <v-alert type="info" variant="tonal" class="text-left">
            <div class="mb-1"><strong>Логин:</strong> {{ createdCredentials.email }}</div>
            <div><strong>Пароль:</strong> {{ createdCredentials.password }}</div>
          </v-alert>
        </v-card-text>
        <v-card-actions class="px-4 pb-4">
          <v-spacer></v-spacer>
          <v-btn color="primary" variant="flat" @click="closeSuccessDialog">Закрыть</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/services/api' 

const authStore = useAuthStore()
const activeTab = ref('profile')

// ==============================
// ЛОГИКА: Аудит
// ==============================
const auditLogs = ref([])
const loadingAudit = ref(false)
const auditHeaders = [
  { title: 'Дата и Время', key: 'created_at', width: '200px' },
  { title: 'Пользователь (ID)', key: 'user_id', width: '150px' },
  { title: 'Действие', key: 'action', width: '250px' },
  { title: 'Детали (JSON)', key: 'details' }
]

async function loadAudit() {
  if (!authStore.isAdmin) return
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

// ==============================
// ЛОГИКА: Создание организации
// ==============================
const isFormValid = ref(false)
const isLoading = ref(false)
const orgForm = ref(null)
const successDialog = ref(false)

const newOrg = reactive({
  name: '',
  inn: '',
  is_smp: false
})

const createdCredentials = reactive({
  email: '',
  password: ''
})

const createOrganization = async () => {
  if (!isFormValid.value) return

  isLoading.value = true
  try {
    const response = await api.post('/organizations/', {
      name: newOrg.name,
      inn: newOrg.inn,
      is_smp: newOrg.is_smp
    })
    
    // Бэкенд возвращает сгенерированный email, пароль = ИНН
    createdCredentials.email = response.data.email
    createdCredentials.password = newOrg.inn
    
    successDialog.value = true
    orgForm.value?.reset()
    
    // Если после создания мы перейдем в аудит, нужно сбросить старый лог, чтобы подтянулся новый
    auditLogs.value = [] 
  } catch (error) {
    console.error('Ошибка создания:', error)
    const errorMsg = error.response?.data?.detail || 'Произошла ошибка при создании'
    alert(`Ошибка: ${errorMsg}`)
  } finally {
    isLoading.value = false
  }
}

const closeSuccessDialog = () => {
  successDialog.value = false
}
</script>
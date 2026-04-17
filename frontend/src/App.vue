<template>
  <template v-if="route.meta.layout === 'blank'">
    <router-view />
  </template>

  <template v-else>
    <v-app :theme="darkMode ? 'dark' : 'light'">
      <v-navigation-drawer v-model="drawer" :rail="rail" permanent class="sidebar-drawer" color="#0F2439" width="280">
        <div class="sidebar-brand" :class="{ 'sidebar-brand--rail': rail }">
          <div class="brand-icon"> 
            <v-icon size="28" color="white">mdi-chart-areaspline</v-icon>
          </div>
          <transition name="fade">
            <div v-if="!rail" class="brand-text">
              <div class="brand-title">ИнвестМонитор72</div>
              <div class="brand-subtitle">Деп. образования и науки ТО</div>
            </div>
          </transition>
        </div>

        <v-divider class="mx-3 mb-2" color="rgba(255,255,255,0.1)" />

        <v-list density="compact" nav class="px-2">
          <v-list-item
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            :prepend-icon="item.icon"
            :title="item.title"
            rounded="lg"
            class="nav-item mb-1"
            active-class="nav-item--active"
          />

        </v-list>

        <template #append>
          <v-divider class="mx-3" color="rgba(255,255,255,0.1)" />
          <div class="sidebar-user" :class="{ 'sidebar-user--rail': rail }" @click="router.push('/profile')" style="cursor: pointer; border-radius: 8px; transition: background 0.2s;" onmouseover="this.style.backgroundColor='rgba(255,255,255,0.08)'" onmouseout="this.style.backgroundColor='transparent'" title="Профиль и Аудит">
            <v-avatar size="36" color="#1B3A5C">
              <v-icon color="white" size="20">mdi-account</v-icon>
            </v-avatar>
            <transition name="fade">
              <div v-if="!rail" class="user-info">
                <div class="user-email">{{ authStore.user?.email || '—' }}</div>
                <div class="user-role">{{ authStore.isAdmin ? 'Администратор' : 'Организация' }}</div>
              </div>
            </transition>
          </div>

          <div class="sidebar-actions" :class="{ 'sidebar-actions--rail': rail }">
            <v-btn icon variant="text" size="small" color="rgba(255,255,255,0.5)" @click="rail = !rail">
              <v-icon>{{ rail ? 'mdi-chevron-right' : 'mdi-chevron-left' }}</v-icon>
            </v-btn>
            <v-btn v-if="!rail" variant="text" size="small" color="rgba(255,255,255,0.5)" prepend-icon="mdi-logout" @click="handleLogout">Выйти</v-btn>
            <v-btn v-else icon variant="text" size="small" color="rgba(255,255,255,0.5)" @click="handleLogout">
              <v-icon>mdi-logout</v-icon>
            </v-btn>
          </div>
        </template>
      </v-navigation-drawer>

      <v-app-bar flat color="white" elevation="0" class="app-topbar" border="b">
        <v-app-bar-title class="topbar-title">{{ currentPageTitle }}</v-app-bar-title>
        <v-spacer></v-spacer>
        <template #append>
          
          <v-menu :close-on-content-click="false" location="bottom end">
            <template v-slot:activator="{ props }">
              <v-btn icon v-bind="props" class="mr-3" color="#1B3A5C">
                <v-badge :content="unreadNotificationsCount" :model-value="unreadNotificationsCount > 0" color="error">
                  <v-icon>mdi-bell-outline</v-icon>
                </v-badge>
              </v-btn>
            </template>
            <v-card min-width="320" max-width="400" class="rounded-lg">
              <v-card-title class="text-subtitle-1 font-weight-bold bg-grey-lighten-4 pb-2">Уведомления</v-card-title>
              
              <div v-if="authStore.isAuthenticated && authStore.user && !authStore.user.is_email_verified" class="pa-3 bg-warning-lighten-5 border-b">
                <div class="text-caption text-warning font-weight-bold mb-1"><v-icon size="small" class="mr-1">mdi-alert</v-icon>Требуется подтверждение почты</div>
                <v-btn block color="warning" variant="tonal" size="small" :loading="isRequestingCode" @click="handleRequestCode">Подтвердить Email</v-btn>
              </div>

              <v-list v-if="notifications.length > 0" class="pa-0" lines="two">
                <v-list-item v-for="n in notifications" :key="n.id" :class="{'bg-blue-grey-lighten-5': !n.is_read}" class="border-b">
                  <v-list-item-subtitle class="text-caption text-grey mt-1">{{ new Date(n.created_at).toLocaleString('ru-RU') }}</v-list-item-subtitle>
                  <div class="text-body-2 mt-1 mb-1" style="color: var(--text-primary); line-height: 1.4;">{{ n.message }}</div>
                  <template v-slot:append v-if="!n.is_read">
                      <v-btn icon="mdi-check-all" size="small" variant="text" color="#1B3A5C" title="Прочитано" @click="markAsRead(n.id)"></v-btn>
                  </template>
                </v-list-item>
              </v-list>
              <div v-else class="pa-6 text-center text-grey text-body-2">
                <v-icon size="40" color="grey-lighten-1" class="mb-2">mdi-bell-sleep-outline</v-icon><br>Нет новых уведомлений
              </div>
            </v-card>
          </v-menu>

          <v-btn icon variant="text" size="small" class="mr-1" @click="darkMode = !darkMode">
            <v-icon>{{ darkMode ? 'mdi-weather-night' : 'mdi-weather-sunny' }}</v-icon>
          </v-btn>
        </template>
      </v-app-bar>

      <v-main class="main-content" :style="{ backgroundColor: darkMode ? '#121212' : '#F5F7FA' }">
        <div class="content-wrapper">
          <v-dialog v-model="showVerifyModal" max-width="450" persistent>
            <v-card class="stat-card pa-4">
              <v-card-title class="text-center font-weight-bold text-h6">Подтверждение Email</v-card-title>
              <v-card-text class="text-center">
                <p class="mb-4 text-body-2" style="color: var(--text-secondary)">Мы отправили 6-значный код на <strong>{{ authStore.user?.email }}</strong>.</p>
                <v-otp-input v-model="verificationCode" :length="6" :loading="isVerifying" @finish="submitVerification"></v-otp-input>
                <div v-if="verifyError" class="text-error mt-3 text-caption">{{ verifyError }}</div>
              </v-card-text>
              <v-card-actions class="justify-center mt-2">
                <v-btn variant="text" color="grey-darken-1" @click="showVerifyModal = false" :disabled="isVerifying">Отмена</v-btn>
                <v-btn color="#1B3A5C" variant="flat" :loading="isVerifying" :disabled="verificationCode.length !== 6" @click="submitVerification">Подтвердить</v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>

          <router-view v-slot="{ Component }">
            <transition name="page" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </div>
      </v-main>

      <v-snackbar v-model="snackbar" :color="snackbarColor" timeout="3000">{{ snackbarText }}</v-snackbar>
    </v-app>
  </template>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { notificationsAPI, authAPI } from '@/services/api' 

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const drawer = ref(true)
const rail = ref(false)
const darkMode = ref(false)
const snackbar = ref(false)
const snackbarText = ref('')
const snackbarColor = ref('success')

const adminNav = [
  { to: '/', icon: 'mdi-view-dashboard-outline', title: 'Главная' },
  { to: '/monitoring', icon: 'mdi-clipboard-check-outline', title: 'Мониторинг сдачи' },
  { to: '/organizations', icon: 'mdi-domain', title: 'Организации' },
  { to: '/upload', icon: 'mdi-cloud-upload-outline', title: 'Загрузка данных' },
  { to: '/debtors', icon: 'mdi-account-alert-outline', title: 'Реестр должников' },
]

const orgNav = [
  { to: '/org-dashboard', icon: 'mdi-view-dashboard-outline', title: 'Мой кабинет' },
]

const navItems = computed(() => authStore.isOrganization ? orgNav : adminNav)

const pageTitles = {
  '/': 'Главная',
  '/monitoring': 'Мониторинг сдачи отчётности',
  '/organizations': 'Организации',
  '/upload': 'Загрузка данных',
  '/org-dashboard': 'Личный кабинет',
  '/profile': 'Профиль и Аудит',
  '/debtors': 'Контроль сроков (Должники)' // <-- Добавлено название страницы
}

const currentPageTitle = computed(() => {
  if (route.path.startsWith('/districts/')) return `Район: ${route.params.name}`
  if (route.path.startsWith('/organizations/') && route.params.id) return 'Карточка организации'
  return pageTitles[route.path] || ''
})

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}

// УВЕДОМЛЕНИЯ
const notifications = ref([])
const unreadNotificationsCount = computed(() => notifications.value.filter(n => !n.is_read).length)

async function fetchNotifications() {
  if (!authStore.isAuthenticated) return;
  try {
    const { data } = await notificationsAPI.getMy()
    notifications.value = data
  } catch (e) { console.error('Ошибка загрузки уведомлений', e) }
}

async function markAsRead(id) {
  try {
    await notificationsAPI.markRead(id)
    const notif = notifications.value.find(x => x.id === id)
    if (notif) notif.is_read = true
  } catch (e) { console.error('Ошибка отметки', e) }
}

// ВЕРИФИКАЦИЯ
const showVerifyModal = ref(false)
const verificationCode = ref('')
const isRequestingCode = ref(false)
const isVerifying = ref(false)
const verifyError = ref('')

async function handleRequestCode() {
  isRequestingCode.value = true
  try {
    await authAPI.requestEmailVerification()
    verificationCode.value = ''
    verifyError.value = ''
    showVerifyModal.value = true
  } catch (e) {
    snackbarText.value = 'Ошибка отправки кода'
    snackbarColor.value = 'error'
    snackbar.value = true
  } finally {
    isRequestingCode.value = false
  }
}

async function submitVerification() {
  if (verificationCode.value.length !== 6) return
  isVerifying.value = true
  verifyError.value = ''
  
  try {
    await authAPI.verifyEmail({ code: verificationCode.value })
    if (authStore.user) {
      authStore.user.is_email_verified = true
      localStorage.setItem('user', JSON.stringify(authStore.user))
    }
    showVerifyModal.value = false
    snackbarText.value = 'Email успешно подтвержден'
    snackbarColor.value = 'success'
    snackbar.value = true
  } catch (e) {
    verifyError.value = e.response?.data?.detail || 'Неверный код или истек срок действия'
    verificationCode.value = ''
  } finally {
    isVerifying.value = false
  }
}

onMounted(() => {
  fetchNotifications()
  setInterval(fetchNotifications, 30000)
})
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Golos+Text:wght@400;500;600;700;800&display=swap');

:root {
  --primary: #1B3A5C;
  --success: #2E7D32;
  --warning: #F57C00;
  --danger: #D32F2F;
  --sidebar-bg: #0F2439;
  --sidebar-hover: rgba(255, 255, 255, 0.08);
  --sidebar-active: rgba(46, 125, 50, 0.25);
  --font-body: 'Golos Text', 'Segoe UI', sans-serif;
}

* { font-family: var(--font-body) !important; }

.sidebar-brand { display: flex; align-items: center; gap: 12px; padding: 20px 16px 16px; min-height: 68px; }
.sidebar-brand--rail { justify-content: center; padding: 20px 8px 16px; }
.brand-icon { width: 40px; height: 40px; border-radius: 10px; background: linear-gradient(135deg, #1B3A5C, #2E7D32); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.brand-title { color: white; font-size: 15px; font-weight: 700; letter-spacing: 0.5px; line-height: 1.2; }
.brand-subtitle { color: rgba(255, 255, 255, 0.6); font-size: 11px; font-weight: 400; margin-top: 2px; }
.nav-item { color: rgba(255, 255, 255, 0.65) !important; font-size: 13.5px !important; font-weight: 500 !important; transition: all 0.2s ease; min-height: 44px; }
.nav-item:hover { background: var(--sidebar-hover) !important; color: white !important; }
.nav-item--active { background: var(--sidebar-active) !important; color: #4CAF50 !important; }
.nav-item--active .v-icon { color: #4CAF50 !important; }
.sidebar-user { display: flex; align-items: center; gap: 10px; padding: 12px 16px; }
.sidebar-user--rail { justify-content: center; padding: 12px 8px; }
.user-email { color: rgba(255, 255, 255, 0.8); font-size: 12px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 170px; }
.user-role { color: rgba(255, 255, 255, 0.4); font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }
.sidebar-actions { display: flex; justify-content: space-between; align-items: center; padding: 8px 12px 16px; }
.sidebar-actions--rail { flex-direction: column; gap: 4px; padding: 8px 4px 16px; }
.app-topbar { z-index: 900 !important; }
.topbar-title { font-size: 18px !important; font-weight: 600 !important; color: var(--text-primary) !important; }
.main-content { min-height: 100vh; }
.content-wrapper { padding: 24px; max-width: 1600px; margin: 0 auto; }
.page-enter-active, .page-leave-active { transition: opacity 0.25s ease, transform 0.25s ease; }
.page-enter-from { opacity: 0; transform: translateX(15px); }
.page-leave-to { opacity: 0; transform: translateX(-15px); }
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.stat-card { border-radius: 12px !important; border: 1px solid rgba(0,0,0,0.05) !important; transition: box-shadow 0.3s ease, transform 0.3s ease; }
.stat-card:hover { box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08) !important; transform: translateY(-2px); }
</style>
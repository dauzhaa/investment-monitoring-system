<template>
  <v-app>
    <div class="login-page">
      <div class="login-brand">
        <div class="brand-content">
          <div class="brand-badge">
            <v-icon size="36" color="white">mdi-chart-areaspline</v-icon>
          </div>
          <h1 class="brand-heading">ИнвестМонитор72</h1>
          <div class="brand-divider"></div>
          <p class="brand-org">Департамент образования и науки Тюменской области<br>Тюменской области</p>
        </div>
        <div class="brand-footer">
          <span>© {{ new Date().getFullYear() }} ИнвестМонитор72</span>
        </div>
      </div>

      <div class="login-form-panel">
        <div class="login-form-wrapper">
          <h2 class="form-title">Вход в систему</h2>
          <p class="form-subtitle">Введите учётные данные для доступа</p>

          <v-alert
            v-if="errorMessage"
            type="error"
            variant="tonal"
            class="mb-4"
            density="compact"
            closable
            @click:close="errorMessage = null"
          >
            {{ errorMessage }}
          </v-alert>

          <form @submit.prevent="handleLogin">
            <label class="field-label">Email</label>
            <v-text-field
              v-model="email"
              placeholder="user@example.com"
              variant="outlined"
              density="comfortable"
              prepend-inner-icon="mdi-email-outline"
              class="mb-3"
              :disabled="isLoading"
              hide-details
            />

            <label class="field-label">Пароль</label>
            <v-text-field
              v-model="password"
              placeholder="Введите пароль"
              variant="outlined"
              density="comfortable"
              prepend-inner-icon="mdi-lock-outline"
              :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
              :type="showPassword ? 'text' : 'password'"
              @click:append-inner="showPassword = !showPassword"
              class="mb-5"
              :disabled="isLoading"
              hide-details
            />

            <v-btn
              type="submit"
              block
              size="large"
              color="#1B3A5C"
              :loading="isLoading"
              class="login-btn"
            >
              Войти
            </v-btn>
          </form>
        </div>
      </div>
    </div>
  </v-app>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const showPassword = ref(false)

// НОВЫЕ ПЕРЕМЕННЫЕ для управления состоянием формы
const isLoading = ref(false)
const errorMessage = ref(null)

async function handleLogin() {
  if (!email.value || !password.value) return
  
  isLoading.value = true
  errorMessage.value = null
  
  try {
    const success = await authStore.login(email.value, password.value)
    if (success) {
      router.push(authStore.isOrganization ? '/org-dashboard' : '/')
    }
  } catch (e) {
    // Выводим ошибку, если пароль неверный
    errorMessage.value = e.response?.data?.detail || 'Ошибка авторизации. Проверьте логин и пароль.'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
/* ВСЕ ТВОИ СТИЛИ И ЦВЕТОВАЯ ПАЛИТРА ОСТАВЛЕНЫ БЕЗ ИЗМЕНЕНИЙ */
.login-page {
  display: flex;
  min-height: 100vh;
}

/* Brand panel */
.login-brand {
  width: 440px;
  background: linear-gradient(165deg, #0F2439 0%, #1B3A5C 50%, #1a5c3a 100%);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 48px;
  color: white;
  position: relative;
  overflow: hidden;
}
.login-brand::before {
  content: '';
  position: absolute;
  top: -100px;
  right: -100px;
  width: 300px;
  height: 300px;
  border-radius: 50%;
  background: rgba(46, 125, 50, 0.1);
}
.login-brand::after {
  content: '';
  position: absolute;
  bottom: -60px;
  left: -60px;
  width: 200px;
  height: 200px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.03);
}

.brand-content {
  position: relative;
  z-index: 1;
  margin-top: 80px;
}
.brand-badge {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: rgba(46, 125, 50, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
}
.brand-heading {
  font-size: 32px;
  font-weight: 800;
  letter-spacing: 1px;
  margin-bottom: 12px;
}
.brand-desc {
  font-size: 14px;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.7);
}
.brand-divider {
  width: 48px;
  height: 3px;
  background: #4CAF50;
  border-radius: 2px;
  margin: 24px 0;
}
.brand-org {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  line-height: 1.5;
}
.brand-footer {
  position: relative;
  z-index: 1;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.3);
}

/* Form panel */
.login-form-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #F8F9FB;
}
.login-form-wrapper {
  width: 100%;
  max-width: 400px;
  padding: 40px;
}
.form-title {
  font-size: 24px;
  font-weight: 700;
  color: #1A1A2E;
  margin-bottom: 4px;
}
.form-subtitle {
  font-size: 14px;
  color: #6B7280;
  margin-bottom: 32px;
}
.field-label {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
  display: block;
  margin-bottom: 6px;
}
.login-btn {
  font-weight: 600 !important;
  letter-spacing: 0.3px !important;
  text-transform: none !important;
  font-size: 15px !important;
  border-radius: 8px !important;
}

/* Mobile */
@media (max-width: 900px) {
  .login-brand {
    display: none;
  }
}
</style>
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI } from '@/services/api'
import api from '@/services/api' // Базовый инстанс для кастомных запросов

export const useAuthStore = defineStore('auth', () => {
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  const isAuthenticated = computed(() => !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isOrganization = computed(() => user.value?.role === 'organization')

  async function login(email, password) {
    try {
      const response = await authAPI.login(email, password)
      
      // 1. Проверяем, нужна ли двухфакторка (статус 202)
      if (response.status === 202 || response.data?.require_2fa) {
        return { require2FA: true }
      }

      // 2. Если 2FA не нужна (например, почта еще не подтверждена)
      if (response.data?.access_token) {
        localStorage.setItem('access_token', response.data.access_token)
      }
      const userResponse = await authAPI.testToken()
      user.value = userResponse.data
      localStorage.setItem('user', JSON.stringify(user.value))
      
      return { require2FA: false }
    } catch (error) {
      console.error('Ошибка авторизации:', error)
      throw error
    }
  }

  // НОВЫЙ МЕТОД: Отправка введенного 6-значного кода
  async function verify2FA(email, password, code) {
    try {
      const response = await api.post('/auth/login/verify-2fa', { email, password, code })
      
      const userResponse = await authAPI.testToken()
      user.value = userResponse.data
      localStorage.setItem('user', JSON.stringify(user.value))
      return true
    } catch (error) {
      console.error('Ошибка проверки 2FA:', error)
      throw error
    }
  }

  async function logout() {
    user.value = null
    localStorage.removeItem('user')
    localStorage.removeItem('access_token')
  }

  return { user, isAuthenticated, isAdmin, isOrganization, login, verify2FA, logout }
})
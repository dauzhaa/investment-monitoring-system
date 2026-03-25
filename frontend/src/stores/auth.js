import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI } from '@/services/api' // Импортируем правильный метод из API

export const useAuthStore = defineStore('auth', () => {
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  const isAuthenticated = computed(() => !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isOrganization = computed(() => user.value?.role === 'organization')

  async function login(email, password) {
    try {
      // 1. Авторизуемся (отправляем Form Data, как того требует FastAPI)
      const tokenResponse = await authAPI.login(email, password)
      
      // 2. Сохраняем токен
      if (tokenResponse.data.access_token) {
        localStorage.setItem('access_token', tokenResponse.data.access_token)
      }

      // 3. Запрашиваем профиль пользователя
      const userResponse = await authAPI.testToken()
      user.value = userResponse.data
      localStorage.setItem('user', JSON.stringify(user.value))
      
      return true
    } catch (error) {
      console.error('Ошибка авторизации:', error)
      throw error
    }
  }

  async function logout() {
    user.value = null
    localStorage.removeItem('user')
    localStorage.removeItem('access_token')
  }

  return { user, isAuthenticated, isAdmin, isOrganization, login, logout }
})
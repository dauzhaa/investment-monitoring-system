import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || '/api/v1'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true 
})

// ВОЗВРАЩАЕМ ПЕРЕХВАТЧИК ТОКЕНА
api.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Interceptor: обработка 401 (Неавторизован)
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('user')
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

// ============ AUTH & VERIFICATION ============
export const authAPI = {
  login(email, password) {
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)
    // ИСПРАВЛЕНО: теперь стучимся на /auth/login
    return api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
  },
  testToken() {
    return api.get('/auth/me')
  },
  requestEmailVerification() {
    return api.post('/auth/request-verification')
  },
  verifyEmail(data) {
    return api.post('/auth/verify-email', data)
  }
}
// ============ AUDIT & NOTIFICATIONS (НОВОЕ) ============
export const auditAPI = {
  getLogs(params) {
    return api.get('/audit/', { params })
  }
}

export const notificationsAPI = {
  getMy() {
    return api.get('/notifications/')
  },
  markRead(id) {
    return api.put(`/notifications/${id}/read`)
  },
  send(data) {
    return api.post('/notifications/send', data)
  }
}

// ============ ANALYTICS / DASHBOARD ============
export const analyticsAPI = {
  getDashboard(params) {
    return api.get('/analytics/dashboard', { params })
  },
  getTrends(params) {
    return api.get('/analytics/trends', { params })
  },
  getQuarters(params) {
    return api.get('/analytics/quarters', { params })
  },
  getMapData(params) {
    return api.get('/analytics/map', { params })
  },
  // НОВЫЙ МЕТОД ДЛЯ PDF
  exportPdf(params) {
    return api.get('/export/analytics-pdf', { 
      params, 
      responseType: 'blob' // Обязательно указываем, что ждем бинарный файл
    })
  }
}
// ============ ORGANIZATIONS ============
export const organizationsAPI = {
  getAll(params = {}) {
    return api.get('/organizations', { params })
  },
  getById(id) {
    return api.get(`/organizations/${id}`)
  },
  getCount() {
    return api.get('/organizations/count')
  },
  exportExcel(params = {}) {
    return api.get('/organizations/export', {
      params,
      responseType: 'blob'
    })
  }
}

// ============ MONITORING ============
export const monitoringAPI = {
  getStatus(params = {}) {
    return api.get('/monitoring/status', { params })
  },
  getSummary(year) {
    return api.get('/monitoring/summary', { params: { year } })
  },
  sendReminders(year, quarter) {
    return api.post('/monitoring/remind', null, { params: { year, quarter } })
  },
  sendReminderToOrg(orgId, year, quarter) {
    return api.post(`/monitoring/remind/${orgId}`, null, { params: { year, quarter } })
  }
}

// ============ DISTRICTS ============
export const districtsAPI = {
  getDetails(districtName) {
    return api.get(`/districts/${encodeURIComponent(districtName)}`)
  }
}

// ============ DICTIONARIES ============
export const dictionariesAPI = {
  getDistricts() {
    return api.get('/dictionaries/districts')
  },
  getOkveds() {
    return api.get('/dictionaries/okveds')
  }
}

// ============ REPORTS ============
export const reportsAPI = {
  upload(file, reportType, year) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('report_type', reportType)
    formData.append('year', year)
    return api.post('/reports/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  downloadTemplate(reportType) {
    return api.get(`/reports/template/${reportType}`, { responseType: 'blob' })
  },
  exportYearly() {
    return api.get('/reports/export/yearly', { responseType: 'blob' })
  },
  exportDistricts(year) {
    return api.get('/reports/export/districts', { params: { year }, responseType: 'blob' })
  },
  exportDistrict(year, district) {
    return api.get('/reports/export/district', { params: { year, district }, responseType: 'blob' })
  },
  getHistory() {
    return api.get('/reports/history')
  }
}
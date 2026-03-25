import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'), // Убрали View
    meta: { requiresAuth: false, layout: 'blank' }
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'), // Убрали View
    meta: { requiresAuth: true, roles: ['admin'] }
  },
  {
    path: '/org-dashboard',
    name: 'OrgDashboard',
    component: () => import('@/views/OrganizationDashboard.vue'), // Переименовали под твой файл
    meta: { requiresAuth: true, roles: ['organization'] }
  },
  {
    path: '/monitoring',
    name: 'Monitoring',
    component: () => import('@/views/Monitoring.vue'), // Убрали View
    meta: { requiresAuth: true, roles: ['admin'] }
  },
  {
    path: '/organizations',
    name: 'Organizations',
    component: () => import('@/views/Organizations.vue'), // Убрали View
    meta: { requiresAuth: true, roles: ['admin'] }
  },
  {
    path: '/upload',
    name: 'Upload',
    component: () => import('@/views/Upload.vue'), // Убрали View
    meta: { requiresAuth: true, roles: ['admin'] }
  },
  {
    path: '/districts/:name',
    name: 'DistrictDetail',
    component: () => import('@/views/District.vue'), // Переименовали под твой файл
    meta: { requiresAuth: true, roles: ['admin'] }
  },
  // Наш файл Профиля и Аудита (мы создавали его с суффиксом View на шаге 2)
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/ProfileView.vue'), 
    meta: { requiresAuth: true }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard (без JWT, проверяем только объект user)
router.beforeEach((to, from, next) => {
  const userStr = localStorage.getItem('user')
  const user = userStr ? JSON.parse(userStr) : null
  const isAuthenticated = !!user

  // Публичные маршруты
  if (to.meta.requiresAuth === false) {
    if (isAuthenticated) {
      return next(user?.role === 'organization' ? '/org-dashboard' : '/')
    }
    return next()
  }

  // Проверка авторизации
  if (!isAuthenticated) {
    return next('/login')
  }

  // Проверка роли
  if (to.meta.roles && user) {
    if (!to.meta.roles.includes(user.role)) {
      return next(user.role === 'organization' ? '/org-dashboard' : '/')
    }
  }

  next()
})

export default router
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false, layout: 'blank' }
  },
  {
    path: '/',
    name: 'Главная', // Изменено с Dashboard
    component: () => import('@/views/Dashboard.vue'),
    meta: { requiresAuth: true, roles: ['admin'] }
  },
  {
    path: '/org-dashboard',
    name: 'OrgDashboard',
    component: () => import('@/views/OrganizationDashboard.vue'),
    meta: { requiresAuth: true, roles: ['organization'] }
  },
  {
    path: '/monitoring',
    name: 'Monitoring',
    component: () => import('@/views/Monitoring.vue'),
    meta: { requiresAuth: true, roles: ['admin'] }
  },
  {
    path: '/organizations',
    name: 'Organizations',
    component: () => import('@/views/Organizations.vue'),
    meta: { requiresAuth: true, roles: ['admin'] }
  },
  {
    path: '/upload',
    name: 'Upload',
    component: () => import('@/views/Upload.vue'),
    meta: { requiresAuth: true, roles: ['admin'] }
  },
  {
    path: '/districts/:name',
    name: 'DistrictDetail',
    component: () => import('@/views/District.vue'),
    meta: { requiresAuth: true, roles: ['admin'] }
  },
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

router.beforeEach((to, from, next) => {
  const userStr = localStorage.getItem('user')
  const user = userStr ? JSON.parse(userStr) : null
  const isAuthenticated = !!user

  if (to.meta.requiresAuth === false) {
    if (isAuthenticated) {
      return next(user?.role === 'organization' ? '/org-dashboard' : '/')
    }
    return next()
  }

  if (!isAuthenticated) return next('/login')

  if (to.meta.roles && user) {
    if (!to.meta.roles.includes(user.role)) {
      return next(user.role === 'organization' ? '/org-dashboard' : '/')
    }
  }

  next()
})

export default router
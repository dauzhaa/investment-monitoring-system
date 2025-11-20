import { createRouter, createWebHistory } from 'vue-router';

import Login from '@/views/Login.vue';
import Upload from '@/views/Upload.vue';
import Dashboard from '@/views/Dashboard.vue'; // Используй @ для единообразия
import Organizations from '@/views/Organizations.vue';
import Analytics from '@/views/Analytics.vue';
import Monitoring from '@/views/Monitoring.vue';

const routes = [
  // 1. Специфичные маршруты - СНАЧАЛА
  {
    path: '/login',
    name: 'Login',
    component: Login,
  },
  {
    path: '/upload',
    name: 'Upload',
    component: Upload,
    meta: { requiresAuth: true },
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }
  },
  
  // 2. Корневой маршрут
  {
    path: '/',
    redirect: '/dashboard'
  },

  {
    path: '/analytics',
    name: 'analytics',
    component: Analytics,
    meta: { requiresAuth: true }
},

  {
    path: '/organizations',
    name: 'organizations',
    component: Organizations,
    meta: { requiresAuth: true }
  },

{
  path: '/monitoring',
  name: 'monitoring',
  component: Monitoring,
  meta: { requiresAuth: true }
},

  // 3. Ловушка для всех несуществующих страниц - В САМОМ КОНЦЕ
  {
    path: '/:pathMatch(.*)*',
    redirect: '/login',
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL), // Для Vite лучше использовать import.meta.env
  routes,
});

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token');

  // Если маршрут требует входа, а токена нет -> на логин
  if (to.meta.requiresAuth && !token) {
    next('/login');
  } 
  // Если мы уже залогинены и пытаемся зайти на логин -> на дашборд
  else if (to.path === '/login' && token) {
    next('/dashboard');
  }
  else {
    next();
  }
});

export default router;
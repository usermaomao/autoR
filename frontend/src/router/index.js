import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/Home.vue')
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue')
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/Register.vue')
  },
  {
    path: '/review',
    name: 'review',
    component: () => import('@/views/Review.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/cards',
    name: 'cards',
    component: () => import('@/views/Cards.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/cards/new',
    name: 'new-card',
    component: () => import('@/views/CardForm.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/stats',
    name: 'stats',
    component: () => import('@/views/Stats.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 导航守卫
router.beforeEach((to, from, next) => {
  const isAuthenticated = localStorage.getItem('user')

  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login')
  } else {
    next()
  }
})

export default router

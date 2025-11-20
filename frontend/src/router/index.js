import { createRouter, createWebHistory } from 'vue-router'
import axios from 'axios'

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
    path: '/cards/:id/edit',
    name: 'edit-card',
    component: () => import('@/views/CardForm.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/cards/import-export',
    name: 'import-export',
    component: () => import('@/views/ImportExport.vue'),
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
router.beforeEach(async (to, from, next) => {
  // 如果不需要认证,直接放行
  if (!to.meta.requiresAuth) {
    next()
    return
  }

  // 先检查 localStorage 中是否有用户信息(快速检查)
  const hasLocalUser = localStorage.getItem('user')

  if (!hasLocalUser) {
    // 没有本地用户信息,直接跳转登录
    next('/login')
    return
  }

  // 验证会话是否有效
  try {
    await axios.get('/api/auth/me/')
    // 会话有效,允许访问
    next()
  } catch (error) {
    // 会话无效,清除本地数据并跳转登录
    localStorage.removeItem('user')
    next('/login')
  }
})

export default router

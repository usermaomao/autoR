<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-500 to-primary-700 px-4">
    <div class="max-w-md w-full bg-white rounded-lg shadow-xl p-8">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-gray-900">登录</h1>
        <p class="text-gray-600 mt-2">登录您的账户开始复习</p>
      </div>

      <form @submit.prevent="handleLogin">
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              用户名
            </label>
            <input
              v-model="form.username"
              type="text"
              required
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="请输入用户名"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              密码
            </label>
            <input
              v-model="form.password"
              type="password"
              required
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="请输入密码"
            />
          </div>

          <div v-if="error" class="text-red-600 text-sm">
            {{ error }}
          </div>

          <button
            type="submit"
            :disabled="isLoading"
            class="w-full btn btn-primary py-3"
          >
            {{ isLoading ? '登录中...' : '登录' }}
          </button>
        </div>
      </form>

      <div class="mt-6 text-center">
        <router-link to="/register" class="text-primary-600 hover:text-primary-700">
          还没有账户？立即注册
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const form = ref({
  username: '',
  password: ''
})

const error = ref('')
const isLoading = ref(false)

async function handleLogin() {
  error.value = ''
  isLoading.value = true

  try {
    const result = await userStore.login(form.value.username, form.value.password)

    if (result.success) {
      router.push('/')
    } else {
      error.value = result.error
    }
  } finally {
    isLoading.value = false
  }
}
</script>

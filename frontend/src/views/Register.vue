<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-500 to-green-700 px-4">
    <div class="max-w-md w-full bg-white rounded-lg shadow-xl p-8">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-gray-900">注册</h1>
        <p class="text-gray-600 mt-2">创建新账户</p>
      </div>

      <form @submit.prevent="handleRegister">
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">用户名</label>
            <input
              v-model="form.username"
              type="text"
              required
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
            <input
              v-model="form.email"
              type="email"
              required
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">密码</label>
            <input
              v-model="form.password"
              type="password"
              required
              minlength="6"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">确认密码</label>
            <input
              v-model="form.password_confirm"
              type="password"
              required
              minlength="6"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
          </div>

          <div v-if="error" class="text-red-600 text-sm">{{ error }}</div>

          <button type="submit" :disabled="isLoading" class="w-full btn bg-green-600 text-white hover:bg-green-700 py-3">
            {{ isLoading ? '注册中...' : '注册' }}
          </button>
        </div>
      </form>

      <div class="mt-6 text-center">
        <router-link to="/login" class="text-green-600 hover:text-green-700">
          已有账户？立即登录
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

const form = ref({ username: '', email: '', password: '', password_confirm: '' })
const error = ref('')
const isLoading = ref(false)

async function handleRegister() {
  error.value = ''

  // 验证密码匹配
  if (form.value.password !== form.value.password_confirm) {
    error.value = '两次输入的密码不一致'
    return
  }

  // 验证密码长度
  if (form.value.password.length < 6) {
    error.value = '密码长度至少需要6个字符'
    return
  }

  isLoading.value = true

  try {
    const result = await userStore.register(
      form.value.username,
      form.value.email,
      form.value.password,
      form.value.password_confirm
    )
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

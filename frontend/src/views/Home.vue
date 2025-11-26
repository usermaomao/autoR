<template>
  <div class="min-h-screen bg-gray-50">
    <!-- 顶部导航 -->
    <nav class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div class="flex justify-between items-center">
          <h1 class="text-2xl font-bold text-primary-600">词汇学习</h1>
          <div class="flex items-center space-x-4">
            <span class="text-gray-700">{{ userStore.user?.username }}</span>
            <button @click="handleLogout" class="text-gray-600 hover:text-gray-900">
              退出登录
            </button>
          </div>
        </div>
      </div>
    </nav>

    <!-- 主内容 -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <!-- 开始复习 -->
        <router-link
          to="/review"
          class="bg-gradient-to-br from-primary-500 to-primary-700 rounded-xl shadow-lg p-8 text-white hover:shadow-xl transition-shadow"
        >
          <div class="text-5xl mb-4">📚</div>
          <h2 class="text-2xl font-bold mb-2">开始复习</h2>
          <p class="text-primary-100">进入复习会话，强化记忆</p>
        </router-link>

        <!-- 添加卡片 -->
        <router-link
          to="/cards/new"
          class="bg-gradient-to-br from-green-500 to-green-700 rounded-xl shadow-lg p-8 text-white hover:shadow-xl transition-shadow"
        >
          <div class="text-5xl mb-4">✏️</div>
          <h2 class="text-2xl font-bold mb-2">添加卡片</h2>
          <p class="text-green-100">录入新的单词或汉字</p>
        </router-link>

        <!-- 卡片管理 -->
        <router-link
          to="/cards"
          class="bg-gradient-to-br from-blue-500 to-blue-700 rounded-xl shadow-lg p-8 text-white hover:shadow-xl transition-shadow"
        >
          <div class="text-5xl mb-4">📇</div>
          <h2 class="text-2xl font-bold mb-2">卡片管理</h2>
          <p class="text-blue-100">查看和编辑所有卡片</p>
        </router-link>

        <!-- 学习统计 -->
        <router-link
          to="/stats"
          class="bg-gradient-to-br from-purple-500 to-purple-700 rounded-xl shadow-lg p-8 text-white hover:shadow-xl transition-shadow"
        >
          <div class="text-5xl mb-4">📊</div>
          <h2 class="text-2xl font-bold mb-2">学习统计</h2>
          <p class="text-purple-100">查看学习进度和数据</p>
        </router-link>

        <!-- AI助手设置 -->
        <router-link
          to="/ai-settings"
          class="bg-gradient-to-br from-orange-500 to-orange-700 rounded-xl shadow-lg p-8 text-white hover:shadow-xl transition-shadow"
        >
          <div class="text-5xl mb-4">🤖</div>
          <h2 class="text-2xl font-bold mb-2">AI助手</h2>
          <p class="text-orange-100">配置AI学习辅助</p>
        </router-link>
      </div>

      <!-- 快速统计 -->
      <div class="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="bg-white rounded-lg shadow p-6">
          <div class="text-3xl font-bold text-primary-600 mb-2">{{ stats.due_today }}</div>
          <div class="text-gray-600">今日待复习</div>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
          <div class="text-3xl font-bold text-green-600 mb-2">{{ stats.total_cards }}</div>
          <div class="text-gray-600">总卡片数</div>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
          <div class="text-3xl font-bold text-blue-600 mb-2">{{ stats.streak }}</div>
          <div class="text-gray-600">连续打卡</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import axios from 'axios'

const router = useRouter()
const userStore = useUserStore()

const stats = ref({
  due_today: 0,
  total_cards: 0,
  streak: 0
})

onMounted(async () => {
  try {
    const response = await axios.get('/api/cards/stats/')
    stats.value = response.data
  } catch (err) {
    console.error('Failed to load stats:', err)
  }
})

async function handleLogout() {
  await userStore.logout()
  router.push('/login')
}
</script>

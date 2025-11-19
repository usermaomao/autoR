<template>
  <div class="min-h-screen bg-gray-50">
    <!-- 顶部导航 -->
    <nav class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div class="flex justify-between items-center">
          <div class="flex items-center space-x-4">
            <router-link to="/" class="text-gray-600 hover:text-gray-900">
              ← 返回
            </router-link>
            <h1 class="text-xl font-bold">复习会话</h1>
          </div>
          <div class="text-sm text-gray-600">
            {{ reviewStore.progress.current + 1 }} / {{ reviewStore.progress.total }}
          </div>
        </div>
      </div>
    </nav>

    <!-- 主内容区 -->
    <div class="max-w-4xl mx-auto px-4 py-8">
      <!-- 加载状态 -->
      <div v-if="reviewStore.isLoading" class="text-center py-20">
        <div class="inline-block animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent"></div>
        <p class="mt-4 text-gray-600">正在加载复习队列...</p>
      </div>

      <!-- 无卡片状态 -->
      <div v-else-if="!reviewStore.currentCard" class="text-center py-20">
        <div class="text-6xl mb-4">🎉</div>
        <h2 class="text-2xl font-bold text-gray-900 mb-2">复习完成！</h2>
        <p class="text-gray-600 mb-6">
          今天已完成 {{ reviewStore.stats.completed }} 张卡片
          <br />
          正确率: {{ reviewStore.accuracy }}%
        </p>
        <button @click="router.push('/')" class="btn btn-primary">
          返回首页
        </button>
      </div>

      <!-- 闪卡区域 -->
      <div v-else>
        <FlashCard
          :card="reviewStore.currentCard"
          :is-flipped="isFlipped"
          @flip="isFlipped = !isFlipped"
          @rate="handleRate"
        />

        <!-- 键盘提示 -->
        <div class="mt-6 text-center text-sm text-gray-500">
          <p>键盘快捷键: <kbd>S</kbd> 显示答案 | <kbd>1</kbd> 再来 | <kbd>2</kbd> 困难 | <kbd>3</kbd> 良好 | <kbd>4/空格</kbd> 简单 | <kbd>Z</kbd> 撤销</p>
        </div>

        <!-- 统计信息 -->
        <div class="mt-8 grid grid-cols-3 gap-4 text-center">
          <div class="bg-white rounded-lg p-4 shadow">
            <div class="text-2xl font-bold text-primary-600">{{ reviewStore.stats.completed }}</div>
            <div class="text-sm text-gray-600">已完成</div>
          </div>
          <div class="bg-white rounded-lg p-4 shadow">
            <div class="text-2xl font-bold text-green-600">{{ reviewStore.accuracy }}%</div>
            <div class="text-sm text-gray-600">正确率</div>
          </div>
          <div class="bg-white rounded-lg p-4 shadow">
            <div class="text-2xl font-bold text-blue-600">{{ avgTime }}s</div>
            <div class="text-sm text-gray-600">平均耗时</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useReviewStore } from '@/stores/review'
import FlashCard from '@/components/FlashCard.vue'

const router = useRouter()
const reviewStore = useReviewStore()

const isFlipped = ref(false)
const startTime = ref(Date.now())

const avgTime = computed(() => {
  if (reviewStore.stats.completed === 0) return 0
  return Math.round(reviewStore.stats.totalTime / reviewStore.stats.completed / 1000)
})

async function handleRate(quality) {
  if (!isFlipped.value) {
    isFlipped.value = true
    return
  }

  const timeTaken = Date.now() - startTime.value
  await reviewStore.submitReview(quality, timeTaken)

  // 重置状态
  isFlipped.value = false
  startTime.value = Date.now()
}

async function handleUndo() {
  const result = await reviewStore.undoLastReview()
  if (result.success) {
    isFlipped.value = false
    startTime.value = Date.now()
  }
}

// 键盘快捷键
function handleKeydown(e) {
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return

  switch(e.key) {
    case '1':
      handleRate(0)
      break
    case '2':
      handleRate(2)
      break
    case '3':
      handleRate(4)
      break
    case '4':
    case ' ':
      e.preventDefault()
      handleRate(5)
      break
    case 's':
    case 'S':
      isFlipped.value = !isFlipped.value
      break
    case 'z':
    case 'Z':
      handleUndo()
      break
  }
}

onMounted(async () => {
  await reviewStore.loadQueue(50)
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
kbd {
  @apply inline-block px-2 py-1 bg-gray-200 border border-gray-300 rounded text-xs font-mono;
}
</style>

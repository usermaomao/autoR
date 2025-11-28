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
            <h1 class="text-xl font-bold">
              {{ isPracticeMode ? '巩固练习' : '复习会话' }}
            </h1>
          </div>
          <div class="text-sm text-gray-600">
            {{ currentIndex + 1 }} / {{ totalCards }}
          </div>
        </div>
      </div>
    </nav>

    <!-- 主内容区 -->
    <div class="max-w-4xl mx-auto px-4 py-8">
      <!-- 加载状态 -->
      <div v-if="isLoading" class="text-center py-20">
        <div class="inline-block animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent"></div>
        <p class="mt-4 text-gray-600">正在加载复习队列...</p>
      </div>

      <!-- 无卡片状态（真正完全没有卡片） -->
      <div v-else-if="totalCards === 0" class="text-center py-20">
        <div class="text-6xl mb-4">🎉</div>
        <h2 class="text-2xl font-bold text-gray-900 mb-2">暂无卡片！</h2>
        <p class="text-gray-600 mb-6">
          请先添加一些卡片吧
        </p>
        <button @click="$router.push('/cards/new')" class="btn btn-primary">
          添加卡片
        </button>
      </div>

      <!-- 练习模式提示 -->
      <div v-else-if="isPracticeMode && currentCard" class="mb-6">
        <div class="bg-blue-50 border-l-4 border-blue-400 p-4 rounded-lg">
          <div class="flex items-center">
            <div class="text-2xl mr-3">🎯</div>
            <div>
              <p class="font-semibold text-blue-800">巩固练习模式</p>
              <p class="text-sm text-blue-700">
                {{ statsMessage }}
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- 闪卡区域 -->
      <div v-if="currentCard">
        <FlashCard
          :card="currentCard"
          :is-flipped="isFlipped"
          @flip="handleFlip"
          @rate="handleRate"
        />

        <!-- 评分完成后，点击“完成”进入下一张 -->
        <div v-if="hasRatedCurrent" class="mt-4 flex justify-center">
          <button
            class="btn btn-primary px-8 py-2"
            @click="goToNextCard"
          >
            完成，下一张
          </button>
        </div>

        <!-- 会话统计 -->
        <div v-if="stats" class="mt-4 text-center text-sm text-gray-600">
          <span>本次会话：{{ returnedCount }} 张</span>
          <span class="mx-2">|</span>
          <span>到期 {{ dueCount }} · 难项 {{ leechCount }} · 新卡 {{ newCount }}</span>
        </div>

        <!-- 键盘提示 -->
        <div class="mt-6 text-center text-sm text-gray-500">
          <p>键盘快捷键: <kbd>1</kbd> 再来 | <kbd>2</kbd> 困难 | <kbd>3</kbd> 良好 | <kbd>4/空格</kbd> 简单 | <kbd>S</kbd> 显示答案 | <kbd>Z</kbd> 撤销 | <kbd>Enter</kbd> 完成并进入下一张</p>
        </div>

        <!-- 统计信息 -->
        <div class="mt-8 grid grid-cols-3 gap-4 text-center">
          <div class="bg-white rounded-lg p-4 shadow">
            <div class="text-2xl font-bold text-primary-600">{{ completedCount }}</div>
            <div class="text-sm text-gray-600">已完成</div>
          </div>
          <div class="bg-white rounded-lg p-4 shadow">
            <div class="text-2xl font-bold text-green-600">{{ accuracy }}%</div>
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
import axios from 'axios'
import FlashCard from '@/components/FlashCard.vue'

const router = useRouter()
const SESSION_LIMIT = 30

// 状态管理
const isLoading = ref(false)
const cards = ref([])
const currentIndex = ref(0)
const isFlipped = ref(false)
const startTime = ref(Date.now())

// 统计数据
const completedCount = ref(0)
const correctCount = ref(0)
const totalTime = ref(0)
const isPracticeMode = ref(false)
const statsMessage = ref('')
const stats = ref(null)
const hasRatedCurrent = ref(false)

// 计算属性
const currentCard = computed(() => cards.value[currentIndex.value] || null)
const totalCards = computed(() => cards.value.length)

const accuracy = computed(() => {
  if (completedCount.value === 0) return 0
  return Math.round((correctCount.value / completedCount.value) * 100)
})

const avgTime = computed(() => {
  if (completedCount.value === 0) return 0
  return Math.round(totalTime.value / completedCount.value / 1000)
})

// 会话与队列统计
const dueCount = computed(() => (stats.value?.due_count ?? 0))
const leechCount = computed(() => (stats.value?.leech_count ?? 0))
const newCount = computed(() => (stats.value?.new_count ?? 0))
const sessionLimit = computed(() => (stats.value?.session_limit ?? totalCards.value))
const returnedCount = computed(() => (stats.value?.returned_count ?? totalCards.value))

// 加载复习队列（一次请求视为一轮会话）
async function loadQueue() {
  isLoading.value = true

  // 开启新会话时重置统计
  completedCount.value = 0
  correctCount.value = 0
  totalTime.value = 0
  hasRatedCurrent.value = false

  try {
    const response = await axios.get('/api/review/queue/', {
      params: { limit: SESSION_LIMIT }
    })

    cards.value = response.data.cards || []

    const responseStats = response.data.stats || {}
    stats.value = responseStats
    isPracticeMode.value = responseStats.is_practice_mode || false
    statsMessage.value = responseStats.message || ''

    currentIndex.value = 0
    isFlipped.value = false

    if (cards.value.length > 0) {
      startTime.value = Date.now()
    }

  } catch (error) {
    console.error('加载复习队列失败:', error)
    alert('加载失败，请重试')
  } finally {
    isLoading.value = false
  }
}

// 处理翻转
function handleFlip() {
  isFlipped.value = !isFlipped.value
}

// 处理评分：先评分→自动翻转到背面→点击“完成”再进入下一张
async function handleRate(quality) {
  if (!currentCard.value) return

  // 已经对当前卡片评分则不再重复提交
  if (hasRatedCurrent.value) {
    return
  }

  const timeTaken = Date.now() - startTime.value

  try {
    // 提交评分
    await axios.post('/api/review/submit/', {
      card_id: currentCard.value.id,
      quality: quality,
      time_taken: timeTaken
    })

    // 更新统计
    completedCount.value++
    totalTime.value += timeTaken
    if (quality >= 4) {  // Good or Easy
      correctCount.value++
    }

    // 标记当前卡片已评分
    hasRatedCurrent.value = true

    // 评分后自动翻转到背面，查看 SVG 反面/详细信息
    if (!isFlipped.value) {
      isFlipped.value = true
    }

  } catch (error) {
    console.error('提交评分失败:', error)
    alert('评分提交失败，请重试')
  }
}

// 进入下一张卡片（需已完成评分）
function goToNextCard() {
  if (!currentCard.value) return

  if (!hasRatedCurrent.value) {
    alert('请先选择难易，再进入下一张卡片')
    return
  }

  if (currentIndex.value < cards.value.length - 1) {
    currentIndex.value++
    isFlipped.value = false
    hasRatedCurrent.value = false
    startTime.value = Date.now()
  } else {
    // 全部完成
    showCompletionScreen()
  }
}

// 显示完成界面
function showCompletionScreen() {
  const message = isPracticeMode.value
    ? `巩固练习完成！\n已复习 ${completedCount.value} 张卡片\n正确率: ${accuracy.value}%`
    : `今日复习完成！\n已完成 ${completedCount.value} 张卡片\n正确率: ${accuracy.value}%`

  if (confirm(message + '\n\n是否返回首页？')) {
    router.push('/')
  } else {
    // 重新加载队列（可能有新的待复习卡片）
    loadQueue()
  }
}

// 撤销上一次复习
async function handleUndo() {
  if (currentIndex.value === 0 || completedCount.value === 0) {
    return // 没有可撤销的
  }

  try {
    // 获取上一张卡片
    const prevCard = cards.value[currentIndex.value - 1]

    // 调用撤销 API
    await axios.post('/api/review/undo/', {
      card_id: prevCard.id
    })

    // 回退状态
    currentIndex.value--
    isFlipped.value = false
    hasRatedCurrent.value = false
    startTime.value = Date.now()
    completedCount.value--

    alert('已撤销上一次评分')

  } catch (error) {
    console.error('撤销失败:', error)
    alert('撤销失败，请重试')
  }
}

// 键盘快捷键
function handleKeydown(e) {
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return
  if (!currentCard.value) return

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
    case 'Enter':
      // 已经评分后，回车直接进入下一张
      if (hasRatedCurrent.value) {
        goToNextCard()
      }
      break
    case 's':
    case 'S':
      handleFlip()
      break
    case 'z':
    case 'Z':
      handleUndo()
      break
  }
}

onMounted(async () => {
  await loadQueue()
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

<template>
  <div class="min-h-screen bg-gray-50">
    <nav class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
        <router-link to="/" class="text-gray-600 hover:text-gray-900">← 返回</router-link>
        <div class="flex gap-2">
          <router-link to="/cards/import-export" class="btn border border-gray-300 text-gray-700 hover:bg-gray-50">
            📥📤 导入/导出
          </router-link>
          <router-link to="/cards/new" class="btn bg-blue-600 text-white hover:bg-blue-700">
            + 添加卡片
          </router-link>
        </div>
      </div>
    </nav>

    <div class="max-w-7xl mx-auto px-4 py-8">
      <h1 class="text-3xl font-bold mb-8">卡片管理</h1>

      <!-- 成功消息提示 -->
      <div v-if="successMessage" class="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex justify-between items-center">
        <div class="flex items-center gap-2">
          <svg class="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
          </svg>
          <span class="text-green-800">{{ successMessage }}</span>
        </div>
        <button @click="successMessage = ''" class="text-green-600 hover:text-green-800">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
          </svg>
        </button>
      </div>

      <!-- 筛选和搜索 -->
      <div class="bg-white rounded-lg shadow p-6 mb-6">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <!-- 卡组筛选 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">卡组</label>
            <select v-model="filters.deck_id" @change="loadCards" class="w-full px-4 py-2 border border-gray-300 rounded-lg">
              <option value="">全部卡组</option>
              <option v-for="deck in decks" :key="deck.id" :value="deck.id">
                {{ deck.name }}
              </option>
            </select>
          </div>

          <!-- 类型筛选 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">类型</label>
            <select v-model="filters.card_type" @change="loadCards" class="w-full px-4 py-2 border border-gray-300 rounded-lg">
              <option value="">全部类型</option>
              <option value="en">英语单词</option>
              <option value="zh">汉字</option>
            </select>
          </div>

          <!-- 搜索 -->
          <div class="md:col-span-2">
            <label class="block text-sm font-medium text-gray-700 mb-2">搜索</label>
            <input
              v-model="filters.search"
              @input="handleSearchDebounced"
              type="text"
              placeholder="搜索单词或释义..."
              class="w-full px-4 py-2 border border-gray-300 rounded-lg"
            />
          </div>
        </div>
      </div>

      <!-- 批量操作 -->
      <div v-if="selectedCards.length > 0" class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <div class="flex justify-between items-center">
          <span class="text-blue-800">已选择 {{ selectedCards.length }} 张卡片</span>
          <div class="flex gap-2 flex-wrap">
            <button @click="showBatchMoveDialog = true" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              📁 移动到卡组
            </button>
            <button @click="showBatchTagsDialog = true" class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
              🏷️ 修改标签
            </button>
            <button @click="handleBatchResetProgress" class="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700">
              🔄 重置进度
            </button>
            <button @click="handleBatchDelete" class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700">
              🗑️ 批量删除
            </button>
            <button @click="selectedCards = []" class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50">
              取消选择
            </button>
          </div>
        </div>
      </div>

      <!-- 卡片列表 -->
      <div class="bg-white rounded-lg shadow">
        <div v-if="isLoading" class="p-8 text-center text-gray-500">
          加载中...
        </div>

        <div v-else-if="cards.length === 0" class="p-8 text-center text-gray-500">
          暂无卡片，<router-link to="/cards/new" class="text-blue-600 hover:underline">点击添加</router-link>
        </div>

        <div v-else class="overflow-x-auto">
          <table class="w-full">
            <thead class="bg-gray-50 border-b">
              <tr>
                <th class="px-4 py-3 text-left">
                  <input
                    type="checkbox"
                    @change="handleSelectAll"
                    :checked="selectedCards.length === cards.length && cards.length > 0"
                  />
                </th>
                <th class="px-4 py-3 text-left text-sm font-medium text-gray-700">单词/字符</th>
                <th class="px-4 py-3 text-left text-sm font-medium text-gray-700">类型</th>
                <th class="px-4 py-3 text-left text-sm font-medium text-gray-700">释义</th>
                <th class="px-4 py-3 text-left text-sm font-medium text-gray-700">卡组</th>
                <th class="px-4 py-3 text-left text-sm font-medium text-gray-700">难度系数</th>
                <th class="px-4 py-3 text-left text-sm font-medium text-gray-700">
                  下次复习
                  <span class="text-xs text-gray-500">(悬停查看时间轴)</span>
                </th>
                <th class="px-4 py-3 text-left text-sm font-medium text-gray-700">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200">
              <tr v-for="card in cards" :key="card.id" class="hover:bg-gray-50">
                <td class="px-4 py-3">
                  <input
                    type="checkbox"
                    :value="card.id"
                    v-model="selectedCards"
                  />
                </td>
                <td class="px-4 py-3 font-medium">{{ card.word }}</td>
                <td class="px-4 py-3">
                  <span :class="[
                    'px-2 py-1 rounded text-xs',
                    card.card_type === 'en' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'
                  ]">
                    {{ card.card_type === 'en' ? '英语' : '汉字' }}
                  </span>
                </td>
                <td class="px-4 py-3 text-sm text-gray-600 truncate max-w-xs">{{ card.meaning }}</td>
                <td class="px-4 py-3 text-sm">{{ getDeckName(card.deck) }}</td>
                <td class="px-4 py-3 text-sm">{{ card.ef.toFixed(2) }}</td>
                <td class="px-4 py-3 text-sm">
                  <div
                    class="flex items-center gap-1 cursor-help"
                    @mouseenter="showTooltip(card, $event)"
                    @mouseleave="hideTooltip"
                  >
                    <span>{{ formatDueDate(card.due_at) }}</span>
                    <span class="text-gray-400 text-xs">ℹ️</span>
                  </div>
                </td>
                <td class="px-4 py-3">
                  <div class="flex gap-2">
                    <button @click="handleEdit(card)" class="text-blue-600 hover:text-blue-800">编辑</button>
                    <button @click="handleDelete(card)" class="text-red-600 hover:text-red-800">删除</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 分页 -->
        <div v-if="totalPages > 1" class="border-t px-4 py-3 flex justify-between items-center">
          <span class="text-sm text-gray-700">
            第 {{ currentPage }} / {{ totalPages }} 页，共 {{ totalCount }} 张卡片
          </span>
          <div class="flex gap-2">
            <button
              @click="changePage(currentPage - 1)"
              :disabled="currentPage === 1"
              class="px-3 py-1 border border-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed"
            >
              上一页
            </button>
            <button
              @click="changePage(currentPage + 1)"
              :disabled="currentPage === totalPages"
              class="px-3 py-1 border border-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed"
            >
              下一页
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 批量移动卡组对话框 -->
    <div v-if="showBatchMoveDialog" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="showBatchMoveDialog = false">
      <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
        <h2 class="text-2xl font-bold mb-4">移动到卡组</h2>
        <p class="text-gray-600 mb-4">将选中的 {{ selectedCards.length }} 张卡片移动到：</p>

        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-2">目标卡组</label>
          <select v-model="batchMoveTargetDeck" class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500">
            <option value="">请选择卡组</option>
            <option v-for="deck in decks" :key="deck.id" :value="deck.id">
              {{ deck.name }}
            </option>
          </select>
        </div>

        <div v-if="batchError" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {{ batchError }}
        </div>

        <div class="flex gap-3">
          <button
            @click="handleBatchMove"
            :disabled="!batchMoveTargetDeck || isBatchProcessing"
            class="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {{ isBatchProcessing ? '处理中...' : '确认移动' }}
          </button>
          <button
            @click="showBatchMoveDialog = false"
            class="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
          >
            取消
          </button>
        </div>
      </div>
    </div>

    <!-- 批量修改标签对话框 -->
    <div v-if="showBatchTagsDialog" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="showBatchTagsDialog = false">
      <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
        <h2 class="text-2xl font-bold mb-4">批量修改标签</h2>
        <p class="text-gray-600 mb-4">为选中的 {{ selectedCards.length }} 张卡片修改标签：</p>

        <div class="mb-4">
          <label class="block text-sm font-medium text-gray-700 mb-2">操作模式</label>
          <select v-model="batchTagsMode" class="w-full px-4 py-2 border border-gray-300 rounded-lg mb-3">
            <option value="add">添加标签（保留原有标签）</option>
            <option value="replace">替换标签（清除原有标签）</option>
            <option value="remove">移除标签</option>
          </select>

          <label class="block text-sm font-medium text-gray-700 mb-2">标签（逗号分隔）</label>
          <input
            v-model="batchTagsInput"
            type="text"
            placeholder="例如: 四级,高频,动词"
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500"
          />
          <p class="text-xs text-gray-500 mt-1">
            {{ batchTagsMode === 'add' ? '这些标签将添加到现有标签中' : batchTagsMode === 'replace' ? '这些标签将替换所有现有标签' : '这些标签将从卡片中移除' }}
          </p>
        </div>

        <div v-if="batchError" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {{ batchError }}
        </div>

        <div class="flex gap-3">
          <button
            @click="handleBatchTags"
            :disabled="!batchTagsInput.trim() || isBatchProcessing"
            class="flex-1 bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {{ isBatchProcessing ? '处理中...' : '确认修改' }}
          </button>
          <button
            @click="showBatchTagsDialog = false"
            class="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
          >
            取消
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Teleport Tooltip: 复习时间轴 (渲染到 body，避免被表格 overflow 截断) -->
  <Teleport to="body">
    <div
      v-if="tooltipCard"
      class="fixed bg-gray-900 text-white text-xs rounded-lg shadow-2xl p-3 w-80 max-h-96 overflow-y-auto z-[9999]"
      :style="{ left: tooltipPosition.x + 'px', top: tooltipPosition.y + 'px' }"
    >
      <div class="font-semibold mb-2 border-b border-gray-700 pb-2">
        📅 复习时间轴预测
        <span class="text-gray-400 ml-1">(基于SM-2算法)</span>
      </div>

      <div class="space-y-1.5">
        <!-- 当前状态 -->
        <div class="flex justify-between text-yellow-300">
          <span>📍 当前状态:</span>
          <span class="font-mono">{{ getCardStateText(tooltipCard.state) }}</span>
        </div>

        <!-- 当前间隔 -->
        <div class="flex justify-between">
          <span>⏱️ 当前间隔:</span>
          <span class="font-mono">{{ tooltipCard.interval }} 天</span>
        </div>

        <!-- 易忘因子 -->
        <div class="flex justify-between">
          <span>🎯 难度系数 (EF):</span>
          <span class="font-mono">{{ tooltipCard.ef.toFixed(2) }}</span>
        </div>

        <!-- 错误次数 -->
        <div v-if="tooltipCard.lapses > 0" class="flex justify-between text-red-300">
          <span>❌ 错误次数:</span>
          <span class="font-mono">{{ tooltipCard.lapses }} 次</span>
        </div>

        <div class="border-t border-gray-700 my-2"></div>

        <!-- 未来复习时间点预测 -->
        <div class="font-semibold mb-1">🔮 未来复习时间点:</div>
        <div
          v-for="(review, index) in predictFutureReviews(tooltipCard)"
          :key="index"
          class="flex justify-between pl-2"
          :class="index === 0 ? 'text-green-300' : 'text-gray-300'"
        >
          <span>第 {{ index + 1 }} 次:</span>
          <span class="font-mono">{{ review.date }} ({{ review.interval }}天)</span>
        </div>

        <div class="text-gray-400 text-xs mt-2 italic">
          * 预测假设每次评分为"Good"(4分)
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import { formatDueTime } from '@/utils/timeFormatter'

const router = useRouter()
const route = useRoute()

const cards = ref([])
const decks = ref([])
const selectedCards = ref([])
const isLoading = ref(false)
const successMessage = ref('')

// Tooltip 状态
const tooltipCard = ref(null)
const tooltipPosition = reactive({ x: 0, y: 0 })

// 批量操作相关状态
const showBatchMoveDialog = ref(false)
const showBatchTagsDialog = ref(false)
const batchMoveTargetDeck = ref('')
const batchTagsMode = ref('add')
const batchTagsInput = ref('')
const isBatchProcessing = ref(false)
const batchError = ref('')

const filters = reactive({
  deck_id: '',
  card_type: '',
  search: ''
})

const currentPage = ref(1)
const totalPages = ref(1)
const totalCount = ref(0)
const pageSize = 20

// 加载卡组列表
onMounted(async () => {
  // 检查是否有成功消息
  if (route.query.successMessage) {
    successMessage.value = route.query.successMessage
    // 3秒后自动关闭消息
    setTimeout(() => {
      successMessage.value = ''
    }, 5000)
  }

  await loadDecks()
  await loadCards()
})

async function loadDecks() {
  try {
    const response = await axios.get('/api/decks/')
    decks.value = response.data.results || response.data
  } catch (err) {
    console.error('Failed to load decks:', err)
  }
}

// 加载卡片列表
async function loadCards() {
  isLoading.value = true

  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize
    }

    if (filters.deck_id) params.deck = filters.deck_id
    if (filters.card_type) params.card_type = filters.card_type
    if (filters.search) params.search = filters.search

    const response = await axios.get('/api/cards/', { params })

    cards.value = response.data.results || response.data
    totalCount.value = response.data.count || cards.value.length
    totalPages.value = Math.ceil(totalCount.value / pageSize)
  } catch (err) {
    console.error('Failed to load cards:', err)
  } finally {
    isLoading.value = false
  }
}

// 防抖搜索
let searchTimeout = null
function handleSearchDebounced() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    currentPage.value = 1
    loadCards()
  }, 500)
}

// 切换页码
function changePage(page) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  loadCards()
}

// 全选/取消全选
function handleSelectAll(event) {
  if (event.target.checked) {
    selectedCards.value = cards.value.map(c => c.id)
  } else {
    selectedCards.value = []
  }
}

// 编辑卡片
function handleEdit(card) {
  router.push(`/cards/${card.id}/edit`)
}

// 删除单个卡片
async function handleDelete(card) {
  if (!confirm(`确定删除卡片"${card.word}"吗？`)) return

  try {
    await axios.delete(`/api/cards/${card.id}/`)
    await loadCards()
  } catch (err) {
    console.error('Failed to delete card:', err)
    alert('删除失败，请稍后重试')
  }
}

// 批量删除
async function handleBatchDelete() {
  if (!confirm(`确定删除选中的 ${selectedCards.value.length} 张卡片吗？`)) return

  try {
    await Promise.all(
      selectedCards.value.map(id => axios.delete(`/api/cards/${id}/`))
    )
    selectedCards.value = []
    await loadCards()
  } catch (err) {
    console.error('Failed to batch delete:', err)
    alert('批量删除失败，请稍后重试')
  }
}

// 批量移动到卡组
async function handleBatchMove() {
  if (!batchMoveTargetDeck.value) {
    batchError.value = '请选择目标卡组'
    return
  }

  isBatchProcessing.value = true
  batchError.value = ''

  try {
    // 逐个更新卡片的卡组
    await Promise.all(
      selectedCards.value.map(async (cardId) => {
        const card = cards.value.find(c => c.id === cardId)
        if (!card) return

        // 获取完整卡片数据
        const response = await axios.get(`/api/cards/${cardId}/`)
        const fullCard = response.data

        // 更新卡组字段
        await axios.put(`/api/cards/${cardId}/`, {
          ...fullCard,
          deck: batchMoveTargetDeck.value
        })
      })
    )

    // 关闭对话框并重置
    showBatchMoveDialog.value = false
    batchMoveTargetDeck.value = ''
    selectedCards.value = []

    // 重新加载卡片列表
    await loadCards()

    alert(`成功移动 ${selectedCards.value.length} 张卡片`)
  } catch (err) {
    console.error('Failed to batch move:', err)
    batchError.value = '批量移动失败，请稍后重试'
  } finally {
    isBatchProcessing.value = false
  }
}

// 批量修改标签
async function handleBatchTags() {
  if (!batchTagsInput.value.trim()) {
    batchError.value = '请输入标签'
    return
  }

  isBatchProcessing.value = true
  batchError.value = ''

  try {
    // 解析输入的标签
    const inputTags = batchTagsInput.value
      .split(',')
      .map(t => t.trim())
      .filter(t => t.length > 0)

    // 逐个更新卡片的标签
    const updateCount = selectedCards.value.length
    await Promise.all(
      selectedCards.value.map(async (cardId) => {
        const card = cards.value.find(c => c.id === cardId)
        if (!card) return

        // 获取完整卡片数据
        const response = await axios.get(`/api/cards/${cardId}/`)
        const fullCard = response.data

        let newTags = []
        if (batchTagsMode.value === 'add') {
          // 添加模式：合并标签并去重
          newTags = [...new Set([...(fullCard.tags || []), ...inputTags])]
        } else if (batchTagsMode.value === 'replace') {
          // 替换模式：直接使用新标签
          newTags = inputTags
        } else if (batchTagsMode.value === 'remove') {
          // 移除模式：从现有标签中移除指定标签
          newTags = (fullCard.tags || []).filter(t => !inputTags.includes(t))
        }

        // 更新标签字段
        await axios.put(`/api/cards/${cardId}/`, {
          ...fullCard,
          tags: newTags
        })
      })
    )

    // 关闭对话框并重置
    showBatchTagsDialog.value = false
    batchTagsInput.value = ''
    batchTagsMode.value = 'add'
    selectedCards.value = []

    // 重新加载卡片列表
    await loadCards()

    const modeText = batchTagsMode.value === 'add' ? '添加' : batchTagsMode.value === 'replace' ? '替换' : '移除'
    alert(`成功为 ${updateCount} 张卡片${modeText}标签`)
  } catch (err) {
    console.error('Failed to batch update tags:', err)
    batchError.value = '批量修改标签失败，请稍后重试'
  } finally {
    isBatchProcessing.value = false
  }
}

// 批量重置进度
async function handleBatchResetProgress() {
  if (!confirm(`确定重置选中的 ${selectedCards.value.length} 张卡片的学习进度吗？\n\n重置后，这些卡片将回到初始状态，所有学习记录将被清除。`)) {
    return
  }

  try {
    // 逐个重置卡片的学习进度
    await Promise.all(
      selectedCards.value.map(async (cardId) => {
        const card = cards.value.find(c => c.id === cardId)
        if (!card) return

        // 获取完整卡片数据
        const response = await axios.get(`/api/cards/${cardId}/`)
        const fullCard = response.data

        // 重置学习相关字段
        await axios.put(`/api/cards/${cardId}/`, {
          ...fullCard,
          ef: 2.5,              // 重置难度系数为默认值
          interval: 0,          // 重置间隔天数
          learning_step: 0,     // 重置学习步骤
          lapses: 0,            // 重置错误次数
          state: 'new',         // 重置为新卡状态
          due_at: new Date().toISOString()  // 设置为今天需要复习
        })
      })
    )

    selectedCards.value = []
    await loadCards()

    alert(`成功重置 ${selectedCards.value.length} 张卡片的学习进度`)
  } catch (err) {
    console.error('Failed to batch reset progress:', err)
    alert('批量重置进度失败，请稍后重试')
  }
}

// 获取卡组名称
function getDeckName(deckId) {
  const deck = decks.value.find(d => d.id === deckId)
  return deck ? deck.name : '-'
}

// 获取卡片状态文本
function getCardStateText(state) {
  const stateMap = {
    'new': '新卡片',
    'learning': '学习中',
    'review': '复习中'
  }
  return stateMap[state] || state
}

// 预测未来复习时间点（基于SM-2算法）
function predictFutureReviews(card, count = 5) {
  const reviews = []

  // 从当前due_at开始预测
  let currentDate = new Date(card.due_at)
  let currentInterval = card.interval
  let currentEf = card.ef

  // 如果是9999-12-31（未安排），从今天开始
  if (currentDate.getFullYear() === 9999) {
    currentDate = new Date()
    currentInterval = 0
  }

  for (let i = 0; i < count; i++) {
    // 计算下一次间隔（假设评分为Good=4）
    let nextInterval

    if (currentInterval === 0) {
      nextInterval = 1  // 第一次复习: 1天
    } else if (currentInterval === 1) {
      nextInterval = 6  // 第二次复习: 6天
    } else {
      // 后续复习: interval × EF
      nextInterval = Math.floor(currentInterval * currentEf)
    }

    // 计算下一次复习日期
    const nextDate = new Date(currentDate)
    nextDate.setDate(nextDate.getDate() + nextInterval)

    // 格式化日期
    const year = nextDate.getFullYear()
    const month = String(nextDate.getMonth() + 1).padStart(2, '0')
    const day = String(nextDate.getDate()).padStart(2, '0')

    reviews.push({
      date: `${year}-${month}-${day}`,
      interval: nextInterval
    })

    // 更新状态为下一次预测
    currentDate = nextDate
    currentInterval = nextInterval

    // EF在Good评分(4)下的变化: EF' = EF + (0.1 - (5-4) * (0.08 + (5-4) * 0.02))
    // = EF + (0.1 - 0.1) = EF (保持不变)
    // 所以Good评分下EF不变
  }

  return reviews
}

// 格式化到期时间 - 使用工具函数（当天显示小时，否则显示天数）
function formatDueDate(dueAt) {
  return formatDueTime(dueAt)
}

// 显示 Tooltip
function showTooltip(card, event) {
  tooltipCard.value = card

  const target = event.currentTarget
  const rect = target.getBoundingClientRect()
  const tooltipWidth = 320 // w-80 = 320px
  const tooltipHeight = 384 // max-h-96 = 384px
  const gap = 8 // mb-2

  // 计算水平位置（居中对齐触发元素）
  let x = rect.left + (rect.width / 2) - (tooltipWidth / 2)

  // 防止左侧超出视口
  if (x < 10) x = 10

  // 防止右侧超出视口
  if (x + tooltipWidth > window.innerWidth - 10) {
    x = window.innerWidth - tooltipWidth - 10
  }

  // 计算垂直位置（显示在上方）
  let y = rect.top - tooltipHeight - gap

  // 如果上方空间不足，显示在下方
  if (y < 10) {
    y = rect.bottom + gap
  }

  tooltipPosition.x = x
  tooltipPosition.y = y
}

// 隐藏 Tooltip
function hideTooltip() {
  tooltipCard.value = null
}
</script>

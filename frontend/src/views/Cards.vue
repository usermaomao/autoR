<template>
  <div class="min-h-screen bg-gray-50">
    <nav class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
        <router-link to="/" class="text-gray-600 hover:text-gray-900">← 返回</router-link>
        <router-link to="/cards/new" class="btn bg-blue-600 text-white hover:bg-blue-700">
          + 添加卡片
        </router-link>
      </div>
    </nav>

    <div class="max-w-7xl mx-auto px-4 py-8">
      <h1 class="text-3xl font-bold mb-8">卡片管理</h1>

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
          <div class="flex gap-2">
            <button @click="handleBatchDelete" class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700">
              批量删除
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
                <th class="px-4 py-3 text-left text-sm font-medium text-gray-700">下次复习</th>
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
                <td class="px-4 py-3 text-sm">{{ formatDueDate(card.due_at) }}</td>
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()

const cards = ref([])
const decks = ref([])
const selectedCards = ref([])
const isLoading = ref(false)

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
  await loadDecks()
  await loadCards()
})

async function loadDecks() {
  try {
    const response = await axios.get('/api/cards/decks/')
    decks.value = response.data
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

    if (filters.deck_id) params.deck_id = filters.deck_id
    if (filters.card_type) params.card_type = filters.card_type
    if (filters.search) params.search = filters.search

    const response = await axios.get('/api/cards/cards/', { params })

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
  // TODO: 实现编辑功能（可以导航到编辑页面）
  console.log('Edit card:', card)
  alert('编辑功能待实现')
}

// 删除单个卡片
async function handleDelete(card) {
  if (!confirm(`确定删除卡片"${card.word}"吗？`)) return

  try {
    await axios.delete(`/api/cards/cards/${card.id}/`)
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
      selectedCards.value.map(id => axios.delete(`/api/cards/cards/${id}/`))
    )
    selectedCards.value = []
    await loadCards()
  } catch (err) {
    console.error('Failed to batch delete:', err)
    alert('批量删除失败，请稍后重试')
  }
}

// 获取卡组名称
function getDeckName(deckId) {
  const deck = decks.value.find(d => d.id === deckId)
  return deck ? deck.name : '-'
}

// 格式化到期时间
function formatDueDate(dueAt) {
  const date = new Date(dueAt)
  const now = new Date()
  const diffMs = date - now
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays < 0) {
    return `逾期 ${Math.abs(diffDays)} 天`
  } else if (diffDays === 0) {
    return '今天'
  } else if (diffDays === 1) {
    return '明天'
  } else {
    return `${diffDays} 天后`
  }
}
</script>

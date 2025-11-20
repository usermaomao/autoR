<template>
  <div class="space-y-6">
    <h3 class="text-lg font-semibold">导出卡片</h3>

    <!-- 导出参数 -->
    <div class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">选择卡组（可选）</label>
        <select v-model="exportParams.deckId" class="w-full px-4 py-2 border border-gray-300 rounded-lg">
          <option value="">所有卡组</option>
          <option v-for="deck in decks" :key="deck.id" :value="deck.id">
            {{ deck.name }} ({{ deck.card_count }} 张卡片)
          </option>
        </select>
        <p class="mt-1 text-xs text-gray-500">
          不选择则导出所有卡片
        </p>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">导出格式</label>
        <div class="grid grid-cols-2 gap-4">
          <button
            @click="exportParams.format = 'csv'"
            :class="[
              'p-4 border-2 rounded-lg text-left transition-colors',
              exportParams.format === 'csv'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            ]"
          >
            <div class="flex items-start">
              <div class="flex-shrink-0">
                <svg class="h-6 w-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div class="ml-3">
                <div class="text-sm font-medium text-gray-900">CSV 格式</div>
                <div class="text-xs text-gray-500 mt-1">
                  适合 Excel 和 Anki 导入
                </div>
              </div>
            </div>
          </button>

          <button
            @click="exportParams.format = 'json'"
            :class="[
              'p-4 border-2 rounded-lg text-left transition-colors',
              exportParams.format === 'json'
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            ]"
          >
            <div class="flex items-start">
              <div class="flex-shrink-0">
                <svg class="h-6 w-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                </svg>
              </div>
              <div class="ml-3">
                <div class="text-sm font-medium text-gray-900">JSON 格式</div>
                <div class="text-xs text-gray-500 mt-1">
                  包含完整元数据，适合备份
                </div>
              </div>
            </div>
          </button>
        </div>
      </div>

      <!-- 导出统计 -->
      <div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <div class="text-sm text-gray-600">
          <p class="mb-2">将要导出：</p>
          <ul class="list-disc list-inside space-y-1">
            <li>卡片数量：约 {{ exportCount }} 张</li>
            <li>文件格式：{{ exportParams.format.toUpperCase() }}</li>
            <li>包含字段：正面、背面、标签、状态、间隔、易忘因子</li>
          </ul>
        </div>
      </div>

      <!-- 格式示例 -->
      <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div class="flex items-start">
          <svg class="h-5 w-5 text-blue-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
          </svg>
          <div class="ml-3 text-sm text-blue-700">
            <p class="font-medium mb-2">{{ exportParams.format.toUpperCase() }} 格式示例：</p>
            <pre v-if="exportParams.format === 'csv'" class="text-xs bg-white p-2 rounded border border-blue-200 overflow-x-auto">Front,Back,Tags,State,Interval,EF,Created
apple,苹果,水果,复习,7,2.5,2025-01-01
banana,香蕉,"水果,热带",学习中,0,2.5,2025-01-02</pre>
            <pre v-else class="text-xs bg-white p-2 rounded border border-blue-200 overflow-x-auto">{
  "cards": [
    {
      "Front": "apple",
      "Back": "苹果",
      "Tags": ["水果"],
      "State": "review",
      "Interval": 7,
      "EF": 2.5,
      "Metadata": {...},
      "Created": "2025-01-01T00:00:00Z"
    }
  ]
}</pre>
          </div>
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="flex justify-end gap-3">
      <button
        @click="handleExport"
        :disabled="isExporting"
        class="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
      >
        <svg v-if="!isExporting" class="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
        <svg v-else class="animate-spin h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        {{ isExporting ? '导出中...' : '开始导出' }}
      </button>
    </div>

    <!-- 导出成功提示 -->
    <div v-if="exportSuccess" class="bg-green-50 border border-green-200 rounded-lg p-4">
      <div class="flex items-start">
        <svg class="h-5 w-5 text-green-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
        </svg>
        <div class="ml-3 text-sm text-green-700">
          <p class="font-medium">导出成功！</p>
          <p class="mt-1">文件已开始下载，请查看浏览器下载目录。</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { exportCards } from '../services/importExportService'

const decks = ref([])
const exportParams = ref({
  deckId: '',
  format: 'csv'
})
const isExporting = ref(false)
const exportSuccess = ref(false)
const stats = ref(null)

// 计算导出数量
const exportCount = computed(() => {
  if (!exportParams.value.deckId) {
    // 所有卡片
    return stats.value?.total_cards || 0
  } else {
    // 指定卡组
    const deck = decks.value.find(d => d.id === exportParams.value.deckId)
    return deck?.card_count || 0
  }
})

// 加载卡组列表
async function loadDecks() {
  try {
    const response = await axios.get('/api/decks/')
    decks.value = response.data
  } catch (error) {
    console.error('加载卡组列表失败:', error)
  }
}

// 加载统计信息
async function loadStats() {
  try {
    const response = await axios.get('/api/cards/stats/')
    stats.value = response.data
  } catch (error) {
    console.error('加载统计信息失败:', error)
  }
}

// 处理导出
async function handleExport() {
  isExporting.value = true
  exportSuccess.value = false

  try {
    const result = await exportCards(
      exportParams.value.format,
      exportParams.value.deckId || null
    )

    if (result.success) {
      exportSuccess.value = true
      setTimeout(() => {
        exportSuccess.value = false
      }, 5000)
    } else {
      alert('导出失败: ' + result.error)
    }
  } catch (error) {
    alert('导出失败: ' + error.message)
  } finally {
    isExporting.value = false
  }
}

onMounted(() => {
  loadDecks()
  loadStats()
})
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <nav class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
        <router-link to="/cards" class="text-gray-600 hover:text-gray-900">← 返回卡片</router-link>
        <h2 class="text-lg font-semibold">导入/导出卡片</h2>
        <div></div>
      </div>
    </nav>

    <div class="max-w-4xl mx-auto px-4 py-8">
      <!-- 标签页切换 -->
      <div class="bg-white rounded-lg shadow mb-6">
        <div class="border-b border-gray-200">
          <nav class="flex -mb-px">
            <button
              @click="activeTab = 'import'"
              :class="[
                'px-6 py-4 text-sm font-medium border-b-2 transition-colors',
                activeTab === 'import'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              ]"
            >
              📥 导入卡片
            </button>
            <button
              @click="activeTab = 'export'"
              :class="[
                'px-6 py-4 text-sm font-medium border-b-2 transition-colors',
                activeTab === 'export'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              ]"
            >
              📤 导出卡片
            </button>
          </nav>
        </div>

        <!-- 导入面板 -->
        <div v-if="activeTab === 'import'" class="p-6">
          <ImportPanel @import-success="handleImportSuccess" />
        </div>

        <!-- 导出面板 -->
        <div v-if="activeTab === 'export'" class="p-6">
          <ExportPanel />
        </div>
      </div>

      <!-- 导入历史 -->
      <div v-if="importHistory.length > 0" class="bg-white rounded-lg shadow p-6">
        <h3 class="text-lg font-semibold mb-4">最近导入记录</h3>
        <div class="space-y-3">
          <div
            v-for="(record, index) in importHistory"
            :key="index"
            class="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
          >
            <div class="flex-1">
              <div class="text-sm font-medium">{{ record.filename }}</div>
              <div class="text-xs text-gray-500 mt-1">
                {{ record.timestamp }} · 导入 {{ record.imported }}/{{ record.total }} 张卡片
              </div>
            </div>
            <div class="ml-4">
              <span
                v-if="record.imported === record.total"
                class="px-2 py-1 bg-green-100 text-green-800 text-xs rounded"
              >
                成功
              </span>
              <span
                v-else
                class="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded"
              >
                部分成功
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ImportPanel from '../components/ImportPanel.vue'
import ExportPanel from '../components/ExportPanel.vue'

const activeTab = ref('import')
const importHistory = ref([])

function handleImportSuccess(result) {
  // 添加到导入历史
  importHistory.value.unshift({
    filename: result.filename,
    timestamp: new Date().toLocaleString('zh-CN'),
    total: result.data.total,
    imported: result.data.imported,
    skipped: result.data.skipped,
    failed: result.data.failed
  })

  // 只保留最近 10 条记录
  if (importHistory.value.length > 10) {
    importHistory.value = importHistory.value.slice(0, 10)
  }

  // 保存到 localStorage
  localStorage.setItem('importHistory', JSON.stringify(importHistory.value))
}

// 从 localStorage 加载历史记录
if (localStorage.getItem('importHistory')) {
  try {
    importHistory.value = JSON.parse(localStorage.getItem('importHistory'))
  } catch (e) {
    console.error('加载导入历史失败:', e)
  }
}
</script>

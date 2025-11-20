<template>
  <div class="space-y-6">
    <!-- 步骤指示器 -->
    <div class="flex items-center justify-between">
      <div
        v-for="(step, index) in steps"
        :key="index"
        class="flex items-center"
        :class="{ 'flex-1': index < steps.length - 1 }"
      >
        <div class="flex items-center">
          <div
            :class="[
              'w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium',
              currentStep > index
                ? 'bg-green-500 text-white'
                : currentStep === index
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 text-gray-500'
            ]"
          >
            {{ index + 1 }}
          </div>
          <div class="ml-3">
            <div class="text-sm font-medium">{{ step }}</div>
          </div>
        </div>
        <div
          v-if="index < steps.length - 1"
          class="flex-1 h-0.5 mx-4"
          :class="currentStep > index ? 'bg-green-500' : 'bg-gray-200'"
        ></div>
      </div>
    </div>

    <!-- 步骤 1: 选择文件和参数 -->
    <div v-if="currentStep === 0" class="space-y-4">
      <h3 class="text-lg font-semibold">选择要导入的文件</h3>

      <!-- 文件选择 -->
      <div class="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
        <input
          ref="fileInput"
          type="file"
          accept=".csv,.json"
          @change="handleFileSelect"
          class="hidden"
        />

        <div v-if="!selectedFile" @click="$refs.fileInput.click()" class="cursor-pointer">
          <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <p class="mt-2 text-sm text-gray-600">
            点击选择文件或拖拽文件到这里
          </p>
          <p class="mt-1 text-xs text-gray-500">
            支持 CSV 和 JSON 格式，最大 10MB
          </p>
        </div>

        <div v-else class="space-y-3">
          <div class="flex items-center justify-center">
            <svg class="h-12 w-12 text-green-500" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
          </div>
          <div>
            <div class="text-sm font-medium">{{ selectedFile.name }}</div>
            <div class="text-xs text-gray-500">{{ formatFileSize(selectedFile.size) }}</div>
          </div>
          <button
            @click="selectedFile = null"
            class="text-sm text-red-600 hover:text-red-800"
          >
            重新选择
          </button>
        </div>
      </div>

      <!-- 导入参数 -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">目标卡组 *</label>
          <select v-model="importParams.deckId" class="w-full px-4 py-2 border border-gray-300 rounded-lg">
            <option value="">请选择卡组</option>
            <option v-for="deck in decks" :key="deck.id" :value="deck.id">
              {{ deck.name }}
            </option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">卡片类型</label>
          <select v-model="importParams.cardType" class="w-full px-4 py-2 border border-gray-300 rounded-lg">
            <option value="en">英语单词</option>
            <option value="zh">汉字</option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">文件格式</label>
          <select v-model="importParams.format" class="w-full px-4 py-2 border border-gray-300 rounded-lg">
            <option value="csv">CSV</option>
            <option value="json">JSON</option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">重复处理策略</label>
          <select v-model="importParams.conflictStrategy" class="w-full px-4 py-2 border border-gray-300 rounded-lg">
            <option value="skip">跳过重复项</option>
            <option value="overwrite">覆盖已有卡片</option>
            <option value="merge">合并标签和元数据</option>
          </select>
        </div>
      </div>

      <!-- 帮助提示 -->
      <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div class="flex">
          <svg class="h-5 w-5 text-blue-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
          </svg>
          <div class="ml-3 text-sm text-blue-700">
            <p class="font-medium mb-1">文件格式要求：</p>
            <ul class="list-disc list-inside space-y-1">
              <li>CSV 格式：必须包含 Front（正面）和 Back（背面）列</li>
              <li>JSON 格式：{"cards": [{"Front": "单词", "Back": "释义", "Tags": "标签"}]}</li>
              <li>支持 Anki 导出格式</li>
            </ul>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="flex justify-end gap-3">
        <button
          @click="$router.push('/cards')"
          class="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
        >
          取消
        </button>
        <button
          @click="parseFile"
          :disabled="!selectedFile || !importParams.deckId"
          class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          下一步：预览数据
        </button>
      </div>
    </div>

    <!-- 步骤 2: 预览数据 -->
    <div v-if="currentStep === 1" class="space-y-4">
      <h3 class="text-lg font-semibold">数据预览</h3>

      <!-- 解析结果统计 -->
      <div class="grid grid-cols-3 gap-4">
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div class="text-2xl font-bold text-blue-600">{{ previewData.length }}</div>
          <div class="text-sm text-gray-600">总卡片数</div>
        </div>
        <div class="bg-green-50 border border-green-200 rounded-lg p-4">
          <div class="text-2xl font-bold text-green-600">{{ validCount }}</div>
          <div class="text-sm text-gray-600">有效卡片</div>
        </div>
        <div class="bg-red-50 border border-red-200 rounded-lg p-4">
          <div class="text-2xl font-bold text-red-600">{{ errorCount }}</div>
          <div class="text-sm text-gray-600">错误数</div>
        </div>
      </div>

      <!-- 错误信息 -->
      <div v-if="validationResult && validationResult.errors.length > 0" class="bg-red-50 border border-red-200 rounded-lg p-4">
        <div class="flex items-start">
          <svg class="h-5 w-5 text-red-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
          <div class="ml-3 text-sm text-red-700">
            <p class="font-medium mb-2">发现以下错误：</p>
            <ul class="list-disc list-inside space-y-1">
              <li v-for="(error, index) in validationResult.errors" :key="index">
                {{ error }}
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- 预览表格 -->
      <div class="border border-gray-200 rounded-lg overflow-hidden">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">序号</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">正面 (Front)</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">背面 (Back)</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">标签 (Tags)</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="(row, index) in displayPreviewData" :key="index">
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ index + 1 }}</td>
              <td class="px-6 py-4 text-sm text-gray-900">{{ row.word }}</td>
              <td class="px-6 py-4 text-sm text-gray-700">{{ row.meaning }}</td>
              <td class="px-6 py-4">
                <div class="flex flex-wrap gap-1">
                  <span
                    v-for="(tag, idx) in row.tags"
                    :key="idx"
                    class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                  >
                    {{ tag }}
                  </span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="previewData.length > 5" class="text-sm text-gray-500 text-center">
        显示前 5 条，共 {{ previewData.length }} 条
      </div>

      <!-- 操作按钮 -->
      <div class="flex justify-end gap-3">
        <button
          @click="currentStep = 0"
          class="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
        >
          上一步
        </button>
        <button
          @click="startImport"
          :disabled="!validationResult || !validationResult.valid"
          class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          开始导入
        </button>
      </div>
    </div>

    <!-- 步骤 3: 导入进度 -->
    <div v-if="currentStep === 2" class="space-y-4">
      <h3 class="text-lg font-semibold">正在导入...</h3>

      <!-- 进度条 -->
      <div>
        <div class="flex justify-between text-sm text-gray-600 mb-2">
          <span>上传进度</span>
          <span>{{ uploadProgress }}%</span>
        </div>
        <div class="w-full bg-gray-200 rounded-full h-2.5">
          <div
            class="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
            :style="{ width: uploadProgress + '%' }"
          ></div>
        </div>
      </div>

      <div class="text-center text-sm text-gray-600">
        请稍候，正在处理您的文件...
      </div>
    </div>

    <!-- 步骤 4: 导入结果 -->
    <div v-if="currentStep === 3" class="space-y-4">
      <div class="text-center">
        <svg class="mx-auto h-16 w-16 text-green-500" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
        </svg>
        <h3 class="mt-4 text-lg font-semibold text-gray-900">导入完成！</h3>
      </div>

      <!-- 导入统计 -->
      <div v-if="importResult" class="grid grid-cols-4 gap-4">
        <div class="bg-gray-50 border border-gray-200 rounded-lg p-4 text-center">
          <div class="text-2xl font-bold text-gray-900">{{ importResult.total }}</div>
          <div class="text-sm text-gray-600">总数</div>
        </div>
        <div class="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
          <div class="text-2xl font-bold text-green-600">{{ importResult.imported }}</div>
          <div class="text-sm text-gray-600">成功</div>
        </div>
        <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center">
          <div class="text-2xl font-bold text-yellow-600">{{ importResult.skipped }}</div>
          <div class="text-sm text-gray-600">跳过</div>
        </div>
        <div class="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
          <div class="text-2xl font-bold text-red-600">{{ importResult.failed }}</div>
          <div class="text-sm text-gray-600">失败</div>
        </div>
      </div>

      <!-- 重复项详情 -->
      <div v-if="importResult && importResult.duplicates && importResult.duplicates.length > 0" class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div class="flex items-start">
          <svg class="h-5 w-5 text-yellow-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
          <div class="ml-3 text-sm text-yellow-700">
            <p class="font-medium mb-2">跳过的重复项（前 5 条）：</p>
            <ul class="list-disc list-inside space-y-1">
              <li v-for="(dup, index) in importResult.duplicates.slice(0, 5)" :key="index">
                {{ dup.word }} - {{ dup.reason }}
              </li>
            </ul>
            <p v-if="importResult.duplicates.length > 5" class="mt-2">
              ...还有 {{ importResult.duplicates.length - 5 }} 条
            </p>
          </div>
        </div>
      </div>

      <!-- 错误详情 -->
      <div v-if="importResult && importResult.errors && importResult.errors.length > 0" class="bg-red-50 border border-red-200 rounded-lg p-4">
        <div class="flex items-start">
          <svg class="h-5 w-5 text-red-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
          <div class="ml-3 text-sm text-red-700">
            <p class="font-medium mb-2">导入错误：</p>
            <ul class="list-disc list-inside space-y-1">
              <li v-for="(error, index) in importResult.errors.slice(0, 10)" :key="index">
                {{ error }}
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="flex justify-end gap-3">
        <button
          @click="$router.push('/cards')"
          class="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
        >
          返回卡片列表
        </button>
        <button
          @click="resetImport"
          class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          继续导入
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import {
  importCards,
  parseCSV,
  parseJSON,
  validateImportData,
  generatePreview
} from '../services/importExportService'

const emit = defineEmits(['import-success'])

const steps = ['选择文件', '预览数据', '导入中', '完成']
const currentStep = ref(0)

// 文件和参数
const selectedFile = ref(null)
const fileInput = ref(null)
const decks = ref([])
const importParams = ref({
  deckId: '',
  cardType: 'en',
  format: 'csv',
  conflictStrategy: 'skip'
})

// 预览数据
const previewData = ref([])
const validationResult = ref(null)

// 导入状态
const uploadProgress = ref(0)
const importResult = ref(null)

// 计算属性
const validCount = computed(() => {
  return validationResult.value?.valid ? previewData.value.length : 0
})

const errorCount = computed(() => {
  return validationResult.value?.errors.length || 0
})

const displayPreviewData = computed(() => {
  return previewData.value.slice(0, 5)
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

// 处理文件选择
function handleFileSelect(event) {
  const file = event.target.files[0]
  if (!file) return

  // 检查文件大小 (10MB)
  if (file.size > 10 * 1024 * 1024) {
    alert('文件大小不能超过 10MB')
    return
  }

  // 自动检测格式
  const ext = file.name.split('.').pop().toLowerCase()
  if (ext === 'csv') {
    importParams.value.format = 'csv'
  } else if (ext === 'json') {
    importParams.value.format = 'json'
  }

  selectedFile.value = file
}

// 解析文件
async function parseFile() {
  try {
    let parsedData
    if (importParams.value.format === 'csv') {
      const result = await parseCSV(selectedFile.value)
      parsedData = result.data
    } else {
      const result = await parseJSON(selectedFile.value)
      parsedData = result.data
    }

    // 验证数据
    validationResult.value = validateImportData(parsedData)

    // 生成预览
    previewData.value = generatePreview(parsedData, parsedData.length)

    currentStep.value = 1
  } catch (error) {
    alert('文件解析失败: ' + error.message)
  }
}

// 开始导入
async function startImport() {
  currentStep.value = 2
  uploadProgress.value = 0

  const result = await importCards(
    selectedFile.value,
    importParams.value.format,
    importParams.value.deckId,
    importParams.value.cardType,
    importParams.value.conflictStrategy,
    (progress) => {
      uploadProgress.value = progress
    }
  )

  if (result.success) {
    importResult.value = result.data
    currentStep.value = 3

    // 触发成功事件
    emit('import-success', {
      filename: selectedFile.value.name,
      data: result.data
    })
  } else {
    alert('导入失败: ' + result.error)
    currentStep.value = 0
  }
}

// 重置导入
function resetImport() {
  currentStep.value = 0
  selectedFile.value = null
  previewData.value = []
  validationResult.value = null
  uploadProgress.value = 0
  importResult.value = null
}

// 格式化文件大小
function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

onMounted(() => {
  loadDecks()
})
</script>

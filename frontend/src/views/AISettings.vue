<template>
  <div class="min-h-screen bg-gray-50">
    <nav class="bg-white shadow-sm">
      <div class="max-w-4xl mx-auto px-4 py-4">
        <router-link to="/" class="text-gray-600 hover:text-gray-900">← 返回首页</router-link>
      </div>
    </nav>

    <div class="max-w-4xl mx-auto px-4 py-8">
      <div class="bg-white rounded-lg shadow-lg p-6">
        <h1 class="text-3xl font-bold mb-2">🤖 AI助手配置</h1>
        <p class="text-gray-600 mb-6">配置AI模型来帮助你更好地学习和记忆词汇</p>

        <!-- 加载状态 -->
        <div v-if="isLoading" class="text-center py-8 text-gray-500">
          加载中...
        </div>

        <!-- 配置表单 -->
        <form v-else @submit.prevent="saveConfig" class="space-y-6">
          <!-- 启用开关 -->
          <div class="flex items-center justify-between p-4 bg-blue-50 rounded-lg">
            <div>
              <label class="text-lg font-semibold text-blue-900">启用AI功能</label>
              <p class="text-sm text-blue-700 mt-1">开启后可在复习时使用AI总结词汇</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                v-model="config.enabled"
                class="sr-only peer"
              />
              <div class="w-14 h-7 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[4px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-6 after:w-6 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          <!-- AI提供商选择 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              AI提供商 <span class="text-red-500">*</span>
            </label>
            <select
              v-model="config.provider"
              required
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="openai">OpenAI (GPT)</option>
              <option value="anthropic">Anthropic (Claude)</option>
              <option value="local">本地模型 (OpenAI兼容)</option>
            </select>
            <p class="text-xs text-gray-500 mt-1">
              {{ getProviderHint(config.provider) }}
            </p>
          </div>

          <!-- Base URL -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              API Base URL <span class="text-red-500">*</span>
            </label>
            <input
              v-model="config.base_url"
              type="url"
              required
              placeholder="https://api.openai.com/v1"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p class="text-xs text-gray-500 mt-1">
              API的基础URL，支持OpenAI兼容的第三方服务
            </p>
          </div>

          <!-- 模型名称 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              模型名称 <span class="text-red-500">*</span>
            </label>
            <input
              v-model="config.model_name"
              type="text"
              required
              placeholder="gpt-3.5-turbo"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <p class="text-xs text-gray-500 mt-1">
              推荐: gpt-3.5-turbo, gpt-4, claude-3-sonnet-20240229 等
            </p>
          </div>

          <!-- API Key -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              API Key <span class="text-red-500">*</span>
              <span v-if="config.has_api_key" class="text-green-600 text-xs ml-2">✓ 已配置</span>
            </label>
            <div class="relative">
              <input
                v-model="apiKeyInput"
                :type="showApiKey ? 'text' : 'password'"
                :placeholder="config.has_api_key ? '已加密保存 (留空保持不变)' : '请输入API Key'"
                class="w-full px-4 py-2 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button
                type="button"
                @click="showApiKey = !showApiKey"
                class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700"
              >
                {{ showApiKey ? '🙈' : '👁️' }}
              </button>
            </div>
            <p class="text-xs text-gray-500 mt-1">
              API密钥将被加密存储，仅用于调用AI服务
            </p>
          </div>

          <!-- 高级设置 -->
          <details class="border border-gray-200 rounded-lg p-4">
            <summary class="font-semibold cursor-pointer">⚙️ 高级设置</summary>
            <div class="mt-4 space-y-4">
              <!-- Temperature -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  Temperature (温度参数)
                </label>
                <input
                  v-model.number="config.temperature"
                  type="number"
                  min="0"
                  max="2"
                  step="0.1"
                  class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
                <p class="text-xs text-gray-500 mt-1">
                  控制输出随机性 (0=确定性, 2=创造性)。推荐: 0.7
                </p>
              </div>

              <!-- Max Tokens -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  最大Token数
                </label>
                <input
                  v-model.number="config.max_tokens"
                  type="number"
                  min="100"
                  max="4000"
                  step="50"
                  class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
                <p class="text-xs text-gray-500 mt-1">
                  控制输出长度。推荐: 500-1000
                </p>
              </div>

              <!-- 自动总结 -->
              <div class="flex items-center">
                <input
                  v-model="config.auto_summarize"
                  type="checkbox"
                  id="auto-summarize"
                  class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <label for="auto-summarize" class="ml-2 text-sm text-gray-700">
                  在查看卡片时自动调用AI总结 (消耗API额度)
                </label>
              </div>
            </div>
          </details>

          <!-- 错误提示 -->
          <div v-if="errorMessage" class="p-4 bg-red-50 border border-red-200 rounded-lg">
            <p class="text-red-700 text-sm">{{ errorMessage }}</p>
          </div>

          <!-- 成功提示 -->
          <div v-if="successMessage" class="p-4 bg-green-50 border border-green-200 rounded-lg">
            <p class="text-green-700 text-sm">{{ successMessage }}</p>
          </div>

          <!-- 操作按钮 -->
          <div class="flex gap-3">
            <button
              type="button"
              @click="testConnection"
              :disabled="isTesting || !config.enabled"
              class="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {{ isTesting ? '测试中...' : '🔌 测试连接' }}
            </button>

            <button
              type="submit"
              :disabled="isSaving"
              class="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed font-semibold"
            >
              {{ isSaving ? '保存中...' : '💾 保存配置' }}
            </button>
          </div>
        </form>

        <!-- 自定义提示词编辑区域 -->
        <div class="mt-8 border-t border-gray-200 pt-8">
          <h2 class="text-2xl font-bold mb-4">📝 自定义汉字提示词</h2>
          <p class="text-gray-600 mb-4">自定义AI生成汉字学习卡片时使用的提示词。留空则使用默认提示词。</p>

          <div class="space-y-4">
            <!-- 提示词编辑器 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                提示词模板
              </label>
              <textarea
                v-model="config.custom_chinese_prompt"
                rows="15"
                placeholder="留空使用默认提示词..."
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
              ></textarea>
              <div class="mt-2 flex items-start gap-2 text-xs text-gray-500">
                <span class="text-blue-600">💡</span>
                <div>
                  <p class="font-semibold text-gray-700 mb-1">占位符说明:</p>
                  <ul class="list-disc list-inside space-y-1">
                    <li><code class="bg-gray-100 px-1 rounded">{char}</code> - 将被替换为用户输入的汉字</li>
                    <li><code class="bg-gray-100 px-1 rounded">{context}</code> - 将被替换为额外的上下文信息(可选)</li>
                  </ul>
                </div>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="flex gap-3">
              <button
                type="button"
                @click="loadDefaultPrompt"
                :disabled="isLoadingDefaultPrompt"
                class="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {{ isLoadingDefaultPrompt ? '加载中...' : '📥 加载默认提示词' }}
              </button>

              <button
                type="button"
                @click="clearCustomPrompt"
                class="px-6 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700"
              >
                🗑️ 清空提示词
              </button>

              <button
                type="button"
                @click="saveCustomPrompt"
                :disabled="isSavingPrompt"
                class="flex-1 bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 disabled:bg-green-400 disabled:cursor-not-allowed font-semibold"
              >
                {{ isSavingPrompt ? '保存中...' : '💾 保存自定义提示词' }}
              </button>
            </div>

            <!-- 保存成功提示 -->
            <div v-if="promptSaveSuccess" class="p-4 bg-green-50 border border-green-200 rounded-lg">
              <p class="text-green-700 text-sm font-semibold">✅ {{ promptSaveSuccess }}</p>
            </div>

            <!-- 保存失败提示 -->
            <div v-if="promptSaveError" class="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p class="text-red-700 text-sm font-semibold mb-2">❌ 保存失败</p>
              <pre class="text-xs text-red-600 whitespace-pre-wrap">{{ promptSaveError }}</pre>
            </div>
          </div>
        </div>

        <!-- 汉字提示词测试区域 -->
        <div class="mt-8 border-t border-gray-200 pt-8">
          <h2 class="text-2xl font-bold mb-4">🧪 汉字提示词测试</h2>
          <p class="text-gray-600 mb-4">测试AI生成汉字学习卡片的完整流程，查看发送的提示词和返回的内容</p>

          <div class="space-y-4">
            <!-- 输入区域 -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                测试汉字 <span class="text-red-500">*</span>
              </label>
              <div class="flex gap-3">
                <input
                  v-model="testChar"
                  type="text"
                  maxlength="1"
                  placeholder="输入一个汉字，如：学"
                  class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-2xl text-center"
                  @keyup.enter="testChinesePrompt"
                />
                <button
                  type="button"
                  @click="testChinesePrompt"
                  :disabled="isTestingPrompt || !testChar || !config.enabled"
                  class="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-semibold"
                >
                  {{ isTestingPrompt ? '生成中...' : '🚀 测试生成' }}
                </button>
              </div>
              <p class="text-xs text-gray-500 mt-1">
                将调用AI生成完整的9节结构学习卡片，并显示所有请求和响应信息
              </p>
            </div>

            <!-- 错误提示 -->
            <div v-if="testError" class="p-4 bg-red-50 border border-red-200 rounded-lg">
              <p class="text-red-700 text-sm font-semibold mb-2">❌ 测试失败</p>
              <pre class="text-xs text-red-600 whitespace-pre-wrap">{{ testError }}</pre>
            </div>

            <!-- 成功提示 -->
            <div v-if="testSuccess" class="p-4 bg-green-50 border border-green-200 rounded-lg">
              <p class="text-green-700 text-sm font-semibold">✅ {{ testSuccess }}</p>
            </div>

            <!-- 发送的提示词 -->
            <div v-if="testPrompt" class="border border-blue-200 rounded-lg overflow-hidden">
              <div class="bg-blue-50 px-4 py-2 border-b border-blue-200 flex items-center justify-between">
                <h3 class="font-semibold text-blue-900">📤 发送的提示词</h3>
                <button
                  type="button"
                  @click="copyToClipboard(testPrompt, 'prompt')"
                  class="text-xs px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  {{ copiedPrompt ? '✓ 已复制' : '📋 复制' }}
                </button>
              </div>
              <div class="p-4 bg-white max-h-96 overflow-y-auto">
                <pre class="text-xs text-gray-800 whitespace-pre-wrap leading-relaxed">{{ testPrompt }}</pre>
              </div>
            </div>

            <!-- AI返回的原始内容 -->
            <div v-if="testResponse" class="border border-green-200 rounded-lg overflow-hidden">
              <div class="bg-green-50 px-4 py-2 border-b border-green-200 flex items-center justify-between">
                <h3 class="font-semibold text-green-900">📥 AI返回的原始内容</h3>
                <button
                  type="button"
                  @click="copyToClipboard(testResponse, 'response')"
                  class="text-xs px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700"
                >
                  {{ copiedResponse ? '✓ 已复制' : '📋 复制' }}
                </button>
              </div>
              <div class="p-4 bg-white max-h-96 overflow-y-auto">
                <pre class="text-xs text-gray-800 whitespace-pre-wrap leading-relaxed">{{ testResponse }}</pre>
              </div>
            </div>

            <!-- 解析后的字段 -->
            <div v-if="testParsed" class="border border-purple-200 rounded-lg overflow-hidden">
              <div class="bg-purple-50 px-4 py-2 border-b border-purple-200">
                <h3 class="font-semibold text-purple-900">🔍 解析后的字段</h3>
              </div>
              <div class="p-4 bg-white">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div v-for="(value, key) in testParsed" :key="key" class="border border-gray-200 rounded p-3">
                    <div class="text-xs font-semibold text-gray-600 mb-1">{{ getFieldLabel(key) }}</div>
                    <div class="text-sm text-gray-800">
                      <template v-if="Array.isArray(value)">
                        <span v-if="value.length === 0" class="text-gray-400 italic">空</span>
                        <span v-else>{{ value.join(', ') }}</span>
                      </template>
                      <template v-else>
                        <span v-if="!value" class="text-gray-400 italic">空</span>
                        <pre v-else class="whitespace-pre-wrap text-xs">{{ value }}</pre>
                      </template>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 请求详情 -->
            <div v-if="testRequestInfo" class="border border-gray-200 rounded-lg overflow-hidden">
              <div class="bg-gray-50 px-4 py-2 border-b border-gray-200">
                <h3 class="font-semibold text-gray-900">ℹ️ 请求详情</h3>
              </div>
              <div class="p-4 bg-white">
                <div class="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span class="text-gray-600">模型:</span>
                    <span class="ml-2 font-mono text-gray-800">{{ testRequestInfo.model }}</span>
                  </div>
                  <div>
                    <span class="text-gray-600">Temperature:</span>
                    <span class="ml-2 font-mono text-gray-800">{{ testRequestInfo.temperature }}</span>
                  </div>
                  <div>
                    <span class="text-gray-600">Max Tokens:</span>
                    <span class="ml-2 font-mono text-gray-800">{{ testRequestInfo.max_tokens }}</span>
                  </div>
                  <div>
                    <span class="text-gray-600">耗时:</span>
                    <span class="ml-2 font-mono text-gray-800">{{ testRequestInfo.duration }}ms</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 使用说明 -->
        <div class="mt-8 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <h3 class="font-semibold text-yellow-900 mb-2">💡 使用提示</h3>
          <ul class="text-sm text-yellow-800 space-y-1">
            <li>• 配置完成后，在复习页面可使用"AI总结"按钮获取词汇学习建议</li>
            <li>• API Key会被加密存储在服务器，请妥善保管</li>
            <li>• 建议先使用"测试连接"验证配置是否正确</li>
            <li>• 使用第三方API服务可降低成本 (如 OpenRouter, Together AI等)</li>
            <li>• 使用"汉字提示词测试"可以查看完整的AI请求和响应，便于调试</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const config = ref({
  provider: 'openai',
  base_url: 'https://api.openai.com/v1',
  model_name: 'gpt-3.5-turbo',
  enabled: false,
  auto_summarize: false,
  temperature: 0.7,
  max_tokens: 500,
  custom_chinese_prompt: '',
  has_api_key: false
})

const apiKeyInput = ref('')
const showApiKey = ref(false)
const isLoading = ref(false)
const isSaving = ref(false)
const isTesting = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

// 自定义提示词相关
const isLoadingDefaultPrompt = ref(false)
const isSavingPrompt = ref(false)
const promptSaveSuccess = ref('')
const promptSaveError = ref('')

// 测试提示词相关
const testChar = ref('')
const isTestingPrompt = ref(false)
const testError = ref('')
const testSuccess = ref('')
const testPrompt = ref('')
const testResponse = ref('')
const testParsed = ref(null)
const testRequestInfo = ref(null)
const copiedPrompt = ref(false)
const copiedResponse = ref(false)

onMounted(async () => {
  await loadConfig()
})

async function loadConfig() {
  isLoading.value = true
  errorMessage.value = ''

  try {
    const response = await axios.get('/api/ai-config/')
    if (response.data) {
      config.value = { ...config.value, ...response.data }
    }
  } catch (err) {
    console.error('Failed to load AI config:', err)
    if (err.response?.status !== 404) {
      errorMessage.value = '加载配置失败'
    }
  } finally {
    isLoading.value = false
  }
}

async function saveConfig() {
  isSaving.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    const payload = {
      provider: config.value.provider,
      base_url: config.value.base_url,
      model_name: config.value.model_name,
      enabled: config.value.enabled,
      auto_summarize: config.value.auto_summarize,
      temperature: config.value.temperature,
      max_tokens: config.value.max_tokens
    }

    // 只在有输入时才发送API Key
    if (apiKeyInput.value.trim()) {
      payload.api_key = apiKeyInput.value.trim()
    }

    const response = await axios.post('/api/ai-config/', payload)
    config.value = { ...config.value, ...response.data }

    successMessage.value = '✓ 配置保存成功！'
    apiKeyInput.value = '' // 清空输入

    setTimeout(() => {
      successMessage.value = ''
    }, 3000)
  } catch (err) {
    console.error('Failed to save AI config:', err)
    errorMessage.value = err.response?.data?.error || '保存配置失败'
  } finally {
    isSaving.value = false
  }
}

async function testConnection() {
  isTesting.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    const response = await axios.post('/api/ai-config/test_connection/')
    successMessage.value = `✓ 连接测试成功！使用模型: ${response.data.model}`

    setTimeout(() => {
      successMessage.value = ''
    }, 3000)
  } catch (err) {
    console.error('Connection test failed:', err)
    errorMessage.value = err.response?.data?.error || '连接测试失败'
  } finally {
    isTesting.value = false
  }
}

function getProviderHint(provider) {
  const hints = {
    'openai': 'OpenAI官方服务或兼容API (如OpenRouter, Together AI)',
    'anthropic': 'Anthropic Claude官方服务',
    'local': '本地部署的大模型 (支持OpenAI格式API)'
  }
  return hints[provider] || ''
}

// 测试汉字提示词
async function testChinesePrompt() {
  if (!testChar.value || testChar.value.length !== 1) {
    testError.value = '请输入一个汉字'
    return
  }

  isTestingPrompt.value = true
  testError.value = ''
  testSuccess.value = ''
  testPrompt.value = ''
  testResponse.value = ''
  testParsed.value = null
  testRequestInfo.value = null

  const startTime = Date.now()

  try {
    const response = await axios.post('/api/ai-config/test-chinese-prompt/', {
      char: testChar.value
    })

    const duration = Date.now() - startTime

    // 显示发送的提示词
    testPrompt.value = response.data.prompt

    // 显示AI返回的原始内容
    testResponse.value = response.data.response

    // 显示解析后的字段
    testParsed.value = response.data.parsed

    // 显示请求详情
    testRequestInfo.value = {
      model: response.data.model,
      temperature: response.data.temperature,
      max_tokens: response.data.max_tokens,
      duration: duration
    }

    testSuccess.value = `✓ 测试成功！汉字「${testChar.value}」的学习卡片已生成`

  } catch (err) {
    console.error('Test Chinese prompt failed:', err)

    if (err.response?.data) {
      const errorData = err.response.data
      testError.value = errorData.error || errorData.detail || '测试失败'

      // 如果有部分数据也显示出来
      if (errorData.prompt) {
        testPrompt.value = errorData.prompt
      }
      if (errorData.response) {
        testResponse.value = errorData.response
      }
    } else {
      testError.value = '网络连接失败，请检查网络设置'
    }
  } finally {
    isTestingPrompt.value = false
  }
}

// 复制到剪贴板
async function copyToClipboard(text, type) {
  try {
    await navigator.clipboard.writeText(text)

    if (type === 'prompt') {
      copiedPrompt.value = true
      setTimeout(() => {
        copiedPrompt.value = false
      }, 2000)
    } else if (type === 'response') {
      copiedResponse.value = true
      setTimeout(() => {
        copiedResponse.value = false
      }, 2000)
    }
  } catch (err) {
    console.error('Failed to copy:', err)
  }
}

// 获取字段标签
function getFieldLabel(key) {
  const labels = {
    pinyin: '拼音',
    meaning: '释义',
    radical: '部首',
    strokes: '笔画',
    structure: '结构',
    examples: '例句',
    memoryTips: '记忆技巧',
    confusion: '易混辨析',
    exercises: '小练习',
    keyPoints: '关键要点',
    writingTips: '书写与笔顺',
    memoryScript: '记忆方案',
    summary: '一句话总结'
  }
  return labels[key] || key
}

// 加载默认提示词
async function loadDefaultPrompt() {
  isLoadingDefaultPrompt.value = true
  promptSaveError.value = ''
  promptSaveSuccess.value = ''

  try {
    const response = await axios.get('/api/ai-config/default-prompt/')
    config.value.custom_chinese_prompt = response.data.prompt
    promptSaveSuccess.value = '✓ 默认提示词已加载到编辑器，点击"保存"以应用'
  } catch (err) {
    console.error('Load default prompt failed:', err)
    promptSaveError.value = '加载默认提示词失败，请检查网络连接'
  } finally {
    isLoadingDefaultPrompt.value = false
  }
}

// 清空自定义提示词
function clearCustomPrompt() {
  if (confirm('确定要清空自定义提示词吗？清空后将使用默认提示词。')) {
    config.value.custom_chinese_prompt = ''
    promptSaveSuccess.value = '✓ 已清空自定义提示词（尚未保存）'
    promptSaveError.value = ''
  }
}

// 保存自定义提示词
async function saveCustomPrompt() {
  isSavingPrompt.value = true
  promptSaveError.value = ''
  promptSaveSuccess.value = ''

  try {
    const payload = {
      custom_chinese_prompt: config.value.custom_chinese_prompt || null
    }

    await axios.post('/api/ai-config/', payload)
    promptSaveSuccess.value = '✓ 自定义提示词已保存成功！'

    // 3秒后自动隐藏成功提示
    setTimeout(() => {
      promptSaveSuccess.value = ''
    }, 3000)
  } catch (err) {
    console.error('Save custom prompt failed:', err)
    promptSaveError.value = err.response?.data?.detail || '保存失败，请稍后重试'
  } finally {
    isSavingPrompt.value = false
  }
}
</script>

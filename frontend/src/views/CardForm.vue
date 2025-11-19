<template>
  <div class="min-h-screen bg-gray-50">
    <nav class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 py-4">
        <router-link to="/" class="text-gray-600 hover:text-gray-900">← 返回</router-link>
      </div>
    </nav>

    <div class="max-w-4xl mx-auto px-4 py-8">
      <h1 class="text-3xl font-bold mb-8">添加卡片</h1>

      <div class="bg-white rounded-lg shadow p-6">
        <form @submit.prevent="handleSubmit">
          <!-- 卡组选择 -->
          <div class="mb-6">
            <label class="block text-sm font-medium text-gray-700 mb-2">卡组</label>
            <select v-model="form.deck_id" required class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
              <option value="">请选择卡组</option>
              <option v-for="deck in decks" :key="deck.id" :value="deck.id">
                {{ deck.name }}
              </option>
            </select>
          </div>

          <!-- 类型选择 -->
          <div class="mb-6">
            <label class="block text-sm font-medium text-gray-700 mb-2">类型</label>
            <div class="flex gap-4">
              <label class="flex items-center">
                <input type="radio" v-model="form.card_type" value="en" class="mr-2" />
                <span>英语单词</span>
              </label>
              <label class="flex items-center">
                <input type="radio" v-model="form.card_type" value="zh" class="mr-2" />
                <span>汉字</span>
              </label>
            </div>
          </div>

          <!-- 单词/字符输入 -->
          <div class="mb-6">
            <label class="block text-sm font-medium text-gray-700 mb-2">
              {{ form.card_type === 'en' ? '英语单词' : '汉字' }}
            </label>
            <input
              v-model="form.word"
              @blur="handleWordBlur"
              type="text"
              required
              :placeholder="form.card_type === 'en' ? '输入英语单词，失焦后自动查询字典' : '输入汉字，失焦后自动查询字典'"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <div v-if="isLookingUp" class="mt-2 text-sm text-blue-600">
              🔍 正在查询字典...
            </div>
          </div>

          <!-- 拼音选择（仅中文） -->
          <div v-if="form.card_type === 'zh' && pinyinCandidates.length > 0" class="mb-6">
            <label class="block text-sm font-medium text-gray-700 mb-2">拼音（多音字）</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="(candidate, idx) in pinyinCandidates"
                :key="idx"
                type="button"
                @click="form.metadata.pinyin = candidate"
                :class="[
                  'px-4 py-2 rounded-lg border',
                  form.metadata.pinyin === candidate
                    ? 'bg-blue-500 text-white border-blue-500'
                    : 'bg-white text-gray-700 border-gray-300 hover:border-blue-500'
                ]"
              >
                {{ candidate }}
              </button>
            </div>
          </div>

          <!-- 释义（自动填充） -->
          <div class="mb-6">
            <label class="block text-sm font-medium text-gray-700 mb-2">释义</label>
            <textarea
              v-model="form.meaning"
              rows="3"
              required
              placeholder="将在查询字典后自动填充，也可手动编辑"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            ></textarea>
          </div>

          <!-- 例句（可选） -->
          <div class="mb-6">
            <label class="block text-sm font-medium text-gray-700 mb-2">例句（可选）</label>
            <textarea
              v-model="form.example"
              rows="2"
              placeholder="将在查询字典后自动填充（如有），也可手动编辑"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            ></textarea>
          </div>

          <!-- 标签（可选） -->
          <div class="mb-6">
            <label class="block text-sm font-medium text-gray-700 mb-2">标签（可选，逗号分隔）</label>
            <input
              v-model="tagsInput"
              type="text"
              placeholder="例如: 四级,高频,动词"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <!-- 字典查询结果预览 -->
          <div v-if="dictResult" class="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div class="text-sm text-blue-800 mb-2">
              📖 字典查询结果（来源: {{ dictResult.source }}）
            </div>
            <div class="text-sm text-gray-700" v-html="formatDictResult(dictResult.data)"></div>
          </div>

          <!-- 错误提示 -->
          <div v-if="error" class="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {{ error }}
          </div>

          <!-- 提交按钮 -->
          <div class="flex gap-4">
            <button
              type="submit"
              :disabled="isSubmitting"
              class="flex-1 bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {{ isSubmitting ? '保存中...' : '保存卡片' }}
            </button>
            <button
              type="button"
              @click="handleReset"
              class="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              重置
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { lookupWord } from '@/services/dictService'

const router = useRouter()

const form = reactive({
  deck_id: '',
  card_type: 'en',
  word: '',
  meaning: '',
  example: '',
  metadata: {},
  tags: []
})

const decks = ref([])
const tagsInput = ref('')
const pinyinCandidates = ref([])
const dictResult = ref(null)
const isLookingUp = ref(false)
const isSubmitting = ref(false)
const error = ref('')

// 获取卡组列表
onMounted(async () => {
  try {
    const response = await axios.get('/api/cards/decks/')
    decks.value = response.data

    // 如果只有一个卡组，自动选中
    if (decks.value.length === 1) {
      form.deck_id = decks.value[0].id
    }
  } catch (err) {
    console.error('Failed to load decks:', err)
    error.value = '加载卡组列表失败'
  }
})

// 字典查询和自动填充逻辑
async function handleWordBlur() {
  // 1. 检查输入是否为空
  if (!form.word || !form.word.trim()) {
    return
  }

  const word = form.word.trim()

  // 2. 显示加载状态
  isLookingUp.value = true
  error.value = ''

  try {
    // 3. 调用字典查询服务
    const result = await lookupWord(word, form.card_type)

    if (result && result.data) {
      // 保存查询结果用于预览
      dictResult.value = result

      // 4. 根据类型自动填充表单
      if (form.card_type === 'en') {
        // 英文单词
        const data = result.data

        // 提取释义
        if (data.translation) {
          form.meaning = data.translation
        } else if (data.definition) {
          form.meaning = data.definition
        }

        // 提取例句
        if (data.example) {
          form.example = data.example
        }

        // 保存音标到 metadata
        if (data.phonetic) {
          form.metadata.phonetic = data.phonetic
        }
      } else if (form.card_type === 'zh') {
        // 中文字符
        const data = result.data

        // 提取释义
        if (data.definition) {
          form.meaning = data.definition
        }

        // 4. 调用拼音推断API获取多音字候选项
        try {
          const pinyinResponse = await axios.post('/api/cards/dict/zh/infer-pinyin/', {
            text: word
          })

          if (pinyinResponse.data && pinyinResponse.data.candidates) {
            pinyinCandidates.value = pinyinResponse.data.candidates

            // 自动选择第一个拼音
            if (pinyinCandidates.value.length > 0) {
              form.metadata.pinyin = pinyinCandidates.value[0]
            }
          }
        } catch (pinyinErr) {
          console.error('Failed to infer pinyin:', pinyinErr)
          // 拼音推断失败不影响主流程
        }
      }
    } else {
      // 查询失败，提示用户手动输入
      error.value = '未找到该词的字典信息，请手动输入释义'
    }
  } catch (err) {
    console.error('Dictionary lookup failed:', err)
    error.value = '字典查询失败，请手动输入释义'
  } finally {
    // 7. 恢复加载状态
    isLookingUp.value = false
  }
}

// 格式化字典结果用于预览
function formatDictResult(data) {
  if (!data) return ''

  let html = ''
  if (data.phonetic) {
    html += `<div><strong>音标:</strong> ${data.phonetic}</div>`
  }
  if (data.translation) {
    html += `<div><strong>释义:</strong> ${data.translation}</div>`
  }
  if (data.definition) {
    html += `<div><strong>定义:</strong> ${data.definition}</div>`
  }
  if (data.example) {
    html += `<div><strong>例句:</strong> ${data.example}</div>`
  }
  return html
}

// 提交表单
async function handleSubmit() {
  error.value = ''
  isSubmitting.value = true

  try {
    // 解析标签
    form.tags = tagsInput.value
      .split(',')
      .map(t => t.trim())
      .filter(t => t.length > 0)

    // 提交到后端
    await axios.post('/api/cards/cards/', form)

    // 成功后跳转到卡片列表
    router.push('/cards')
  } catch (err) {
    console.error('Failed to create card:', err)
    error.value = err.response?.data?.detail || '保存失败，请稍后重试'
  } finally {
    isSubmitting.value = false
  }
}

// 重置表单
function handleReset() {
  form.word = ''
  form.meaning = ''
  form.example = ''
  form.metadata = {}
  form.tags = []
  tagsInput.value = ''
  pinyinCandidates.value = []
  dictResult.value = null
  error.value = ''
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <nav class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 py-4">
        <router-link to="/" class="text-gray-600 hover:text-gray-900">← 返回</router-link>
      </div>
    </nav>

    <div class="max-w-4xl mx-auto px-4 py-8">
      <h1 class="text-3xl font-bold mb-8">{{ isEditMode ? '编辑卡片' : '添加卡片' }}</h1>

      <div class="bg-white rounded-lg shadow p-6">
        <!-- 加载状态 -->
        <div v-if="isLoading" class="text-center py-8">
          <svg class="animate-spin h-8 w-8 mx-auto text-blue-600" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p class="mt-4 text-gray-600">加载中...</p>
        </div>

        <form v-else @submit.prevent="handleSubmit">
          <!-- 卡组选择 -->
          <div class="mb-6">
            <label class="block text-sm font-medium text-gray-700 mb-2">卡组</label>

            <!-- 没有卡组时的提示 -->
            <div v-if="decks.length === 0" class="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div class="flex items-start">
                <svg class="w-5 h-5 text-yellow-600 mr-2 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"/>
                </svg>
                <div class="flex-1">
                  <h3 class="text-sm font-medium text-yellow-800">您还没有创建任何卡组</h3>
                  <p class="mt-1 text-sm text-yellow-700">请先创建一个卡组来存放您的卡片</p>
                  <button
                    type="button"
                    @click="showQuickCreateDeck = true"
                    class="mt-2 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 text-sm"
                  >
                    快速创建卡组
                  </button>
                </div>
              </div>
            </div>

            <!-- 卡组选择下拉框 -->
            <div v-else class="space-y-2">
              <select v-model="form.deck" @change="handleDeckChange" required class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                <option value="">请选择卡组</option>
                <option v-for="deck in decks" :key="deck.id" :value="deck.id">
                  {{ deck.name }}
                </option>
                <option value="__create_new__">+ 新建卡组</option>
              </select>
            </div>
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
              :disabled="isSubmitting || decks.length === 0"
              class="flex-1 bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {{ isSubmitting ? '保存中...' : isEditMode ? '更新卡片' : '保存卡片' }}
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

      <!-- 快速创建卡组对话框 -->
      <div v-if="showQuickCreateDeck" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="showQuickCreateDeck = false">
        <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
          <h2 class="text-2xl font-bold mb-4">创建新卡组</h2>

          <form @submit.prevent="handleQuickCreateDeck">
            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-2">卡组名称</label>
              <input
                v-model="newDeck.name"
                type="text"
                required
                placeholder="例如: 四级词汇、常用汉字"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div class="mb-4">
              <label class="block text-sm font-medium text-gray-700 mb-2">描述（可选）</label>
              <textarea
                v-model="newDeck.description"
                rows="2"
                placeholder="卡组的简短描述"
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              ></textarea>
            </div>

            <div v-if="deckError" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {{ deckError }}
            </div>

            <div class="flex gap-3">
              <button
                type="submit"
                :disabled="isCreatingDeck"
                class="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
              >
                {{ isCreatingDeck ? '创建中...' : '创建卡组' }}
              </button>
              <button
                type="button"
                @click="showQuickCreateDeck = false"
                class="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                取消
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import { lookupWord } from '@/services/dictService'

const router = useRouter()
const route = useRoute()

// 判断是否为编辑模式
const cardId = computed(() => route.params.id)
const isEditMode = computed(() => !!cardId.value)

const form = reactive({
  deck: '',
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
const isLoading = ref(false)
const error = ref('')

// 快速创建卡组相关状态
const showQuickCreateDeck = ref(false)
const isCreatingDeck = ref(false)
const deckError = ref('')
const newDeck = reactive({
  name: '',
  description: ''
})

// 监听卡组选择变化
function handleDeckChange() {
  if (form.deck === '__create_new__') {
    form.deck = ''
    showQuickCreateDeck.value = true
  }
}

// 获取卡组列表和卡片数据（编辑模式）
onMounted(async () => {
  try {
    // 加载卡组列表
    const response = await axios.get('/api/decks/')
    decks.value = response.data.results || response.data

    // 如果是编辑模式，加载卡片数据
    if (isEditMode.value) {
      await loadCardData()
    } else {
      // 添加模式：如果只有一个卡组，自动选中
      if (decks.value.length === 1) {
        form.deck = decks.value[0].id
      }
    }
  } catch (err) {
    console.error('Failed to load decks:', err)
    error.value = '加载卡组列表失败'
  }
})

// 加载卡片数据（编辑模式）
async function loadCardData() {
  isLoading.value = true
  error.value = ''

  try {
    const response = await axios.get(`/api/cards/${cardId.value}/`)
    const card = response.data

    // 填充表单
    form.deck = card.deck
    form.card_type = card.card_type
    form.word = card.word
    form.metadata = card.metadata || {}
    form.tags = card.tags || []

    // 从 metadata 中提取释义和例句
    if (card.metadata) {
      if (card.card_type === 'en') {
        form.meaning = card.metadata.meaning_zh || card.metadata.meaning_en || ''
        form.example = card.metadata.examples ? card.metadata.examples.join('\n') : ''
      } else if (card.card_type === 'zh') {
        form.meaning = card.metadata.meaning_zh || ''
        form.example = card.metadata.examples ? card.metadata.examples.join('\n') : ''

        // 恢复拼音候选项
        if (card.metadata.pinyin) {
          if (Array.isArray(card.metadata.pinyin)) {
            pinyinCandidates.value = card.metadata.pinyin
          } else {
            pinyinCandidates.value = [card.metadata.pinyin]
          }
        }
      }
    }

    // 恢复标签输入
    tagsInput.value = card.tags ? card.tags.join(', ') : ''

  } catch (err) {
    console.error('Failed to load card:', err)
    error.value = '加载卡片数据失败'

    // 如果加载失败，返回列表页
    setTimeout(() => {
      router.push('/cards')
    }, 2000)
  } finally {
    isLoading.value = false
  }
}

// 快速创建卡组
async function handleQuickCreateDeck() {
  deckError.value = ''
  isCreatingDeck.value = true

  try {
    const response = await axios.post('/api/decks/', {
      name: newDeck.name,
      description: newDeck.description,
      daily_new_limit: 20,
      daily_review_limit: 200
    })

    // 添加到卡组列表
    decks.value.push(response.data)

    // 自动选中新创建的卡组
    form.deck = response.data.id

    // 关闭对话框并重置表单
    showQuickCreateDeck.value = false
    newDeck.name = ''
    newDeck.description = ''

  } catch (err) {
    console.error('Failed to create deck:', err)
    deckError.value = err.response?.data?.detail || '创建卡组失败，请稍后重试'
  } finally {
    isCreatingDeck.value = false
  }
}

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

        // 提取释义 (支持多种字段名)
        if (data.meaning_zh) {
          form.meaning = data.meaning_zh
        } else if (data.definition) {
          form.meaning = data.definition
        }

        // 提取例句
        if (data.examples && data.examples.length > 0) {
          // 如果有多个例句,取前3个并用换行符连接
          form.example = data.examples.slice(0, 3).join('\n')
        }

        // 保存部首、笔画等元数据
        if (data.radical) {
          form.metadata.radical = data.radical
        }
        if (data.strokes) {
          form.metadata.strokes = data.strokes
        }
        if (data.traditional) {
          form.metadata.traditional = data.traditional
        }

        // 处理拼音 - 优先使用API返回的拼音
        if (data.pinyin && data.pinyin.length > 0) {
          pinyinCandidates.value = data.pinyin

          // 保存完整的拼音数组（支持多音字）
          form.metadata.pinyin = data.pinyin
        } else {
          // 如果API没有返回拼音,调用拼音推断API
          try {
            const pinyinResponse = await axios.post('/api/dict/zh/infer-pinyin/', {
              text: word
            })

            if (pinyinResponse.data && pinyinResponse.data.candidates) {
              pinyinCandidates.value = pinyinResponse.data.candidates

              // 保存完整的拼音数组（支持多音字）
              if (pinyinCandidates.value.length > 0) {
                form.metadata.pinyin = pinyinCandidates.value
              }
            }
          } catch (pinyinErr) {
            console.error('Failed to infer pinyin:', pinyinErr)
            // 拼音推断失败不影响主流程
          }
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

  // 英文单词字段
  if (data.phonetic || data.ipa) {
    html += `<div><strong>音标:</strong> ${data.phonetic || data.ipa}</div>`
  }
  if (data.translation) {
    html += `<div><strong>翻译:</strong> ${data.translation}</div>`
  }
  if (data.meaning_en) {
    html += `<div><strong>英文释义:</strong> ${data.meaning_en}</div>`
  }

  // 中文汉字字段
  if (data.pinyin && Array.isArray(data.pinyin)) {
    html += `<div><strong>拼音:</strong> ${data.pinyin.join(', ')}</div>`
  }
  if (data.meaning_zh) {
    // 截取前200字符避免太长
    const meaning = data.meaning_zh.length > 200
      ? data.meaning_zh.substring(0, 200) + '...'
      : data.meaning_zh
    html += `<div><strong>释义:</strong> ${meaning}</div>`
  }
  if (data.definition) {
    html += `<div><strong>定义:</strong> ${data.definition}</div>`
  }
  if (data.radical) {
    html += `<div><strong>部首:</strong> ${data.radical}</div>`
  }
  if (data.strokes) {
    html += `<div><strong>笔画:</strong> ${data.strokes}</div>`
  }

  // 例句
  if (data.examples && data.examples.length > 0) {
    const examplesList = data.examples.slice(0, 2).join('<br>')
    html += `<div><strong>例句:</strong><br>${examplesList}</div>`
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

    // 构建提交数据
    const submitData = {
      deck: form.deck,
      card_type: form.card_type,
      word: form.word,
      tags: form.tags,
      metadata: { ...form.metadata }
    }

    // 将释义和例句存入 metadata
    if (form.card_type === 'en') {
      submitData.metadata.meaning_zh = form.meaning
      submitData.metadata.meaning_en = form.meaning
    } else if (form.card_type === 'zh') {
      submitData.metadata.meaning_zh = form.meaning
    }

    // 将例句存入 metadata
    if (form.example && form.example.trim()) {
      submitData.metadata.examples = form.example.split('\n').filter(e => e.trim())
    }

    // 根据模式选择 API 方法
    if (isEditMode.value) {
      // 更新模式：使用 PUT
      await axios.put(`/api/cards/${cardId.value}/`, submitData)
    } else {
      // 添加模式：使用 POST
      await axios.post('/api/cards/', submitData)
    }

    // 成功后跳转到卡片列表
    router.push('/cards')
  } catch (err) {
    console.error('Failed to save card:', err)
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

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
            <div class="flex gap-2">
              <input
                v-model="form.word"
                @blur="handleWordBlur"
                type="text"
                required
                :placeholder="form.card_type === 'en' ? '输入英语单词，失焦后自动查询字典' : '输入汉字，失焦后自动查询字典'"
                class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <!-- AI记忆卡生成按钮（仅汉字） -->
              <button
                v-if="form.card_type === 'zh' && form.word.trim()"
                type="button"
                @click="generateAIMemoryCard"
                :disabled="isGeneratingAI"
                class="px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-700 hover:to-indigo-700 disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed flex items-center gap-2 whitespace-nowrap"
                title="使用AI生成专业的快速记忆卡内容"
              >
                <span>🤖</span>
                <span v-if="isGeneratingAI">生成中...</span>
                <span v-else>AI记忆卡</span>
              </button>
            </div>
            <div v-if="isLookingUp" class="mt-2 text-sm text-blue-600">
              🔍 正在查询字典...
            </div>
            <div v-if="isGeneratingAI" class="mt-2 text-sm text-purple-600">
              ✨ AI正在为您生成专业记忆卡...
            </div>
            <div v-if="aiError" class="mt-2 text-sm text-red-600">
              {{ aiError }}
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

          <!-- 字典/AI查询结果预览 -->
          <div v-if="dictResult" class="mb-6 p-4 rounded-lg" :class="dictResult.source.includes('AI') ? 'bg-purple-50 border border-purple-200' : 'bg-blue-50 border border-blue-200'">
            <div class="flex items-start justify-between mb-2">
              <div class="text-sm font-medium" :class="dictResult.source.includes('AI') ? 'text-purple-800' : 'text-blue-800'">
                <span v-if="dictResult.source.includes('AI')">✨ AI生成内容</span>
                <span v-else>📖 字典查询结果</span>
                <span class="ml-2 text-xs opacity-75">({{ dictResult.source }})</span>
              </div>
              <button
                v-if="dictResult.source.includes('AI')"
                @click="showFullAIContent = !showFullAIContent"
                type="button"
                class="text-xs text-purple-600 hover:text-purple-800 underline"
              >
                {{ showFullAIContent ? '收起' : '查看完整内容' }}
              </button>
            </div>

            <!-- 简化视图（默认） -->
            <div v-if="!showFullAIContent" class="text-sm text-gray-700">
              <div v-if="dictResult.data.pinyin" class="mb-1">
                <strong>拼音:</strong> {{ Array.isArray(dictResult.data.pinyin) ? dictResult.data.pinyin.join(', ') : dictResult.data.pinyin }}
              </div>
              <div v-if="dictResult.data.meaning_zh" class="mb-1">
                <strong>释义:</strong> {{ dictResult.data.meaning_zh.substring(0, 100) }}{{ dictResult.data.meaning_zh.length > 100 ? '...' : '' }}
              </div>
              <div v-if="dictResult.data.examples && dictResult.data.examples.length > 0" class="mb-1">
                <strong>例句:</strong> {{ dictResult.data.examples.slice(0, 2).join('、') }}
              </div>
            </div>

            <!-- 完整视图（展开后） -->
            <div v-else class="text-sm text-gray-700 space-y-2 max-h-96 overflow-y-auto">
              <div v-html="formatDictResult(dictResult.data)"></div>
              <div v-if="form.metadata.ai_full_content" class="mt-3 pt-3 border-t border-purple-200">
                <div class="font-medium text-purple-800 mb-2">📄 AI原始输出:</div>
                <pre class="whitespace-pre-wrap text-xs bg-white p-3 rounded border border-purple-100">{{ form.metadata.ai_full_content }}</pre>
              </div>
            </div>
          </div>

          <!-- SVG 卡片预览 -->
          <div v-if="svgPreview" class="mb-6 p-4 rounded-lg bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200">
            <div class="flex items-center justify-between mb-3">
              <h3 class="text-lg font-semibold text-blue-900">🎨 SVG 卡片预览</h3>
              <span v-if="isGeneratingSVG" class="text-sm text-blue-600">生成中...</span>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="bg-white rounded-lg p-3 shadow-sm">
                <p class="text-xs font-medium text-gray-600 mb-2 text-center">正面（识记）</p>
                <SVGCard :svgContent="svgPreview.front" :width="800" :height="500" />
              </div>
              <div class="bg-white rounded-lg p-3 shadow-sm">
                <p class="text-xs font-medium text-gray-600 mb-2 text-center">反面（应用）</p>
                <SVGCard :svgContent="svgPreview.back" :width="800" :height="500" />
              </div>
            </div>
            <p class="text-xs text-blue-700 mt-3 text-center">💡 保存卡片后,复习时可在 SVG/文字模式间切换</p>
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
import { formatDueTime } from '@/utils/timeFormatter'
import SVGCard from '@/components/SVGCard.vue'

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

// AI记忆卡生成相关状态
const isGeneratingAI = ref(false)
const aiError = ref('')
const showFullAIContent = ref(false)  // 新增：控制AI内容展开/收起

// SVG 预览相关状态
const svgPreview = ref(null)
const isGeneratingSVG = ref(false)

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

    // 将释义和例句存入 metadata (如果不是AI生成,则手动填充)
    if (form.card_type === 'en') {
      if (!submitData.metadata.meaning_zh) {
        submitData.metadata.meaning_zh = form.meaning
      }
      if (!submitData.metadata.meaning_en) {
        submitData.metadata.meaning_en = form.meaning
      }
    } else if (form.card_type === 'zh') {
      if (!submitData.metadata.meaning_zh) {
        submitData.metadata.meaning_zh = form.meaning
      }
    }

    // 将例句存入 metadata (如果不是AI生成,则手动填充)
    if (form.example && form.example.trim() && !submitData.metadata.examples) {
      submitData.metadata.examples = form.example.split('\n').filter(e => e.trim())
    }

    // 根据模式选择 API 方法
    let response
    if (isEditMode.value) {
      // 更新模式：使用 PUT
      response = await axios.put(`/api/cards/${cardId.value}/`, submitData)
    } else {
      // 添加模式：使用 POST
      response = await axios.post('/api/cards/', submitData)
    }

    // 获取保存后的卡片数据（包含复习时间）
    const savedCard = response.data

    // 显示成功消息（包含复习时间）
    const reviewTimeText = formatDueTime(savedCard.due_at)

    // 可以在这里添加成功提示
    console.log(`卡片保存成功！下次复习时间：${reviewTimeText}`)

    // 成功后跳转到卡片列表
    router.push({
      path: '/cards',
      query: {
        successMessage: `卡片保存成功！下次复习时间：${reviewTimeText}`
      }
    })
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
  aiError.value = ''
}

// AI记忆卡生成
async function generateAIMemoryCard() {
  // 清除之前的错误信息
  aiError.value = ''
  error.value = ''

  // 检查是否输入了汉字
  if (!form.word || !form.word.trim()) {
    aiError.value = '请先输入汉字'
    return
  }

  // 检查是否为汉字类型
  if (form.card_type !== 'zh') {
    aiError.value = 'AI记忆卡功能仅支持汉字'
    return
  }

  isGeneratingAI.value = true

  try {
    // 调用AI总结API
    const response = await axios.post('/api/ai/summarize/', {
      word: form.word.trim(),
      card_type: 'zh',
      context: ''  // 可选的额外上下文
    })

    if (response.data && response.data.summary) {
      const aiContent = response.data.summary

      // 解析AI返回的结构化内容
      const parsed = parseAIContent(aiContent)

      // 填充解析后的数据到表单
      if (parsed.pinyin) {
        form.metadata.pinyin = parsed.pinyin
        pinyinCandidates.value = parsed.pinyin
      }

      // 🆕 优先使用原始章节内容填充释义框
      if (parsed.meaningRaw) {
        form.meaning = parsed.meaningRaw
        form.metadata.meaning_zh = parsed.meaningRaw
      } else if (parsed.meaning) {
        form.meaning = parsed.meaning
        form.metadata.meaning_zh = parsed.meaning
      }

      if (parsed.radical) {
        form.metadata.radical = parsed.radical
      }

      if (parsed.strokes) {
        form.metadata.strokes = parsed.strokes
      }

      if (parsed.structure) {
        form.metadata.structure = parsed.structure
      }

      // 🆕 优先使用原始章节内容填充例句框
      if (parsed.exampleRaw) {
        form.example = parsed.exampleRaw
        // 同时保存解析后的数组格式（如果有）
        if (parsed.examples && parsed.examples.length > 0) {
          form.metadata.examples = parsed.examples
        }
      } else if (parsed.examples && parsed.examples.length > 0) {
        form.example = parsed.examples.join('\n')
        form.metadata.examples = parsed.examples
      }

      // 保存完整AI内容用于复习时展示
      form.metadata.ai_full_content = aiContent
      form.metadata.ai_generated = true
      form.metadata.ai_model = response.data.model || 'unknown'

      // 保存记忆法等额外信息
      if (parsed.memoryTips) {
        form.metadata.memory_tips = parsed.memoryTips
      }
      if (parsed.confusion) {
        form.metadata.confusion = parsed.confusion
      }
      if (parsed.exercises) {
        form.metadata.exercises = parsed.exercises
      }

      // 保存新增的9节结构字段
      if (parsed.keyPoints) {
        form.metadata.key_points = parsed.keyPoints
      }
      if (parsed.writingTips) {
        form.metadata.writing_tips = parsed.writingTips
      }
      if (parsed.memoryScript) {
        form.metadata.memory_script = parsed.memoryScript
      }
      if (parsed.summary) {
        form.metadata.summary = parsed.summary
      }

      // 提示用户成功
      dictResult.value = {
        source: `AI记忆卡 (${response.data.model})`,
        data: {
          pinyin: parsed.pinyin,
          meaning_zh: parsed.meaning,
          radical: parsed.radical,
          strokes: parsed.strokes,
          examples: parsed.examples
        }
      }

      // 🆕 自动生成 SVG 预览
      await generateSVGPreview()
    }
  } catch (err) {
    console.error('Failed to generate AI memory card:', err)

    // 处理错误信息
    if (err.response) {
      const errorData = err.response.data
      if (errorData.error) {
        aiError.value = `AI生成失败: ${errorData.error}`
      } else if (err.response.status === 400) {
        aiError.value = '请先在设置中配置AI功能'
      } else if (err.response.status === 500) {
        aiError.value = 'AI服务暂时不可用，请稍后再试'
      } else {
        aiError.value = 'AI生成失败，请检查网络或稍后再试'
      }
    } else {
      aiError.value = '网络连接失败，请检查网络设置'
    }
  } finally {
    isGeneratingAI.value = false
  }
}

// 生成 SVG 预览
async function generateSVGPreview() {
  if (!form.word || !form.card_type) {
    return
  }

  isGeneratingSVG.value = true

  try {
    const response = await axios.post('/api/cards/preview_svg/', {
      word: form.word,
      card_type: form.card_type,
      metadata: form.metadata
    })

    svgPreview.value = {
      front: response.data.svg_front,
      back: response.data.svg_back
    }
  } catch (err) {
    console.error('Failed to generate SVG preview:', err)
    // SVG 预览失败不影响用户继续操作,静默处理
  } finally {
    isGeneratingSVG.value = false
  }
}

// 解析AI返回的结构化内容（支持多种格式自适应）
function parseAIContent(content) {
  const result = {
    pinyin: [],
    meaning: '',
    meaningRaw: '',     // 🆕 新增：读音与核心意思章节原始文本
    exampleRaw: '',     // 🆕 新增：经典固定短语/句子章节原始文本
    radical: '',
    strokes: '',
    structure: '',
    examples: [],
    memoryTips: '',
    confusion: '',
    exercises: '',
    keyPoints: '',      // 新增：关键要点
    writingTips: '',    // 新增：书写与笔顺
    memoryScript: '',   // 新增：记忆方案设计
    summary: ''         // 新增：一句话总结
  }

  if (!content) {
    console.warn('AI返回内容为空')
    return result
  }

  const warnings = []

  try {
    // ===== 格式检测：判断是简化格式还是9节结构 =====
    const isSimpleFormat = content.includes('**汉字：') ||
                          content.includes('**读音与核心意思**') ||
                          content.includes('**高频词组**')

    // 新增：检测星号标题格式（带项目符号和分隔线）
    // 支持两种格式：
    // 1. **是否多音字：** (旧格式)
    // 2. ## ✅ 是否多音字：**是** (新格式)
    const isStarFormat = (content.includes('是否多音字') || content.includes('读音与核心意思')) &&
                        (content.includes('高频词组') || content.includes('常用词')) &&
                        (content.includes('- **hǎo**') || content.includes('- **'))

    const is9SectionFormat = /\*\*\s*1\s*[.。、]\s*关键要点\s*\*\*/.test(content) &&
                            /\*\*\s*2\s*[.。、]\s*核心卡片\s*\*\*/.test(content)

    console.log(`🔍 格式检测: ${isSimpleFormat ? '简化格式' : ''} ${isStarFormat ? '星号标题格式' : ''} ${is9SectionFormat ? '9节结构' : ''} ${!isSimpleFormat && !isStarFormat && !is9SectionFormat ? '通用格式' : ''}`)

    // ===== 分支0: 星号标题格式解析（优先级最高）=====
    if (isStarFormat) {
      console.log('⭐ 使用星号标题格式解析器')

      // 🆕 提取原始章节内容（用于直接填充到释义框和例句框）
      // 提取"读音与核心意思"章节的完整原始文本
      const readingSection = content.match(/(?:##?\s*[📢🔊]?\s*读音与核心意思|读音与核心意思)[^\n]*\n+([\s\S]*?)(?=\n##|\n---|\n\n##|$)/i)
      if (readingSection) {
        result.meaningRaw = readingSection[1].trim()
      }

      // 提取"经典固定短语/句子"章节的完整原始文本
      const sentenceSection = content.match(/(?:##?\s*[💡📝]?\s*经典固定短语[^#\n]*|经典.*?句子)[^\n]*\n+([\s\S]*?)(?=\n##|\n---|\n\n##|$)/i)
      if (sentenceSection) {
        result.exampleRaw = sentenceSection[1].trim()
      }

      // 提取多音字读音 "- **hǎo** 三声：美好、优秀；友爱、喜爱"
      const readingMatches = content.matchAll(/[-•]\s*\*\*([a-zāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜü]+)\*\*\s*[一二三四]声[：:]\s*([^-\n]+)/gi)
      const pinyinList = []
      const meaningList = []
      for (const match of readingMatches) {
        pinyinList.push(match[1].trim())
        meaningList.push(match[2].trim())
      }
      if (pinyinList.length > 0) {
        result.pinyin = pinyinList
        result.meaning = meaningList.join('；')
      }

      // 备用：提取简单读音行（无项目符号）
      if (result.pinyin.length === 0) {
        const simpleMatch = content.match(/([a-zāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜü]+)\s*[一二三四]声[：:]\s*([^-\n]+)/i)
        if (simpleMatch) {
          result.pinyin = [simpleMatch[1].trim()]
          result.meaning = simpleMatch[2].trim()
        }
      }

      // 提取高频词组 - 支持多种格式
      // 格式1: "1. 好人\n2. 爱好"
      // 格式2: "好人、好吃、爱好、好奇"
      // 格式3: "- **好人、好事、美好、你好**"
      const wordsMatch = content.match(/(?:高频词组|常用词)[^#\n]*[\s\S]*?(?=\n##|\n---|\n\n##|$)/i)
      if (wordsMatch) {
        const wordsSection = wordsMatch[0]

        // 尝试提取markdown列表中的粗体词组 "- **好人、好事、美好、你好**"
        const boldWordsMatches = wordsSection.matchAll(/[-•]\s*\*\*([^*]+)\*\*/g)
        const boldWords = []
        for (const match of boldWordsMatches) {
          const words = match[1].split(/[、，,]/).map(w => w.trim()).filter(w => w)
          boldWords.push(...words)
        }

        if (boldWords.length > 0) {
          result.examples = boldWords
        } else {
          // 备用：尝试按编号列表提取 "1. 好人\n2. 爱好"
          const numberedWords = wordsSection
            .split(/\n/)
            .map(line => line.trim())
            .filter(line => /^\d+\.\s*/.test(line))
            .map(line => line.replace(/^\d+\.\s*/, ''))
            .filter(w => w)

          if (numberedWords.length > 0) {
            result.examples = numberedWords
          } else {
            // 最后备用：按顿号/逗号分隔
            const commaWords = wordsSection
              .split(/[、，,]/)
              .map(w => w.trim())
              .filter(w => w && w.length >= 2 && !/^[#\-*]/.test(w))
            result.examples = commaWords.slice(0, 10) // 最多取10个
          }
        }
      }

      // 提取经典句子 - 支持多种格式
      // 格式1: **"这个好人..."** (双引号)
      // 格式2: 这个好人... (无引号)
      const sentenceMatch = content.match(/(?:经典固定短语|经典.*?句子)[^\n]*[\s\S]*?[""]([^""]+)[""]|(?:经典固定短语|经典.*?句子)[^\n]*\n\n([^\n#]+)/i)
      if (sentenceMatch) {
        const sentence = (sentenceMatch[1] || sentenceMatch[2] || '').trim()
        if (sentence && result.examples.length < 10) {
          result.examples.push(sentence)
        }
      }

      // 提取联想记忆 - 支持多种格式
      // 格式1: ## 🎨 一句话联想记忆
      // 格式2: **一句话联想记忆**
      const memoryMatch = content.match(/(?:##?\s*[🎨🧠💡]?\s*一句话联想记忆|一句话联想记忆)[^\n]*[\s\S]*?(?=\n##|\n---|\n\n##|$)/i)
      if (memoryMatch) {
        result.memoryTips = memoryMatch[0]
          .replace(/##?\s*[🎨🧠💡]?\s*一句话联想记忆[^\n]*\n+/i, '')
          .trim()
      }

      // 提取近形字辨析 - 支持多种格式
      // 格式1: 表格 | **好** | 女 | hǎo | 优秀 |
      // 格式2: 编号 1. **好**（女+子）— 女子组合
      // 格式3: 子弹 - **好**（女+子）...
      const confusionMatch = content.match(/(?:##?\s*[⚡🔍]?\s*近形字|近形字快速辨析)[^\n]*[\s\S]*?(?=\n##|\n---|\n\n##|$)/i)
      if (confusionMatch) {
        const confusionText = confusionMatch[0]

        // 尝试提取表格格式
        const tableRows = confusionText
          .split(/\n/)
          .filter(line => /^\|.*\|$/.test(line.trim()) && !line.includes('---'))
          .slice(1) // 跳过表头

        if (tableRows.length > 0) {
          const confusionList = tableRows.map(row => {
            const cells = row.split('|').map(c => c.trim()).filter(c => c)
            if (cells.length >= 2) {
              return `**${cells[0]}** ${cells.slice(1).join(' ')}`
            }
            return null
          }).filter(Boolean)
          result.confusion = confusionList.join('\n')
        } else {
          // 尝试按数字编号提取
          const numberedList = confusionText
            .split(/\n/)
            .map(line => line.trim())
            .filter(line => /^\d+\.\s*\*\*/.test(line))
            .map(line => line.replace(/^\d+\.\s*/, ''))

          if (numberedList.length > 0) {
            result.confusion = numberedList.join('\n')
          } else {
            // 最后尝试子弹列表
            const bulletList = confusionText
              .split(/\n/)
              .map(line => line.trim())
              .filter(line => /^[-•]\s*\*\*/.test(line))
              .map(line => line.replace(/^[-•]\s*/, ''))
              .filter(c => c)
            result.confusion = bulletList.join('\n')
          }
        }
      }

      // 提取记忆口诀作为总结
      const summaryMatch = content.match(/\*\*记忆口诀\*\*\s*([^\n*]+)/i)
      if (summaryMatch) {
        result.summary = summaryMatch[1].trim()
      }

      console.log('✅ 星号标题格式解析完成:', result)
      return result
    }

    // ===== 分支1: 简化格式解析 =====
    if (isSimpleFormat && !is9SectionFormat) {
      console.log('📋 使用简化格式解析器')

      // 提取读音 "nán □声：意思1：男性"
      let readingMatch = content.match(/(\w+)\s*□声[：:]\s*意思\d+[：:](.+?)(?:\s*\/|$)/i)
      if (readingMatch) {
        result.pinyin = [readingMatch[1].trim()]
        result.meaning = readingMatch[2].trim()
      }

      // 备用：提取纯读音行 "nán □声："
      if (result.pinyin.length === 0) {
        readingMatch = content.match(/^(\w+)\s*□声/m)
        if (readingMatch) {
          result.pinyin = [readingMatch[1].trim()]
        }
      }

      // 提取意思（从多个"意思X"行合并）
      if (!result.meaning) {
        const meaningLines = []
        const meaningMatches = content.matchAll(/意思\d+[：:](.+?)(?:\s*\/\s*意思\d+|$)/g)
        for (const match of meaningMatches) {
          meaningLines.push(match[1].trim())
        }
        if (meaningLines.length > 0) {
          result.meaning = meaningLines.join('、')
        }
      }

      // 提取高频词组
      const wordsMatch = content.match(/\*\*高频词组\*\*\s*([\s\S]*?)(?=\*\*|$)/i)
      if (wordsMatch) {
        const wordsList = wordsMatch[1]
          .split(/\n/)
          .map(line => line.trim())
          .filter(line => /^\d+\.\s*/.test(line))
          .map(line => line.replace(/^\d+\.\s*/, ''))
          .filter(w => w)
        result.examples = wordsList
      }

      // 提取联想记忆作为记忆技巧
      const memoryMatch = content.match(/\*\*一句话联想记忆\*\*\s*([\s\S]*?)(?=\*\*|$)/i)
      if (memoryMatch) {
        result.memoryTips = memoryMatch[1].trim()
      }

      // 提取近形字辨析
      const confusionMatch = content.match(/\*\*近形字快速辨析\*\*\s*([\s\S]*?)(?=通过上述|$)/i)
      if (confusionMatch) {
        const confusionList = confusionMatch[1]
          .split(/\n/)
          .map(line => line.trim())
          .filter(line => /^\d+\.\s*/.test(line))
          .map(line => line.replace(/^\d+\.\s*/, ''))
          .filter(c => c)
        result.confusion = confusionList.join('\n')
      }

      // 提取经典句子作为例句补充
      const sentenceMatch = content.match(/\*\*经典固定短语\/句子\*\*\s*[""](.+?)[""]/)
      if (sentenceMatch && result.examples.length < 5) {
        result.examples.push(sentenceMatch[1].trim())
      }

      console.log('✅ 简化格式解析完成:', result)
      return result
    }

    // ===== 分支2: 9节结构解析（原有逻辑） =====

    // 1. 提取拼音（三层备用方案）
    let pinyinText = null
    // 方案1: 标准格式 "拼音与声调: xxx"
    let match = content.match(/拼音[与和]?声调[：:]\s*([^\n]+)/i)
    if (match) pinyinText = match[1]
    // 方案2: 简化格式 "拼音: xxx"
    if (!pinyinText) {
      match = content.match(/拼音[^：:\n]{0,5}[：:]\s*([^\n]+)/i)
      if (match) pinyinText = match[1]
    }
    // 方案3: 按行查找包含"拼音"的行
    if (!pinyinText) {
      const lines = content.split('\n')
      const pinyinLine = lines.find(l => /拼音/.test(l) && /[：:]/.test(l))
      if (pinyinLine) {
        pinyinText = pinyinLine.split(/[：:]/)[1]?.trim()
      }
    }
    // 解析拼音为数组
    if (pinyinText) {
      result.pinyin = pinyinText
        .replace(/[（）\(\)\[\]【】《》""'']/g, '')  // 移除各种括号引号
        .split(/[,，、；; ]+/)  // 支持多种分隔符
        .map(p => p.trim())
        .filter(p => p && /^[a-zāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜü]+\d?$/i.test(p))  // 只保留有效拼音
    }

    // 2. 提取释义（三层备用方案）
    let meaningText = null
    // 方案1: 标准格式 "高频义项: xxx"
    match = content.match(/高频义项[^：:\n]{0,10}[：:]\s*([^\n]+)/i)
    if (match) meaningText = match[1]
    // 方案2: 备用格式 "义项" 或 "释义"
    if (!meaningText) {
      match = content.match(/(?:义项|释义|含义)[^：:\n]{0,10}[：:]\s*([^\n]+)/i)
      if (match) meaningText = match[1]
    }
    // 方案3: 从"核心卡片"章节中按行提取
    if (!meaningText) {
      const coreMatch = content.match(/\*\*\s*2\s*[.。、]\s*核心卡片\s*\*\*[\s\S]{0,500}/i)
      if (coreMatch) {
        const lines = coreMatch[0].split('\n')
        const meaningLine = lines.find(l => /(义项|释义|含义)[：:]/.test(l))
        if (meaningLine) {
          meaningText = meaningLine.split(/[：:]/)[1]?.trim()
        }
      }
    }
    if (meaningText) {
      result.meaning = meaningText.trim()
    }

    // 3. 提取例句/常见词（三层备用方案）
    let examplesText = null
    // 方案1: 标准格式 "常见词: xxx"
    match = content.match(/常见词[^：:\n]{0,10}[：:]\s*([^\n]+)/i)
    if (match) examplesText = match[1]
    // 方案2: 备用格式 "高频搭配" 或 "造句"
    if (!examplesText) {
      match = content.match(/(?:高频搭配|例词|词组)[^：:\n]{0,10}[：:]\s*([^\n]+)/i)
      if (match) examplesText = match[1]
    }
    // 方案3: 提取"造句"内容
    if (!examplesText) {
      match = content.match(/造句[^：:\n]{0,10}[：:]\s*([^\n]+)/i)
      if (match) examplesText = match[1]
    }
    if (examplesText) {
      result.examples = examplesText
        .split(/[、，,;；]/)
        .map(w => w.trim())
        .filter(w => w && w.length >= 2 && w.length <= 20)  // 过滤无效内容
    }

    // 4. 提取部首/笔画（容错）
    match = content.match(/部首[/\s]*结构[/\s]*笔画[：:]\s*([^\n]+)/i)
    if (match) {
      const parts = match[1].split(/[；;，,]/).map(p => p.trim())
      if (parts[0]) result.radical = parts[0]
      if (parts[1]) result.structure = parts[1]
      if (parts[2]) result.strokes = parts[2].replace(/[^0-9]/g, '')
    }

    // ===== 以下为扩展字段（原有逻辑保留） =====

    // 1. 解析关键要点
    const keyPointsMatch = content.match(/\*\*\s*1\s*[.。、]\s*关键要点\s*\*\*[\s\S]*?([\s\S]*?)(?=\n\s*\*\*\s*2\s*[.。、]|$)/i)
    if (keyPointsMatch) {
      result.keyPoints = keyPointsMatch[1].trim()
        .split('\n')
        .map(line => line.trim())
        .filter(line => line && /^[-—·•]\s*/.test(line))
        .map(line => line.replace(/^[-—·•]\s*/, ''))
        .join('\n')
    }

    // 2. 解析构形拆解、读音记忆(合并到记忆法) - 增强版
    const structureMatch = content.match(/\*\*\s*3\s*[.。、]\s*构形拆解[与和]?联想\s*\*\*[\s\S]*?([\s\S]*?)(?=\n\s*\*\*\s*4\s*[.。、]|$)/i)
    const pronunciationMatch = content.match(/\*\*\s*4\s*[.。、]\s*读音记忆\s*\*\*[\s\S]*?([\s\S]*?)(?=\n\s*\*\*\s*5\s*[.。、]|$)/i)

    let memoryParts = []
    if (structureMatch) {
      const structureText = structureMatch[1].trim()
        .split('\n')
        .map(l => l.trim())
        .filter(l => l && /^[-—·•]\s*/.test(l))  // 支持多种列表符号
        .map(l => l.replace(/^[-—·•]\s*/, ''))
        .join('\n')
      if (structureText) memoryParts.push('**构形记忆**:\n' + structureText)
    }
    if (pronunciationMatch) {
      const pronText = pronunciationMatch[1].trim()
        .split('\n')
        .map(l => l.trim())
        .filter(l => l && /^[-—·•]\s*/.test(l))  // 支持多种列表符号
        .map(l => l.replace(/^[-—·•]\s*/, ''))
        .join('\n')
      if (pronText) memoryParts.push('**读音记忆**:\n' + pronText)
    }
    result.memoryTips = memoryParts.join('\n\n')

    // 5. 解析书写与笔顺 - 增强版
    const writingMatch = content.match(/\*\*\s*5\s*[.。、]\s*书写[与和]?笔顺\s*\*\*[\s\S]*?([\s\S]*?)(?=\n\s*\*\*\s*6\s*[.。、]|$)/i)
    if (writingMatch) {
      result.writingTips = writingMatch[1].trim()
        .split('\n')
        .map(l => l.trim())
        .filter(l => l && /^[-—·•]\s*/.test(l))  // 支持多种列表符号
        .map(l => l.replace(/^[-—·•]\s*/, ''))
        .join('\n')
    }

    // 6. 解析易混辨析 - 增强版
    const confusionMatch = content.match(/\*\*\s*6\s*[.。、]\s*易混辨析\s*\*\*[\s\S]*?([\s\S]*?)(?=\n\s*\*\*\s*7\s*[.。、]|$)/i)
    if (confusionMatch) {
      result.confusion = confusionMatch[1].trim()
        .split('\n')
        .map(l => l.trim())
        .filter(l => l && /^[-—·•]\s*/.test(l))  // 支持多种列表符号
        .map(l => l.replace(/^[-—·•]\s*与?\s*/, ''))  // 移除"与"字
        .join('\n')
    }

    // 7. 解析语境与搭配(补充到examples) - 增强版
    const contextMatch = content.match(/\*\*\s*7\s*[.。、]\s*语境[与和]?搭配\s*\*\*[\s\S]*?([\s\S]*?)(?=\n\s*\*\*\s*8\s*[.。、]|$)/i)
    if (contextMatch) {
      const contextText = contextMatch[1]
      const examplesMatch2 = contextText.match(/高频搭配[^：:]*[：:]\s*(.+?)(?:\n|$)/i)
      const sentenceMatch = contextText.match(/造句[^：:]*[：:]\s*(.+?)(?:\n|$)/i)

      if (examplesMatch2 && !result.examples.length) {
        result.examples = examplesMatch2[1]
          .split(/[、，,]/)
          .map(w => w.trim())
          .filter(w => w)
      }
      if (sentenceMatch) {
        result.examples.push(sentenceMatch[1].trim())
      }
    }

    // 8. 解析记忆方案设计 - 增强版
    const memoryScriptMatch = content.match(/\*\*\s*8\s*[.。、]\s*记忆方案设计\s*\*\*[\s\S]*?([\s\S]*?)(?=\n\s*\*\*\s*9\s*[.。、]|$)/i)
    if (memoryScriptMatch) {
      result.memoryScript = memoryScriptMatch[1].trim()
        .split('\n')
        .map(l => l.trim())
        .filter(l => l && /^[-—·•]\s*/.test(l))  // 支持多种列表符号
        .map(l => l.replace(/^[-—·•]\s*/, ''))
        .join('\n')
    }

    // 9. 解析一句话总结 - 增强版
    const summaryMatch = content.match(/\*\*\s*9\s*[.。、]\s*一句话总结\s*\*\*[\s\S]*?[-—·•]\s*(.+?)(?:\n|$)/i)
    if (summaryMatch) {
      result.summary = summaryMatch[1].trim()
    }

    // 检查必需字段 (增强版 - 包含9节结构的关键字段)
    const requiredFields = {
      pinyin: '拼音',
      meaning: '释义',
      keyPoints: '关键要点',
      writingTips: '书写与笔顺',
      memoryScript: '记忆方案',
      summary: '一句话总结'
    }

    for (const [field, label] of Object.entries(requiredFields)) {
      if (!result[field] || (Array.isArray(result[field]) && result[field].length === 0)) {
        warnings.push(`${label}解析失败或为空`)
      }
    }

    // 输出警告 (增强版 - 更详细的调试信息)
    if (warnings.length > 0) {
      console.warn('❌ AI内容解析警告:', warnings)
      console.log('📄 原始内容(前500字):', content.substring(0, 500) + '...')
      console.log('📊 解析结果:', result)
    } else {
      console.log('✅ AI内容解析成功,所有必需字段已填充')
    }

  } catch (error) {
    console.error('AI内容解析错误:', error)
    console.log('原始内容:', content)
  }

  return result
}

</script>

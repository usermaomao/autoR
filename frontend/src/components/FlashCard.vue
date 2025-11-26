<template>
  <div class="flashcard" :class="{ flipped: isFlipped }">
    <div class="flashcard-inner">
      <!-- 正面 -->
      <div class="flashcard-front bg-white rounded-2xl shadow-2xl p-8 min-h-[400px] flex flex-col justify-center items-center">
        <div class="text-center w-full max-w-2xl">
          <!-- 英语单词：显示单词本身 -->
          <template v-if="card.card_type === 'en'">
            <div class="text-6xl font-bold text-gray-900 mb-4">
              {{ card.word }}
            </div>
            <div class="text-xl text-gray-600 mb-8">
              英语单词
            </div>
          </template>

          <!-- 汉字：只显示拼音和释义，不显示汉字本身 -->
          <template v-else>
            <div class="mb-6">
              <div class="text-sm text-gray-500 mb-2">拼音</div>
              <div class="text-4xl font-bold text-indigo-600 mb-6">
                {{ formatPinyin(card.metadata?.pinyin) }}
              </div>
            </div>

            <div class="mb-6">
              <div class="text-sm text-gray-500 mb-2">释义</div>
              <div class="text-2xl text-gray-800 px-6 py-4 bg-gray-50 rounded-lg">
                {{ card.metadata?.meaning_zh || '暂无释义' }}
              </div>
            </div>

            <div class="mt-4 p-4 bg-yellow-50 border-l-4 border-yellow-400 rounded text-left">
              <div class="text-sm font-semibold text-yellow-800 mb-2">💡 复习提示</div>
              <ul class="text-sm text-yellow-700 space-y-1">
                <li>• 请尝试说出包含这个字的<strong>2-3个词语</strong></li>
                <li>• 请尝试用这个字<strong>造一个句子</strong></li>
              </ul>
            </div>
          </template>

          <button
            v-if="!isFlipped"
            @click="$emit('flip')"
            class="btn btn-primary px-8 py-3 mt-6"
          >
            显示答案 (S)
          </button>
        </div>
      </div>

      <!-- 背面 -->
      <div class="flashcard-back bg-white rounded-2xl shadow-2xl p-8 min-h-[400px]">
        <div class="h-full flex flex-col">
          <!-- 答案区域 -->
          <div class="flex-1">
            <div class="text-center mb-6">
              <div class="text-4xl font-bold text-gray-900 mb-2">
                {{ card.word }}
              </div>

              <!-- 英语单词 -->
              <template v-if="card.card_type === 'en'">
                <div class="text-gray-600 mb-2">
                  {{ card.metadata?.ipa || '' }}
                </div>
                <div class="text-lg text-gray-800 mb-4">
                  {{ card.metadata?.meaning_zh || card.metadata?.meaning_en || '' }}
                </div>
                <div v-if="card.metadata?.examples?.length" class="text-sm text-gray-600 space-y-2">
                  <div v-for="(example, idx) in card.metadata.examples" :key="idx" class="italic">
                    {{ example }}
                  </div>
                </div>
              </template>

              <!-- 汉字 -->
              <template v-else>
                <div class="text-gray-600 mb-2">
                  {{ formatPinyin(card.metadata?.pinyin) }}
                </div>
                <div class="text-lg text-gray-800 mb-4 leading-relaxed">
                  {{ card.metadata?.meaning_zh || '' }}
                </div>

                <!-- 词语示例（从AI生成的内容或例句中提取） -->
                <div v-if="card.metadata?.examples?.length" class="mt-4 mb-4">
                  <div class="text-sm font-semibold text-gray-700 mb-2">📚 词语和例句</div>
                  <div class="space-y-2 text-sm text-gray-700 text-left bg-blue-50 p-4 rounded-lg">
                    <div v-for="(example, idx) in card.metadata.examples" :key="idx" class="leading-relaxed">
                      {{ example }}
                    </div>
                  </div>
                </div>

                <div class="text-sm text-gray-500 mt-4">
                  部首: {{ card.metadata?.radical || '' }} |
                  笔画: {{ card.metadata?.strokes || '' }}
                </div>
              </template>

              <!-- 关键要点 -->
              <div v-if="card.metadata?.key_points" class="mt-4 p-4 bg-blue-50 border-l-4 border-blue-400 rounded-lg">
                <div class="text-sm font-semibold text-blue-800 mb-2 flex items-center gap-2">
                  <span>🎯</span>
                  <span>关键要点</span>
                </div>
                <div class="text-sm text-blue-700 whitespace-pre-wrap leading-relaxed">
                  {{ card.metadata.key_points }}
                </div>
              </div>

              <!-- AI生成的记忆法 -->
              <div v-if="card.metadata?.memory_tips" class="mt-4 p-4 bg-purple-50 border-l-4 border-purple-400 rounded-lg">
                <div class="text-sm font-semibold text-purple-800 mb-2 flex items-center gap-2">
                  <span>💡</span>
                  <span>记忆技巧</span>
                </div>
                <div class="text-sm text-purple-700 whitespace-pre-wrap leading-relaxed">
                  {{ card.metadata.memory_tips }}
                </div>
              </div>

              <!-- 易混辨析 -->
              <div v-if="card.metadata?.confusion" class="mt-4 p-4 bg-orange-50 border-l-4 border-orange-400 rounded-lg">
                <div class="text-sm font-semibold text-orange-800 mb-2 flex items-center gap-2">
                  <span>⚠️</span>
                  <span>易混辨析</span>
                </div>
                <div class="text-sm text-orange-700 whitespace-pre-wrap leading-relaxed">
                  {{ card.metadata.confusion }}
                </div>
              </div>

              <!-- 微练习 -->
              <div v-if="card.metadata?.exercises" class="mt-4 p-4 bg-green-50 border-l-4 border-green-400 rounded-lg">
                <div class="text-sm font-semibold text-green-800 mb-2 flex items-center gap-2">
                  <span>✏️</span>
                  <span>小练习</span>
                </div>
                <div class="text-sm text-green-700 whitespace-pre-wrap leading-relaxed">
                  {{ card.metadata.exercises }}
                </div>
              </div>

              <!-- 书写与笔顺 -->
              <div v-if="card.metadata?.writing_tips" class="mt-4 p-4 bg-indigo-50 border-l-4 border-indigo-400 rounded-lg">
                <div class="text-sm font-semibold text-indigo-800 mb-2 flex items-center gap-2">
                  <span>✍️</span>
                  <span>书写与笔顺</span>
                </div>
                <div class="text-sm text-indigo-700 whitespace-pre-wrap leading-relaxed">
                  {{ card.metadata.writing_tips }}
                </div>
              </div>

              <!-- 记忆方案设计 -->
              <div v-if="card.metadata?.memory_script" class="mt-4 p-4 bg-pink-50 border-l-4 border-pink-400 rounded-lg">
                <div class="text-sm font-semibold text-pink-800 mb-2 flex items-center gap-2">
                  <span>🎬</span>
                  <span>记忆方案</span>
                </div>
                <div class="text-sm text-pink-700 whitespace-pre-wrap leading-relaxed">
                  {{ card.metadata.memory_script }}
                </div>
              </div>

              <!-- 一句话总结 -->
              <div v-if="card.metadata?.summary" class="mt-4 p-4 bg-amber-50 border-l-4 border-amber-400 rounded-lg">
                <div class="text-sm font-semibold text-amber-800 mb-2 flex items-center gap-2">
                  <span>📝</span>
                  <span>一句话总结</span>
                </div>
                <div class="text-sm text-amber-700 whitespace-pre-wrap leading-relaxed">
                  {{ card.metadata.summary }}
                </div>
              </div>

              <!-- 用户备注 -->
              <div v-if="card.notes" class="mt-4 p-4 bg-yellow-50 rounded-lg text-sm text-gray-700">
                {{ card.notes }}
              </div>
            </div>
          </div>

          <!-- AI总结功能 -->
          <div class="mb-4 border-t border-gray-200 pt-4">
            <button
              @click="toggleAISummary"
              :disabled="isLoadingAI"
              class="w-full flex items-center justify-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500 to-indigo-600 text-white rounded-lg hover:from-purple-600 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              <span class="text-lg">🤖</span>
              <span>{{ isLoadingAI ? 'AI思考中...' : (showAISummary && aiSummary ? '收起AI总结' : 'AI学习助手') }}</span>
            </button>

            <!-- AI总结内容展示 -->
            <div
              v-if="showAISummary"
              class="mt-3 p-4 bg-gradient-to-br from-purple-50 to-indigo-50 rounded-lg border border-purple-200"
            >
              <!-- 加载状态 -->
              <div v-if="isLoadingAI" class="text-center py-4">
                <div class="inline-block animate-spin rounded-full h-8 w-8 border-3 border-purple-500 border-t-transparent"></div>
                <p class="text-sm text-purple-700 mt-2">AI正在为你分析这个词汇...</p>
              </div>

              <!-- 错误状态 -->
              <div v-else-if="aiError" class="text-red-700 text-sm">
                <p class="font-semibold mb-1">❌ {{ aiError }}</p>
                <p class="text-xs text-red-600">
                  提示: 请前往
                  <router-link to="/ai-settings" class="underline hover:text-red-800">AI设置</router-link>
                  配置AI助手
                </p>
              </div>

              <!-- 总结内容 -->
              <div v-else-if="aiSummary" class="prose prose-sm max-w-none">
                <div class="text-gray-800 whitespace-pre-wrap leading-relaxed text-sm">
                  {{ aiSummary }}
                </div>
                <div class="mt-3 pt-3 border-t border-purple-200 text-xs text-purple-600">
                  💡 由AI助手生成，仅供参考
                </div>
              </div>
            </div>
          </div>

          <!-- 评分按钮 -->
          <div class="grid grid-cols-4 gap-2">
            <button
              @click="$emit('rate', 0)"
              class="btn btn-again py-3 text-sm"
            >
              再来 (1)
            </button>
            <button
              @click="$emit('rate', 2)"
              class="btn btn-hard py-3 text-sm"
            >
              困难 (2)
            </button>
            <button
              @click="$emit('rate', 4)"
              class="btn btn-good py-3 text-sm"
            >
              良好 (3)
            </button>
            <button
              @click="$emit('rate', 5)"
              class="btn btn-easy py-3 text-sm"
            >
              简单 (4)
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import axios from 'axios'

// 定义props并保存引用以便在函数中使用
const props = defineProps({
  card: {
    type: Object,
    required: true
  },
  isFlipped: {
    type: Boolean,
    default: false
  }
})

defineEmits(['flip', 'rate'])

// AI总结相关状态
const showAISummary = ref(false)
const isLoadingAI = ref(false)
const aiSummary = ref('')
const aiError = ref('')

// 切换AI总结显示
async function toggleAISummary() {
  showAISummary.value = !showAISummary.value

  // 如果展开且还没有总结内容，则调用API
  if (showAISummary.value && !aiSummary.value && !aiError.value) {
    await fetchAISummary()
  }
}

// 获取AI总结
async function fetchAISummary() {
  isLoadingAI.value = true
  aiError.value = ''

  try {
    const response = await axios.post('/api/ai/summarize/', {
      word: props.card.word,
      card_type: props.card.card_type,
      context: props.card.meaning || ''
    })

    aiSummary.value = response.data.summary
  } catch (err) {
    console.error('AI summarize failed:', err)
    aiError.value = err.response?.data?.error || 'AI总结失败，请检查配置'
  } finally {
    isLoadingAI.value = false
  }
}

// 监听卡片变化，重置AI状态
watch(() => props.card, () => {
  showAISummary.value = false
  aiSummary.value = ''
  aiError.value = ''
})

// 格式化拼音显示（处理数组或字符串）
function formatPinyin(pinyin) {
  if (!pinyin) return '暂无拼音'
  if (Array.isArray(pinyin)) {
    return pinyin.join(', ')
  }
  return pinyin
}
</script>

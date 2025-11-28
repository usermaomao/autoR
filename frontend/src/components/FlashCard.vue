<template>
  <div class="flashcard" :class="{ flipped: isFlipped }">
    <div class="flashcard-inner">
      <!-- 正面 -->
      <div class="flashcard-front bg-white rounded-2xl shadow-2xl p-8 min-h-[500px] flex flex-col">
        <!-- 有 SVG 时优先显示 SVG -->
        <div v-if="hasSVG" class="flex-1 flex flex-col">
          <div class="flex-1 flex items-center justify-center w-full">
            <SVGCard :svgContent="card.metadata.svg_front" />
          </div>

          <!-- SVG 模式下的评分按钮（在正面显示） -->
          <div v-if="!isFlipped" class="mt-6">
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
            <button
              @click="$emit('flip')"
              class="w-full mt-3 btn btn-secondary py-2 text-sm"
            >
              查看详细信息 (S)
            </button>
          </div>
        </div>

        <!-- 无 SVG 时才显示文字模式 -->
        <div v-else class="flex-1 flex flex-col justify-center items-center text-center w-full max-w-2xl mx-auto">
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

          <!-- 文字模式下的按钮 -->
          <div v-if="!isFlipped" class="mt-6 w-full">
            <button
              @click="$emit('flip')"
              class="btn btn-primary px-8 py-3 w-full"
            >
              显示答案 (S)
            </button>
          </div>
        </div>
      </div>

      <!-- 背面 -->
      <div class="flashcard-back bg-white rounded-2xl shadow-2xl p-8 min-h-[500px] flex flex-col">
        <!-- 有 SVG 时优先显示 SVG -->
        <div v-if="hasSVG" class="flex-1 flex flex-col">
          <div class="flex-1 flex items-center justify-center w-full overflow-auto">
            <SVGCard :svgContent="card.metadata.svg_back" />
          </div>
        </div>

        <!-- 无 SVG 时才显示文字模式 -->
        <div v-else class="flex-1 overflow-auto">
          <!-- 答案区域 -->
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

              <!-- 词语示例 -->
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

            <!-- AI增强字段 -->
            <div v-if="card.metadata?.key_points" class="mt-4 p-4 bg-blue-50 border-l-4 border-blue-400 rounded-lg text-left">
              <div class="text-sm font-semibold text-blue-800 mb-2 flex items-center gap-2">
                <span>🎯</span>
                <span>关键要点</span>
              </div>
              <div class="text-sm text-blue-700 whitespace-pre-wrap leading-relaxed">
                {{ card.metadata.key_points }}
              </div>
            </div>

            <div v-if="card.metadata?.memory_tips" class="mt-4 p-4 bg-purple-50 border-l-4 border-purple-400 rounded-lg text-left">
              <div class="text-sm font-semibold text-purple-800 mb-2 flex items-center gap-2">
                <span>💡</span>
                <span>记忆技巧</span>
              </div>
              <div class="text-sm text-purple-700 whitespace-pre-wrap leading-relaxed">
                {{ card.metadata.memory_tips }}
              </div>
            </div>

            <!-- 用户备注 -->
            <div v-if="card.notes" class="mt-4 p-4 bg-yellow-50 rounded-lg text-sm text-gray-700 text-left">
              <div class="font-semibold mb-1">📝 备注</div>
              {{ card.notes }}
            </div>
          </div>
        </div>

        <!-- 评分按钮（背面，仅无 SVG 卡片使用；有 SVG 时在正面评分） -->
        <div v-if="!hasSVG" class="grid grid-cols-4 gap-2 mt-4">
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
</template>

<script setup>
import { computed } from 'vue'
import SVGCard from './SVGCard.vue'

const props = defineProps({
  card: {
    type: Object,
    required: true
  },
  isFlipped: {
    type: Boolean,
    default: false
  },
  showRatingOnFront: {
    type: Boolean,
    default: false
  },
  allowViewSwitch: {
    type: Boolean,
    default: true
  }
})

defineEmits(['flip', 'rate'])

// 计算是否有 SVG 数据
const hasSVG = computed(() => {
  return !!(props.card.metadata?.svg_front && props.card.metadata?.svg_back)
})

// 格式化拼音显示
function formatPinyin(pinyin) {
  if (!pinyin) return '暂无拼音'
  if (Array.isArray(pinyin)) {
    return pinyin.join(', ')
  }
  return pinyin
}
</script>

<style scoped>
.flashcard {
  perspective: 1000px;
}

.flashcard-inner {
  position: relative;
  width: 100%;
  transition: transform 0.6s;
  transform-style: preserve-3d;
}

.flashcard.flipped .flashcard-inner {
  transform: rotateY(180deg);
}

.flashcard-front,
.flashcard-back {
  position: absolute;
  width: 100%;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
}

.flashcard-back {
  transform: rotateY(180deg);
}

.flashcard:not(.flipped) .flashcard-front {
  position: relative;
}

.flashcard:not(.flipped) .flashcard-back {
  position: absolute;
}

.flashcard.flipped .flashcard-front {
  position: absolute;
}

.flashcard.flipped .flashcard-back {
  position: relative;
}

/* 评分按钮样式 */
.btn-again {
  @apply bg-red-500 hover:bg-red-600 text-white font-medium rounded-lg transition-colors;
}

.btn-hard {
  @apply bg-orange-500 hover:bg-orange-600 text-white font-medium rounded-lg transition-colors;
}

.btn-good {
  @apply bg-green-500 hover:bg-green-600 text-white font-medium rounded-lg transition-colors;
}

.btn-easy {
  @apply bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-lg transition-colors;
}

.btn-secondary {
  @apply bg-gray-200 hover:bg-gray-300 text-gray-800 font-medium rounded-lg transition-colors;
}
</style>

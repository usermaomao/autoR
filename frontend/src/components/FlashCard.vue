<template>
  <div class="flashcard" :class="{ flipped: isFlipped }">
    <div class="flashcard-inner">
      <!-- 正面 -->
      <div class="flashcard-front bg-white rounded-2xl shadow-2xl p-8 min-h-[400px] flex flex-col justify-center items-center">
        <div class="text-center">
          <div class="text-6xl font-bold text-gray-900 mb-4">
            {{ card.word }}
          </div>

          <div class="text-xl text-gray-600 mb-8">
            {{ card.card_type === 'en' ? '英语单词' : '汉字' }}
          </div>

          <button
            v-if="!isFlipped"
            @click="$emit('flip')"
            class="btn btn-primary px-8 py-3"
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
                  {{ (card.metadata?.pinyin || []).join(', ') }}
                </div>
                <div class="text-lg text-gray-800 mb-4">
                  {{ card.metadata?.meaning_zh || '' }}
                </div>
                <div class="text-sm text-gray-500">
                  部首: {{ card.metadata?.radical || '' }} |
                  笔画: {{ card.metadata?.strokes || '' }}
                </div>
              </template>

              <!-- 用户备注 -->
              <div v-if="card.notes" class="mt-4 p-4 bg-yellow-50 rounded-lg text-sm text-gray-700">
                {{ card.notes }}
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
defineProps({
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
</script>

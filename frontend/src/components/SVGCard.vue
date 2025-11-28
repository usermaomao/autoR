<template>
  <div class="svg-card-wrapper">
    <div v-if="svgContent" class="svg-container" :style="containerStyle">
      <!-- 使用 v-html 渲染 SVG,确保 SVG 已经过服务器端清洗 -->
      <div v-html="svgContent" class="svg-content"></div>
    </div>
    <div v-else class="svg-placeholder">
      <p class="text-gray-500">暂无 SVG 卡片</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  svgContent: {
    type: String,
    default: ''
  },
  width: {
    type: Number,
    default: 800
  },
  height: {
    type: Number,
    default: 500
  },
  responsive: {
    type: Boolean,
    default: true
  }
})

const containerStyle = computed(() => {
  if (props.responsive) {
    // 响应式模式:使用 aspect-ratio 保持宽高比
    return {
      width: '100%',
      maxWidth: `${props.width}px`,
      aspectRatio: `${props.width} / ${props.height}`
    }
  } else {
    // 固定尺寸模式
    return {
      width: `${props.width}px`,
      height: `${props.height}px`
    }
  }
})
</script>

<style scoped>
.svg-card-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
}

.svg-container {
  position: relative;
  overflow: hidden;
  border-radius: 8px;
  background: #f0f4f8;
}

.svg-content {
  width: 100%;
  height: 100%;
}

.svg-content :deep(svg) {
  display: block;
  width: 100%;
  height: 100%;
}

.svg-placeholder {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  width: 100%;
  background-color: #f9fafb;
  border: 2px dashed #d1d5db;
  border-radius: 8px;
}
</style>

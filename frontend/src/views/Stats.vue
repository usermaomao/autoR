<template>
  <div class="min-h-screen bg-gray-50">
    <nav class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 py-4">
        <router-link to="/" class="text-gray-600 hover:text-gray-900">← 返回</router-link>
      </div>
    </nav>

    <div class="max-w-7xl mx-auto px-4 py-8">
      <h1 class="text-3xl font-bold mb-8">学习统计</h1>

      <!-- 今日概览 -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-lg shadow p-6">
          <div class="text-sm text-gray-600 mb-1">今日新增</div>
          <div class="text-3xl font-bold text-blue-600">{{ stats.today.new_cards }}</div>
          <div class="text-xs text-gray-500 mt-1">张卡片</div>
        </div>

        <div class="bg-white rounded-lg shadow p-6">
          <div class="text-sm text-gray-600 mb-1">今日复习</div>
          <div class="text-3xl font-bold text-green-600">{{ stats.today.reviewed_cards }}</div>
          <div class="text-xs text-gray-500 mt-1">张卡片</div>
        </div>

        <div class="bg-white rounded-lg shadow p-6">
          <div class="text-sm text-gray-600 mb-1">今日正确率</div>
          <div class="text-3xl font-bold text-purple-600">{{ stats.today.accuracy }}%</div>
          <div class="text-xs text-gray-500 mt-1">平均评分 {{ stats.today.avg_rating.toFixed(1) }}</div>
        </div>

        <div class="bg-white rounded-lg shadow p-6">
          <div class="text-sm text-gray-600 mb-1">连续学习</div>
          <div class="text-3xl font-bold text-orange-600">{{ stats.streak_days }}</div>
          <div class="text-xs text-gray-500 mt-1">天</div>
        </div>
      </div>

      <!-- 总体统计 -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div class="bg-white rounded-lg shadow p-6">
          <div class="text-sm font-medium text-gray-700 mb-4">卡片总览</div>
          <div class="space-y-3">
            <div class="flex justify-between">
              <span class="text-gray-600">总卡片数</span>
              <span class="font-semibold">{{ stats.total.total_cards }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">新卡片</span>
              <span class="font-semibold text-blue-600">{{ stats.total.new_cards }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">学习中</span>
              <span class="font-semibold text-green-600">{{ stats.total.learning_cards }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">熟悉</span>
              <span class="font-semibold text-purple-600">{{ stats.total.mature_cards }}</span>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-lg shadow p-6">
          <div class="text-sm font-medium text-gray-700 mb-4">复习记录</div>
          <div class="space-y-3">
            <div class="flex justify-between">
              <span class="text-gray-600">总复习次数</span>
              <span class="font-semibold">{{ stats.total.total_reviews }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">正确次数</span>
              <span class="font-semibold text-green-600">{{ stats.total.correct_reviews }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">总体正确率</span>
              <span class="font-semibold">{{ stats.total.overall_accuracy }}%</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">平均用时</span>
              <span class="font-semibold">{{ stats.total.avg_time }}秒</span>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-lg shadow p-6">
          <div class="text-sm font-medium text-gray-700 mb-4">学习预测</div>
          <div class="space-y-3">
            <div class="flex justify-between">
              <span class="text-gray-600">今日待复习</span>
              <span class="font-semibold text-orange-600">{{ stats.forecast.due_today }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">明日预计</span>
              <span class="font-semibold">{{ stats.forecast.due_tomorrow }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">7日预计</span>
              <span class="font-semibold">{{ stats.forecast.due_next_7days }}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600">平均每日</span>
              <span class="font-semibold">{{ stats.forecast.avg_daily }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 图表区域 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <!-- 近30天复习趋势 -->
        <div class="bg-white rounded-lg shadow p-6">
          <h2 class="text-lg font-semibold mb-4">近30天复习趋势</h2>
          <canvas ref="reviewTrendChart"></canvas>
        </div>

        <!-- 未来7天预测 -->
        <div class="bg-white rounded-lg shadow p-6">
          <h2 class="text-lg font-semibold mb-4">未来7天复习预测</h2>
          <canvas ref="forecastChart"></canvas>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- 卡片状态分布 -->
        <div class="bg-white rounded-lg shadow p-6">
          <h2 class="text-lg font-semibold mb-4">卡片状态分布</h2>
          <canvas ref="cardStatusChart"></canvas>
        </div>

        <!-- 评分分布 -->
        <div class="bg-white rounded-lg shadow p-6">
          <h2 class="text-lg font-semibold mb-4">复习评分分布</h2>
          <canvas ref="ratingDistChart"></canvas>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import axios from 'axios'
import { Chart, registerables } from 'chart.js'

// 注册 Chart.js 组件
Chart.register(...registerables)

const reviewTrendChart = ref(null)
const forecastChart = ref(null)
const cardStatusChart = ref(null)
const ratingDistChart = ref(null)

const stats = ref({
  today: {
    new_cards: 0,
    reviewed_cards: 0,
    accuracy: 0,
    avg_rating: 0
  },
  total: {
    total_cards: 0,
    new_cards: 0,
    learning_cards: 0,
    mature_cards: 0,
    total_reviews: 0,
    correct_reviews: 0,
    overall_accuracy: 0,
    avg_time: 0
  },
  forecast: {
    due_today: 0,
    due_tomorrow: 0,
    due_next_7days: 0,
    avg_daily: 0
  },
  streak_days: 0,
  review_trend: [],  // 近30天数据
  forecast_data: [], // 未来7天数据
  card_status: {},   // 卡片状态分布
  rating_dist: {}    // 评分分布
})

let chartInstances = []

onMounted(async () => {
  await loadStats()
  await nextTick()
  renderCharts()
})

async function loadStats() {
  try {
    const response = await axios.get('/api/cards/stats/')

    // 如果后端还没实现统计API,使用模拟数据
    if (response.data) {
      stats.value = response.data
    } else {
      // 模拟数据用于演示
      generateMockData()
    }
  } catch (err) {
    console.error('Failed to load stats:', err)
    // 使用模拟数据
    generateMockData()
  }
}

function generateMockData() {
  const today = new Date()

  // 今日统计
  stats.value.today = {
    new_cards: 5,
    reviewed_cards: 23,
    accuracy: 87,
    avg_rating: 4.2
  }

  // 总体统计
  stats.value.total = {
    total_cards: 156,
    new_cards: 42,
    learning_cards: 68,
    mature_cards: 46,
    total_reviews: 892,
    correct_reviews: 751,
    overall_accuracy: 84,
    avg_time: 6.5
  }

  // 预测数据
  stats.value.forecast = {
    due_today: 28,
    due_tomorrow: 32,
    due_next_7days: 178,
    avg_daily: 25
  }

  stats.value.streak_days = 12

  // 近30天趋势
  stats.value.review_trend = Array.from({ length: 30 }, (_, i) => {
    const date = new Date(today)
    date.setDate(date.getDate() - (29 - i))
    return {
      date: date.toISOString().split('T')[0],
      reviews: Math.floor(Math.random() * 30) + 10,
      new_cards: Math.floor(Math.random() * 8)
    }
  })

  // 未来7天预测
  stats.value.forecast_data = Array.from({ length: 7 }, (_, i) => {
    const date = new Date(today)
    date.setDate(date.getDate() + i)
    return {
      date: date.toISOString().split('T')[0],
      due_count: Math.floor(Math.random() * 20) + 15
    }
  })

  // 卡片状态分布
  stats.value.card_status = {
    new: 42,
    learning: 68,
    mature: 46
  }

  // 评分分布
  stats.value.rating_dist = {
    again: 108,
    hard: 156,
    good: 425,
    easy: 203
  }
}

function renderCharts() {
  // 清理旧图表
  chartInstances.forEach(chart => chart.destroy())
  chartInstances = []

  // 1. 近30天复习趋势
  if (reviewTrendChart.value) {
    const ctx = reviewTrendChart.value.getContext('2d')
    const chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: stats.value.review_trend.map(d => d.date.slice(5)),
        datasets: [
          {
            label: '复习卡片数',
            data: stats.value.review_trend.map(d => d.reviews),
            borderColor: 'rgb(59, 130, 246)',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            tension: 0.4
          },
          {
            label: '新增卡片数',
            data: stats.value.review_trend.map(d => d.new_cards),
            borderColor: 'rgb(34, 197, 94)',
            backgroundColor: 'rgba(34, 197, 94, 0.1)',
            tension: 0.4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: { position: 'top' }
        },
        scales: {
          y: { beginAtZero: true }
        }
      }
    })
    chartInstances.push(chart)
  }

  // 2. 未来7天预测
  if (forecastChart.value) {
    const ctx = forecastChart.value.getContext('2d')
    const chart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: stats.value.forecast_data.map(d => d.date.slice(5)),
        datasets: [{
          label: '预计复习数',
          data: stats.value.forecast_data.map(d => d.due_count),
          backgroundColor: 'rgba(249, 115, 22, 0.6)',
          borderColor: 'rgb(249, 115, 22)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: { position: 'top' }
        },
        scales: {
          y: { beginAtZero: true }
        }
      }
    })
    chartInstances.push(chart)
  }

  // 3. 卡片状态分布
  if (cardStatusChart.value) {
    const ctx = cardStatusChart.value.getContext('2d')
    const chart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['新卡片', '学习中', '已熟悉'],
        datasets: [{
          data: [
            stats.value.card_status.new,
            stats.value.card_status.learning,
            stats.value.card_status.mature
          ],
          backgroundColor: [
            'rgba(59, 130, 246, 0.6)',
            'rgba(34, 197, 94, 0.6)',
            'rgba(168, 85, 247, 0.6)'
          ],
          borderColor: [
            'rgb(59, 130, 246)',
            'rgb(34, 197, 94)',
            'rgb(168, 85, 247)'
          ],
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: { position: 'bottom' }
        }
      }
    })
    chartInstances.push(chart)
  }

  // 4. 评分分布
  if (ratingDistChart.value) {
    const ctx = ratingDistChart.value.getContext('2d')
    const chart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['Again', 'Hard', 'Good', 'Easy'],
        datasets: [{
          label: '次数',
          data: [
            stats.value.rating_dist.again,
            stats.value.rating_dist.hard,
            stats.value.rating_dist.good,
            stats.value.rating_dist.easy
          ],
          backgroundColor: [
            'rgba(239, 68, 68, 0.6)',
            'rgba(251, 146, 60, 0.6)',
            'rgba(34, 197, 94, 0.6)',
            'rgba(59, 130, 246, 0.6)'
          ],
          borderColor: [
            'rgb(239, 68, 68)',
            'rgb(251, 146, 60)',
            'rgb(34, 197, 94)',
            'rgb(59, 130, 246)'
          ],
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: { beginAtZero: true }
        }
      }
    })
    chartInstances.push(chart)
  }
}
</script>

import { defineStore } from 'pinia'
import axios from 'axios'

export const useReviewStore = defineStore('review', {
  state: () => ({
    queue: [],
    currentCard: null,
    currentIndex: 0,
    isLoading: false,
    reviewHistory: [],
    stats: {
      completed: 0,
      correct: 0,
      totalTime: 0
    }
  }),

  getters: {
    hasCards: (state) => state.queue.length > 0,
    progress: (state) => ({
      current: state.currentIndex,
      total: state.queue.length
    }),
    accuracy: (state) => {
      if (state.stats.completed === 0) return 0
      return Math.round((state.stats.correct / state.stats.completed) * 100)
    }
  },

  actions: {
    async loadQueue(limit = 50) {
      this.isLoading = true
      try {
        const response = await axios.get('/api/review/queue/', {
          params: { limit }
        })

        this.queue = response.data.cards
        this.currentIndex = 0
        this.currentCard = this.queue[0] || null
        this.reviewHistory = []
        this.stats = { completed: 0, correct: 0, totalTime: 0 }

      } catch (error) {
        console.error('Failed to load queue:', error)
      } finally {
        this.isLoading = false
      }
    },

    async submitReview(quality, timeTaken) {
      if (!this.currentCard) return

      try {
        const response = await axios.post('/api/review/submit/', {
          card_id: this.currentCard.id,
          quality,
          time_taken: timeTaken
        })

        // 更新统计
        this.stats.completed++
        this.stats.totalTime += timeTaken
        if (quality >= 3) {
          this.stats.correct++
        }

        // 保存到历史记录
        this.reviewHistory.push({
          cardId: this.currentCard.id,
          quality,
          reviewLogId: response.data.review_log?.id
        })

        // 下一张卡片
        this.nextCard()

        return { success: true }
      } catch (error) {
        console.error('Failed to submit review:', error)
        return { success: false, error: error.response?.data?.error }
      }
    },

    async undoLastReview() {
      if (this.reviewHistory.length === 0) return { success: false }

      try {
        await axios.post('/api/review/undo/')

        // 回退
        const lastReview = this.reviewHistory.pop()
        if (this.currentIndex > 0) {
          this.currentIndex--
          this.currentCard = this.queue[this.currentIndex]
        }

        // 更新统计
        this.stats.completed = Math.max(0, this.stats.completed - 1)

        return { success: true }
      } catch (error) {
        console.error('Failed to undo:', error)
        return { success: false }
      }
    },

    nextCard() {
      this.currentIndex++
      if (this.currentIndex < this.queue.length) {
        this.currentCard = this.queue[this.currentIndex]
      } else {
        this.currentCard = null
      }
    }
  }
})

import { defineStore } from 'pinia'
import axios from 'axios'

export const useUserStore = defineStore('user', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('user')) || null,
    isAuthenticated: !!localStorage.getItem('user')
  }),

  actions: {
    async login(username, password) {
      try {
        const response = await axios.post('/api/auth/login/', {
          username,
          password
        })

        this.user = response.data.user
        this.isAuthenticated = true
        localStorage.setItem('user', JSON.stringify(response.data.user))

        return { success: true }
      } catch (error) {
        return {
          success: false,
          error: error.response?.data?.error || '登录失败'
        }
      }
    },

    async register(username, email, password, password_confirm) {
      try {
        const response = await axios.post('/api/auth/register/', {
          username,
          email,
          password,
          password_confirm
        })

        this.user = response.data.user
        this.isAuthenticated = true
        localStorage.setItem('user', JSON.stringify(response.data.user))

        return { success: true }
      } catch (error) {
        return {
          success: false,
          error: error.response?.data?.error || error.response?.data?.detail || '注册失败'
        }
      }
    },

    async logout() {
      try {
        await axios.post('/api/auth/logout/')
      } catch (error) {
        console.error('Logout error:', error)
      } finally {
        this.user = null
        this.isAuthenticated = false
        localStorage.removeItem('user')
      }
    }
  }
})

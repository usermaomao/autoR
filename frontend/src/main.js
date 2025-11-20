import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import axios from 'axios'
import App from './App.vue'
import './style.css'

// Configure axios defaults for Django session authentication
// Note: Vite proxy handles /api -> http://localhost:8000, so no baseURL needed
axios.defaults.withCredentials = true

// Add CSRF token to requests
axios.interceptors.request.use(config => {
  const csrfToken = document.cookie
    .split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1]

  if (csrfToken) {
    config.headers['X-CSRFToken'] = csrfToken
  }
  return config
})

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.mount('#app')

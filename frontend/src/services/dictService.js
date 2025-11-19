import axios from 'axios'

class LocalCache {
  constructor(namespace = 'rpd') {
    this.namespace = namespace
  }

  set(key, value, ttl = 7 * 24 * 60 * 60 * 1000) {
    const item = {
      value,
      expires: Date.now() + ttl
    }
    localStorage.setItem(`${this.namespace}:${key}`, JSON.stringify(item))
  }

  get(key) {
    const raw = localStorage.getItem(`${this.namespace}:${key}`)
    if (!raw) return null

    const item = JSON.parse(raw)
    if (Date.now() > item.expires) {
      this.remove(key)
      return null
    }
    return item.value
  }

  remove(key) {
    localStorage.removeItem(`${this.namespace}:${key}`)
  }

  clear() {
    Object.keys(localStorage)
      .filter(k => k.startsWith(this.namespace))
      .forEach(k => localStorage.removeItem(k))
  }
}

const cache = new LocalCache('dict')

export async function lookupWord(word, type = 'en') {
  // L1: 检查 localStorage 缓存
  const cached = cache.get(`${type}:${word}`)
  if (cached) {
    return { source: 'cache', data: cached }
  }

  try {
    // L2: 后端本地字典 (ECDICT/UniHan)
    const url = type === 'en'
      ? `/api/dict/en/${word}/`
      : `/api/dict/zh/${word}/`

    const res = await axios.get(url, { timeout: 2000 })
    cache.set(`${type}:${word}`, res.data)
    return { source: 'local-dict', data: res.data }

  } catch (error) {
    if (error.response?.status === 404) {
      // L3: 在线 API (仅英语)
      if (type === 'en') {
        try {
          const res = await axios.get(
            `https://api.dictionaryapi.dev/api/v2/entries/en/${word}`,
            { timeout: 3000 }
          )

          const apiData = res.data[0]
          const data = {
            word: apiData.word,
            ipa: apiData.phonetic || '',
            meaning_en: apiData.meanings[0]?.definitions[0]?.definition || '',
            examples: apiData.meanings[0]?.definitions.slice(0, 3).map(d => d.example).filter(Boolean) || []
          }

          cache.set(`${type}:${word}`, data)
          return { source: 'online-api', data }
        } catch {
          // L4: 手动填写
          return { source: 'manual', data: null }
        }
      }
    }

    return { source: 'manual', data: null }
  }
}

export async function inferPinyin(char, context = '') {
  try {
    const res = await axios.post('/api/dict/zh/infer-pinyin/', {
      char,
      context
    })
    return res.data
  } catch (error) {
    console.error('Failed to infer pinyin:', error)
    return { char, pinyin: null, confidence: 0, alternatives: [] }
  }
}

export { LocalCache }

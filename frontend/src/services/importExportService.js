import axios from 'axios'
import Papa from 'papaparse'

/**
 * 导入导出服务
 * 提供卡片的导入导出功能
 */

/**
 * 导入卡片
 * @param {File} file - 文件对象 (CSV 或 JSON)
 * @param {string} format - 文件格式 ('csv' 或 'json')
 * @param {number} deckId - 目标卡组ID
 * @param {string} cardType - 卡片类型 ('en' 或 'zh')
 * @param {string} conflictStrategy - 冲突策略 ('skip', 'overwrite', 'merge')
 * @param {function} onProgress - 进度回调函数
 * @returns {Promise<object>} 导入结果
 */
export async function importCards(file, format, deckId, cardType = 'en', conflictStrategy = 'skip', onProgress = null) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('format', format)
  formData.append('deck_id', deckId)
  formData.append('card_type', cardType)
  formData.append('conflict_strategy', conflictStrategy)

  try {
    const response = await axios.post('/api/cards/import/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(percentCompleted)
        }
      }
    })

    return {
      success: true,
      data: response.data
    }
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.error || error.message
    }
  }
}

/**
 * 导出卡片
 * @param {string} format - 导出格式 ('csv' 或 'json')
 * @param {number|null} deckId - 卡组ID（可选）
 * @returns {Promise<void>} 触发文件下载
 */
export async function exportCards(format = 'csv', deckId = null) {
  try {
    const params = { format }
    if (deckId) {
      params.deck_id = deckId
    }

    const response = await axios.get('/api/cards/export/', {
      params,
      responseType: 'blob'  // 重要：接收二进制数据
    })

    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url

    // 从响应头获取文件名
    const contentDisposition = response.headers['content-disposition']
    let filename = `cards_export_${new Date().toISOString().split('T')[0]}.${format}`

    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?(.+)"?/)
      if (filenameMatch) {
        filename = filenameMatch[1]
      }
    }

    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()

    // 清理
    link.remove()
    window.URL.revokeObjectURL(url)

    return { success: true }
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.error || error.message
    }
  }
}

/**
 * 解析 CSV 文件
 * @param {File} file - CSV 文件
 * @returns {Promise<object>} 解析结果
 */
export function parseCSV(file) {
  return new Promise((resolve, reject) => {
    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        if (results.errors.length > 0) {
          reject(new Error(`CSV 解析错误: ${results.errors[0].message}`))
        } else {
          resolve({
            data: results.data,
            meta: results.meta
          })
        }
      },
      error: (error) => {
        reject(error)
      }
    })
  })
}

/**
 * 解析 JSON 文件
 * @param {File} file - JSON 文件
 * @returns {Promise<object>} 解析结果
 */
export function parseJSON(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()

    reader.onload = (e) => {
      try {
        const data = JSON.parse(e.target.result)

        // 支持两种格式
        // 1. {cards: [...]}
        // 2. [...]
        const cards = Array.isArray(data) ? data : (data.cards || [])

        resolve({
          data: cards
        })
      } catch (error) {
        reject(new Error(`JSON 解析错误: ${error.message}`))
      }
    }

    reader.onerror = () => {
      reject(new Error('文件读取失败'))
    }

    reader.readAsText(file)
  })
}

/**
 * 验证导入文件格式
 * @param {Array} data - 解析后的数据
 * @returns {object} 验证结果
 */
export function validateImportData(data) {
  const errors = []

  if (!Array.isArray(data)) {
    return {
      valid: false,
      errors: ['数据格式错误：应该是数组']
    }
  }

  if (data.length === 0) {
    return {
      valid: false,
      errors: ['文件为空']
    }
  }

  // 检查每一行是否有必需字段
  data.forEach((row, index) => {
    if (!row.Front || row.Front.trim() === '') {
      errors.push(`第 ${index + 1} 行: 缺少 Front 字段`)
    }
    if (!row.Back || row.Back.trim() === '') {
      errors.push(`第 ${index + 1} 行: 缺少 Back 字段`)
    }
  })

  // 只显示前 10 个错误
  if (errors.length > 10) {
    errors.splice(10)
    errors.push(`...还有 ${errors.length - 10} 个错误`)
  }

  return {
    valid: errors.length === 0,
    errors
  }
}

/**
 * 生成导入预览
 * @param {Array} data - 解析后的数据
 * @param {number} limit - 预览行数限制
 * @returns {Array} 预览数据
 */
export function generatePreview(data, limit = 5) {
  return data.slice(0, limit).map(row => ({
    word: row.Front,
    meaning: row.Back,
    tags: row.Tags ? row.Tags.split(',').map(t => t.trim()) : []
  }))
}

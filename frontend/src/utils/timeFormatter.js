/**
 * 时间格式化工具函数
 */

/**
 * 格式化复习时间
 * - 如果是当天，显示"XX小时后"或"XX分钟后"
 * - 如果是未来某天，显示"XX天后"
 * - 如果已过期，显示"已到期"
 *
 * @param {string|Date} dueAt - 到期时间（ISO字符串或Date对象）
 * @returns {string} 格式化后的时间字符串
 */
export function formatDueTime(dueAt) {
  if (!dueAt) {
    return '未设置'
  }

  // 解析时间
  const dueDate = new Date(dueAt)
  const now = new Date()

  // 检查是否为哨兵值（9999-12-31表示未进入复习队列）
  if (dueDate.getFullYear() === 9999) {
    return '尚未开始'
  }

  // 计算时间差（毫秒）
  const diffMs = dueDate - now

  // 已过期
  if (diffMs < 0) {
    return '已到期'
  }

  // 转换为分钟、小时、天
  const diffMinutes = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  // 判断是否为当天
  const isToday = dueDate.toDateString() === now.toDateString()

  if (isToday) {
    // 当天：显示小时或分钟
    if (diffMinutes < 60) {
      return `${diffMinutes}分钟后`
    } else {
      const hours = Math.floor(diffMinutes / 60)
      const minutes = diffMinutes % 60
      if (minutes > 0) {
        return `${hours}小时${minutes}分钟后`
      }
      return `${hours}小时后`
    }
  } else {
    // 非当天：显示天数
    if (diffDays === 0) {
      // 不到24小时但跨天了
      return `明天`
    } else if (diffDays === 1) {
      return `1天后`
    } else {
      return `${diffDays}天后`
    }
  }
}

/**
 * 格式化为完整日期时间
 * @param {string|Date} dateTime - 日期时间
 * @returns {string} 格式化后的日期时间字符串（YYYY-MM-DD HH:mm）
 */
export function formatFullDateTime(dateTime) {
  if (!dateTime) {
    return ''
  }

  const date = new Date(dateTime)

  // 检查是否为哨兵值
  if (date.getFullYear() === 9999) {
    return '尚未开始'
  }

  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')

  return `${year}-${month}-${day} ${hours}:${minutes}`
}

/**
 * 格式化为简短日期
 * @param {string|Date} dateTime - 日期时间
 * @returns {string} 格式化后的日期字符串（MM-DD）
 */
export function formatShortDate(dateTime) {
  if (!dateTime) {
    return ''
  }

  const date = new Date(dateTime)

  // 检查是否为哨兵值
  if (date.getFullYear() === 9999) {
    return '尚未开始'
  }

  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')

  return `${month}-${day}`
}

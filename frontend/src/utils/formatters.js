export const formatDate = (date) => {
  if (!date) return ''
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export const formatCurrency = (amount) => {
  if (!amount) return '$0.00'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount)
}

export const formatPercentage = (value, decimals = 1) => {
  if (!value) return '0%'
  return `${(value).toFixed(decimals)}%`
}

export const truncateText = (text, length = 50) => {
  if (!text) return ''
  if (text.length <= length) return text
  return `${text.substring(0, length)}...`
}

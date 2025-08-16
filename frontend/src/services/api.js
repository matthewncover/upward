const API_BASE_URL = 'http://localhost:8000/api'

class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
    this.name = 'ApiError'
  }
}

async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    ...options
  }

  try {
    const response = await fetch(url, config)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new ApiError(
        errorData.detail || `HTTP ${response.status}`, 
        response.status
      )
    }

    const contentType = response.headers.get('content-type')
    if (contentType && contentType.includes('application/json')) {
      return await response.json()
    }
    return await response.text()
  } catch (error) {
    if (error instanceof ApiError) throw error
    throw new ApiError(`Network error: ${error.message}`, 0)
  }
}

// Habit API functions
export async function getHabits() {
  return apiRequest('/habits/')
}

export async function createHabit(habit) {
  return apiRequest('/habits/', {
    method: 'POST',
    body: JSON.stringify(habit)
  })
}

export async function updateHabit(habitId, updates) {
  return apiRequest(`/habits/${habitId}`, {
    method: 'PUT',
    body: JSON.stringify(updates)
  })
}

export async function deleteHabit(habitId) {
  return apiRequest(`/habits/${habitId}`, {
    method: 'DELETE'
  })
}

// Habit Entry API functions
export async function getHabitEntries(date = null) {
  const params = date ? `?entry_date=${date}` : ''
  return apiRequest(`/habits/entries${params}`)
}

export async function createHabitEntry(entry) {
  return apiRequest('/habits/entries', {
    method: 'POST',
    body: JSON.stringify(entry)
  })
}

export async function createHabitEntriesBatch(entries) {
  return apiRequest('/habits/entries/batch', {
    method: 'POST',
    body: JSON.stringify(entries)
  })
}

export async function getHabitEntriesById(habitId, days = 30) {
  return apiRequest(`/habits/entries/${habitId}?days=${days}`)
}

// Scoring API functions
export async function getDailyScores(startDate = null, endDate = null, days = 30) {
  const params = new URLSearchParams()
  if (startDate) params.append('start_date', startDate)
  if (endDate) params.append('end_date', endDate)
  if (!startDate && !endDate) params.append('days', days)
  
  const queryString = params.toString() ? `?${params.toString()}` : ''
  return apiRequest(`/scores/daily${queryString}`)
}

export async function getHabitPerformance(habitId, days = 30) {
  return apiRequest(`/scores/habits/${habitId}?days=${days}`)
}

export async function recalculateScores(startDate = null, endDate = null) {
  const body = {}
  if (startDate) body.start_date = startDate
  if (endDate) body.end_date = endDate
  
  return apiRequest('/scores/recalculate', {
    method: 'POST',
    body: JSON.stringify(body)
  })
}

export async function getScoresSummary() {
  return apiRequest('/scores/summary')
}

export async function getAllHabitScores(date = null) {
  const params = date ? `?target_date=${date}` : ''
  return apiRequest(`/scores/habits${params}`)
}

export async function getScoreTrends(days = 30) {
  return apiRequest(`/scores/trends?days=${days}`)
}

export async function getWeeklyProgress() {
  return apiRequest('/notifications/weekly-progress')
}

// WHOOP API functions
export async function connectWhoop() {
  return apiRequest('/auth/whoop')
}

export async function checkWhoopStatus() {
  return apiRequest('/auth/whoop/status')
}

export async function syncWhoopData(days = 30) {
  return apiRequest('/whoop/sync', {
    method: 'POST',
    body: JSON.stringify({ days })
  })
}

export async function getWhoopData(startDate = null, endDate = null, days = 30) {
  const params = new URLSearchParams()
  if (startDate) params.append('start_date', startDate)
  if (endDate) params.append('end_date', endDate)
  if (!startDate && !endDate) params.append('days', days)
  
  const queryString = params.toString() ? `?${params.toString()}` : ''
  return apiRequest(`/whoop/data${queryString}`)
}

export async function getWhoopSyncStatus() {
  return apiRequest('/whoop/status')
}

// Utility functions
export function formatDate(date) {
  if (date instanceof Date) {
    return date.toISOString().split('T')[0]
  }
  return date
}

export function parseDate(dateString) {
  return new Date(dateString)
}

export { ApiError }
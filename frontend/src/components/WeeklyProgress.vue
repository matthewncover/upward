<template>
  <div class="weekly-progress">
    <div class="page-header">
      <h2>Weekly Progress Dashboard</h2>
      <div class="date-info">
        <span>Week of {{ formatWeekStart(currentWeek) }}</span>
        <div class="week-navigation">
          <button @click="changeWeek(-1)" class="nav-btn">← Previous Week</button>
          <button @click="goToCurrentWeek" class="nav-btn">Current Week</button>
          <button @click="changeWeek(1)" class="nav-btn">Next Week →</button>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      Loading weekly data...
    </div>

    <div v-else-if="error" class="error">
      <div class="error-message">{{ error }}</div>
      <button @click="loadWeekData" class="retry-btn">Retry</button>
    </div>

    <div v-else class="dashboard-content">
      <!-- Weekly Summary Cards -->
      <div class="summary-cards">
        <div class="summary-card">
          <div class="card-icon">📊</div>
          <div class="card-content">
            <h3>Week Average</h3>
            <div class="card-value">{{ weeklyStats.averageScore.toFixed(2) }}</div>
            <div class="card-change" :class="changeClass(weeklyStats.weekOverWeekChange)">
              {{ formatChange(weeklyStats.weekOverWeekChange) }} vs last week
            </div>
          </div>
        </div>

        <div class="summary-card">
          <div class="card-icon">🔥</div>
          <div class="card-content">
            <h3>Current Streak</h3>
            <div class="card-value">{{ weeklyStats.currentStreak }} days</div>
            <div class="card-subtext">Longest: {{ weeklyStats.longestStreak }} days</div>
          </div>
        </div>

        <div class="summary-card">
          <div class="card-icon">🎯</div>
          <div class="card-content">
            <h3>Habits On Track</h3>
            <div class="card-value">{{ habitsOnTrack }}/{{ habits.length }}</div>
            <div class="card-subtext">{{ Math.round((habitsOnTrack / habits.length) * 100) }}% success rate</div>
          </div>
        </div>

        <div class="summary-card" v-if="whoopConnected">
          <div class="card-icon">💚</div>
          <div class="card-content">
            <h3>WHOOP Avg</h3>
            <div class="card-value">{{ weeklyStats.whoopAverage.toFixed(1) }}%</div>
            <div class="card-subtext">Recovery & Sleep</div>
          </div>
        </div>
      </div>

      <!-- Habit Progress Grid -->
      <div class="habits-grid">
        <div v-for="habit in habits" :key="habit.id" class="habit-progress-card">
          <div class="habit-header">
            <h3>{{ habit.name }}</h3>
            <div class="momentum-indicator" :class="getMomentumClass(habit.id)">
              {{ getMomentumLabel(habit.id) }}
            </div>
          </div>

          <!-- 7-day progress visualization -->
          <div class="daily-progress">
            <div class="days-grid">
              <div 
                v-for="(day, index) in weekDays" 
                :key="index"
                class="day-cell"
                :class="getDayClass(habit.id, day)"
                :title="getDayTooltip(habit.id, day)"
              >
                <div class="day-label">{{ getDayLabel(day) }}</div>
                <div class="day-value">{{ getDayValue(habit.id, day) }}</div>
              </div>
            </div>
          </div>

          <!-- Progress statistics -->
          <div class="habit-stats">
            <div class="stat-row">
              <span class="stat-label">Target:</span>
              <span class="stat-value">{{ habit.target_days_per_week }}/7 days</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">Completed:</span>
              <span class="stat-value">{{ getHabitCompletedDays(habit.id) }}/7 days</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">Momentum:</span>
              <span class="stat-value">{{ getMomentumMultiplier(habit.id) }}x</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">Weekly Score:</span>
              <span class="stat-value">{{ getHabitWeeklyScore(habit.id).toFixed(2) }}</span>
            </div>
          </div>

          <!-- Progress bar -->
          <div class="progress-bar-container">
            <div class="progress-bar">
              <div 
                class="progress-fill" 
                :class="getProgressBarClass(habit.id)"
                :style="{ width: `${getProgressPercentage(habit.id)}%` }"
              ></div>
            </div>
            <div class="progress-text">
              {{ getProgressPercentage(habit.id) }}% of weekly target
            </div>
          </div>
        </div>
      </div>

      <!-- WHOOP Integration Status -->
      <div v-if="whoopStatus" class="whoop-section">
        <div class="section-header">
          <h3>WHOOP Integration</h3>
          <button @click="syncWhoopData" :disabled="syncing" class="sync-btn">
            {{ syncing ? 'Syncing...' : 'Sync Data' }}
          </button>
        </div>
        
        <div class="whoop-stats">
          <div class="whoop-stat">
            <span class="label">Data Coverage:</span>
            <span class="value">{{ whoopStatus.data_coverage.toFixed(0) }}%</span>
          </div>
          <div class="whoop-stat">
            <span class="label">Last Sync:</span>
            <span class="value">{{ formatDate(whoopStatus.last_sync) }}</span>
          </div>
          <div class="whoop-stat">
            <span class="label">Missing Days:</span>
            <span class="value">{{ whoopStatus.missing_dates.length }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { 
  getHabits,
  getHabitEntries,
  getAllHabitScores,
  getScoresSummary,
  getWhoopSyncStatus,
  syncWhoopData as apiSyncWhoopData,
  checkWhoopStatus,
  formatDate as apiFormatDate
} from '../services/api.js'

export default {
  name: 'WeeklyProgress',
  setup() {
    const currentWeek = ref(new Date())
    const loading = ref(false)
    const syncing = ref(false)
    const error = ref('')
    
    const habits = ref([])
    const weeklyEntries = reactive({})
    const habitScores = reactive({})
    const momentumStatus = reactive({})
    const weeklyStats = reactive({
      averageScore: 0,
      weekOverWeekChange: 0,
      currentStreak: 0,
      longestStreak: 0,
      whoopAverage: 0
    })
    const whoopStatus = ref(null)
    const whoopConnected = ref(false)
    
    // Generate array of 7 days for current week
    const weekDays = computed(() => {
      const days = []
      const startOfWeek = new Date(currentWeek.value)
      startOfWeek.setDate(startOfWeek.getDate() - startOfWeek.getDay()) // Sunday
      
      for (let i = 0; i < 7; i++) {
        const day = new Date(startOfWeek)
        day.setDate(startOfWeek.getDate() + i)
        days.push(day)
      }
      return days
    })
    
    const habitsOnTrack = computed(() => {
      return habits.value.filter(habit => {
        const completed = getHabitCompletedDays(habit.id)
        return completed >= habit.target_days_per_week
      }).length
    })
    
    function formatWeekStart(date) {
      const startOfWeek = new Date(date)
      startOfWeek.setDate(startOfWeek.getDate() - startOfWeek.getDay())
      return startOfWeek.toLocaleDateString('en-US', { 
        month: 'long', 
        day: 'numeric', 
        year: 'numeric' 
      })
    }
    
    function formatDate(dateString) {
      if (!dateString) return 'Never'
      return new Date(dateString).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric'
      })
    }
    
    function formatChange(change) {
      if (change > 0) return `+${change.toFixed(1)}%`
      return `${change.toFixed(1)}%`
    }
    
    function changeClass(change) {
      if (change > 5) return 'change-positive'
      if (change < -5) return 'change-negative'
      return 'change-neutral'
    }
    
    function getDayLabel(date) {
      return date.toLocaleDateString('en-US', { weekday: 'short' })
    }
    
    function getDayValue(habitId, date) {
      const dateKey = apiFormatDate(date)
      const entries = weeklyEntries[habitId] || {}
      const entry = entries[dateKey]
      
      if (!entry) return ''
      
      const habit = habits.value.find(h => h.id === habitId)
      if (!habit) return ''
      
      if (habit.habit_type === 'binary') {
        return entry.value > 0 ? '✓' : ''
      } else if (habit.habit_type === 'duration') {
        return `${entry.value}m`
      } else {
        return entry.value.toString()
      }
    }
    
    function getDayClass(habitId, date) {
      const dateKey = apiFormatDate(date)
      const entries = weeklyEntries[habitId] || {}
      const entry = entries[dateKey]
      const habit = habits.value.find(h => h.id === habitId)
      
      if (!entry || !habit) return 'day-empty'
      
      const score = calculateHabitScore(habit, entry.value)
      
      if (score >= 1.5) return 'day-stretch'
      if (score >= 1.0) return 'day-goal'
      if (score >= 0.3) return 'day-nonzero'
      return 'day-empty'
    }
    
    function getDayTooltip(habitId, date) {
      const habit = habits.value.find(h => h.id === habitId)
      const value = getDayValue(habitId, date)
      
      if (!habit || !value) return 'No entry'
      
      const dateStr = date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      })
      
      return `${habit.name} on ${dateStr}: ${value}`
    }
    
    function calculateHabitScore(habit, value) {
      if (habit.is_inverted) {
        if (value >= habit.nonzero_threshold) return 0.0
        if (value <= habit.stretch_threshold) return 1.5
        if (value <= habit.goal_threshold) return 1.0
        return 0.3
      } else {
        if (value === 0) return 0.0
        if (value >= habit.stretch_threshold) return 1.5
        if (value >= habit.goal_threshold) return 1.0
        if (value >= habit.nonzero_threshold) return 0.3
        return 0.0
      }
    }
    
    function getHabitCompletedDays(habitId) {
      const entries = weeklyEntries[habitId] || {}
      return Object.values(entries).filter(entry => entry.value > 0).length
    }
    
    function getMomentumClass(habitId) {
      const status = momentumStatus[habitId]
      if (!status) return 'momentum-neutral'
      
      if (status.trend === 'growing') return 'momentum-positive'
      if (status.trend === 'decaying') return 'momentum-negative'
      return 'momentum-neutral'
    }
    
    function getMomentumLabel(habitId) {
      const status = momentumStatus[habitId]
      if (!status) return 'Stable'
      
      return status.trend === 'growing' ? 'Rising' : 
             status.trend === 'decaying' ? 'Falling' : 'Stable'
    }
    
    function getMomentumMultiplier(habitId) {
      const status = momentumStatus[habitId]
      return status ? status.current_multiplier.toFixed(2) : '1.00'
    }
    
    function getHabitWeeklyScore(habitId) {
      const scores = habitScores[habitId] || []
      if (scores.length === 0) return 0
      
      const sum = scores.reduce((total, score) => total + score.final_score, 0)
      return sum / scores.length
    }
    
    function getProgressPercentage(habitId) {
      const habit = habits.value.find(h => h.id === habitId)
      if (!habit) return 0
      
      const completed = getHabitCompletedDays(habitId)
      return Math.min((completed / habit.target_days_per_week) * 100, 100)
    }
    
    function getProgressBarClass(habitId) {
      const percentage = getProgressPercentage(habitId)
      
      if (percentage >= 100) return 'progress-excellent'
      if (percentage >= 80) return 'progress-good'
      if (percentage >= 60) return 'progress-okay'
      return 'progress-poor'
    }
    
    async function loadWeekData() {
      loading.value = true
      error.value = ''
      
      try {
        // Load habits
        const habitsData = await getHabits()
        habits.value = habitsData
        
        // Load entries for the week
        const weekStart = new Date(currentWeek.value)
        weekStart.setDate(weekStart.getDate() - weekStart.getDay())
        
        for (const habit of habitsData) {
          weeklyEntries[habit.id] = {}
          
          for (let i = 0; i < 7; i++) {
            const date = new Date(weekStart)
            date.setDate(weekStart.getDate() + i)
            const dateKey = apiFormatDate(date)
            
            try {
              const entries = await getHabitEntries(dateKey)
              const habitEntry = entries.find(e => e.habit_id === habit.id)
              
              if (habitEntry) {
                weeklyEntries[habit.id][dateKey] = habitEntry
              }
            } catch (err) {
              console.error(`Failed to load entry for ${dateKey}:`, err)
            }
          }
        }
        
        // Load scores summary and momentum data
        const summary = await getScoresSummary()
        Object.assign(weeklyStats, {
          averageScore: summary.current_week_average || 0,
          weekOverWeekChange: summary.week_over_week_change || 0,
          currentStreak: summary.current_streak || 0,
          longestStreak: summary.longest_streak || 0,
          whoopAverage: 75 // Placeholder
        })
        
        Object.assign(momentumStatus, summary.momentum_status || {})
        
        // Check WHOOP connection
        const whoopConnectionStatus = await checkWhoopStatus()
        whoopConnected.value = whoopConnectionStatus.connected
        
        if (whoopConnectionStatus.connected) {
          const status = await getWhoopSyncStatus()
          whoopStatus.value = status
        }
        
      } catch (err) {
        error.value = `Failed to load weekly data: ${err.message}`
      } finally {
        loading.value = false
      }
    }
    
    async function syncWhoopData() {
      syncing.value = true
      try {
        await apiSyncWhoopData(7)
        
        // Refresh WHOOP status
        const status = await getWhoopSyncStatus()
        whoopStatus.value = status
        
      } catch (err) {
        error.value = `Failed to sync WHOOP data: ${err.message}`
      } finally {
        syncing.value = false
      }
    }
    
    function changeWeek(direction) {
      const newWeek = new Date(currentWeek.value)
      newWeek.setDate(newWeek.getDate() + (direction * 7))
      currentWeek.value = newWeek
      loadWeekData()
    }
    
    function goToCurrentWeek() {
      currentWeek.value = new Date()
      loadWeekData()
    }
    
    onMounted(loadWeekData)
    
    return {
      currentWeek,
      loading,
      syncing,
      error,
      habits,
      weekDays,
      weeklyStats,
      whoopStatus,
      whoopConnected,
      habitsOnTrack,
      formatWeekStart,
      formatDate,
      formatChange,
      changeClass,
      getDayLabel,
      getDayValue,
      getDayClass,
      getDayTooltip,
      getHabitCompletedDays,
      getMomentumClass,
      getMomentumLabel,
      getMomentumMultiplier,
      getHabitWeeklyScore,
      getProgressPercentage,
      getProgressBarClass,
      loadWeekData,
      syncWhoopData,
      changeWeek,
      goToCurrentWeek
    }
  }
}
</script>

<style scoped>
.weekly-progress {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.page-header h2 {
  color: #2c3e50;
  margin: 0;
}

.date-info {
  text-align: right;
}

.date-info span {
  display: block;
  color: #6c757d;
  margin-bottom: 0.5rem;
}

.week-navigation {
  display: flex;
  gap: 0.5rem;
}

.nav-btn {
  padding: 0.5rem 1rem;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.nav-btn:hover {
  background: #e9ecef;
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 4rem;
  color: #6c757d;
}

.spinner {
  width: 2rem;
  height: 2rem;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.error {
  text-align: center;
  padding: 2rem;
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
  border-radius: 8px;
  margin: 2rem 0;
}

.retry-btn {
  background: #dc3545;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.summary-card {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  gap: 1rem;
}

.card-icon {
  font-size: 2rem;
  width: 3rem;
  text-align: center;
}

.card-content h3 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
  font-size: 1rem;
}

.card-value {
  font-size: 1.5rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 0.25rem;
}

.card-change, .card-subtext {
  font-size: 0.85rem;
  color: #6c757d;
}

.change-positive { color: #28a745; }
.change-negative { color: #dc3545; }
.change-neutral { color: #6c757d; }

.habits-grid {
  display: grid;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.habit-progress-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.habit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.habit-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.1rem;
}

.momentum-indicator {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
}

.momentum-positive {
  background: #d4edda;
  color: #155724;
}

.momentum-negative {
  background: #f8d7da;
  color: #721c24;
}

.momentum-neutral {
  background: #e2e3e5;
  color: #495057;
}

.days-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.day-cell {
  aspect-ratio: 1;
  border-radius: 6px;
  border: 2px solid #e9ecef;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  transition: all 0.3s;
  cursor: pointer;
}

.day-label {
  font-weight: 500;
  margin-bottom: 0.25rem;
  color: #6c757d;
}

.day-value {
  font-weight: 600;
  font-size: 0.7rem;
}

.day-empty {
  background: #f8f9fa;
  border-color: #e9ecef;
  color: #6c757d;
}

.day-nonzero {
  background: #fff3cd;
  border-color: #ffeaa7;
  color: #856404;
}

.day-goal {
  background: #d1ecf1;
  border-color: #bee5eb;
  color: #0c5460;
}

.day-stretch {
  background: #d4edda;
  border-color: #c3e6cb;
  color: #155724;
}

.habit-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  background: #f8f9fa;
  border-radius: 4px;
}

.stat-label {
  font-size: 0.9rem;
  color: #6c757d;
}

.stat-value {
  font-weight: 500;
  color: #2c3e50;
}

.progress-bar-container {
  margin-top: 1rem;
}

.progress-bar {
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s;
}

.progress-excellent { background: #28a745; }
.progress-good { background: #17a2b8; }
.progress-okay { background: #ffc107; }
.progress-poor { background: #dc3545; }

.progress-text {
  text-align: center;
  font-size: 0.9rem;
  color: #6c757d;
}

.whoop-section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.section-header h3 {
  margin: 0;
  color: #2c3e50;
}

.sync-btn {
  background: #e74c3c;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.sync-btn:hover:not(:disabled) {
  background: #c0392b;
}

.sync-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.whoop-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.whoop-stat {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
}

.whoop-stat .label {
  color: #6c757d;
}

.whoop-stat .value {
  font-weight: 500;
  color: #2c3e50;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .date-info {
    text-align: center;
  }
  
  .summary-cards {
    grid-template-columns: 1fr;
  }
  
  .days-grid {
    font-size: 0.7rem;
  }
  
  .habit-stats {
    grid-template-columns: 1fr;
  }
  
  .whoop-stats {
    grid-template-columns: 1fr;
  }
  
  .week-navigation {
    justify-content: center;
  }
}
</style>
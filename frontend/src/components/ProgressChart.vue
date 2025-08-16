<template>
  <div class="progress-chart">
    <div class="chart-header">
      <h2>Progress Visualization</h2>
      <div class="chart-controls">
        <div class="view-toggle">
          <label>View:</label>
          <select v-model="selectedView" @change="updateChart">
            <option value="daily">Daily Scores</option>
            <option value="cumulative">Cumulative Score</option>
            <option value="habits">Individual Habits</option>
            <option value="whoop">WHOOP Data</option>
          </select>
        </div>
        
        <div class="date-range">
          <label>Time Range:</label>
          <select v-model="dayRange" @change="loadData">
            <option :value="7">7 days</option>
            <option :value="14">14 days</option>
            <option :value="30">30 days</option>
            <option :value="60">60 days</option>
            <option :value="90">90 days</option>
          </select>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      Loading chart data...
    </div>

    <div v-else-if="error" class="error">
      <div class="error-message">{{ error }}</div>
      <button @click="loadData" class="retry-btn">Retry</button>
    </div>

    <div v-else class="chart-container">
      <div class="chart-wrapper">
        <Line :key="chartKey" :data="chartData" :options="chartOptions" />
      </div>
      
      <!-- Statistics panel -->
      <div class="stats-panel">
        <div class="stat-card">
          <h3>Statistics</h3>
          <div class="stats-grid">
            <div class="stat-item">
              <span class="stat-label">Average Score</span>
              <span class="stat-value">{{ statistics.averageScore.toFixed(2) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Best Day</span>
              <span class="stat-value">{{ statistics.maxScore.toFixed(2) }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Trend</span>
              <span class="stat-value" :class="trendClass">{{ statistics.trend }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Consistency</span>
              <span class="stat-value">{{ statistics.consistency }}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Habit selection for individual view -->
    <div v-if="selectedView === 'habits' && habits.length > 0" class="habit-selector">
      <h3>Select Habits to Display</h3>
      <div class="habit-checkboxes">
        <div v-for="habit in habits" :key="habit.id" class="habit-checkbox">
          <input 
            :id="`habit-${habit.id}`"
            type="checkbox" 
            :value="habit.id"
            v-model="selectedHabits"
            @change="updateChart"
          >
          <label :for="`habit-${habit.id}`">{{ habit.name }}</label>
        </div>
      </div>
    </div>

    <!-- WHOOP data selection -->
    <div v-if="selectedView === 'whoop'" class="whoop-selector">
      <h3>Select WHOOP Metrics to Display</h3>
      <div class="whoop-checkboxes">
        <div class="whoop-checkbox">
          <input 
            id="whoop-recovery"
            type="checkbox" 
            value="recovery_score"
            v-model="selectedWhoopMetrics"
            @change="updateChart"
          >
          <label for="whoop-recovery">Recovery Score (%)</label>
        </div>
        <div class="whoop-checkbox">
          <input 
            id="whoop-sleep"
            type="checkbox" 
            value="sleep_score"
            v-model="selectedWhoopMetrics"
            @change="updateChart"
          >
          <label for="whoop-sleep">Sleep Performance (%)</label>
        </div>
        <div class="whoop-checkbox">
          <input 
            id="whoop-hrv"
            type="checkbox" 
            value="hrv_score"
            v-model="selectedWhoopMetrics"
            @change="updateChart"
          >
          <label for="whoop-hrv">HRV (ms)</label>
        </div>
        <div class="whoop-checkbox">
          <input 
            id="whoop-multiplier"
            type="checkbox" 
            value="whoop_multiplier"
            v-model="selectedWhoopMetrics"
            @change="updateChart"
          >
          <label for="whoop-multiplier">WHOOP Multiplier</label>
        </div>
      </div>
    </div>

    <!-- Moving averages toggle -->
    <div class="chart-options">
      <div class="option-group">
        <label>
          <input type="checkbox" v-model="showMovingAverage" @change="updateChart">
          Show 7-day moving average
        </label>
      </div>
      <div v-if="selectedView === 'daily'" class="option-group">
        <label>
          <input type="checkbox" v-model="showWhoopData" @change="updateChart">
          Include WHOOP multiplier
        </label>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { Line } from 'vue-chartjs'
import { 
  getDailyScores, 
  getHabits, 
  getHabitPerformance,
  getWhoopData,
  formatDate 
} from '../services/api.js'
import { 
  scoreChartConfig, 
  cumulativeChartConfig, 
  habitChartConfig,
  chartColors,
  generateDatasetColors,
  formatDateForChart,
  createGradient
} from '../utils/chartConfig.js'

// WHOOP chart configuration
const whoopChartConfig = {
  ...scoreChartConfig,
  plugins: {
    ...scoreChartConfig.plugins,
    title: {
      display: true,
      text: 'WHOOP Biometric Data',
      font: { size: 16, weight: 'bold' },
      padding: 20
    }
  },
  scales: {
    ...scoreChartConfig.scales,
    y: {
      ...scoreChartConfig.scales.y,
      title: { display: true, text: 'Score (%)' },
      beginAtZero: true,
      max: 100,
      position: 'left'
    },
    y1: {
      type: 'linear',
      display: true,
      position: 'right',
      title: { display: true, text: 'Multiplier' },
      beginAtZero: true,
      max: 2.0,
      grid: {
        drawOnChartArea: false
      }
    }
  }
}

export default {
  name: 'ProgressChart',
  components: {
    Line
  },
  setup() {
    const selectedView = ref('daily')
    const dayRange = ref(30)
    const loading = ref(false)
    const error = ref('')
    const showMovingAverage = ref(false)
    const showWhoopData = ref(false)
    const selectedHabits = ref([])
    const selectedWhoopMetrics = ref(['recovery_score', 'sleep_score', 'hrv_score'])
    const chartKey = ref(0)
    
    const dailyScores = ref([])
    const habits = ref([])
    const habitScores = reactive({})
    const whoopData = ref([])
    
    const statistics = computed(() => {
      if (dailyScores.value.length === 0) {
        return {
          averageScore: 0,
          maxScore: 0,
          trend: 'No data',
          consistency: 0
        }
      }
      
      const scores = dailyScores.value.map(d => d.final_score)
      const avg = scores.reduce((sum, score) => sum + score, 0) / scores.length
      const max = Math.max(...scores)
      
      // Calculate trend (simple linear regression slope)
      const n = scores.length
      const indices = scores.map((_, i) => i)
      const sumX = indices.reduce((sum, i) => sum + i, 0)
      const sumY = scores.reduce((sum, score) => sum + score, 0)
      const sumXY = indices.reduce((sum, i) => sum + i * scores[i], 0)
      const sumXX = indices.reduce((sum, i) => sum + i * i, 0)
      
      const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX)
      const trend = slope > 0.01 ? 'Rising' : slope < -0.01 ? 'Falling' : 'Stable'
      
      // Calculate consistency (percentage of days with score > 0)
      const activeDays = scores.filter(score => score > 0).length
      const consistency = Math.round((activeDays / scores.length) * 100)
      
      return {
        averageScore: avg,
        maxScore: max,
        trend,
        consistency
      }
    })
    
    const trendClass = computed(() => {
      const trend = statistics.value.trend
      if (trend === 'Rising') return 'trend-positive'
      if (trend === 'Falling') return 'trend-negative'
      return 'trend-neutral'
    })
    
    const chartData = computed(() => {
      if (selectedView.value === 'daily') {
        return createDailyChartData()
      } else if (selectedView.value === 'cumulative') {
        return createCumulativeChartData()
      } else if (selectedView.value === 'habits') {
        return createHabitChartData()
      } else if (selectedView.value === 'whoop') {
        return createWhoopChartData()
      }
      return { datasets: [] }
    })
    
    const chartOptions = computed(() => {
      if (selectedView.value === 'daily') {
        return scoreChartConfig
      } else if (selectedView.value === 'cumulative') {
        return cumulativeChartConfig
      } else if (selectedView.value === 'habits') {
        return habitChartConfig
      } else if (selectedView.value === 'whoop') {
        return whoopChartConfig
      }
      return scoreChartConfig
    })
    
    function createDailyChartData() {
      if (dailyScores.value.length === 0) return { datasets: [] }
      
      const labels = dailyScores.value.map(d => formatDateForChart(d.date))
      const datasets = []
      
      // Main daily scores
      datasets.push({
        label: 'Daily Score',
        data: dailyScores.value.map(d => d.final_score),
        borderColor: chartColors.primary,
        backgroundColor: chartColors.primary + '20',
        borderWidth: 2,
        fill: true,
        tension: 0.1
      })
      
      // Base score (without WHOOP multiplier)
      if (showWhoopData.value) {
        datasets.push({
          label: 'Base Score',
          data: dailyScores.value.map(d => d.base_score),
          borderColor: chartColors.secondary,
          backgroundColor: 'transparent',
          borderWidth: 2,
          borderDash: [5, 5],
          fill: false,
          tension: 0.1
        })
      }
      
      // Moving average
      if (showMovingAverage.value && dailyScores.value.length >= 7) {
        const movingAvg = calculateMovingAverage(dailyScores.value.map(d => d.final_score), 7)
        datasets.push({
          label: '7-day Average',
          data: movingAvg,
          borderColor: chartColors.warning,
          backgroundColor: 'transparent',
          borderWidth: 3,
          fill: false,
          tension: 0.3
        })
      }
      
      return { labels, datasets }
    }
    
    function createCumulativeChartData() {
      if (dailyScores.value.length === 0) return { datasets: [] }
      
      const labels = dailyScores.value.map(d => formatDateForChart(d.date))
      
      return {
        labels,
        datasets: [{
          label: 'Cumulative Score',
          data: dailyScores.value.map(d => d.cumulative_score),
          borderColor: chartColors.success,
          backgroundColor: chartColors.success + '20',
          borderWidth: 2,
          fill: true,
          tension: 0.1
        }]
      }
    }
    
    function createHabitChartData() {
      if (selectedHabits.value.length === 0) return { datasets: [] }
      
      // Get the dates from any habit (they should all have the same dates)
      const firstHabitId = selectedHabits.value[0]
      const firstHabitData = habitScores[firstHabitId] || []
      
      if (firstHabitData.length === 0) return { datasets: [] }
      
      const labels = firstHabitData.map(d => formatDateForChart(d.date))
      const colors = generateDatasetColors(selectedHabits.value.length)
      
      const datasets = selectedHabits.value.map((habitId, index) => {
        const habit = habits.value.find(h => h.id === habitId)
        const data = habitScores[habitId] || []
        
        return {
          label: habit?.name || `Habit ${habitId}`,
          data: data.map(d => d.final_score),
          borderColor: colors[index],
          backgroundColor: colors[index] + '20',
          borderWidth: 2,
          fill: false,
          tension: 0.1
        }
      })
      
      return { labels, datasets }
    }
    
    function createWhoopChartData() {
      if (whoopData.value.length === 0 || selectedWhoopMetrics.value.length === 0) {
        return { datasets: [] }
      }
      
      const labels = whoopData.value.map(d => formatDateForChart(d.date))
      const colors = generateDatasetColors(selectedWhoopMetrics.value.length)
      
      const metricLabels = {
        'recovery_score': 'Recovery Score (%)',
        'sleep_score': 'Sleep Performance (%)',
        'hrv_score': 'HRV (ms)',
        'whoop_multiplier': 'WHOOP Multiplier'
      }
      
      const datasets = selectedWhoopMetrics.value.map((metric, index) => {
        let data = whoopData.value.map(d => {
          const value = d[metric]
          // Normalize HRV to percentage scale for better visualization
          if (metric === 'hrv_score' && value) {
            return Math.min(value, 100) // Cap HRV display at 100 for chart scaling
          }
          // Keep multiplier in original scale for secondary axis
          return value
        })
        
        const dataset = {
          label: metricLabels[metric],
          data,
          borderColor: colors[index],
          backgroundColor: colors[index] + '20',
          borderWidth: 2,
          fill: false,
          tension: 0.1
        }
        
        // Assign multiplier to secondary y-axis
        if (metric === 'whoop_multiplier') {
          dataset.yAxisID = 'y1'
        }
        
        return dataset
      })
      
      return { labels, datasets }
    }
    
    function calculateMovingAverage(data, window) {
      const result = []
      for (let i = 0; i < data.length; i++) {
        if (i < window - 1) {
          result.push(null)
        } else {
          const sum = data.slice(i - window + 1, i + 1).reduce((a, b) => a + b, 0)
          result.push(sum / window)
        }
      }
      return result
    }
    
    async function loadData() {
      loading.value = true
      error.value = ''
      
      try {
        // Load daily scores
        const scores = await getDailyScores(null, null, dayRange.value)
        dailyScores.value = scores.sort((a, b) => new Date(a.date) - new Date(b.date))
        
        // Load habits
        const habitsData = await getHabits()
        habits.value = habitsData
        
        // Initialize selected habits if none selected
        if (selectedHabits.value.length === 0 && habitsData.length > 0) {
          selectedHabits.value = habitsData.slice(0, 3).map(h => h.id)
        }
        
        // Load habit performance data
        await loadHabitData()
        
        // Load WHOOP data
        await loadWhoopData()
        
      } catch (err) {
        error.value = `Failed to load chart data: ${err.message}`
      } finally {
        loading.value = false
      }
    }
    
    async function loadHabitData() {
      try {
        for (const habit of habits.value) {
          const performance = await getHabitPerformance(habit.id, dayRange.value)
          habitScores[habit.id] = performance.sort((a, b) => new Date(a.date) - new Date(b.date))
        }
      } catch (err) {
        console.error('Failed to load habit data:', err)
      }
    }
    
    async function loadWhoopData() {
      try {
        const data = await getWhoopData(null, null, dayRange.value)
        whoopData.value = data.sort((a, b) => new Date(a.date) - new Date(b.date))
        chartKey.value++ // Force chart re-render
      } catch (err) {
        console.error('Failed to load WHOOP data:', err)
        // Don't show error to user if WHOOP data fails - it's optional
      }
    }
    
    function updateChart() {
      chartKey.value++ // Force chart re-render
    }
    
    // Watch for day range changes
    watch(dayRange, loadData)
    
    // Watch for WHOOP metrics selection changes
    watch(selectedWhoopMetrics, () => {
      if (selectedView.value === 'whoop') {
        chartKey.value++
      }
    }, { deep: true })
    
    onMounted(loadData)
    
    return {
      selectedView,
      dayRange,
      loading,
      error,
      showMovingAverage,
      showWhoopData,
      selectedHabits,
      selectedWhoopMetrics,
      habits,
      statistics,
      trendClass,
      chartData,
      chartOptions,
      chartKey,
      loadData,
      updateChart
    }
  }
}
</script>

<style scoped>
.progress-chart {
  max-width: 1200px;
  margin: 0 auto;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.chart-header h2 {
  color: #2c3e50;
  margin: 0;
}

.chart-controls {
  display: flex;
  gap: 2rem;
  align-items: center;
  flex-wrap: wrap;
}

.view-toggle, .date-range {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.view-toggle label, .date-range label {
  font-weight: 500;
  color: #495057;
}

.view-toggle select, .date-range select {
  padding: 0.5rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  background: white;
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

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
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

.error-message {
  margin-bottom: 1rem;
}

.retry-btn {
  background: #dc3545;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}

.chart-container {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 2rem;
  margin-bottom: 2rem;
}

.chart-wrapper {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  height: 400px;
}

.stats-panel {
  display: flex;
  flex-direction: column;
}

.stat-card {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.stat-card h3 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
  font-size: 1.1rem;
}

.stats-grid {
  display: grid;
  gap: 1rem;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 6px;
}

.stat-label {
  font-size: 0.9rem;
  color: #6c757d;
}

.stat-value {
  font-weight: 600;
  font-size: 1rem;
}

.trend-positive {
  color: #28a745;
}

.trend-negative {
  color: #dc3545;
}

.trend-neutral {
  color: #6c757d;
}

.habit-selector, .whoop-selector {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-bottom: 2rem;
}

.habit-selector h3, .whoop-selector h3 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
}

.habit-checkboxes, .whoop-checkboxes {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.habit-checkbox, .whoop-checkbox {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.habit-checkbox input, .whoop-checkbox input {
  width: 1.2rem;
  height: 1.2rem;
}

.habit-checkbox label, .whoop-checkbox label {
  cursor: pointer;
  color: #495057;
}

.chart-options {
  display: flex;
  gap: 2rem;
  flex-wrap: wrap;
  background: white;
  padding: 1rem 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.option-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.option-group input {
  width: 1.1rem;
  height: 1.1rem;
}

.option-group label {
  cursor: pointer;
  color: #495057;
  font-size: 0.9rem;
}

@media (max-width: 768px) {
  .chart-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .chart-controls {
    justify-content: space-between;
  }
  
  .chart-container {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .habit-checkboxes {
    grid-template-columns: 1fr;
  }
  
  .chart-options {
    flex-direction: column;
    gap: 1rem;
  }
}
</style>
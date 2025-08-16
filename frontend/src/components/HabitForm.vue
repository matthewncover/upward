<template>
  <div class="habit-form">
    <div class="form-header">
      <h2>Daily Habit Entry</h2>
      <div class="date-selector">
        <label for="entry-date">Date:</label>
        <input 
          id="entry-date" 
          type="date" 
          v-model="selectedDate"
          :max="today"
          @change="loadEntriesForDate"
        >
      </div>
    </div>

    <div v-if="loading" class="loading">Loading habits...</div>
    
    <div v-else-if="error" class="error">
      {{ error }}
      <button @click="loadHabits" class="retry-btn">Retry</button>
    </div>

    <div v-else class="habits-container">
      <div v-for="habit in habits" :key="habit.id" class="habit-card">
        <div class="habit-header">
          <h3>{{ habit.name }}</h3>
          <div class="habit-type">{{ getHabitTypeLabel(habit.habit_type) }}</div>
        </div>
        
        <div class="habit-input">
          <label :for="`habit-${habit.id}`">
            {{ getInputLabel(habit) }}
          </label>
          
          <!-- Binary habit (checkbox + quick buttons) -->
          <div v-if="habit.habit_type === 'binary'" class="binary-input">
            <input 
              :id="`habit-${habit.id}`"
              type="checkbox" 
              :checked="entries[habit.id] === 1"
              @change="updateEntry(habit.id, $event.target.checked ? 1 : 0)"
            >
            <label :for="`habit-${habit.id}`" class="checkbox-label">Completed</label>
            
            <!-- Quick buttons for binary -->
            <div class="quick-buttons">
              <button 
                type="button"
                class="quick-btn"
                :class="{ active: entries[habit.id] === 0 }"
                @click="setQuickValue(habit.id, 0)"
              >
                No
              </button>
              <button 
                type="button"
                class="quick-btn"
                :class="{ active: entries[habit.id] === 1 }"
                @click="setQuickValue(habit.id, 1)"
              >
                Yes
              </button>
            </div>
          </div>
          
          <!-- Duration or Pages habit (number input + quick buttons) -->
          <div v-else class="number-input">
            <div class="input-row">
              <input 
                :id="`habit-${habit.id}`"
                type="number" 
                :min="0"
                :step="habit.habit_type === 'duration' || habit.habit_type === 'reps' ? 1 : 0.1"
                v-model.number="entries[habit.id]"
                @input="updateEntry(habit.id, entries[habit.id] || 0)"
                :placeholder="getPlaceholder(habit)"
              >
              <span class="input-unit">{{ getUnit(habit.habit_type) }}</span>
            </div>
            
            <!-- Quick buttons for numeric values -->
            <div class="quick-buttons">
              <button 
                type="button"
                class="quick-btn"
                :class="{ active: isButtonActive(habit, entries[habit.id] || 0, 'zero') }"
                @click="setQuickValue(habit.id, habit.is_inverted ? (habit.zero_threshold || 0) : 0)"
              >
                Zero
              </button>
              <button 
                type="button"
                class="quick-btn"
                :class="{ active: isButtonActive(habit, entries[habit.id] || 0, 'nonzero') }"
                @click="setQuickValue(habit.id, habit.nonzero_threshold)"
              >
                Nonzero
              </button>
              <button 
                type="button"
                class="quick-btn"
                :class="{ active: isButtonActive(habit, entries[habit.id] || 0, 'goal') }"
                @click="setQuickValue(habit.id, habit.goal_threshold)"
              >
                Goal
              </button>
              <button 
                type="button"
                class="quick-btn"
                :class="{ active: isButtonActive(habit, entries[habit.id] || 0, 'stretch') }"
                @click="setQuickValue(habit.id, habit.stretch_threshold)"
              >
                Stretch
              </button>
            </div>
          </div>
        </div>
        
        <!-- Progress indicators -->
        <div class="progress-indicators">
          <div class="thresholds">
            <div class="threshold" :class="{ active: getScore(habit, entries[habit.id] || 0) >= 0.3 }">
              <span class="label">Nonzero</span>
              <span class="value">{{ formatThreshold(habit, habit.nonzero_threshold) }}</span>
            </div>
            <div class="threshold" :class="{ active: getScore(habit, entries[habit.id] || 0) >= 1.0 }">
              <span class="label">Goal</span>
              <span class="value">{{ formatThreshold(habit, habit.goal_threshold) }}</span>
            </div>
            <div class="threshold" :class="{ active: getScore(habit, entries[habit.id] || 0) >= 1.5 }">
              <span class="label">Stretch</span>
              <span class="value">{{ formatThreshold(habit, habit.stretch_threshold) }}</span>
            </div>
          </div>
          
          <!-- Weekly progress -->
          <div class="weekly-progress" v-if="weeklyProgress[habit.id]">
            <span class="progress-text">
              This week: {{ weeklyProgress[habit.id].completed }}/{{ habit.target_days_per_week }} days
            </span>
            <div class="progress-bar">
              <div 
                class="progress-fill" 
                :style="{ width: `${(weeklyProgress[habit.id].completed / habit.target_days_per_week) * 100}%` }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Summary section -->
    <div v-if="!loading && habits.length > 0" class="summary">
      <div class="daily-summary">
        <h3>Today's Summary</h3>
        <div class="summary-stats">
          <div class="stat">
            <span class="label">Habits Completed:</span>
            <span class="value">{{ completedHabits }}/{{ habits.length }}</span>
          </div>
          <div class="stat">
            <span class="label">Estimated Score:</span>
            <span class="value">{{ estimatedScore.toFixed(2) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Action buttons -->
    <div class="form-actions">
      <button @click="saveAllEntries" :disabled="saving || !hasChanges" class="save-btn">
        {{ saving ? 'Saving...' : 'Save All Entries' }}
      </button>
      <button @click="clearAll" class="clear-btn">Clear All</button>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { 
  getHabits, 
  getHabitEntries, 
  createHabitEntriesBatch,
  getWeeklyProgress,
  formatDate 
} from '../services/api.js'

export default {
  name: 'HabitForm',
  setup() {
    const habits = ref([])
    const entries = reactive({})
    const originalEntries = reactive({})
    const weeklyProgress = reactive({})
    const selectedDate = ref(formatDate(new Date()))
    const today = formatDate(new Date())
    const loading = ref(false)
    const saving = ref(false)
    const error = ref('')

    const hasChanges = computed(() => {
      return Object.keys(entries).some(habitId => 
        entries[habitId] !== originalEntries[habitId]
      )
    })

    const completedHabits = computed(() => {
      return Object.values(entries).filter(value => value > 0).length
    })

    const estimatedScore = computed(() => {
      if (habits.value.length === 0) return 0
      
      let totalScore = 0
      let totalWeight = 0
      
      habits.value.forEach(habit => {
        const value = entries[habit.id] || 0
        const score = getScore(habit, value)
        totalScore += score * habit.weight
        totalWeight += habit.weight
      })
      
      return totalWeight > 0 ? totalScore / totalWeight : 0
    })

    function getScore(habit, value) {
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

    function getHabitTypeLabel(type) {
      const labels = {
        'duration': 'Minutes',
        'pages': 'Pages',
        'binary': 'Yes/No',
        'reps': 'Reps'
      }
      return labels[type] || type
    }

    function getInputLabel(habit) {
      if (habit.habit_type === 'binary') {
        return 'Did you complete this activity?'
      } else if (habit.habit_type === 'duration') {
        return `How many minutes of ${habit.name.toLowerCase()}?`
      } else if (habit.habit_type === 'pages') {
        return `How many pages did you read?`
      } else if (habit.habit_type === 'reps') {
        return `How many ${habit.name.toLowerCase()}?`
      }
      return `Enter value for ${habit.name}`
    }

    function getPlaceholder(habit) {
      return `Goal: ${habit.goal_threshold} ${getUnit(habit.habit_type)}`
    }

    function getUnit(type) {
      const units = {
        'duration': 'min',
        'pages': 'pages',
        'binary': '',
        'reps': 'reps'
      }
      return units[type] || ''
    }

    function formatThreshold(habit, threshold) {
      if (habit.habit_type === 'binary') {
        return threshold > 0 ? 'Yes' : 'No'
      }
      return `${threshold}${getUnit(habit.habit_type)}`
    }

    async function loadHabits() {
      loading.value = true
      error.value = ''
      
      try {
        const habitData = await getHabits()
        habits.value = habitData
        
        // Initialize entries
        habitData.forEach(habit => {
          if (!(habit.id in entries)) {
            entries[habit.id] = 0
            originalEntries[habit.id] = 0
          }
        })
        
        // Load existing entries for selected date
        await loadEntriesForDate()
        
        // Load weekly progress
        await loadWeeklyProgress()
        
      } catch (err) {
        error.value = `Failed to load habits: ${err.message}`
      } finally {
        loading.value = false
      }
    }

    async function loadEntriesForDate() {
      try {
        const existingEntries = await getHabitEntries(selectedDate.value)
        
        // Reset all entries to 0 first
        habits.value.forEach(habit => {
          entries[habit.id] = 0
          originalEntries[habit.id] = 0
        })
        
        // Set existing values
        existingEntries.forEach(entry => {
          entries[entry.habit_id] = entry.value
          originalEntries[entry.habit_id] = entry.value
        })
        
      } catch (err) {
        error.value = `Failed to load entries: ${err.message}`
      }
    }

    async function loadWeeklyProgress() {
      try {
        const progress = await getWeeklyProgress()
        
        // Convert API response format (by habit name) to our format (by habit id)
        for (const habit of habits.value) {
          const habitProgress = progress[habit.name]
          if (habitProgress) {
            weeklyProgress[habit.id] = {
              completed: habitProgress.completed_days,
              target: habitProgress.target_days
            }
          } else {
            // No data for this habit
            weeklyProgress[habit.id] = {
              completed: 0,
              target: habit.target_days_per_week
            }
          }
        }
      } catch (err) {
        console.error('Failed to load weekly progress:', err)
        // Fallback to empty progress
        for (const habit of habits.value) {
          weeklyProgress[habit.id] = {
            completed: 0,
            target: habit.target_days_per_week
          }
        }
      }
    }

    async function updateEntry(habitId, value) {
      entries[habitId] = value
      // Auto-save individual entries could be implemented here
    }

    function setQuickValue(habitId, value) {
      const habit = habits.value.find(h => h.id === habitId)
      console.log(`Setting quick value for ${habit?.name}: ${value}`, habit)
      entries[habitId] = value
      updateEntry(habitId, value)
    }

    async function saveAllEntries() {
      saving.value = true
      
      try {
        const entriesToSave = Object.entries(entries)
          .filter(([habitId, value]) => value !== originalEntries[habitId])
          .map(([habitId, value]) => ({
            habit_id: parseInt(habitId),
            date: selectedDate.value,
            value: value || 0
          }))
        
        if (entriesToSave.length === 0) {
          return
        }
        
        await createHabitEntriesBatch(entriesToSave)
        
        // Update original entries to reflect saved state
        Object.assign(originalEntries, entries)
        
        // Refresh weekly progress
        await loadWeeklyProgress()
        
      } catch (err) {
        error.value = `Failed to save entries: ${err.message}`
      } finally {
        saving.value = false
      }
    }

    function clearAll() {
      habits.value.forEach(habit => {
        entries[habit.id] = 0
      })
    }

    function getActiveButtonLevel(habit, value) {
      const score = getScore(habit, value)
      if (score >= 1.5) return 'stretch'
      if (score >= 1.0) return 'goal'  
      if (score >= 0.3) return 'nonzero'
      return 'zero'
    }

    function isButtonActive(habit, value, buttonType) {
      if (buttonType === 'zero') {
        // Zero button is active only when the value equals what clicking Zero would set
        return value === (habit.is_inverted ? (habit.zero_threshold || 0) : 0)
      }
      // Other buttons are active based on the performance level achieved
      return getActiveButtonLevel(habit, value) === buttonType
    }

    // Watch for date changes
    watch(selectedDate, loadEntriesForDate)

    onMounted(loadHabits)

    return {
      habits,
      entries,
      weeklyProgress,
      selectedDate,
      today,
      loading,
      saving,
      error,
      hasChanges,
      completedHabits,
      estimatedScore,
      getScore,
      getHabitTypeLabel,
      getInputLabel,
      getPlaceholder,
      getUnit,
      formatThreshold,
      loadHabits,
      loadEntriesForDate,
      updateEntry,
      setQuickValue,
      saveAllEntries,
      clearAll,
      getActiveButtonLevel,
      isButtonActive
    }
  }
}
</script>

<style scoped>
.habit-form {
  max-width: 800px;
  margin: 0 auto;
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.form-header h2 {
  color: #2c3e50;
  margin: 0;
}

.date-selector {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.date-selector label {
  font-weight: 500;
}

.date-selector input {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.loading, .error {
  text-align: center;
  padding: 2rem;
  border-radius: 8px;
  margin: 2rem 0;
}

.loading {
  background: #f8f9fa;
  color: #6c757d;
}

.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.retry-btn {
  background: #dc3545;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  margin-left: 1rem;
  cursor: pointer;
}

.habits-container {
  display: grid;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.habit-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  border: 1px solid #e9ecef;
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

.habit-type {
  background: #e9ecef;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.8rem;
  color: #6c757d;
}

.habit-input {
  margin-bottom: 1rem;
}

.habit-input label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #495057;
}

.binary-input {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.binary-input > div:first-child {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.binary-input input[type="checkbox"] {
  width: 1.2rem;
  height: 1.2rem;
}

.checkbox-label {
  margin: 0 !important;
  cursor: pointer;
}

.number-input {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.input-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.number-input input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 1rem;
}

.input-unit {
  color: #6c757d;
  font-size: 0.9rem;
  min-width: 3rem;
}

.quick-buttons {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.quick-btn {
  padding: 0.5rem 0.75rem;
  border: 1px solid #dee2e6;
  background: #f8f9fa;
  color: #6c757d;
  border-radius: 4px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 60px;
}

.quick-btn:hover {
  background: #e9ecef;
  border-color: #adb5bd;
}

.quick-btn.active {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.quick-btn.active:hover {
  background: #0056b3;
  border-color: #0056b3;
}

.progress-indicators {
  border-top: 1px solid #e9ecef;
  padding-top: 1rem;
}

.thresholds {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.threshold {
  flex: 1;
  text-align: center;
  padding: 0.5rem;
  border-radius: 4px;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  transition: all 0.3s;
}

.threshold.active {
  background: #d4edda;
  border-color: #c3e6cb;
  color: #155724;
}

.threshold .label {
  display: block;
  font-size: 0.8rem;
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.threshold .value {
  display: block;
  font-size: 0.9rem;
}

.weekly-progress {
  margin-top: 0.5rem;
}

.progress-text {
  display: block;
  font-size: 0.9rem;
  color: #6c757d;
  margin-bottom: 0.25rem;
}

.progress-bar {
  height: 6px;
  background: #e9ecef;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #28a745;
  border-radius: 3px;
  transition: width 0.3s;
}

.summary {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.summary h3 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
}

.summary-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.stat {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 4px;
}

.stat .label {
  font-weight: 500;
  color: #495057;
}

.stat .value {
  font-weight: 600;
  color: #2c3e50;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
}

.save-btn, .clear-btn {
  padding: 0.75rem 2rem;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.save-btn {
  background: #28a745;
  color: white;
}

.save-btn:hover:not(:disabled) {
  background: #218838;
}

.save-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.clear-btn {
  background: #6c757d;
  color: white;
}

.clear-btn:hover {
  background: #545b62;
}

@media (max-width: 768px) {
  .form-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .thresholds {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .summary-stats {
    grid-template-columns: 1fr;
  }
  
  .form-actions {
    flex-direction: column;
  }
  
  .save-btn, .clear-btn {
    width: 100%;
  }
}
</style>
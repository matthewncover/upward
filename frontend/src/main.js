import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import HabitForm from './components/HabitForm.vue'
import ProgressChart from './components/ProgressChart.vue'
import WeeklyProgress from './components/WeeklyProgress.vue'

const routes = [
  { path: '/', component: HabitForm },
  { path: '/progress', component: ProgressChart },
  { path: '/weekly', component: WeeklyProgress }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const app = createApp(App)
app.use(router)
app.mount('#app')
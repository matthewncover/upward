import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

export const defaultChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    intersect: false,
    mode: 'index'
  },
  plugins: {
    legend: {
      position: 'top',
      labels: {
        usePointStyle: true,
        padding: 20
      }
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      titleColor: 'white',
      bodyColor: 'white',
      borderColor: '#ddd',
      borderWidth: 1,
      cornerRadius: 6,
      displayColors: true,
      callbacks: {
        title: (tooltipItems) => {
          const date = new Date(tooltipItems[0].label)
          return date.toLocaleDateString('en-US', { 
            weekday: 'long', 
            month: 'short', 
            day: 'numeric' 
          })
        }
      }
    }
  },
  scales: {
    x: {
      display: true,
      title: {
        display: true,
        text: 'Date'
      },
      grid: {
        color: 'rgba(0, 0, 0, 0.1)'
      }
    },
    y: {
      display: true,
      title: {
        display: true,
        text: 'Score'
      },
      grid: {
        color: 'rgba(0, 0, 0, 0.1)'
      },
      beginAtZero: true
    }
  }
}

export const scoreChartConfig = {
  ...defaultChartOptions,
  plugins: {
    ...defaultChartOptions.plugins,
    title: {
      display: true,
      text: 'Daily Progress Scores',
      font: {
        size: 16,
        weight: 'bold'
      },
      padding: 20
    }
  }
}

export const cumulativeChartConfig = {
  ...defaultChartOptions,
  plugins: {
    ...defaultChartOptions.plugins,
    title: {
      display: true,
      text: 'Cumulative Score Progress',
      font: {
        size: 16,
        weight: 'bold'
      },
      padding: 20
    }
  },
  scales: {
    ...defaultChartOptions.scales,
    y: {
      ...defaultChartOptions.scales.y,
      title: {
        display: true,
        text: 'Cumulative Score'
      }
    }
  }
}

export const habitChartConfig = {
  ...defaultChartOptions,
  plugins: {
    ...defaultChartOptions.plugins,
    title: {
      display: true,
      text: 'Individual Habit Performance',
      font: {
        size: 16,
        weight: 'bold'
      },
      padding: 20
    }
  },
  scales: {
    ...defaultChartOptions.scales,
    y: {
      ...defaultChartOptions.scales.y,
      title: {
        display: true,
        text: 'Habit Score'
      },
      max: 2.0 // Cap at 2.0 for habit scores
    }
  }
}

// Color palette for consistent theming
export const chartColors = {
  primary: '#3498db',
  secondary: '#2ecc71',
  accent: '#e74c3c',
  warning: '#f39c12',
  info: '#9b59b6',
  success: '#27ae60',
  light: '#ecf0f1',
  dark: '#2c3e50'
}

// Generate colors for multiple datasets
export function generateDatasetColors(count) {
  const colors = [
    chartColors.primary,
    chartColors.secondary,
    chartColors.accent,
    chartColors.warning,
    chartColors.info,
    chartColors.success,
    '#16a085',
    '#8e44ad',
    '#d35400',
    '#c0392b'
  ]
  
  const result = []
  for (let i = 0; i < count; i++) {
    result.push(colors[i % colors.length])
  }
  return result
}

// Helper function to format dates for chart labels
export function formatDateForChart(dateString) {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

// Helper function to create gradient backgrounds
export function createGradient(ctx, color) {
  const gradient = ctx.createLinearGradient(0, 0, 0, 400)
  gradient.addColorStop(0, `${color}40`) // 25% opacity
  gradient.addColorStop(1, `${color}10`) // 6% opacity
  return gradient
}
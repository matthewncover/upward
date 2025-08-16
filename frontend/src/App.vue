<template>
  <div id="app">
    <nav class="navbar">
      <div class="nav-brand">
        <h1>Upward</h1>
      </div>
      <div class="nav-links">
        <router-link to="/" class="nav-link">Daily Entry</router-link>
        <router-link to="/progress" class="nav-link">Progress</router-link>
        <router-link to="/weekly" class="nav-link">Weekly</router-link>
      </div>
    </nav>
    
    <main class="main-content">
      <router-view></router-view>
    </main>
    
    <!-- WHOOP status section - positioned in bottom right -->
    <div class="whoop-section">
      <div v-if="connectionStatus.connected" class="whoop-connected">
        <span class="whoop-icon">💚</span>
        <span class="whoop-text">WHOOP Connected</span>
      </div>
      <button 
        v-else 
        @click="connectWhoop" 
        :disabled="connectionStatus.loading" 
        class="whoop-connect-btn"
      >
        <span v-if="connectionStatus.loading">Connecting...</span>
        <span v-else>
          <span class="whoop-icon">🔗</span>
          Connect WHOOP
        </span>
      </button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { checkWhoopStatus, connectWhoop as apiConnectWhoop } from './services/api.js'

export default {
  name: 'App',
  setup() {
    const connectionStatus = ref({
      connected: false,
      loading: false,
      showWhoopButton: true
    })

    const checkWhoopConnection = async () => {
      try {
        const status = await checkWhoopStatus()
        connectionStatus.value.connected = status.connected
      } catch (error) {
        console.error('Error checking WHOOP status:', error)
      }
    }

    const connectWhoop = async () => {
      connectionStatus.value.loading = true
      try {
        const result = await apiConnectWhoop()
        if (result.auth_url) {
          window.location.href = result.auth_url
        }
      } catch (error) {
        console.error('Error connecting to WHOOP:', error)
      } finally {
        connectionStatus.value.loading = false
      }
    }

    onMounted(() => {
      checkWhoopConnection()
      
      // Check if we just returned from WHOOP OAuth
      const urlParams = new URLSearchParams(window.location.search)
      if (urlParams.get('whoop_connected') === 'true') {
        connectionStatus.value.connected = true
        // Clean up URL
        window.history.replaceState({}, document.title, window.location.pathname)
      }
    })

    return {
      connectionStatus,
      connectWhoop
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  line-height: 1.6;
  color: #333;
  background-color: #f5f5f5;
}

#app {
  min-height: 100vh;
}

.navbar {
  background: #2c3e50;
  color: white;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.nav-brand h1 {
  font-size: 1.5rem;
  font-weight: 600;
}

.nav-links {
  display: flex;
  gap: 2rem;
}

.nav-link {
  color: white;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.nav-link:hover,
.nav-link.router-link-active {
  background-color: #34495e;
}

.main-content {
  max-width: 1200px;
  margin: 2rem auto;
  padding: 0 2rem;
}

.whoop-section {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  z-index: 1000;
}

.whoop-connected {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(39, 174, 96, 0.1);
  color: #27ae60;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  border: 1px solid rgba(39, 174, 96, 0.3);
  backdrop-filter: blur(10px);
}

.whoop-connect-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #e74c3c;
  color: white;
  border: none;
  padding: 0.75rem 1.25rem;
  border-radius: 8px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 2px 8px rgba(231, 76, 60, 0.3);
}

.whoop-connect-btn:hover:not(:disabled) {
  background: #c0392b;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(231, 76, 60, 0.4);
}

.whoop-connect-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.whoop-icon {
  font-size: 1rem;
}

@media (max-width: 768px) {
  .navbar {
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
  }
  
  .nav-links {
    gap: 1rem;
  }
  
  .main-content {
    padding: 0 1rem;
    margin: 1rem auto;
  }
  
  .whoop-section {
    position: fixed;
    bottom: 1rem;
    right: 1rem;
    left: 1rem;
  }
  
  .whoop-connected,
  .whoop-connect-btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  server: {
    host: '0.0.0.0', // Bind to all network interfaces
    allowedHosts: true, // Allow all hostnames (use with caution)
  },
  plugins: [react()],
})

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/upload': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
      '/chat': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      }
    }
  }
})
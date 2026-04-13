import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    allowedHosts: true,
    proxy: {
      '/api': process.env.VITE_API_HOST || 'http://localhost:8000',
      '/asp': process.env.VITE_API_HOST || 'http://localhost:8000',
      '/health': process.env.VITE_API_HOST || 'http://localhost:8000',
      '/auth': process.env.VITE_API_HOST || 'http://localhost:8000',
    }
  },
  build: {
    outDir: '../static',
    emptyOutDir: true,
  }
})

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../mybackend/frontend_build',
    emptyOutDir: true,
    manifest: 'manifest.json',
    rollupOptions: {
      input: 'src/main.jsx',
    },
  },
  base: "/static/",
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})

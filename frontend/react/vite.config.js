import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: { outDir: '../../static-react', emptyOutDir: true },
  server: {
    proxy: {
      '/health': 'http://localhost:8100',
      '/metrics': 'http://localhost:8100',
      '/predict': 'http://localhost:8100',
      '/dropdown-values': 'http://localhost:8100'
    }
  }
})

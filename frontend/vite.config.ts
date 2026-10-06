import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Mode data FE (lihat .env.example):
//   VITE_API_MODE=mock → baca ../contract/examples langsung, tanpa backend
//   VITE_API_MODE=api  → panggil backend lewat proxy /api → http://localhost:8000
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(import.meta.dirname, './src'),
      '@contract': path.resolve(import.meta.dirname, '../contract'),
    },
  },
  server: {
    fs: { allow: ['..'] },
    proxy: { '/api': 'http://localhost:8000' },
  },
})

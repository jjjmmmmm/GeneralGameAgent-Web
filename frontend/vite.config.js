import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 开发代理：前端访问 /api 转发到 FastAPI（避免跨域与 CORS 配置）
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})

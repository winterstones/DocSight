import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"
import { TanStackRouterVite } from "@tanstack/router-plugin/vite"

export default defineConfig({
  plugins: [
    // TanStack Router génère les routes automatiquement depuis src/routes/
    TanStackRouterVite(),
    react(),
  ],
  server: {
    port: 5173,
    host: true,
    proxy: {
      // Proxy des appels API vers Django en dev
      "/api": {
        target:       "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/mocks/setup.ts',
  },
})

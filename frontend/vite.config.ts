import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
  server: {
    proxy: {
      // Proxy /api/v1 requests to the backend server
      '/api/v1': {
        target: 'http://localhost:8000', // Your backend server address
        changeOrigin: true, // Needed for virtual hosted sites
        // You might not need rewrite if your backend already expects /api/v1
        // rewrite: (path) => path.replace(/^\/api\/v1/, '')
      }
    }
  }
});

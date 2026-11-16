import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig(({ command }) => ({
  plugins: [react()],
  // On GitHub Pages the repo is served at /SchedX_OS_project-/
  // In local dev (command === 'serve') use '/' so the proxy still works.
  base: command === 'serve' ? '/' : '/SchedX_OS_project-/',
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
}));

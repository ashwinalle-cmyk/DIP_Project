import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { defineConfig, loadEnv } from 'vite';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '');

  return {
    plugins: [react(), tailwindcss()],

    define: {
      'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY),
    },

    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      },
    },

    server: {
      host: '127.0.0.1',   // ✅ FIX: stable localhost binding
      port: 5173,          // ✅ FIX: explicit port
      strictPort: true,    // ✅ prevents random port issues

      hmr: false,          // ✅ disables WebSocket (fixes your error)

      watch: {
        usePolling: true,  // ✅ improves reliability (important)
      },
    },
  };
});
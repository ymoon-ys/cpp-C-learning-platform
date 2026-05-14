import { defineConfig } from 'vite';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export default defineConfig({
  build: {
    outDir: resolve(__dirname, 'static/dist'),
    emptyOutDir: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'static/src/js/main.js')
      },
      output: {
        entryFileNames: 'assets/[name].js',
        chunkFileNames: 'assets/[name].js',
        assetFileNames: 'assets/[name][extname]'
      }
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/auth': 'http://localhost:5001',
      '/admin': 'http://localhost:5001',
      '/teacher': 'http://localhost:5001',
      '/student': 'http://localhost:5001',
      '/course': 'http://localhost:5001',
      '/ai': 'http://localhost:5001',
      '/community': 'http://localhost:5001'
    }
  },
  css: {
    preprocessorOptions: {
      scss: {}
    }
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'static/src'),
      '@scss': resolve(__dirname, 'static/src/scss')
    }
  }
});

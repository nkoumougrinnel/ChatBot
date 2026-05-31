import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { visualizer } from 'rollup-plugin-visualizer'
export default defineConfig({
plugins: [
react(),
visualizer({ open: false, filename: 'dist/stats.html' })
],
build: {
rollupOptions: {
output: {
    manualChunks: {
vendor: ['react', 'react-dom', 'react-router-dom'],
http: ['axios'],
}
}
},
minify: 'esbuild', // Plus rapide que terser
sourcemap: false, // Désactiver en production
chunkSizeWarningLimit: 500,
},
server: {
port: 3000,
proxy: {
'/api': 'http://localhost:8000' // Dev local uniquement
}
}
})
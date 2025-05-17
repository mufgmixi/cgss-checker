// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  base: '/cgss-checker/',
  publicDir: 'public',
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      injectRegister: 'auto',
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,json,vue,txt,woff2}']
      },
      manifest: {
        name: 'デレステカードチェッカー',
        short_name: 'CGSSChecker',
        description: 'アイドルマスターシンデレラガールズ スターライトステージのカードチェッカー',
        theme_color: '#1890ff',
        background_color: '#ffffff',
        display: 'standalone',
        scope: '/cgss-checker/',
        start_url: '/cgss-checker/',
        icons: [
          {
            src: 'cgss_checker.png',
            sizes: '1024x1024',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          },
          {
            src: 'pwa-maskable-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable'
          }
        ]
      }
    })
  ]
})

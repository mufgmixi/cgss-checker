// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa' // インポート

export default defineConfig({
  base: '/cgss-checker/', // ★★★ あなたのリポジトリ名に合わせてください ★★★
  publicDir: 'public', // ← 明示的に必要
  plugins: [
    vue(),
    VitePWA({ // PWAプラグインの設定
      registerType: 'autoUpdate', // 自動更新を推奨
      injectRegister: 'auto',
      workbox: { // Service Workerの生成設定 (詳細はドキュメント参照)
        globPatterns: ['**/*.{js,css,html,ico,png,svg,json,vue,txt,woff2}']
      },
      manifest: { // アプリのマニフェスト情報
        name: 'デレステカードチェッカー',
        short_name: 'CGSSChecker',
        description: 'アイドルマスターシンデレラガールズ スターライトステージのカードチェッカー',
        theme_color: '#1890ff', // アプリのテーマカラー
        background_color: '#ffffff', // スプラッシュスクリーンの背景色
        display: 'standalone', // アプリのように表示
        scope: '/cgss-checker/',
        start_url: '/cgss-checker/',
        icons: [
          {
            src: 'cgss_checker.png', // public/cgss_checker.png を指す
            sizes: '1024x1024', // 画像の実際のサイズに合わせてください
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png', // 例: public/pwa-512x512.png
            sizes: '512x512',
            type: 'image/png'
          },
          { // マスク可能なアイコン (オプション)
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
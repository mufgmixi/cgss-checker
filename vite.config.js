// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'
// import path from 'path' // root を指定しない場合は不要

export default defineConfig({
  // GitHub Pagesにデプロイする場合のベースパス (例: /リポジトリ名/)
  base: '/cgss-checker/', // ★★★ あなたのリポジトリ名に合わせてください ★★★

  // publicDir はデフォルトで 'public' なので、通常は指定不要
  // publicDir: 'public',

  // serverオプションはローカル開発用なので、デプロイ時には直接影響しません
  // server: {
  //   host: true,
  //   port: 8080
  // },

  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate', // Service Workerの更新戦略 (自動更新を推奨)
      injectRegister: 'auto',    // Service Workerを登録するスクリプトを自動で挿入
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,json,vue,txt,woff2}'], // キャッシュするファイルのパターン
        // runtimeCaching: [ ... ] // 必要に応じて実行時のキャッシュ戦略を追加
      },
      manifest: {
        name: 'デレステカードチェッカー',
        short_name: 'CGSSChecker',
        description: 'アイドルマスターシンデレラガールズ スターライトステージのカードチェッカーです。',
        theme_color: '#69c0ff', // アプリのテーマカラー (ヘッダーの色など)
        background_color: '#0a0f1f', // スプラッシュスクリーンの背景色 (サイバーパンク風の暗い色)
        display: 'standalone', // アプリのように表示 (アドレスバーなどを隠す)
        scope: '/cgss-checker/',         // ★★★ base と合わせる ★★★
        start_url: '/cgss-checker/',       // ★★★ base と合わせる ★★★
        icons: [
          // 用意したアプリアイコンへのパス (publicフォルダからの相対パス)
          {
            src: 'pwa-192x192.png', // 例: public/pwa-192x192.png
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png', // 例: public/pwa-512x512.png
            sizes: '512x512',
            type: 'image/png'
          },
          {
            src: 'pwa-maskable-512x512.png', // 例: public/pwa-maskable-512x512.png
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable' // マスク可能アイコン
          }
          // 必要に応じて他のサイズのアイコンも追加
        ]
      }
    })
  ]
})
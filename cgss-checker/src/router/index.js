import { createRouter, createWebHistory } from 'vue-router';
import App from '../App.vue'; // メインのチェッカー画面 (あるいはリスト表示用の新しいコンポーネント)
import StarRankEditor from '../views/StarRankEditor.vue';

const routes = [
  {
    path: '/',
    name: 'CardChecker',
    component: App // App.vue をそのまま使うか、リスト表示部分を別コンポーネントに切り出す
  },
  {
    path: '/star-editor', // スターランク編集画面のパス
    name: 'StarRankEditor',
    component: StarRankEditor
  }
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
});

export default router;
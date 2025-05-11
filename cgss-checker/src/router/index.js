import { createRouter, createWebHashHistory } from 'vue-router'; // ← 修正済み
import App from '../App.vue';
import StarRankEditor from '../views/StarRankEditor.vue';

const routes = [
  {
    path: '/',
    name: 'CardChecker',
    component: App
  },
  {
    path: '/star-editor',
    name: 'StarRankEditor',
    component: StarRankEditor
  }
];

const router = createRouter({
  history: createWebHashHistory(import.meta.env.BASE_URL), // ← 修正済み
  routes
});

export default router;

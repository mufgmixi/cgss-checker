<script setup>
// import { defineProps, defineEmits } from 'vue'; // Vue 3.2.25+ ならインポート不要

const props = defineProps({
  card: {
    type: Object,
    required: true
  }
});

const emit = defineEmits(['toggle-owned']);

const handleToggleOwned = () => {
  // クリックされたら、親コンポーネントにイベントを通知するだけ
  emit('toggle-owned', props.card);
};

const onImageError = (event) => {
  // console.warn('画像読み込みエラー:', event.target.src);
  // event.target.src = '/path/to/default-image.png'; // 代替画像
};
</script>

<template>
  <!-- ▼▼▼ card-item div全体にクリックイベントを設定 ▼▼▼ -->
  <div class="card-item" :class="{ owned: card.owned }" @click="handleToggleOwned">
    <img :src="card.local_image_url" :alt="card.name" @error="onImageError" class="card-image">
    <p class="card-name">{{ card.name }}</p>
    <p class="card-attribute">属性: {{ card.attribute }}</p>
    <p class="card-rarity">レアリティ: {{ card.rarity }}</p>
    <!-- ▼▼▼ チェックボックスとラベルは削除、またはコメントアウト（視覚的な表示は背景色で行う） ▼▼▼ -->
    <!--
    <label class="owned-checkbox-label">
      <input type="checkbox" :checked="card.owned" @change="handleToggleOwned">
      所持
    </label>
    -->
    <!-- ▲▲▲ チェックボックスとラベルを削除 ▲▲▲ -->
  </div>
</template>

<style scoped>
.card-item {
  border: 1px solid #ccc;
  padding: 10px;
  text-align: center;
  background-color: #f9f9f9;
  border-radius: 8px;
  box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out, background-color 0.2s ease-in-out; /* background-colorもトランジション対象に */
  cursor: pointer; /* クリック可能であることを示すカーソル */
}
.card-item:hover {
  transform: translateY(-5px);
  box-shadow: 4px 4px 10px rgba(0,0,0,0.15);
}
.card-item.owned {
  background-color: #d4edda; /* 所持しているカードの背景色 (少し濃くする例) */
  border-color: #c3e6cb;
}
.card-image {
  max-width: 120px;
  max-height: 180px;
  object-fit: contain;
  display: block;
  margin: 0 auto 10px;
  border-radius: 4px;
  pointer-events: none; /* 画像自体へのクリックイベントを無効化し、親のdivのクリックを優先 */
}
.card-name {
  margin: 5px 0;
  font-size: 0.95em;
  font-weight: bold;
  min-height: 2.4em;
  line-height: 1.2em;
  overflow: hidden;
  text-overflow: ellipsis;
  pointer-events: none; /* テキストへのクリックイベントも無効化 */
}
.card-attribute, .card-rarity {
  margin: 3px 0;
  font-size: 0.85em;
  color: #555;
  pointer-events: none; /* テキストへのクリックイベントも無効化 */
}
/* チェックボックスラベルのスタイルは不要になったので削除またはコメントアウト */
/*
.owned-checkbox-label {
  margin-top: 10px;
  cursor: pointer;
}
*/
</style>
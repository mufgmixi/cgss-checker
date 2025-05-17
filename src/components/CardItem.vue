<script setup>
// defineProps と defineEmits は Vue 3.2.25+ で <script setup> を使う場合、
// インポートが不要になりました。もし古いバージョンをお使いの場合はインポートしてください。
// import { defineProps, defineEmits } from 'vue';

const props = defineProps({
  card: {
    type: Object,
    required: true
  }
});
const emit = defineEmits(['toggle-star-rank-basic']);
const handleCardClick = () => {
  const newStarRank = (props.card.starRank > 0) ? 0 : 1;
  emit('toggle-star-rank-basic', { cardId: props.card.id, starRank: newStarRank });
};
const onImageError = (event) => {
  console.warn('画像読み込みエラー:', event.target.src);
};
</script>

<template>
  <div
    class="card-item"
    :class="{
      owned: card.starRank > 0,
      'attr-cu': card.attribute === 'Cu',
      'attr-co': card.attribute === 'Co',
      'attr-pa': card.attribute === 'Pa',
      'attr-unknown': card.attribute === 'Unknown' || !card.attribute
    }"
    @click="handleCardClick"
  >
    <img :src="card.local_image_url" :alt="card.name" @error="onImageError" class="card-image">
    <p class="card-name">{{ card.name }}</p>
    <p class="card-attribute">属性: {{ card.attribute }}</p>
    <p class="card-rarity">レアリティ: {{ card.rarity }}</p>
    <!-- ▼▼▼ スターランク表示部分の構造を変更 ▼▼▼ -->
    <div class="star-rank-container">
      <div v-if="card.starRank > 0" class="star-rank-badge">
        <span class="star-rank-number">{{ card.starRank }}</span>
      </div>
      <p v-else class="not-owned-text">
        未所持
      </p>
    </div>
    <!-- ▲▲▲ スターランク表示部分の構造を変更 ▲▲▲ -->
  </div>
</template>

<style scoped>
.card-item {
  border: 1px solid #e0e0e0;
  padding: 10px;
  text-align: center;
  background-color: #ffffff;
  border-radius: 12px;
  box-shadow: 0 3px 6px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out, background-color 0.2s ease-in-out;
  cursor: pointer;
  overflow: hidden;
}
.card-item:hover {
  transform: translateY(-4px) scale(1.02);
  box-shadow: 0 6px 12px rgba(0,0,0,0.15);
}

/* 属性ごとのスタイルと所持状態の背景色 */
.card-item.attr-cu.owned {
  background-color: #ffe0f0; /* キュート所持: 淡いピンク */
  border-left: 5px solid #ff77aa;
}
.card-item.attr-co.owned {
  background-color: #e0f0ff; /* クール所持: 淡い水色 */
  border-left: 5px solid #77aaff;
}
.card-item.attr-pa.owned {
  background-color: #fff5e0; /* パッション所持: 淡いオレンジ */
  border-left: 5px solid #ffaa77;
}
.card-item.attr-unknown.owned { /* 属性不明でも所持は分かるように */
  background-color: #e9e9e9;
  border-left: 5px solid #aaaaaa;
}

/* 未所持の場合の属性ごとの枠線スタイル */
.card-item.attr-cu:not(.owned) { border-color: #ffc2d9; }
.card-item.attr-co:not(.owned) { border-color: #c2d9ff; }
.card-item.attr-pa:not(.owned) { border-color: #ffddc2; }
.card-item.attr-unknown:not(.owned) { border-color: #d0d0d0; }


.card-image {
  max-width: 120px;
  max-height: 180px;
  object-fit: contain;
  display: block;
  margin: 0 auto 10px;
  border-radius: 4px;
  pointer-events: none;
}

.card-name {
  margin: 5px 0;
  font-size: 0.95em;
  font-weight: 600;
  min-height: 2.4em;
  line-height: 1.2em;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #444;
  pointer-events: none;
}
.card-attribute, .card-rarity {
  margin: 3px 0;
  font-size: 0.8em;
  color: #666;
  pointer-events: none;
}

.star-rank-container {
  margin-top: 8px;
  /* ▼▼▼ バッジの高さに合わせて調整 (大きくするのであれば、このheightも調整) ▼▼▼ */
  height: 90px; /* 例: 30px * 3 = 90px */
  display: flex;
  justify-content: center;
  align-items: center;
}

.star-rank-badge {
  /* ▼▼▼ サイズを約2倍に変更 ▼▼▼ */
  width: 60px;  /* 例: 30px * 2 */
  height: 60px; /* 例: 30px * 2 */
  background-image: url('/images/star-background.svg'); /* public/images/star-background.svg に配置した場合 */
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  display: flex;
  justify-content: center;
  align-items: center;
  color: #673AB7; /* 紫色 */
  font-weight: bold;
  /* ▼▼▼ フォントサイズも約3倍に変更 ▼▼▼ */
  font-size: 1.8em; /* 例: 0.9em * 2 */
  text-shadow: 2px 2px 3px rgba(0,0,0,0.4); /* 影も少し調整 */
  line-height: 1; /* 数字が上下にはみ出ないように */
}

.star-rank-number {
  /* 数字のさらに細かい位置調整が必要な場合はここに記述 */
  /* 例: transform: translateY(2px); */
}

.not-owned-text {
  color: #aaa;
  font-style: italic;
  font-size: 0.9em; /* こちらは元のサイズのままか、少し大きくするか検討 */
  margin: 0;
}
/* ▼▼▼ スマホなどの狭い画面向けのスタイル ▼▼▼ */
@media (max-width: 768px) {
  .card-item {
    padding: 8px; /* パディングを少し狭く */
    border-radius: 10px; /* 角丸は維持または少し小さく */
  }
  .card-image {
    max-width: 100px; /* 画像サイズを少し小さく */
    max-height: 150px;
    margin-bottom: 8px;
  }
  .card-name {
    font-size: 0.9em;
    min-height: 2.2em; /* 行数に応じて調整 */
  }
  .card-attribute, .card-rarity {
    font-size: 0.75em;
  }
  .star-rank-container {
    /* height はバッジサイズに依存するので、バッジサイズが変われば調整 */
  }
  .star-rank-badge {
    /* 必要であればバッジサイズも調整 */
    /* width: 25px;
    height: 25px;
    font-size: 0.8em; */
  }
  .not-owned-text {
    font-size: 0.85em;
  }
}

@media (max-width: 480px) {
  .card-image {
    max-width: 80px;
    max-height: 120px;
  }
  .card-name {
    font-size: 0.85em;
  }
  /* ... */
}
</style>
<script setup>
import { ref, onMounted, onUnmounted, computed, defineEmits } from 'vue';
import Papa from 'papaparse';

const emit = defineEmits(['back-to-checker']);

const allCardsForEditing = ref([]);
const ownedCardsData = ref({});
const isLoading = ref(false);

const rarityMapping = {
  'ノーマル': { folder: 'N', csv: 'cgss_n_card_list.csv' },
  'レア':    { folder: 'R', csv: 'cgss_r_card_list.csv' },
  'Sレア':   { folder: 'SR', csv: 'cgss_sr_card_list.csv' },
  'SSレア':  { folder: 'SSR', csv: 'cgss_ssr_card_list.csv' }
};

const showEditorScrollToTopButton = ref(false);
const editorScrollThreshold = 200;

const handleEditorScroll = () => {
  if (window.scrollY > editorScrollThreshold) {
    showEditorScrollToTopButton.value = true;
  } else {
    showEditorScrollToTopButton.value = false;
  }
};
const scrollToEditorTop = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

async function loadAllCsvData() {
  isLoading.value = true;
  const loadedCards = [];
  const rarityKeys = Object.keys(rarityMapping);
  const baseUrl = import.meta.env.BASE_URL;
  for (const rarityKey of rarityKeys) {
    const targetRarityInfo = rarityMapping[rarityKey];
    if (!targetRarityInfo || !targetRarityInfo.csv) continue;
    const csvPath = `data/csv/${targetRarityInfo.csv}`;
    let filePath = baseUrl.endsWith('/') ? `${baseUrl}${csvPath}` : `${baseUrl}/${csvPath}`;
    if (filePath.startsWith('//')) filePath = filePath.substring(1);
    try {
      const response = await fetch(filePath);
      if (!response.ok) continue;
      const csvText = await response.text();
      const parseResult = await new Promise((resolve, reject) => {
        Papa.parse(csvText, { header: true, skipEmptyLines: true, complete: resolve, error: reject });
      });
      if (parseResult.errors && parseResult.errors.length > 0) console.warn(`[Editor] PapaParse errors for ${rarityKey}:`, parseResult.errors);
      const processedData = parseResult.data
        .filter(card => card && typeof card.id === 'string' && card.id.trim() !== '' && typeof card.name === 'string' && card.name.trim() !== '')
        .map(card => {
            const cardRarityTrimmed = String(card.rarity || '').trim();
            const currentRarityFolder = rarityMapping[cardRarityTrimmed] ? rarityMapping[cardRarityTrimmed].folder : 'unknown';
            if (!rarityMapping[cardRarityTrimmed]) console.warn(`[Editor] No rarityMapping folder for card rarity: '${cardRarityTrimmed}' ID ${card.id}`);
            const cardId = String(card.id).trim();
            let cardNameForFile = String(card.name).trim().replace(/[\\/:*?"<>|#]/g, '_');
            const filename = `${cardId}_${cardNameForFile}.jpg`;
            const imageBase = import.meta.env.BASE_URL.endsWith('/') ? import.meta.env.BASE_URL : `${import.meta.env.BASE_URL}/`;
            let localImageUrl = `${imageBase}data/images/${currentRarityFolder}/${filename}`;
            if (localImageUrl.startsWith('//')) localImageUrl = localImageUrl.substring(1);
            return {
                id: cardId, name: String(card.name).trim(), rarity: cardRarityTrimmed,
                attribute: String(card.attribute || 'Unknown').trim(),
                availability: String(card.availability || '').trim(),
                filter_category: String(card.filter_category || 'その他').trim(),
                local_image_url: localImageUrl,
            };
        });
      loadedCards.push(...processedData);
    } catch (error) { console.error(`[Editor] Error loading/parsing CSV for ${rarityKey}:`, error); }
  }
  allCardsForEditing.value = loadedCards.sort((a,b) => parseInt(a.id, 10) - parseInt(b.id, 10));
  isLoading.value = false;
}

function loadOwnedData() {
  const data = localStorage.getItem('cgssOwnedCards');
  if (data) { try { ownedCardsData.value = JSON.parse(data); } catch (e) { ownedCardsData.value = {}; } }
}
function updateStarRank(cardId, event) {
  const newStarRank = parseInt(event.target.value, 10);
  const cardIdStr = String(cardId);
  if (newStarRank > 0) { ownedCardsData.value[cardIdStr] = newStarRank; }
  else { delete ownedCardsData.value[cardIdStr]; }
  localStorage.setItem('cgssOwnedCards', JSON.stringify(ownedCardsData.value));
}
const getMaxStarRank = (rarity) => {
  switch (rarity) {
    case 'ノーマル': return 5; case 'レア': return 10; case 'Sレア': return 15; case 'SSレア': return 20; default: return 0;
  }
};

const editorSearchTerm = ref('');
const editorSelectedRarity = ref('All');
const editorSelectedAttribute = ref('All');
const editorSelectedFilterCategory = ref('All');
const editorSortOrder = ref('asc');

const toggleEditorSortOrder = () => {
  editorSortOrder.value = editorSortOrder.value === 'asc' ? 'desc' : 'asc';
};

const editorRarityOptions = computed(() => ['All', ...Object.keys(rarityMapping)]);
const editorAttributeOptions = computed(() => {
    const attrs = new Set(['All']);
    allCardsForEditing.value.forEach(card => { if(card.attribute) attrs.add(card.attribute); });
    return Array.from(attrs).sort((a,b) => { if (a === 'All') return -1; if (b === 'All') return 1; return a.localeCompare(b); });
});
const editorFilterCategoryOptions = computed(() => {
  const categories = new Set(['All']);
  allCardsForEditing.value.forEach(card => { if (card.filter_category) categories.add(card.filter_category); });
  return Array.from(categories).sort((a,b) => { if (a === 'All') return -1; if (b === 'All') return 1; const order = ['恒常', '期間限定ガシャ', 'フェス限定', 'ドミナント限定', 'イベント報酬', 'イベント報酬(コラボ)']; const iA = order.indexOf(a), iB = order.indexOf(b); if (iA !== -1 && iB !== -1) return iA - iB; if (iA !== -1) return -1; if (iB !== -1) return 1; return a.localeCompare(b); });
});
const filteredCardsForEditing = computed(() => {
  let cardsToFilter = allCardsForEditing.value;
  if (!Array.isArray(cardsToFilter)) return [];
  cardsToFilter = cardsToFilter.filter(card => {
    const nameMatch = card.name.toLowerCase().includes(editorSearchTerm.value.toLowerCase());
    const rarityMatch = editorSelectedRarity.value === 'All' || card.rarity === editorSelectedRarity.value;
    const attributeMatch = editorSelectedAttribute.value === 'All' || card.attribute === editorSelectedAttribute.value;
    const categoryMatch = editorSelectedFilterCategory.value === 'All' || card.filter_category === editorSelectedFilterCategory.value;
    return nameMatch && rarityMatch && attributeMatch && categoryMatch;
  });
  return [...cardsToFilter].sort((a, b) => {
    const idA = parseInt(a.id, 10); const idB = parseInt(b.id, 10);
    return editorSortOrder.value === 'asc' ? idA - idB : idB - idA;
  });
});

const goBackToChecker = () => { emit('back-to-checker'); };

onMounted(async () => {
  loadOwnedData();
  await loadAllCsvData();
  window.addEventListener('scroll', handleEditorScroll);
});
onUnmounted(() => {
  window.removeEventListener('scroll', handleEditorScroll);
});
</script>

<template>
  <div class="editor-container-flat">
    <header class="editor-header-flat">
      <h2>スターランク編集</h2>
      <button @click="goBackToChecker" class="back-button-flat">チェッカーに戻る</button>
    </header>

    <div class="editor-filters-flat">
      <input type="text" v-model="editorSearchTerm" placeholder="アイドル名で検索..." class="filter-input-flat">
      <select v-model="editorSelectedRarity" class="filter-select-flat">
        <option v-for="rarity in editorRarityOptions" :key="rarity" :value="rarity">
          {{ rarity === 'All' ? '全レアリティ' : rarity }}
        </option>
      </select>
      <select v-model="editorSelectedAttribute" class="filter-select-flat">
        <option v-for="attr in editorAttributeOptions" :key="attr" :value="attr">
          {{ attr === 'All' ? '全属性' : attr }}
        </option>
      </select>
      <select v-model="editorSelectedFilterCategory" class="filter-select-flat">
        <option v-for="category in editorFilterCategoryOptions" :key="category" :value="category">
          {{ category === 'All' ? '全カテゴリ' : category }}
        </option>
      </select>
      <button @click="toggleEditorSortOrder" class="sort-button-editor">
        ID順: {{ editorSortOrder === 'asc' ? '昇順' : '降順' }}
      </button>
    </div>

    <div v-if="isLoading" class="loading-indicator-flat">
      <p>カードデータを読み込み中...</p>
    </div>
    <div v-else-if="allCardsForEditing.length > 0 && filteredCardsForEditing.length === 0" class="no-cards-message-flat">
        <p>表示するカードがありません。フィルター条件を見直してください。</p>
        <p>(全 {{ allCardsForEditing.length }} 件中)</p>
    </div>
    <div v-else-if="filteredCardsForEditing.length > 0" class="editor-card-grid-flat">
      <div v-for="card in filteredCardsForEditing" :key="card.id" class="editor-card-item-flat">
        <img v-if="card.local_image_url && card.local_image_url !== '/data/images/default_image.png'"
             :src="card.local_image_url" :alt="card.name" class="editor-card-image-flat">
        <div class="editor-card-info-flat">
          <p class="editor-card-name-flat">{{ card.name }}</p>
          <!-- ▼▼▼ 変更点 ▼▼▼ -->
          <p class="editor-card-details-flat">
            {{ card.rarity }} | {{ card.attribute }} | {{ card.filter_category }}
          </p>
          <!-- ▲▲▲ 変更点 ▲▲▲ -->
          <div class="editor-star-selector-flat">
            <label :for="`star-edit-${card.id}`">スターランク:</label>
            <select :id="`star-edit-${card.id}`" @change="updateStarRank(card.id, $event)" :value="ownedCardsData[card.id] || 0">
              <option value="0">未所持/☆0</option>
              <option
                v-for="n in getMaxStarRank(card.rarity)"
                :key="n"
                :value="n"
              >
                ☆{{ n }}
              </option>
            </select>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="no-cards-message-flat">
      <p>データが読み込めませんでした。CSVファイルの配置や内容を確認してください。</p>
      <p>(コンソールログも確認してください)</p>
    </div>
     <button v-if="showEditorScrollToTopButton" @click="scrollToEditorTop" class="scroll-to-top-button-editor">
      ↑ Top
    </button>
  </div>
</template>

<style scoped>
.editor-container-flat {
  padding: 24px;
  max-width: 1200px;
  margin: 30px auto;
  background-color: #0a0f1f;
  color: #e0e0e0;
  border-radius: 8px;
  border: 1px solid #303850;
  box-shadow: 0 0 25px rgba(0, 255, 255, 0.15),
              0 0 15px rgba(255, 0, 255, 0.1);
  font-family: 'Orbitron', 'Share Tech Mono', monospace, sans-serif;
}

.editor-header-flat {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #303850;
}
.editor-header-flat h2 {
  margin: 0;
  font-size: 2em;
  color: #00f0ff;
  font-weight: 700;
  text-shadow: 0 0 5px #00f0ff, 0 0 10px #00f0ff, 0 0 15px rgba(0, 240, 255, 0.5);
  letter-spacing: 1px;
}
.back-button-flat {
  padding: 10px 20px;
  background-color: #ff00ff;
  color: #0a0f1f;
  border: 1px solid #ff00ff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9em;
  font-weight: 600;
  text-transform: uppercase;
  transition: background-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
  box-shadow: 0 0 8px rgba(255, 0, 255, 0.5);
}
.back-button-flat:hover {
  background-color: #e600e6;
  box-shadow: 0 0 15px rgba(255, 0, 255, 0.7);
  transform: scale(1.05);
}

.editor-filters-flat {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 24px;
  padding: 16px;
  background-color: rgba(10, 15, 31, 0.85);
  border-radius: 6px;
  border: 1px solid #4a5578;
}
.filter-input-flat, .filter-select-flat, .sort-button-editor {
  padding: 12px 15px;
  border-radius: 4px;
  border: 1px solid #4a5578;
  background-color: #111827;
  color: #c7d2fe;
  font-size: 0.95em;
  flex-grow: 1;
  min-width: 180px;
  box-sizing: border-box;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  text-align: left;
}
.filter-input-flat::placeholder {
  color: #808a9f;
}
.filter-input-flat:focus, .filter-select-flat:focus, .sort-button-editor:focus {
  border-color: #00f0ff;
  outline: none;
  box-shadow: 0 0 0 3px rgba(0, 240, 255, 0.3), 0 0 10px rgba(0, 240, 255, 0.2);
}
.filter-select-flat, .sort-button-editor {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%2300f0ff'%3E%3Cpath d='M7 10l5 5 5-5H7z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  background-size: 1.2em;
  padding-right: 30px;
}
.sort-button-editor {
  background-image: none;
  padding-right: 15px;
  text-align: center;
  flex-grow: 0;
  min-width: auto;
}
.sort-button-editor:hover {
  background-color: #303850;
  border-color: #00f0ff;
}

.loading-indicator-flat, .no-cards-message-flat {
  text-align: center;
  padding: 30px;
  color: #9ca3af;
  font-size: 1.1em;
}
.no-cards-message-flat p {
    margin: 5px 0;
}

.editor-card-grid-flat {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 24px;
}

.editor-card-item-flat {
  background-color: rgba(27, 34, 59, 0.9);
  border-radius: 6px;
  border: 1px solid #00f0ff;
  overflow: hidden;
  display: flex;
  align-items: center;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.4), inset 0 0 10px rgba(0, 255, 255, 0.05);
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}
.editor-card-item-flat:hover {
  transform: scale(1.02) translateY(-3px);
  box-shadow: 0 5px 15px rgba(0,0,0,0.5), 0 0 20px rgba(0, 255, 255, 0.3);
  border-color: #ff00ff;
}

.editor-card-image-flat {
  width: 80px;
  height: auto;
  object-fit: contain;
  margin-right: 20px;
  border-radius: 4px;
  flex-shrink: 0;
  border: 1px solid rgba(0, 240, 255, 0.5);
}

.editor-card-info-flat {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  /* ▼▼▼ 追加: テキストがはみ出た場合に省略されるようにするため、infoコンテナの幅が適切に制限されるように */
  min-width: 0; /* flexアイテムが縮小できるように */
}

.editor-card-name-flat {
  margin: 0;
  font-size: 1.2em;
  font-weight: 700;
  color: #ccddff;
  text-shadow: 0 0 4px #00aaff;
}

/* ▼▼▼ 変更点 ▼▼▼ */
.editor-card-details-flat {
  margin: 0;
  font-size: 0.85em;
  color: #8899cc;
  line-height: 1.5;
  white-space: nowrap;   /* テキストを1行に強制 */
  overflow: hidden;        /* コンテナからはみ出す部分を隠す */
  text-overflow: ellipsis; /* はみ出す部分を '...' で表示 */
  /* width: 100%; */ /* ellipsis が機能するように、必要であれば幅を指定 */
                     /* editor-card-info-flat に min-width:0 を追加したので、こちらは不要かも */
}
/* .editor-card-details-flat span と span:not(:last-child):after のスタイルは削除しました */
/* ▲▲▲ 変更点 ▲▲▲ */

.editor-star-selector-flat {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.editor-star-selector-flat label {
  font-size: 0.95em;
  color: #f0ff00;
  text-shadow: 0 0 3px #f0ff00, 0 0 6px rgba(240, 255, 0, 0.7);
  white-space: nowrap;
  font-weight: 500;
}
.editor-star-selector-flat select {
  padding: 9px 12px;
  border-radius: 4px;
  border: 1px solid #4a5578;
  font-size: 0.95em;
  background-color: #0a0c1a;
  color: #f0ff00;
  flex-grow: 1;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23f0ff00'%3E%3Cpath d='M7 10l5 5 5-5H7z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  background-size: 1.2em;
  text-shadow: 0 0 2px #f0ff00;
}
.editor-star-selector-flat select option {
  background-color: #111827;
  color: #e0e0e0;
}
.editor-star-selector-flat select:focus {
  border-color: #ff00ff;
  outline: none;
  box-shadow: 0 0 0 3px rgba(255, 0, 255, 0.3), 0 0 10px rgba(255, 0, 255, 0.2);
}

.scroll-to-top-button-editor {
  position: fixed;
  bottom: 30px;
  right: 30px;
  padding: 0;
  width: 50px;
  height: 50px;
  background-color: #00f0ff;
  color: #0a0f1f;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 0 15px rgba(0, 240, 255, 0.5), 0 0 25px rgba(0, 240, 255, 0.3);
  z-index: 1001;
  opacity: 0.9;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.3em;
  text-shadow: none;
}
.scroll-to-top-button-editor:hover {
  opacity: 1;
  transform: scale(1.15);
  box-shadow: 0 0 25px rgba(0, 240, 255, 0.7), 0 0 35px rgba(0, 240, 255, 0.5);
}

/* スマホなどの狭い画面向けのスタイル */
@media (max-width: 768px) {
  .editor-container-flat {
    padding: 15px;
    margin-top: 100px; /* 固定ヘッダーの高さを考慮 */
  }
  .editor-header-flat {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  .editor-header-flat h2 {
    font-size: 1.6em;
  }
  .back-button-flat {
    padding: 8px 15px;
    font-size: 0.85em;
    align-self: flex-end;
  }
  .editor-filters-flat {
    gap: 10px;
    padding: 12px;
    flex-direction: column;
  }
  .filter-input-flat, .filter-select-flat, .sort-button-editor {
    min-width: 100%;
    flex-grow: 0;
    margin-bottom: 8px;
  }
  .sort-button-editor {
    text-align: center;
  }

  .editor-card-grid-flat {
    grid-template-columns: repeat(2, 1fr); /* スマホで2列表示 */
    gap: 12px;
  }
  .editor-card-item-flat {
    padding: 12px;
    flex-direction: column;
    align-items: center;
  }
  .editor-card-image-flat {
    width: 70px;
    margin-right: 0;
    margin-bottom: 10px;
  }
  .editor-card-info-flat {
    text-align: center;
    width: 100%; /* スマホ表示で中央寄せやellipsisのために幅を明確に */
    /* min-width: 0; はPC側で定義済みなのでここでは不要 */
  }
  .editor-card-name-flat {
    font-size: 1.1em;
  }

  /* ▼▼▼ 変更点 ▼▼▼ */
  .editor-card-details-flat {
    font-size: 0.75em;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    text-align: center; /* スマホ表示時は中央寄せ */
    width: 100%; /* 親要素(.editor-card-info-flat)がwidth:100%なので、こちらも合わせる */
                  /* display: flex, flex-direction: columnなどは削除 */
  }
  /* .editor-card-details-flat span:not(:last-child):after のスタイルは削除しました */
  /* ▲▲▲ 変更点 ▲▲▲ */

  .editor-star-selector-flat {
    margin-top: 8px;
    flex-direction: column;
    align-items: stretch;
    gap: 5px;
  }
  .editor-star-selector-flat label {
    text-align: center;
  }
  .editor-star-selector-flat select {
    font-size: 0.9em;
    width: 100%;
    padding-right: 10px;
  }
}

@media (max-width: 480px) {
  .editor-card-grid-flat {
    grid-template-columns: 1fr; /* さらに狭い画面では1列に */
  }
  .editor-header-flat h2 {
    font-size: 1.4em;
  }
  .editor-card-name-flat {
    font-size: 1em;
  }
  .editor-card-details-flat {
    font-size: 0.7em;
    /* 他のスタイルは max-width: 768px から継承されるので、ここではフォントサイズのみ調整 */
  }
}
</style>
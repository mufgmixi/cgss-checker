<script setup>
import { ref, onMounted, computed, defineEmits } from 'vue';
import Papa from 'papaparse';

const emit = defineEmits(['back-to-checker']);

const allCardsForEditing = ref([]);
const ownedCardsData = ref({}); // localStorageから読み込んだスターランクデータ
const isLoading = ref(false);

// App.vue と同じマッピングを使用
const rarityMapping = {
  'ノーマル': { folder: 'N', csv: '/data/csv/cgss_n_card_list.csv' },
  'レア':    { folder: 'R', csv: '/data/csv/cgss_r_card_list.csv' },
  'Sレア':   { folder: 'SR', csv: '/data/csv/cgss_sr_card_list.csv' },
  'SSレア':  { folder: 'SSR', csv: '/data/csv/cgss_ssr_card_list.csv' }
};

const getFilenameFromUrl = (url) => {
  if (!url || typeof url !== 'string') return 'default_image.png';
  const parts = url.split('/');
  return parts[parts.length - 1];
};

async function loadAllCsvData() {
  isLoading.value = true;
  const loadedCards = [];
  const rarityKeys = Object.keys(rarityMapping);

  for (const rarityKey of rarityKeys) {
    const targetRarityInfo = rarityMapping[rarityKey];
    if (!targetRarityInfo || !targetRarityInfo.csv) continue;
    const filePath = targetRarityInfo.csv;
    console.log(`Fetching CSV for editor: ${rarityKey} from ${filePath}...`);
    try {
      const response = await fetch(filePath);
      if (!response.ok) {
        console.warn(`Failed to fetch ${filePath} for editor: ${response.status}`);
        continue;
      }
      const csvText = await response.text();
      const parseResult = await new Promise((resolve, reject) => {
        Papa.parse(csvText, {
          header: true,
          skipEmptyLines: true,
          complete: resolve,
          error: reject
        });
      });

      if (parseResult.errors && parseResult.errors.length > 0) {
        console.warn(`PapaParse errors for ${rarityKey} in editor:`, parseResult.errors);
      }

      const processedData = parseResult.data
        .filter(card => card && typeof card.id === 'string' && card.id.trim() !== '' && typeof card.name === 'string' && card.name.trim() !== '')
        .map(card => {
            const cardRarityTrimmed = String(card.rarity || '').trim();
            const currentRarityInfo = rarityMapping[cardRarityTrimmed];
            const folderName = currentRarityInfo ? currentRarityInfo.folder : 'unknown_rarity_folder';
            if (!currentRarityInfo) {
                console.warn(`No rarityMapping for card rarity: '${cardRarityTrimmed}' ID ${card.id}`);
            }
            const cardId = String(card.id).trim();
            let cardNameForFile = String(card.name).trim().replace(/[\\/:*?"<>|#]/g, '_');
            const filename = `${cardId}_${cardNameForFile}.jpg`;
            return {
                id: cardId, name: String(card.name).trim(), rarity: cardRarityTrimmed,
                attribute: String(card.attribute || 'Unknown').trim(),
                availability: String(card.availability || '').trim(),
                filter_category: String(card.filter_category || 'その他').trim(),
                local_image_url: `/data/images/${folderName}/${filename}`,
            };
        });
      loadedCards.push(...processedData);
    } catch (error) {
      console.error(`Error loading/parsing CSV for ${rarityKey} in editor:`, error);
    }
  }
  allCardsForEditing.value = loadedCards.sort((a,b) => parseInt(a.id, 10) - parseInt(b.id, 10));
  isLoading.value = false;
  console.log('All cards loaded for editing. Total:', allCardsForEditing.value.length);
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
  console.log(`Star rank for card ID ${cardIdStr} updated to ${newStarRank}`);
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
  return allCardsForEditing.value.filter(card => {
    const nameMatch = card.name.toLowerCase().includes(editorSearchTerm.value.toLowerCase());
    const rarityMatch = editorSelectedRarity.value === 'All' || card.rarity === editorSelectedRarity.value;
    const attributeMatch = editorSelectedAttribute.value === 'All' || card.attribute === editorSelectedAttribute.value;
    const categoryMatch = editorSelectedFilterCategory.value === 'All' || card.filter_category === editorSelectedFilterCategory.value;
    return nameMatch && rarityMatch && attributeMatch && categoryMatch;
  });
});

const goBackToChecker = () => { emit('back-to-checker'); };

onMounted(async () => {
  loadOwnedData();
  await loadAllCsvData();
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
    </div>

    <div v-if="isLoading" class="loading-indicator-flat">
      <p>カードデータを読み込み中...</p>
    </div>
    <div v-else-if="filteredCardsForEditing.length > 0" class="editor-card-grid-flat">
      <div v-for="card in filteredCardsForEditing" :key="card.id" class="editor-card-item-flat">
        <img v-if="card.local_image_url && card.local_image_url !== '/data/images/default_image.png'"
             :src="card.local_image_url" :alt="card.name" class="editor-card-image-flat">
        <div class="editor-card-info-flat">
          <p class="editor-card-name-flat">{{ card.name }}</p>
          <p class="editor-card-details-flat">
            <span>ID: {{ card.id }}</span> | <span>{{ card.rarity }}</span> | <span>{{ card.attribute }}</span> | <span>{{ card.filter_category }}</span>
          </p>
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
      <p>該当するカードがありません。フィルター条件を見直してください。</p>
    </div>
  </div>
</template>

<style scoped>
.editor-container-flat {
  padding: 24px;
  max-width: 1200px;
  margin: 30px auto;
  background-color: #0a0f1f; /* ベースは非常に暗い青 */
  color: #e0e0e0; /* 基本の文字色は明るいグレー */
  border-radius: 8px;
  border: 1px solid #303850; /* 少し明るい境界線 */
  box-shadow: 0 0 25px rgba(0, 255, 255, 0.15), /* シアンのグロー */
              0 0 15px rgba(255, 0, 255, 0.1); /* マゼンタのグロー */
  font-family: 'Orbitron', 'Share Tech Mono', monospace, sans-serif; /* サイバーパンク風フォント例 */
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
  color: #00f0ff; /* サイバーなシアン */
  font-weight: 700;
  text-shadow: 0 0 5px #00f0ff, 0 0 10px #00f0ff, 0 0 15px rgba(0, 240, 255, 0.5); /* ネオン風テキストシャドウ */
  letter-spacing: 1px;
}
.back-button-flat {
  padding: 10px 20px;
  background-color: #ff00ff; /* サイバーピンク/マゼンタ */
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
  background-color: rgba(10, 15, 31, 0.85); /* 半透明度を少し上げる */
  border-radius: 6px;
  border: 1px solid #4a5578;
}
.filter-input-flat, .filter-select-flat {
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
}
.filter-input-flat::placeholder {
  color: #808a9f;
}
.filter-input-flat:focus, .filter-select-flat:focus {
  border-color: #00f0ff;
  outline: none;
  box-shadow: 0 0 0 3px rgba(0, 240, 255, 0.3), 0 0 10px rgba(0, 240, 255, 0.2);
}

.loading-indicator-flat, .no-cards-message-flat {
  text-align: center;
  padding: 30px;
  color: #9ca3af;
  font-size: 1.1em;
}

.editor-card-grid-flat {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); /* カード幅を少し広げる */
  gap: 24px;
}

.editor-card-item-flat {
  background-color: rgba(27, 34, 59, 0.9);
  border-radius: 6px;
  border: 1px solid #00f0ff; /* 境界線をシアンに */
  overflow: hidden;
  display: flex;
  align-items: center;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.4), 0 0 15px rgba(0, 255, 255, 0.1); /* グローを少し調整 */
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}
.editor-card-item-flat:hover {
  transform: scale(1.03) translateY(-3px);
  box-shadow: 0 5px 15px rgba(0,0,0,0.5), 0 0 25px rgba(0, 255, 255, 0.3);
  border-color: #ff00ff; /* ホバー時はマゼンタに */
}

.editor-card-image-flat {
  width: 80px;
  height: 120px;
  object-fit: contain;
  margin-right: 20px; /* 画像と情報の間のマージンを広げる */
  border-radius: 4px;
  flex-shrink: 0;
  border: 1px solid rgba(0, 240, 255, 0.5); /* グローに合わせて調整 */
}

.editor-card-info-flat {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  gap: 8px; /* 情報間のギャップを少し広げる */
}

.editor-card-name-flat {
  margin: 0;
  font-size: 1.2em;
  font-weight: 700; /* より太く */
  color: #ccddff; /* 明るい水色系 */
  text-shadow: 0 0 4px #00aaff;
}

.editor-card-details-flat {
  margin: 0;
  font-size: 0.85em;
  color: #8899cc; /* 少し明るめの情報テキスト */
  line-height: 1.6;
}
.editor-card-details-flat span {
  margin-right: 10px;
  display: inline-block; /* 区切り線が縦に並ばないように */
}
.editor-card-details-flat span:not(:last-child):after {
  content: "|";
  margin-left: 10px;
  color: #4a5578; /* 区切り線の色 */
}


.editor-star-selector-flat {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.editor-star-selector-flat label {
  font-size: 0.95em;
  color: #00f0ff;
  white-space: nowrap;
  font-weight: 500;
}
.editor-star-selector-flat select {
  padding: 9px 12px;
  border-radius: 4px;
  border: 1px solid #4a5578;
  font-size: 0.95em;
  background-color: #0a0c1a; /* さらに暗い背景 */
  color: #00f0ff;
  flex-grow: 1;
  cursor: pointer;
  appearance: none; /* ブラウザ標準の矢印を消す (カスタム矢印を作るなら) */
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%2300f0ff'%3E%3Cpath d='M7 10l5 5 5-5H7z'/%3E%3C/svg%3E"); /* 簡単なカスタム矢印 */
  background-repeat: no-repeat;
  background-position: right 10px center;
  background-size: 1.2em;
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
</style>
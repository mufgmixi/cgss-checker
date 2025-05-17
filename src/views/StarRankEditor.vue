<script setup>
import { ref, onMounted, computed, defineEmits } from 'vue';
import Papa from 'papaparse';

const emit = defineEmits(['back-to-checker']);

const allCardsForEditing = ref([]);
const ownedCardsData = ref({}); // localStorageから読み込んだスターランクデータ
const isLoading = ref(false);

// App.vue と同じマッピングを使用
const rarityMapping = {
  'ノーマル': { folder: 'N', csv: 'cgss_n_card_list.csv' },
  'レア':    { folder: 'R', csv: 'cgss_r_card_list.csv' },
  'Sレア':   { folder: 'SR', csv: 'cgss_sr_card_list.csv' },
  'SSレア':  { folder: 'SSR', csv: 'cgss_ssr_card_list.csv' }
};

async function loadAllCsvData() {
  isLoading.value = true;
  const loadedCards = [];
  const rarityKeys = Object.keys(rarityMapping);
  const baseUrl = import.meta.env.BASE_URL; // ベースURLをここで一度取得

  for (const rarityKey of rarityKeys) {
    const targetRarityInfo = rarityMapping[rarityKey];
    if (!targetRarityInfo || !targetRarityInfo.csv) {
      console.error(`[Editor] CSV file mapping not found for rarity: ${rarityKey}`);
      continue;
    }

    const csvPath = `data/csv/${targetRarityInfo.csv}`;
    // ベースURLの末尾が '/' かどうかで結合方法を調整
    let filePath = baseUrl.endsWith('/') ? `${baseUrl}${csvPath}` : `${baseUrl}/${csvPath}`;
    // ローカル開発時などでbaseUrlが単に'/'の場合、filePathが'//data/...'になるのを防ぐ
    if (filePath.startsWith('//')) {
      filePath = filePath.substring(1);
    }

    console.log(`[Editor] Fetching CSV for ${rarityKey} from ${filePath}...`);

    try {
      const response = await fetch(filePath);
      if (!response.ok) {
        console.error(`[Editor] Failed to fetch ${filePath}: ${response.status} ${response.statusText}`);
        continue;
      }
      const csvText = await response.text();
      console.log(`[Editor] CSV text for ${rarityKey} fetched successfully (length: ${csvText.length}).`);

      const parseResult = await new Promise((resolve, reject) => {
        Papa.parse(csvText, {
          header: true,
          skipEmptyLines: true,
          complete: resolve,
          error: reject
        });
      });

      console.log(`[Editor] PapaParse results for ${rarityKey}:`, parseResult);
      if (parseResult.errors && parseResult.errors.length > 0) {
        console.warn(`[Editor] PapaParse errors for ${rarityKey}:`, parseResult.errors);
      }

      const processedData = parseResult.data
        .filter(card => card && typeof card.id === 'string' && card.id.trim() !== '' && typeof card.name === 'string' && card.name.trim() !== '')
        .map(card => {
            const cardRarityTrimmed = String(card.rarity || '').trim();
            const currentRarityFolder = rarityMapping[cardRarityTrimmed] ? rarityMapping[cardRarityTrimmed].folder : 'unknown';
            if (!rarityMapping[cardRarityTrimmed]) {
                console.warn(`[Editor] No rarityMapping folder for card rarity: '${cardRarityTrimmed}' ID ${card.id}, using 'unknown' folder.`);
            }

            const cardId = String(card.id).trim();
            let cardNameForFile = String(card.name).trim().replace(/[\\/:*?"<>|#]/g, '_');
            const filename = `${cardId}_${cardNameForFile}.jpg`;

            const imagePath = `data/images/${currentRarityFolder}/${filename}`;
            let localImageUrl = baseUrl.endsWith('/') ? `${baseUrl}${imagePath}` : `${baseUrl}/${imagePath}`;
            if (localImageUrl.startsWith('//')) {
                localImageUrl = localImageUrl.substring(1);
            }

            return {
                id: cardId,
                name: String(card.name).trim(),
                rarity: cardRarityTrimmed,
                attribute: String(card.attribute || 'Unknown').trim(),
                availability: String(card.availability || '').trim(),
                filter_category: String(card.filter_category || 'その他').trim(),
                local_image_url: localImageUrl,
            };
        });
      console.log(`[Editor] Processed data for ${rarityKey} (length: ${processedData.length}):`, processedData.slice(0,1));
      loadedCards.push(...processedData);
    } catch (error) {
      console.error(`[Editor] Error loading/parsing CSV for ${rarityKey}:`, error);
    }
  }
  allCardsForEditing.value = loadedCards.sort((a,b) => parseInt(a.id, 10) - parseInt(b.id, 10));
  isLoading.value = false;
  console.log('[Editor] All cards loaded for editing. Total:', allCardsForEditing.value.length);
  if (allCardsForEditing.value.length === 0 && !isLoading.value) {
      console.warn('[Editor] No cards were loaded into allCardsForEditing. Check CSV paths, content, and console logs.');
  }
}

function loadOwnedData() {
  const data = localStorage.getItem('cgssOwnedCards');
  if (data) {
    try {
      ownedCardsData.value = JSON.parse(data);
    } catch (e) {
      console.error('[Editor] Failed to parse owned cards from localStorage:', e);
      ownedCardsData.value = {};
    }
  }
}

function updateStarRank(cardId, event) {
  const newStarRank = parseInt(event.target.value, 10);
  const cardIdStr = String(cardId);

  if (newStarRank > 0) {
    ownedCardsData.value[cardIdStr] = newStarRank;
  } else {
    delete ownedCardsData.value[cardIdStr];
  }
  localStorage.setItem('cgssOwnedCards', JSON.stringify(ownedCardsData.value));
  console.log(`[Editor] Star rank for card ID ${cardIdStr} updated to ${newStarRank}`);
}

const getMaxStarRank = (rarity) => {
  switch (rarity) {
    case 'ノーマル': return 5;
    case 'レア': return 10;
    case 'Sレア': return 15;
    case 'SSレア': return 20;
    default: return 0;
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

const goBackToChecker = () => {
  emit('back-to-checker');
};

onMounted(async () => {
  console.log('StarRankEditor.vue onMounted started.');
  loadOwnedData();
  await loadAllCsvData();
  console.log('StarRankEditor.vue onMounted finished.');
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
      <p>データが読み込めませんでした。CSVファイルの配置や内容を確認してください。</p>
      <p>(コンソールログも確認してください)</p>
    </div>
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
}

.editor-card-name-flat {
  margin: 0;
  font-size: 1.2em;
  font-weight: 700;
  color: #ccddff;
  text-shadow: 0 0 4px #00aaff;
}

.editor-card-details-flat {
  margin: 0;
  font-size: 0.85em;
  color: #8899cc;
  line-height: 1.6;
}
.editor-card-details-flat span {
  margin-right: 10px;
  display: inline-block;
}
.editor-card-details-flat span:not(:last-child):after {
  content: "|";
  margin-left: 10px;
  color: #4a5578;
}

.editor-star-selector-flat {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.editor-star-selector-flat label {
  font-size: 0.95em;
  color: #f0ff00; /* 蛍光イエロー */
  text-shadow: 0 0 3px #f0ff00, 0 0 6px rgba(240, 255, 0, 0.7); /* イエローのグロー */
  white-space: nowrap;
  font-weight: 500;
}
.editor-star-selector-flat select {
  padding: 9px 12px;
  border-radius: 4px;
  border: 1px solid #4a5578;
  font-size: 0.95em;
  background-color: #0a0c1a;
  color: #f0ff00; /* 蛍光イエロー */
  flex-grow: 1;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23f0ff00'%3E%3Cpath d='M7 10l5 5 5-5H7z'/%3E%3C/svg%3E"); /* 矢印もイエローに */
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
/* ▼▼▼ スマホなどの狭い画面向けのスタイル ▼▼▼ */
@media (max-width: 768px) {
  .editor-container-flat {
    padding: 15px;
  }
  .editor-header-flat h2 {
    font-size: 1.5em;
  }
  .back-button-flat {
    padding: 8px 15px;
    font-size: 0.85em;
  }
  .editor-filters-flat {
    gap: 10px;
    padding: 12px;
  }
  .filter-input-flat, .filter-select-flat {
    min-width: 100%; /* 狭い画面では各フィルターを横幅いっぱいに */
    flex-grow: 0;
  }

  .editor-card-grid-flat {
    grid-template-columns: 1fr; /* スマホでは1列表示 */
    gap: 15px;
  }
  .editor-card-item-flat {
    padding: 12px;
    /* 必要であれば画像と情報の配置を縦並びに変更 */
    /* flex-direction: column;
    align-items: flex-start; */
  }
  .editor-card-image-flat {
    width: 60px; /* 画像を少し小さく */
    /* height: auto; */ /* 縦並びにするなら */
    margin-right: 12px;
    /* margin-bottom: 10px; */ /* 縦並びにするなら */
  }
  .editor-card-name-flat {
    font-size: 1.1em;
  }
  .editor-card-details-flat {
    font-size: 0.8em;
    /* 必要であれば | 区切りをやめて改行表示なども検討 */
  }
  .editor-star-selector-flat label,
  .editor-star-selector-flat select {
    font-size: 0.9em;
  }
}
</style>
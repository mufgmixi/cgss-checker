<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import Papa from 'papaparse';
import CardItem from './components/CardItem.vue';
import StarRankEditor from './views/StarRankEditor.vue'; // StarRankEditorをインポート

// --- データと状態管理 ---
const allCardsRaw = ref({});
const selectedRarity = ref('SSレア');
const ownedCards = ref({}); // { "カードID": スターランク数 }
const isLoading = ref(false);
const isEditingStarRank = ref(false); // スターランク編集画面の表示状態

const rarityMapping = {
  'ノーマル': { folder: 'N', csv: 'cgss_n_card_list.csv' },
  'レア':    { folder: 'R', csv: 'cgss_r_card_list.csv' },
  'Sレア':   { folder: 'SR', csv: 'cgss_sr_card_list.csv' },
  'SSレア':  { folder: 'SSR', csv: 'cgss_ssr_card_list.csv' }
};

const searchTerm = ref('');
const selectedAttribute = ref('All');
const showOwned = ref('All'); // "All", "Owned", "NotOwned"
const selectedFilterCategory = ref('All');

// --- トップに戻るボタン用の状態とロジック ---
const showScrollToTopButton = ref(false);
const scrollThreshold = 200;

const handleScroll = () => {
  showScrollToTopButton.value = window.scrollY > scrollThreshold;
};

const scrollToTop = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

// --- 全チェッククリア用のメソッド ---
const clearAllOwnedChecks = () => {
  if (confirm('本当に全てのカードの所持情報（スターランク含む）をクリアしますか？この操作は元に戻せません。')) {
    ownedCards.value = {};
    saveOwnedDataToLocalStorage();
    console.log('All owned checks and star ranks cleared.');
  }
};

// --- スターランク編集画面遷移用メソッド ---
const goToStarRankEditor = () => {
  isEditingStarRank.value = true;
};

const handleBackFromEditor = () => {
  isEditingStarRank.value = false;
  loadOwnedDataFromLocalStorage(); // エディタでの変更を反映するために再読み込み
  console.log('Returned from star rank editor. Reloading owned data.');
};


async function loadCsvData(rarityKey) {
  const targetRarityInfo = rarityMapping[rarityKey];
  if (!targetRarityInfo || !targetRarityInfo.csv) {
    console.error(`CSV file mapping not found for rarity: ${rarityKey}`);
    return [];
  }
  const filePath = `/data/csv/${targetRarityInfo.csv}`;
  // isLoading.value = true; // loadCardsForCurrentRarity で制御
  console.log(`Fetching CSV for ${rarityKey} from ${filePath}...`);

  try {
    const response = await fetch(filePath);
    if (!response.ok) {
      console.error(`Failed to fetch ${filePath}: ${response.status} ${response.statusText}`);
      return [];
    }
    const csvText = await response.text();
    console.log(`CSV text for ${rarityKey} fetched successfully.`);

    return new Promise((resolve, reject) => {
      Papa.parse(csvText, {
        header: true,
        skipEmptyLines: true,
        complete: (results) => {
          console.log(`PapaParse results for ${rarityKey}:`, results);
          if (results.errors && results.errors.length > 0) {
            console.warn(`PapaParse errors for ${rarityKey}:`, results.errors);
          }
          const processedData = results.data
            .filter(card => card && typeof card.id === 'string' && card.id.trim() !== '' && typeof card.name === 'string' && card.name.trim() !== '')
            .map(card => {
              const cardRarityTrimmed = String(card.rarity || '').trim();
              const currentRarityFolder = targetRarityInfo.folder;
              const cardId = String(card.id).trim();
              let cardNameForFile = String(card.name).trim().replace(/[\\/:*?"<>|#]/g, '_');
              const filename = `${cardId}_${cardNameForFile}.jpg`;
              return {
                id: cardId,
                name: String(card.name).trim(),
                rarity: cardRarityTrimmed,
                image_url: String(card.image_url || '').trim(),
                detail_url: String(card.detail_url || '').trim(),
                attribute: String(card.attribute || 'Unknown').trim(),
                availability: String(card.availability || '').trim(),
                filter_category: String(card.filter_category || 'その他').trim(),
                local_image_url: `/data/images/${currentRarityFolder}/${filename}`,
              };
            });
          console.log(`Processed data for ${rarityKey} (first 1 item):`, processedData.slice(0, 1));
          resolve(processedData);
        },
        error: (error) => {
          console.error(`Error parsing ${filePath}:`, error);
          reject(error);
        }
      });
    });
  } catch (error) {
    console.error(`Error in loadCsvData for ${rarityKey}:`, error);
    return [];
  }
}

async function loadCardsForCurrentRarity() {
  isLoading.value = true;
  const currentRarityKey = selectedRarity.value;
  if (currentRarityKey && rarityMapping[currentRarityKey]) {
    if (!allCardsRaw.value[currentRarityKey] || allCardsRaw.value[currentRarityKey].length === 0) {
      allCardsRaw.value[currentRarityKey] = await loadCsvData(currentRarityKey);
    }
  } else {
    if(currentRarityKey) allCardsRaw.value[currentRarityKey] = [];
  }
  isLoading.value = false;
}

function loadOwnedDataFromLocalStorage() {
  const data = localStorage.getItem('cgssOwnedCards');
  if (data) { try { ownedCards.value = JSON.parse(data); } catch (e) { ownedCards.value = {}; } }
}

function saveOwnedDataToLocalStorage() {
  try { localStorage.setItem('cgssOwnedCards', JSON.stringify(ownedCards.value)); } catch (e) { console.error(e); }
}

function handleToggleStarRankBasic({ cardId }) {
  const cardIdStr = String(cardId);
  const currentStar = ownedCards.value[cardIdStr] || 0;
  const newStarRank = currentStar > 0 ? 0 : 1;

  if (newStarRank > 0) {
    ownedCards.value[cardIdStr] = newStarRank;
  } else {
    delete ownedCards.value[cardIdStr];
  }
  saveOwnedDataToLocalStorage();
}

const cardsForSelectedRarity = computed(() => {
  const rawData = allCardsRaw.value[selectedRarity.value];
  if (!Array.isArray(rawData)) return [];
  return rawData.map(card => ({
    ...card,
    starRank: ownedCards.value[String(card.id)] || 0
  }));
});

const ownedCountForSelectedRarity = computed(() => {
  const currentCards = cardsForSelectedRarity.value;
  if (!Array.isArray(currentCards)) return 0;
  return currentCards.filter(card => card.starRank > 0).length;
});

const totalCountForSelectedRarity = computed(() => {
  const currentCards = cardsForSelectedRarity.value;
  if (!Array.isArray(currentCards)) return 0;
  return currentCards.length;
});

const ownedPercentageForSelectedRarity = computed(() => {
  if (totalCountForSelectedRarity.value === 0) return 0;
  return Math.round((ownedCountForSelectedRarity.value / totalCountForSelectedRarity.value) * 100);
});

const filterCategoryOptions = computed(() => {
  const categories = new Set(['All']);
  if (Array.isArray(cardsForSelectedRarity.value)) {
    cardsForSelectedRarity.value.forEach(card => {
      if (card.filter_category) categories.add(card.filter_category);
    });
  }
  return Array.from(categories).sort((a,b) => {
    if (a === 'All') return -1; if (b === 'All') return 1;
    const order = ['恒常', '期間限定ガシャ', 'フェス限定', 'ドミナント限定', 'イベント報酬', 'イベント報酬(コラボ)'];
    const iA = order.indexOf(a), iB = order.indexOf(b);
    if (iA !== -1 && iB !== -1) return iA - iB; if (iA !== -1) return -1; if (iB !== -1) return 1;
    return a.localeCompare(b);
  });
});

const filteredCards = computed(() => {
  const currentCards = cardsForSelectedRarity.value;
  if (!Array.isArray(currentCards)) return [];
  const term = searchTerm.value.toLowerCase();
  return currentCards.filter(card => {
    const nameMatch = card.name && typeof card.name === 'string' && card.name.toLowerCase().includes(term);
    const attributeMatch = selectedAttribute.value === 'All' || card.attribute === selectedAttribute.value;
    const categoryMatch = selectedFilterCategory.value === 'All' || card.filter_category === selectedFilterCategory.value;
    let ownedMatch = true;
    if (showOwned.value === 'Owned') ownedMatch = card.starRank > 0;
    else if (showOwned.value === 'NotOwned') ownedMatch = card.starRank === 0;
    return nameMatch && attributeMatch && categoryMatch && ownedMatch;
  });
});

const rarityOptions = computed(() => Object.keys(rarityMapping));
const attributeOptions = ref(['All', 'Cu', 'Co', 'Pa', 'Unknown']);

onMounted(async () => {
  console.log('App.vue onMounted started.');
  loadOwnedDataFromLocalStorage();
  await loadCardsForCurrentRarity();
  window.addEventListener('scroll', handleScroll);
  console.log('App.vue onMounted finished.');
});

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll);
});

watch(selectedRarity, async (newRarity, oldRarity) => {
  if (newRarity !== oldRarity && newRarity) {
    await loadCardsForCurrentRarity();
  }
});
</script>

<template>
  <div id="app-container">
    <StarRankEditor v-if="isEditingStarRank" @back-to-checker="handleBackFromEditor" />

    <div v-else>
      <header class="app-header">
        <h1>デレステカードチェッカー</h1>
        <div class="stats-bar">
          <p>
            選択中レアリティ ({{ selectedRarity }}):
            {{ ownedCountForSelectedRarity }} / {{ totalCountForSelectedRarity }}枚
            ({{ ownedPercentageForSelectedRarity }}%) |
            表示中: {{ filteredCards.length }}枚 |
            総所持数(全レアリティ): {{ Object.keys(ownedCards).length }}枚
          </p>
          <button @click="goToStarRankEditor" class="edit-star-rank-button">スターランク編集</button>
        </div>
      </header>

      <main class="main-content">
        <div class="controls">
          <div class="control-group">
            <label for="rarity-select">レアリティ:</label>
            <select id="rarity-select" v-model="selectedRarity">
              <option v-for="rarityKey in rarityOptions" :key="rarityKey" :value="rarityKey">
                {{ rarityKey }}
              </option>
            </select>
          </div>
          <div class="control-group">
            <button @click="clearAllOwnedChecks" class="clear-all-button">全チェッククリア</button>
          </div>
        </div>

        <div class="filters">
          <input type="text" id="search-term-input" v-model="searchTerm" placeholder="アイドル名で検索..." class="filter-input">
          <div class="filter-group">
            <label for="attribute-select">属性:</label>
            <select id="attribute-select" v-model="selectedAttribute">
              <option v-for="attr in attributeOptions" :key="attr" :value="attr">
                {{ attr === 'All' ? '全属性' : attr }}
              </option>
            </select>
          </div>
          <div class="filter-group">
            <label for="category-select">カテゴリ:</label>
            <select id="category-select" v-model="selectedFilterCategory">
              <option v-for="category in filterCategoryOptions" :key="category" :value="category">
                {{ category === 'All' ? 'すべて' : category }}
              </option>
            </select>
          </div>
          <div class="filter-group">
            <label for="owned-select">表示:</label>
            <select id="owned-select" v-model="showOwned">
              <option value="All">すべて</option>
              <option value="Owned">所持(☆1以上)</option>
              <option value="NotOwned">未所持(☆0)</option>
            </select>
          </div>
        </div>

        <div v-if="isLoading" class="loading-indicator">
          <p>カードデータを読み込み中...</p>
        </div>
        <div v-else-if="filteredCards.length > 0" class="card-grid">
          <CardItem
            v-for="card in filteredCards"
            :key="`${card.rarity}-${card.id}`"
            :card="card"
            @toggle-star-rank-basic="handleToggleStarRankBasic"
          />
        </div>
        <div v-else class="no-cards">
          <p>表示するカードがありません。フィルター条件を見直してください。</p>
          <p v-if="!isLoading && Array.isArray(allCardsRaw[selectedRarity]) && allCardsRaw[selectedRarity].length > 0 && filteredCards.length === 0">
            (選択中の「{{ selectedRarity }}」には {{ allCardsRaw[selectedRarity].length }} 枚のカードがありますが、現在のフィルターで絞り込まれています)
          </p>
          <p v-if="!isLoading && (!allCardsRaw[selectedRarity] || (Array.isArray(allCardsRaw[selectedRarity]) && allCardsRaw[selectedRarity].length === 0))">
            (選択中の「{{ selectedRarity }}」のデータが見つからないか、空のようです。CSVファイルの内容やコンソールのログを確認してください。)
          </p>
        </div>
      </main>

      <button v-if="!isEditingStarRank && showScrollToTopButton" @click="scrollToTop" class="scroll-to-top-button">
        ↑ Top
      </button>
    </div>
  </div>
</template>

<style>
body {
  margin: 0;
  font-family: 'M PLUS Rounded 1c', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  background-color: #0a0f1f; /* 全体の背景を暗く */
  color: #e0e0e0;       /* 基本の文字色を明るく */
  line-height: 1.6;
  padding-top: 130px; /* 固定ヘッダーの高さ (要調整) */
}

#app-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.app-header {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  background: linear-gradient(135deg, #3c006b 0%, #002c5f 100%); /* よりダークなグラデーション */
  color: white;
  padding: 12px 20px;
  box-shadow: 0 3px 8px rgba(0,0,0,0.25); /* 影を少し濃く */
  z-index: 1000;
  box-sizing: border-box;
}
.app-header h1 {
  text-align: center;
  margin: 0 0 10px 0;
  font-size: 2em;
  font-weight: 700;
  color: #00f0ff; /* タイトルをネオンシアンに */
  text-shadow: 0 0 5px #00f0ff, 0 0 10px rgba(0, 240, 255, 0.7);
}
.stats-bar {
  text-align: center;
  font-size: 0.9em;
  background-color: rgba(10, 15, 31, 0.7); /* ヘッダー背景に合わせて少し暗く */
  padding: 10px;
  border-radius: 6px;
  margin-top: 8px;
  color: #c7d2fe; /* 明るめの文字色 */
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
  border-top: 1px solid #303850; /* 区切り線 */
}
.stats-bar p {
  margin: 0;
}

.main-content {
  /* 特に変更なし */
}

.controls, .filters {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 20px;
  padding: 16px;
  background-color: rgba(27, 34, 59, 0.85); /* フィルターエリアの背景も暗めに */
  border-radius: 8px;
  border: 1px solid #4a5578; /* アクセントライン */
  box-shadow: 0 2px 5px rgba(0,0,0,0.2);
}

.control-group, .filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

label {
  font-weight: 500;
  color: #00f0ff; /* ラベル文字色をネオンシアンに */
  font-size: 0.9em;
}

/* ▼▼▼ select と input のスタイルをサイバーパンク風に修正 ▼▼▼ */
select, .filter-input {
  padding: 10px 14px;
  border-radius: 4px;
  border: 1px solid #4a5578;
  background-color: #111827; /* 暗い入力背景 */
  color: #c7d2fe; /* 明るい入力文字色 */
  font-size: 0.95em;
  flex-grow: 1;
  min-width: 150px;
  box-sizing: border-box;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%2300f0ff'%3E%3Cpath d='M7 10l5 5 5-5H7z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  background-size: 1.2em;
}
.filter-input::placeholder {
  color: #808a9f;
}

select option {
  background-color: #111827; /* オプションの背景色 */
  color: #e0e0e0;       /* オプションの文字色 */
}

select:focus, .filter-input:focus {
  border-color: #00f0ff; /* シアンでフォーカス */
  outline: none;
  box-shadow: 0 0 0 3px rgba(0, 240, 255, 0.3), 0 0 10px rgba(0, 240, 255, 0.2);
}
/* ▲▲▲ select と input のスタイルをサイバーパンク風に修正 ▲▲▲ */


button {
  padding: 9px 15px;
  border: 1px solid transparent; /* 初期ボーダーを透明に */
  border-radius: 6px;
  font-size: 0.9em;
  font-weight: 600; /* 少し太く */
  cursor: pointer;
  transition: background-color 0.2s ease, transform 0.1s ease, box-shadow 0.2s ease, border-color 0.2s ease;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
button:hover {
  transform: translateY(-1px) scale(1.02);
  box-shadow: 0 4px 8px rgba(0,0,0,0.3);
}
button:active {
  transform: translateY(0px) scale(1);
  box-shadow: inset 0 1px 3px rgba(0,0,0,0.2);
}

.clear-all-button {
  background-color: #e74c3c; /* 赤系 */
  color: white;
  border-color: #c0392b;
}
.clear-all-button:hover {
  background-color: #c0392b;
  border-color: #a5281b;
}

.edit-star-rank-button {
  background-color: #ff00ff; /* マゼンタ */
  color: #0a0f1f;
  border-color: #cc00cc;
}
.edit-star-rank-button:hover {
  background-color: #e600e6;
  border-color: #b300b3;
}

.loading-indicator, .no-cards {
  text-align: center;
  padding: 40px 20px;
  font-size: 1.1em;
  color: #9ca3af; /* 少し明るいグレー */
  background-color: rgba(27, 34, 59, 0.8); /* 半透明の暗い背景 */
  border-radius: 8px;
  margin-top: 24px;
  border: 1px solid #4a5578;
}
.no-cards p {
  margin: 8px 0;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  gap: 20px;
}

.scroll-to-top-button {
  position: fixed;
  bottom: 30px;
  right: 30px;
  padding: 0;
  width: 50px;
  height: 50px;
  background-color: #00f0ff; /* シアン */
  color: #0a0f1f; /* 暗い文字色 */
  border: none;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 0 15px rgba(0, 240, 255, 0.5), 0 0 25px rgba(0, 240, 255, 0.3); /* グロー強め */
  z-index: 1001;
  opacity: 0.9;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.3em;
  text-shadow: none;
}
.scroll-to-top-button:hover {
  opacity: 1;
  transform: scale(1.15);
  box-shadow: 0 0 25px rgba(0, 240, 255, 0.7), 0 0 35px rgba(0, 240, 255, 0.5);
}
</style>
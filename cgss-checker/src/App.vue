<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import Papa from 'papaparse';
import CardItem from './components/CardItem.vue';

// --- データと状態管理 ---
const allCardsRaw = ref({});
const selectedRarity = ref('SSレア');
const ownedCards = ref({});
const isLoading = ref(false);

const rarityMapping = {
  'ノーマル': { folder: 'N', csv: '/data/csv/cgss_n_card_list.csv' },
  'レア':    { folder: 'R', csv: '/data/csv/cgss_r_card_list.csv' },
  'Sレア':   { folder: 'SR', csv: '/data/csv/cgss_sr_card_list.csv' },
  'SSレア':  { folder: 'SSR', csv: '/data/csv/cgss_ssr_card_list.csv' }
};

const searchTerm = ref('');
const selectedAttribute = ref('All');
const showOwned = ref('All');
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
  if (confirm('本当に全てのカードの所持チェックをクリアしますか？この操作は元に戻せません。')) {
    ownedCards.value = {};
    saveOwnedDataToLocalStorage();
    console.log('All owned checks cleared.');
  }
};

async function loadCsvData(rarityKey) {
  const targetRarityInfo = rarityMapping[rarityKey];
  if (!targetRarityInfo || !targetRarityInfo.csv) {
    console.error(`CSV file path not found for rarity: ${rarityKey}`);
    return [];
  }
  const filePath = targetRarityInfo.csv;
  console.log(`Fetching CSV for ${rarityKey} from ${filePath}...`);
  try {
    const response = await fetch(filePath);
    if (!response.ok) {
      console.error(`Failed to fetch ${filePath}: ${response.status} ${response.statusText}`);
      return [];
    }
    const csvText = await response.text();
    return new Promise((resolve, reject) => {
      Papa.parse(csvText, {
        header: true,
        skipEmptyLines: true,
        complete: (results) => {
          const processedData = results.data
            .filter(card => card && typeof card.id === 'string' && card.id.trim() !== '' && typeof card.name === 'string' && card.name.trim() !== '')
            .map(card => {
              const cardRarityTrimmed = String(card.rarity || '').trim();
              const currentRarityInfo = rarityMapping[cardRarityTrimmed];
              if (!currentRarityInfo) {
                return {
                  id: String(card.id || 'unknown').trim(), name: String(card.name || 'Unknown Name').trim(), rarity: cardRarityTrimmed || 'Unknown Rarity',
                  image_url: String(card.image_url || '').trim(), detail_url: String(card.detail_url || '').trim(), attribute: String(card.attribute || 'Unknown').trim(),
                  availability: String(card.availability || '').trim(), filter_category: String(card.filter_category || '').trim(),
                  local_image_url: '/data/images/default_image.png',
                };
              }
              const cardId = String(card.id).trim();
              let cardNameForFile = String(card.name).trim();
              cardNameForFile = cardNameForFile.replace(/[\\/:*?"<>|#]/g, '_');
              const filename = `${cardId}_${cardNameForFile}.jpg`;
              return {
                id: cardId, name: String(card.name).trim(), rarity: cardRarityTrimmed, image_url: String(card.image_url || '').trim(),
                detail_url: String(card.detail_url || '').trim(), attribute: String(card.attribute || 'Unknown').trim(),
                availability: String(card.availability || '').trim(), filter_category: String(card.filter_category || '').trim(),
                local_image_url: `/data/images/${currentRarityInfo.folder}/${filename}`,
              };
            });
          resolve(processedData);
        },
        error: (error) => reject(error)
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

function handleToggleOwned(clickedCard) {
  if (!clickedCard || !clickedCard.id) return;
  const cardId = String(clickedCard.id);
  if (ownedCards.value[cardId]) { delete ownedCards.value[cardId]; } else { ownedCards.value[cardId] = true; }
  saveOwnedDataToLocalStorage();
}

const cardsForSelectedRarity = computed(() => {
  const rawData = allCardsRaw.value[selectedRarity.value];
  if (!Array.isArray(rawData)) return [];
  return rawData.map(card => ({ ...card, owned: !!ownedCards.value[String(card.id)] }));
});

const ownedCountForSelectedRarity = computed(() => {
  const currentCards = cardsForSelectedRarity.value;
  if (!Array.isArray(currentCards)) return 0;
  return currentCards.filter(card => card.owned).length;
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
      if (card.filter_category) {
        categories.add(card.filter_category);
      }
    });
  }
  return Array.from(categories).sort((a, b) => {
      if (a === 'All') return -1;
      if (b === 'All') return 1;
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
    if (showOwned.value === 'Owned') ownedMatch = card.owned;
    else if (showOwned.value === 'NotOwned') ownedMatch = !card.owned;
    return nameMatch && attributeMatch && categoryMatch && ownedMatch;
  });
});

const rarityOptions = computed(() => Object.keys(rarityMapping));
const attributeOptions = ref(['All', 'Cu', 'Co', 'Pa', 'Unknown']);

onMounted(async () => {
  loadOwnedDataFromLocalStorage();
  await loadCardsForCurrentRarity();
  window.addEventListener('scroll', handleScroll);
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
            <option value="Owned">所持のみ</option>
            <option value="NotOwned">未所持のみ</option>
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
          @toggle-owned="handleToggleOwned"
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

    <button v-if="showScrollToTopButton" @click="scrollToTop" class="scroll-to-top-button">
      ↑ Top
    </button>
  </div>
</template>

<style>
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  background-color: #f0f2f5;
  color: #333;
  padding-top: 120px; /* 固定ヘッダーの高さを考慮 (調整が必要) */
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
  background-color: #fff;
  padding: 10px 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  z-index: 1000;
  box-sizing: border-box;
}
.app-header h1 {
  text-align: center;
  margin: 0 0 10px 0;
  color: #1890ff;
}
.stats-bar {
  text-align: center;
  font-size: 0.9em;
  color: #555;
  border-top: 1px solid #eee;
  padding-top: 8px;
  margin-top: 8px;
}
.stats-bar p {
  margin: 0;
}

.main-content {
  /* padding-topはbody側で対応 */
}

.controls, .filters {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  margin-bottom: 20px;
  padding: 15px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.control-group, .filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

label {
  font-weight: 500;
}

select, .filter-input {
  padding: 8px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  font-size: 1em;
}
.filter-input {
  flex-grow: 1;
}

.loading-indicator, .no-cards {
  text-align: center;
  padding: 40px 20px;
  font-size: 1.1em;
  color: #777;
  background-color: #fff;
  border-radius: 8px;
  margin-top: 20px;
}
.no-cards p {
  margin: 5px 0;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 20px;
}

.scroll-to-top-button {
  position: fixed;
  bottom: 30px;
  right: 30px;
  padding: 10px 15px;
  background-color: #1890ff;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  box-shadow: 0 2px 5px rgba(0,0,0,0.2);
  z-index: 1001;
  opacity: 0.8;
  transition: opacity 0.3s ease;
}

.scroll-to-top-button:hover {
  opacity: 1;
}

.clear-all-button {
  padding: 8px 12px;
  background-color: #ff4d4f;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9em;
}
.clear-all-button:hover {
  background-color: #d9363e;
}
</style>
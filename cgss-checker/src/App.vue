<template>
  <div id="app">
    <header class="header">
      <h1>デレステカードチェッカー</h1>
      <p>
        選択中レアリティ（{{ rarityLabel }}）:
        {{ checkedCards.length }} / {{ totalCards.length }}
        ({{ Math.round((checkedCards.length / totalCards.length) * 100) || 0 }}%)
        | 表示中: {{ filteredCards.length }}枚 |
        総所持数(全レアリティ): {{ totalChecked }}
      </p>
      <button @click="showEditor = !showEditor">スターランク編集</button>
    </header>

    <StarRankEditor v-if="showEditor" @close="showEditor = false" @updated="reload" />

    <div class="filters">
      <label>レアリティ: </label>
      <select v-model="rarity" @change="loadCsv">
        <option v-for="r in rarities" :key="r">{{ r }}</option>
      </select>
      <button @click="clearAll">全チェッククリア</button>
    </div>

    <div class="filters">
      <input v-model="search" placeholder="アイドル名で検索..." />
      <select v-model="filter.attribute">
        <option value="">全属性</option>
        <option value="Cute">キュート</option>
        <option value="Cool">クール</option>
        <option value="Passion">パッション</option>
      </select>
      <select v-model="filter.category">
        <option value="">すべて</option>
        <option value="恒常">恒常</option>
        <option value="限定">限定</option>
        <option value="フェス">フェス</option>
      </select>
      <select v-model="filter.status">
        <option value="">すべて</option>
        <option value="owned">所持</option>
        <option value="unowned">未所持</option>
      </select>
    </div>

    <div class="card-list">
      <div v-if="filteredCards.length === 0" class="empty">
        表示するカードがありません。フィルター条件を見直してください。
        <br />
        (選択中の「{{ rarity }}」のデータが見つからないか、空のようです。CSVファイルの内容やコンソールのログを確認してください。)
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import Papa from 'papaparse'
import StarRankEditor from './views/StarRankEditor.vue'

const showEditor = ref(false)
const search = ref('')
const filter = ref({ attribute: '', category: '', status: '' })
const rarity = ref('SSレア')

const rarities = ['ノーマル', 'レア', 'Sレア', 'SSレア']
const csvMap = {
  'ノーマル': 'cgss_n_card_list.csv',
  'レア': 'cgss_r_card_list.csv',
  'Sレア': 'cgss_sr_card_list.csv',
  'SSレア': 'cgss_ssr_card_list.csv'
}

const totalCards = ref([])
const checkedCards = ref([])

const rarityLabel = computed(() => rarity.value)
const totalChecked = computed(() => checkedCards.value.length)

const filteredCards = computed(() =>
  totalCards.value
    .filter(card => !search.value || card.name?.includes(search.value))
    .filter(card => !filter.value.attribute || card.attribute === filter.value.attribute)
    .filter(card => !filter.value.category || card.category === filter.value.category)
    .filter(card => {
      if (filter.value.status === 'owned') return card.checked
      if (filter.value.status === 'unowned') return !card.checked
      return true
    })
)

const loadCsv = async () => {
  const filename = csvMap[rarity.value]
  const url = new URL(`/data/csv/${filename}`, import.meta.env.BASE_URL).href
  console.log(`Fetching CSV for ${rarity.value} from ${url}...`)

  try {
    const response = await fetch(url)
    if (!response.ok) throw new Error(`status ${response.status}`)
    const text = await response.text()
    const result = Papa.parse(text, { header: true })
    totalCards.value = result.data.filter(row => row.name)
    checkedCards.value = totalCards.value.filter(card => card.checked === 'true')
  } catch (err) {
    console.error(`Failed to fetch ${url}:`, err.message)
    totalCards.value = []
    checkedCards.value = []
  }
}

const clearAll = () => {
  totalCards.value.forEach(card => (card.checked = false))
  checkedCards.value = []
}

const reload = () => {
  loadCsv()
}

onMounted(() => {
  console.log('App.vue onMounted started.')
  loadCsv()
})
</script>

<style scoped>
.header {
  background: linear-gradient(to right, #4facfe, #00f2fe);
  color: white;
  padding: 10px;
  text-align: center;
}
.filters {
  margin: 10px;
  display: flex;
  gap: 10px;
}
.empty {
  text-align: center;
  margin-top: 20px;
}
</style>

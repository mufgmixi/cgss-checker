<script setup>
import { ref, onMounted } from 'vue'
import Papa from 'papaparse'

const rarities = ['ノーマル', 'レア', 'Sレア', 'SSレア']
const cardData = ref({})

const loadCsv = async (rarity) => {
  const filename = {
    ノーマル: 'cgss_n_card_list.csv',
    レア: 'cgss_r_card_list.csv',
    Sレア: 'cgss_sr_card_list.csv',
    SSレア: 'cgss_ssr_card_list.csv'
  }[rarity]

  const url = new URL(`/data/csv/${filename}`, import.meta.env.BASE_URL).href
  console.log(`Fetching CSV for editor: ${rarity} from ${url}...`)

  try {
    const response = await fetch(url)
    if (!response.ok) throw new Error(`${response.status}`)
    const text = await response.text()
    const result = Papa.parse(text, { header: true })
    cardData.value[rarity] = result.data
  } catch (error) {
    console.error(`Failed to fetch ${url} for editor: ${error.message}`)
    cardData.value[rarity] = []
  }
}

onMounted(async () => {
  for (const rarity of rarities) {
    await loadCsv(rarity)
  }
  console.log(`All cards loaded for editing. Total: ${
    Object.values(cardData.value).reduce((sum, list) => sum + list.length, 0)
  }`)
})
</script>

<template>
  <div>
    <h2>スターランク編集</h2>
    <p v-if="Object.values(cardData).every(list => list.length === 0)">
      データが読み込めませんでした。
    </p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const allCards = ref([]);

const rarities = ['ノーマル', 'レア', 'Sレア', 'SSレア'];
const csvMap = {
  'ノーマル': 'cgss_n_card_list.csv',
  'レア': 'cgss_r_card_list.csv',
  'Sレア': 'cgss_sr_card_list.csv',
  'SSレア': 'cgss_ssr_card_list.csv'
};

const loadEditorData = async () => {
  const base = import.meta.env.BASE_URL;

  for (const rarity of rarities) {
    const csvFile = csvMap[rarity];
    const url = `${base}data/csv/${csvFile}`;
    console.log(`Fetching CSV for editor: ${rarity} from ${url}...`);
    try {
      const res = await fetch(url);
      const text = await res.text();
      const lines = text.trim().split('\n');
      const cards = lines.map(line => line.split(','));
      allCards.value.push(...cards);
    } catch (e) {
      console.warn(`Failed to fetch ${url} for editor: ${e}`);
    }
  }
};

onMounted(() => {
  loadEditorData();
});
</script>

<template>
  <div>
    <h2>スターランクエディタ</h2>
    <p>カード数: {{ allCards.length }}</p>
    <ul>
      <li v-for="card in allCards" :key="card[0]">{{ card.join(', ') }}</li>
    </ul>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const cards = ref([]);
const rarity = ref('SSレア');

const rarityMap = {
  'ノーマル': { folder: 'N', csv: 'cgss_n_card_list.csv' },
  'レア': { folder: 'R', csv: 'cgss_r_card_list.csv' },
  'Sレア': { folder: 'SR', csv: 'cgss_sr_card_list.csv' },
  'SSレア': { folder: 'SSR', csv: 'cgss_ssr_card_list.csv' }
};

const loadCSV = async () => {
  const target = rarityMap[rarity.value];
  const base = import.meta.env.BASE_URL;
  const url = `${base}data/csv/${target.csv}`;
  console.log(`Fetching CSV from ${url}...`);

  try {
    const res = await fetch(url);
    const text = await res.text();
    const lines = text.trim().split('\n');
    cards.value = lines.map(line => line.split(','));
  } catch (e) {
    console.error(`Failed to fetch ${url}`, e);
  }
};

onMounted(() => {
  console.log('App.vue onMounted started.');
  loadCSV();
});
</script>

<template>
  <div>
    <h1>デレステカードチェッカー</h1>
    <select v-model="rarity" @change="loadCSV">
      <option v-for="key in Object.keys(rarityMap)" :key="key">{{ key }}</option>
    </select>
    <ul>
      <li v-for="card in cards" :key="card[0]">{{ card.join(', ') }}</li>
    </ul>
  </div>
</template>

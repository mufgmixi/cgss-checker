import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
from urllib.parse import urljoin, urlparse
import json # JSON保存用

BASE_URL = "https://imas.gamedbs.jp"

# 属性ごとの情報を定義 (URLを更新)
ATTRIBUTE_TARGETS = {
    "Cu": {
        "url": "https://imas.gamedbs.jp/cgss/card?q=&a=%E3%82%AD%E3%83%A5%E3%83%BC%E3%83%88&c=0&s=0&p=0",
        "label": "Cu"
    },
    "Co": {
        "url": "https://imas.gamedbs.jp/cgss/card?q=&a=%E3%82%AF%E3%83%BC%E3%83%AB&c=0&s=0&p=0",
        "label": "Co"
    },
    "Pa": {
        "url": "https://imas.gamedbs.jp/cgss/card?q=&a=%E3%83%91%E3%83%83%E3%82%B7%E3%83%A7%E3%83%B3&c=0&s=0&p=0",
        "label": "Pa"
    }
}

def get_soup(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_card_ids_from_page(page_url):
    """1ページ分のカードID (またはユニークキー) を抽出する"""
    soup = get_soup(page_url)
    if not soup:
        return [], None

    card_ids = set()
    card_list_ul = soup.select_one('ul.dblst.flexbox.flexwrap')
    if not card_list_ul:
        print(f"Card list container (ul.dblst.flexbox.flexwrap) not found on {page_url}")
    
    card_items = card_list_ul.select('li > a') if card_list_ul else []

    for item_anchor in card_items:
        detail_href = item_anchor.get('href')
        if detail_href:
            detail_url = urljoin(BASE_URL, detail_href)
            try:
                path_parts = urlparse(detail_url).path.split('/')
                fragment = urlparse(detail_url).fragment
                card_id_str = None
                if fragment and fragment.startswith('card-'):
                    card_id_str = fragment.split('-')[-1]
                elif len(path_parts) > 1 and path_parts[-1].isdigit():
                     card_id_str = path_parts[-1]
                
                if card_id_str and card_id_str.isdigit():
                    card_ids.add(card_id_str)
            except Exception:
                pass

    pagination_div = soup.select_one('div.pagination')
    next_page_url = None
    if pagination_div:
        next_page_tag = pagination_div.select_one('a.page-link[rel="next"]')
        if next_page_tag and next_page_tag.has_attr('href'):
            next_href = next_page_tag['href']
            # page_url (現在のURL) を基準に解決するのが安全
            next_page_url = urljoin(page_url, next_href)
    return list(card_ids), next_page_url

def collect_attribute_card_ids():
    """各属性の全カードIDを収集する"""
    all_attribute_ids = {}

    for attr_key, target_info in ATTRIBUTE_TARGETS.items():
        print(f"\n--- Collecting card IDs for Attribute: {attr_key} ---")
        current_url = target_info["url"]
        page_num = 1
        attribute_card_set = set()

        while current_url:
            print(f"Scraping page {page_num} for {attr_key}: {current_url}")
            ids_on_page, next_url = extract_card_ids_from_page(current_url)
            
            if ids_on_page:
                attribute_card_set.update(ids_on_page)
                print(f"  Found {len(ids_on_page)} IDs on this page. Total unique IDs for {attr_key}: {len(attribute_card_set)}")
            elif page_num == 1:
                print(f"  No cards found on the first page for {attr_key}.")
            
            current_url = next_url
            page_num += 1
            if current_url:
                # テスト用にページ数制限をかける場合
                # if page_num >= 3: # 各属性2ページまで（テスト用）
                #     print(f"  Reached page limit for {attr_key} testing.")
                #     break
                time.sleep(1) 
        
        all_attribute_ids[attr_key] = attribute_card_set
        print(f"Finished collecting for {attr_key}. Total {len(attribute_card_set)} unique card IDs found.")
        
        if attr_key != list(ATTRIBUTE_TARGETS.keys())[-1]:
            print("Waiting 3 seconds before next attribute...")
            time.sleep(3)

    return all_attribute_ids

if __name__ == "__main__":
    attribute_id_map = collect_attribute_card_ids()

    for attr, ids in attribute_id_map.items():
        print(f"\nAttribute {attr} has {len(ids)} cards. First 5: {list(ids)[:5]}")

    try:
        with open("attribute_card_ids.json", "w", encoding="utf-8") as f:
            json_friendly_map = {k: list(v) for k, v in attribute_id_map.items()}
            json.dump(json_friendly_map, f, ensure_ascii=False, indent=2)
        print("\nAttribute card ID map saved to attribute_card_ids.json")
    except Exception as e:
        print(f"\nError saving attribute card ID map to JSON: {e}")
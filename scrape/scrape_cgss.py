import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
import re
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse

BASE_URL = "https://imas.gamedbs.jp"

# 各レアリティの情報を辞書として定義
RARITY_TARGETS = {
    "SSR": {
        "url": "https://imas.gamedbs.jp/cgss/card?q=&r=SS%E3%83%AC%E3%82%A2&c=0&s=0&p=0",
        "rarity_label": "SSレア", # または "SSR"
        "filename": "cgss_ssr_card_list.csv"
    },
    "SR": {
        "url": "https://imas.gamedbs.jp/cgss/card?q=&r=S%E3%83%AC%E3%82%A2&c=0&s=0&p=0",
        "rarity_label": "Sレア", # または "SR"
        "filename": "cgss_sr_card_list.csv"
    },
    "R": {
        "url": "https://imas.gamedbs.jp/cgss/card?q=&r=%E3%83%AC%E3%82%A2&c=0&s=0&p=0",
        "rarity_label": "レア", # または "R"
        "filename": "cgss_r_card_list.csv"
    },
    "N": {
        "url": "https://imas.gamedbs.jp/cgss/card?q=&r=%E3%83%8E%E3%83%BC%E3%83%9E%E3%83%AB&c=0&s=0&p=0", # ノーマルのURLを修正
        "rarity_label": "ノーマル", # または "N"
        "filename": "cgss_n_card_list.csv"
    }
}

def get_soup(url):
    """指定されたURLからHTMLを取得し、BeautifulSoupオブジェクトを返す"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def scrape_cards_from_page(page_url, current_rarity_label):
    """1ページ分のカード情報をスクレイピングする"""
    soup = get_soup(page_url)
    if not soup:
        return [], None

    cards_data = []
    card_list_ul = soup.select_one('ul.dblst.flexbox.flexwrap')
    if not card_list_ul:
        print(f"Card list container (ul.dblst.flexbox.flexwrap) not found on {page_url}")

    card_items = card_list_ul.select('li > a') if card_list_ul else []

    for item_anchor in card_items:
        card_info = {}
        detail_href = item_anchor.get('href')
        if detail_href:
            card_info['detail_url'] = urljoin(BASE_URL, detail_href)
            try:
                path_parts = urlparse(card_info['detail_url']).path.split('/')
                fragment = urlparse(card_info['detail_url']).fragment
                if fragment and fragment.startswith('card-'):
                    card_id_str = fragment.split('-')[-1]
                    if card_id_str.isdigit():
                        card_info['id'] = card_id_str
                    else:
                        if len(path_parts) > 1 and path_parts[-1].isdigit():
                             card_info['id'] = path_parts[-1]
                        else:
                             card_info['id'] = "N/A"
                elif len(path_parts) > 1 and path_parts[-1].isdigit():
                     card_info['id'] = path_parts[-1]
                else:
                    card_info['id'] = "N/A"
            except Exception as e:
                print(f"Error parsing ID from URL {card_info['detail_url']}: {e}")
                card_info['id'] = "N/A"
        else:
            card_info['detail_url'] = "N/A"
            card_info['id'] = "N/A"

        name_div = item_anchor.select_one('div')
        if name_div:
            card_info['name'] = name_div.get_text(strip=True)
        else:
            card_info['name'] = "N/A"

        img_tag = item_anchor.select_one('img.lazy')
        if img_tag and img_tag.has_attr('data-original'):
            img_src = img_tag['data-original']
            card_info['image_url'] = urljoin(BASE_URL, img_src)
        elif img_tag and img_tag.has_attr('src'):
            img_src = img_tag['src']
            card_info['image_url'] = urljoin(BASE_URL, img_src)
        else:
            card_info['image_url'] = "N/A"

        card_info['rarity'] = current_rarity_label

        if card_info['id'] != "N/A" and card_info['id'].isdigit():
            cards_data.append(card_info)

    pagination_div = soup.select_one('div.pagination')
    next_page_url = None
    if pagination_div:
        next_page_tag = pagination_div.select_one('a.page-link[rel="next"]')
        if next_page_tag and next_page_tag.has_attr('href'):
            next_href = next_page_tag['href']
            parsed_next_href = urlparse(next_href)
            if parsed_next_href.scheme and parsed_next_href.netloc:
                next_page_url = next_href
            elif parsed_next_href.query and not parsed_next_href.path and not parsed_next_href.scheme and not parsed_next_href.netloc :
                current_parsed_url = urlparse(page_url)
                new_query_string = parsed_next_href.query
                next_page_url = urlunparse(
                    (current_parsed_url.scheme or "https", # httpかhttpsか不明な場合に備える
                     current_parsed_url.netloc or urlparse(BASE_URL).netloc, # 同上
                     current_parsed_url.path,
                     current_parsed_url.params,
                     new_query_string,
                     current_parsed_url.fragment)
                )
            else: # 相対パスの場合 (例: index/50?r=...) や絶対パス (/cgss/card/index/50?r=...)
                next_page_url = urljoin(page_url, next_href) # page_url を基準にする
    return cards_data, next_page_url

def scrape_rarity(rarity_key, target_info):
    """指定されたレアリティのカードをスクレイピングする"""
    all_cards = []
    current_url = target_info["url"]
    rarity_label = target_info["rarity_label"]
    output_filename = target_info["filename"]
    page_num = 1

    print(f"\n--- Starting scrape for Rarity: {rarity_key} ---")
    print(f"Starting with URL: {current_url}")

    while current_url:
        print(f"Scraping page {page_num} for {rarity_key}: {current_url}")
        cards_on_page, next_url = scrape_cards_from_page(current_url, rarity_label)

        if cards_on_page:
            all_cards.extend(cards_on_page)
            print(f"Found {len(cards_on_page)} cards on this page.")
        elif not cards_on_page and page_num == 1 :
             print(f"No cards found on the first page for {rarity_key}: {current_url}.")
             if not next_url:
                 break
        
        current_url = next_url
        
        if current_url:
            # if page_num >= 2: # テスト用
            #     print(f"Reached page limit for {rarity_key} testing.")
            #     break
            print(f"Waiting 1 second before next page...")
            time.sleep(1)
        else:
            if all_cards or cards_on_page :
                 print(f"No more pages found or finished scraping for {rarity_key}.")
        
        page_num += 1

    if not all_cards:
        print(f"\nNo cards were scraped for Rarity: {rarity_key}.")
        return

    df = pd.DataFrame(all_cards)
    if not df.empty:
        df = df[['id', 'name', 'rarity', 'image_url', 'detail_url']]

    try:
        df.to_csv(output_filename, index=False, encoding='utf-8-sig')
        print(f"\nSuccessfully scraped {len(all_cards)} cards for Rarity: {rarity_key}.")
        print(f"Data saved to {output_filename}")
    except Exception as e:
        print(f"Error saving {rarity_key} to CSV {output_filename}: {e}")
        print(f"\nScraped data for {rarity_key} (first 5 entries):")
        for i, card in enumerate(all_cards[:5]):
            print(card)

def main():
    for rarity_key, target_info in RARITY_TARGETS.items():
        scrape_rarity(rarity_key, target_info)
        if rarity_key != list(RARITY_TARGETS.keys())[-1]:
            print("\nWaiting 3 seconds before starting next rarity...\n")
            time.sleep(3)

    print("\n\nAll scraping tasks completed.")

if __name__ == '__main__':
    main()
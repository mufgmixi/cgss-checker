import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import os
# from urllib.parse import urljoin # 今回は明示的には使っていませんが、requests内で使われる可能性はあります

# --- 設定項目 ---
# CSVファイルが保存されているディレクトリ
CSV_DIRECTORY = '.'
# 詳細ページアクセス間の待機時間 (秒)
DETAIL_PAGE_WAIT_TIME = 1.2 # サーバー負荷を考慮
# リクエストのタイムアウト時間 (秒)
REQUEST_TIMEOUT = 20
# 処理対象のCSVファイルリスト
RARITY_CSV_FILES = [
    "cgss_ssr_card_list.csv",
    "cgss_sr_card_list.csv",
    "cgss_r_card_list.csv",
    "cgss_n_card_list.csv",
]
# --- ここまで設定項目 ---

def get_soup(url, session=None):
    """指定されたURLからHTMLを取得し、BeautifulSoupオブジェクトを返す"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        if session:
            response = session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        else:
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status() # HTTPエラーがあれば例外を発生
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup
    except requests.exceptions.RequestException as e:
        print(f"  Error fetching {url}: {e}")
        return None
    except Exception as e:
        print(f"  Unexpected error fetching {url}: {e}")
        return None

def extract_availability(detail_soup):
    """詳細ページのSoupオブジェクトから「主な入手方法」を抽出する"""
    if not detail_soup:
        return "取得失敗" # もしくは pd.NA

    try:
        # ul.tblbox.flexbox.flexwrap の中から探す
        tblboxes = detail_soup.select('ul.tblbox.flexbox.flexwrap')
        
        for tblbox in tblboxes:
            # 現在のtblbox内で "主な入手方法" のli.hを探す
            li_h_tag = tblbox.find('li', class_='h', string=lambda text: text and "主な入手方法" in text.strip())
            
            if li_h_tag:
                # li.h の次の li 要素が li.d であることを期待
                li_d_tag = li_h_tag.find_next_sibling('li')
                if li_d_tag and 'd' in li_d_tag.get('class', []): # クラス'd'が含まれるか確認
                    # get_text() で取得。もし <br> があれば separator='\n' を検討
                    availability_text = li_d_tag.get_text(strip=True)
                    return availability_text
        
        # 上記で見つからなかった場合 (情報なし、または想定外の構造)
        return "情報なし" # もしくは pd.NA
            
    except Exception as e:
        print(f"    「主な入手方法」の解析中にエラー: {e}")
        return "解析エラー" # もしくは pd.NA

def main():
    # HTTPセッションを使い回す
    with requests.Session() as session:
        for csv_filename in RARITY_CSV_FILES:
            csv_filepath = os.path.join(CSV_DIRECTORY, csv_filename)
            
            if not os.path.exists(csv_filepath):
                print(f"CSVファイルが見つかりません: {csv_filepath}。スキップします。")
                continue

            print(f"\n--- {csv_filename} の「主な入手方法」情報を処理中 ---")
            try:
                df = pd.read_csv(csv_filepath)
            except Exception as e:
                print(f"  エラー: CSVファイルの読み込みに失敗 ({csv_filepath}): {e}")
                continue
            
            if 'detail_url' not in df.columns:
                print(f"  エラー: CSVファイルに 'detail_url' 列が見つかりません: {csv_filename}。スキップします。")
                continue

            # 「availability」列がなければ作成し、pd.NA (または他の初期値) で初期化
            if 'availability' not in df.columns:
                df['availability'] = pd.NA
            else:
                # 既存の列がある場合、空文字列などをpd.NAに変換しておくと後続の判定がしやすい
                df['availability'] = df['availability'].replace('', pd.NA)


            updated_count = 0
            total_rows = len(df)

            for index, row in df.iterrows():
                current_availability = row.get('availability')
                
                # 既に有効な情報がある場合はスキップ (エラーや未取得状態ではない場合)
                # pd.NA もしくはエラーを示す特定の文字列であれば再試行
                should_skip = False
                if pd.notna(current_availability): # NAではない場合
                    if current_availability not in ["取得失敗", "情報なし", "解析エラー", "未取得", "URL無効", "ページ取得失敗"]:
                        should_skip = True
                
                if should_skip:
                    # print(f"  ID {row.get('id', index)}: 既に有効な入手方法あり。スキップ。")
                    continue

                detail_url = row['detail_url']
                card_id = row.get('id', f"index_{index}") 

                if pd.isna(detail_url) or not isinstance(detail_url, str):
                    print(f"  ID {card_id}: detail_urlが無効です。スキップ。")
                    # detail_url が無効な場合、availability を更新 (元がNAの場合のみ)
                    if pd.isna(df.loc[index, 'availability']):
                        df.loc[index, 'availability'] = "URL無効"
                    continue
                
                print(f"  処理中 ({index+1}/{total_rows}) ID: {card_id} - URL: {detail_url}")
                
                detail_soup = get_soup(detail_url, session=session)
                
                if detail_soup:
                    availability_info = extract_availability(detail_soup)
                    df.loc[index, 'availability'] = availability_info
                    if availability_info not in ["取得失敗", "情報なし", "解析エラー"]:
                        updated_count += 1
                        print(f"    -> 入手方法: {str(availability_info)[:60]}...") # 長い場合があるので一部表示
                else:
                    # get_soupでNoneが返ってきた場合 (ページ取得失敗)
                    # availability を更新 (元がNAの場合のみ)
                    if pd.isna(df.loc[index, 'availability']):
                        df.loc[index, 'availability'] = "ページ取得失敗"

                time.sleep(DETAIL_PAGE_WAIT_TIME) 

            # 更新されたDataFrameをCSVに上書き保存
            try:
                df.to_csv(csv_filepath, index=False, encoding='utf-8-sig')
                print(f"  {csv_filename} を更新しました。{updated_count} 件のカードに「主な入手方法」を新規/更新割り当てしました。")
            except Exception as e:
                print(f"  CSVファイルへの書き込みエラー ({csv_filepath}): {e}")

    print("\n全てのCSVファイルの「主な入手方法」情報更新処理が完了しました。")

if __name__ == "__main__":
    main()
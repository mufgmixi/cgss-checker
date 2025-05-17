import pandas as pd
import requests
import os
import time
from urllib.parse import urlparse
import argparse # コマンドライン引数処理用
import re # sanitize_filenameで使用

# --- 設定項目 ---
CSV_DIRECTORY = '.'
IMAGE_SAVE_DIRECTORY_BASE = 'cgss_images'
DOWNLOAD_WAIT_TIME = 1.5
SKIP_EXISTING_FILES = True
REQUEST_TIMEOUT = 20
# ----------------

# 全ての処理対象CSVファイルと情報
ALL_CSV_FILES_INFO = {
    "SSR": {"filename": "cgss_ssr_card_list.csv", "subdir": "SSR"},
    "SR": {"filename": "cgss_sr_card_list.csv", "subdir": "SR"},
    "R": {"filename": "cgss_r_card_list.csv", "subdir": "R"},
    "N": {"filename": "cgss_n_card_list.csv", "subdir": "N"},
}

def sanitize_filename(name):
    """ファイル名として不適切な文字を置換する"""
    name = str(name) # 念のため文字列に変換
    name = re.sub(r'[\\/:*?"<>|]', '_', name)
    # ファイル名の先頭や末尾のスペース、連続するスペースなども考慮するとより良い
    name = re.sub(r'\s+', ' ', name).strip() # 連続スペースを1つに、前後のスペース削除
    return name

def download_image(image_url, save_path, card_name="image"):
    """指定されたURLから画像をダウンロードして保存する"""
    last_message = "" # 最後にprintしたメッセージを保持 (スキップ判定用)
    try:
        if not image_url or pd.isna(image_url) or not isinstance(image_url, str) or not image_url.startswith(('http://', 'https://')):
            last_message = f"無効なURLか、URLが空です。スキップします: {image_url}"
            print(last_message)
            return False, last_message

        if SKIP_EXISTING_FILES and os.path.exists(save_path):
            last_message = f"ファイルが既に存在します。スキップ: {save_path}"
            print(last_message)
            return True, last_message # 既に存在するので成功扱い

        print(f"ダウンロード中 ({card_name}): {image_url} -> {save_path}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(image_url, headers=headers, stream=True, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        last_message = f"ダウンロード完了: {save_path}"
        print(last_message)
        return True, last_message
    except requests.exceptions.RequestException as e:
        last_message = f"ダウンロードエラー ({card_name}, URL: {image_url}): {e}"
        print(last_message)
        return False, last_message
    except Exception as e:
        last_message = f"予期せぬエラー ({card_name}, URL: {image_url}, Path: {save_path}): {e}"
        print(last_message)
        return False, last_message

def main():
    parser = argparse.ArgumentParser(description="デレステカード画像をCSVのURLリストに基づいてダウンロードします。")
    parser.add_argument(
        "-r", "--rarity",
        nargs='+', # 1つ以上の引数をリストとして受け取る
        choices=ALL_CSV_FILES_INFO.keys(), # SSR, SR, R, N から選択
        help=f"処理するレアリティを指定します (例: SSR SR)。指定しない場合は全てのレアリティが対象になります。選択肢: {', '.join(ALL_CSV_FILES_INFO.keys())}",
        default=list(ALL_CSV_FILES_INFO.keys()) # デフォルトは全レアリティ
    )
    args = parser.parse_args()

    if not os.path.exists(IMAGE_SAVE_DIRECTORY_BASE):
        os.makedirs(IMAGE_SAVE_DIRECTORY_BASE)
        print(f"ベース画像保存ディレクトリを作成しました: {IMAGE_SAVE_DIRECTORY_BASE}")

    total_images_processed = 0
    total_images_downloaded = 0
    total_images_skipped = 0
    total_images_failed = 0

    # コマンドライン引数で指定されたレアリティのみを対象にする
    selected_rarities_info = {key: ALL_CSV_FILES_INFO[key] for key in args.rarity if key in ALL_CSV_FILES_INFO}

    if not selected_rarities_info:
        print("処理対象のレアリティが指定されていないか、無効な指定です。")
        return

    print(f"処理対象のレアリティ: {', '.join(selected_rarities_info.keys())}")


    for rarity, info in selected_rarities_info.items():
        csv_file_name = info["filename"]
        rarity_subdir = info["subdir"]
        csv_file_path = os.path.join(CSV_DIRECTORY, csv_file_name)

        current_save_dir = os.path.join(IMAGE_SAVE_DIRECTORY_BASE, rarity_subdir)
        if not os.path.exists(current_save_dir):
            os.makedirs(current_save_dir)
            print(f"{rarity}用の画像保存ディレクトリを作成しました: {current_save_dir}")

        if not os.path.exists(csv_file_path):
            print(f"CSVファイルが見つかりません: {csv_file_path}。このレアリティ ({rarity}) の処理をスキップします。")
            continue

        print(f"\n--- {rarity} の画像ダウンロード処理を開始します ({csv_file_name}) ---")
        try:
            df = pd.read_csv(csv_file_path)
        except FileNotFoundError:
            print(f"エラー: CSVファイルが見つかりません: {csv_file_path}")
            continue
        except Exception as e:
            print(f"エラー: CSVファイルの読み込みに失敗しました ({csv_file_path}): {e}")
            continue

        if 'image_url' not in df.columns:
            print(f"エラー: CSVファイルに 'image_url' 列が見つかりません: {csv_file_name}")
            continue
        if 'id' not in df.columns and 'name' not in df.columns:
            print(f"エラー: CSVファイルに 'id' または 'name' 列が見つかりません (ファイル名生成のため): {csv_file_name}")
            continue

        rarity_processed = 0
        rarity_downloaded = 0
        rarity_skipped = 0
        rarity_failed = 0

        for index, row in df.iterrows():
            total_images_processed += 1
            rarity_processed += 1

            image_url = row.get('image_url')
            card_id = row.get('id', '')
            card_name_original = row.get('name', f'card_{index}')
            safe_card_name = sanitize_filename(card_name_original)

            if not image_url or pd.isna(image_url) or not isinstance(image_url, str):
                print(f"無効な画像URLです。スキップします (ID: {card_id}, Name: {safe_card_name})")
                total_images_failed +=1
                rarity_failed += 1
                continue

            try:
                parsed_url = urlparse(image_url)
                original_filename = os.path.basename(parsed_url.path)
                _, ext = os.path.splitext(original_filename)
                if not ext or len(ext) > 5 : # 拡張子が長すぎる場合も考慮
                    ext = '.jpg'
            except Exception:
                ext = '.jpg'

            if card_id:
                # IDは数値のはずなので、文字列変換してファイル名に使う
                filename_base = f"{str(card_id)}_{safe_card_name}"
            else:
                filename_base = safe_card_name
            
            filename = filename_base + ext

            max_filename_len = 100 # OSのファイル名長制限を考慮
            if len(filename) > max_filename_len:
                name_part = filename_base[:max_filename_len - len(ext) -1] # 拡張子と区切り文字の分を考慮
                filename = name_part + "_" + ext if not name_part.endswith("_") else name_part + ext


            save_path = os.path.join(current_save_dir, filename)

            success, message = download_image(image_url, save_path, card_name=f"{rarity} ID:{card_id} Name:{safe_card_name}")

            if success:
                if "ファイルが既に存在します" in message:
                    total_images_skipped += 1
                    rarity_skipped += 1
                else:
                    total_images_downloaded += 1
                    rarity_downloaded += 1
            else:
                total_images_failed += 1
                rarity_failed += 1

            time.sleep(DOWNLOAD_WAIT_TIME)
        
        print(f"--- {rarity} の処理完了 ---")
        print(f"  処理数: {rarity_processed}, ダウンロード成功: {rarity_downloaded}, スキップ: {rarity_skipped}, 失敗: {rarity_failed}")


    print("\n\n--- 全ての指定された画像ダウンロード処理が完了しました ---")
    print(f"処理した総画像数 (指定レアリティ合計): {total_images_processed}")
    print(f"ダウンロード成功数 (指定レアリティ合計): {total_images_downloaded}")
    print(f"スキップ数 (既存ファイル) (指定レアリティ合計): {total_images_skipped}")
    print(f"ダウンロード失敗数 (指定レアリティ合計): {total_images_failed}")

if __name__ == '__main__':
    main()
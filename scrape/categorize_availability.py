import pandas as pd
import os
import re
from collections import Counter

# --- 設定項目 ---
CSV_DIRECTORY = '.'
RARITY_CSV_FILES_INFO = {
    "SSR": {"filename": "cgss_ssr_card_list.csv", "is_N_or_R": False},
    "SR": {"filename": "cgss_sr_card_list.csv", "is_N_or_R": False},
    "R": {"filename": "cgss_r_card_list.csv", "is_N_or_R": True},
    "N": {"filename": "cgss_n_card_list.csv", "is_N_or_R": True},
}
OUTPUT_COLUMN_NAME = 'filter_category'
# --- ここまで設定項目 ---

def normalize_text_for_filter(text):
    if pd.isna(text):
        return ""
    text = str(text)
    text = text.lower()
    text = re.sub(r'\s+', ' ', text).strip()
    text = text.replace("プラチナオーディションガシャ", "プラチナガシャ")
    text = text.replace("ライブ", "live")
    return text

def determine_filter_category(availability_text_original, is_card_N_or_R):
    if pd.isna(availability_text_original) or not str(availability_text_original).strip():
        # availabilityが空またはNaNの場合、レアリティに関わらず「恒常」（初期カード等と想定）
        return "恒常"

    text = normalize_text_for_filter(availability_text_original)
    original_text_for_gacha_name_check = str(availability_text_original)

    # --- 優先的に判定する特殊ケース ---
    collab_event_names = [
        "ハーモニクス", "ももクロ×デレステコラボイベント", "星街すいせい×デレステコラボ"
    ]
    if any(collab_event.lower() in text for collab_event in collab_event_names):
        return "イベント報酬(コラボ)"
    if "stage for cinderellaガシャ" in text:
        return "期間限定ガシャ"
    if "4/1限定コミュ" in text:
        return "イベント報酬"
    if "＜イベント限定アイドル＞" in availability_text_original:
        return "イベント報酬"
    if "コラボガシャ" in text and "＜期間限定アイドル＞" in availability_text_original:
        return "期間限定ガシャ(コラボ)"

    # --- 通常の判定ロジック ---
    fes_keywords = ["シンデレラフェス", "フェス限定", "ノワール限定", "ブラン限定", "ドミナントガシャ"]
    if any(kw in text for kw in fes_keywords):
        if "復刻" in text:
            return "フェス限定(復刻)"
        return "フェス限定"

    event_keywords = [
        "イベント", "報酬", "ランキング", "ポイント", "メダル", "live carnival", "live groove",
        "live parade", "シンデレラキャラバン", "ススメ！シンデレラロード", "アイドルプロデュース",
        "live infinity"
    ]
    specific_event_reward_patterns = ["＜カーニバルメダルチャンス報酬＞", "ポイント報酬", "ランキング報酬", "メダル交換", "期間中のlive報酬", "達成pt報酬", "動員数報酬", "map報酬", "課題クリア報酬", "イベントpt報酬", "イベント参加報酬"]
    event_name_pattern_general = r'イベント「.*?」'
    is_gacha_by_keyword = "ガシャ" in text or "gacha" in text or "スカウト" in text

    if not is_gacha_by_keyword and \
       (any(kw in text for kw in event_keywords) or \
        any(specific_event_reward_pattern in availability_text_original for specific_event_reward_pattern in specific_event_reward_patterns) or \
        (re.search(event_name_pattern_general, original_text_for_gacha_name_check, re.IGNORECASE) and not is_gacha_by_keyword) ):
        return "イベント報酬"

    limited_gacha_keywords = ["期間限定アイドル", "限定ガシャ", "期間限定"]
    date_period_pattern = r'\d{4}/\d{1,2}/\d{1,2}\s*～\s*\d{4}/\d{1,2}/\d{1,2}|\d{4}年\d{1,2}月\d{1,2}日\s*～\s*\d{1,2}月\d{1,2}日|\(\s*\d{1,2}月\d{1,2}日\s*～\s*\d{1,2}月\d{1,2}日\s*\)|（\s*\d{1,2}月\d{1,2}日\s*～\s*\d{1,2}月\d{1,2}日\s*）|（初回：\d{4}年\d{1,2}月\d{1,2}日\s*～\s*\d{1,2}月\d{1,2}日\s*14:59）'
    specific_gacha_name_patterns = [
        "アニバーサリーパーティーガシャ", "バレンタイン", "クリスマス", "ハロウィン", "温泉ガシャ", "振袖ガシャ", "ブライダル", "サマーガシャ", "水着",
        "ナイトタイムガシャ", "放課後タイムガシャ", "トラベルガシャ", "ストーリーガシャ", "セッションガシャ", "ギフトガシャ"
    ]
    is_limited_by_keyword_in_gacha_context = is_gacha_by_keyword and any(kw in text for kw in limited_gacha_keywords)
    is_limited_by_date_period_in_gacha_context = is_gacha_by_keyword and bool(re.search(date_period_pattern, text))
    is_limited_by_specific_gacha_name = is_gacha_by_keyword and any(pat.lower() in original_text_for_gacha_name_check.lower() for pat in specific_gacha_name_patterns)
    if is_limited_by_keyword_in_gacha_context or is_limited_by_date_period_in_gacha_context or is_limited_by_specific_gacha_name:
        if "復刻" in text:
            return "期間限定ガシャ(復刻)"
        return "期間限定ガシャ"

    if "初期選択" in text or "ローカルガシャ" in text:
        return "恒常"
    if "プラチナガシャ" in text:
        return "恒常"
        
    # N/R CSV のカードで、availability が空でなく、かつ上記ルールに合致しなかった場合も「恒常」
    if is_card_N_or_R:
        return "恒常"

    return "不明"


def main():
    for rarity_key, file_info in RARITY_CSV_FILES_INFO.items():
        csv_filename = file_info["filename"]
        is_N_or_R_file = file_info["is_N_or_R"]

        csv_filepath = os.path.join(CSV_DIRECTORY, csv_filename)
        if not os.path.exists(csv_filepath):
            print(f"CSVファイルが見つかりません: {csv_filepath}。スキップします。")
            continue

        print(f"\n--- {csv_filename} のフィルターカテゴリを処理中 ---")
        try:
            df = pd.read_csv(csv_filepath)
        except Exception as e:
            print(f"  エラー: CSVファイルの読み込みに失敗 ({csv_filepath}): {e}")
            continue
        
        if 'availability' not in df.columns:
            print(f"  エラー: CSVファイルに 'availability' 列が見つかりません: {csv_filename}。スキップします。")
            continue

        if OUTPUT_COLUMN_NAME not in df.columns:
            df[OUTPUT_COLUMN_NAME] = "不明"
        else:
            df[OUTPUT_COLUMN_NAME] = df[OUTPUT_COLUMN_NAME].replace('', "不明").fillna("不明")

        applied_count = 0
        changed_to_specific_count = 0

        for index, row in df.iterrows():
            availability_text = row['availability']
            current_category_in_df = df.loc[index, OUTPUT_COLUMN_NAME]
            
            new_category = determine_filter_category(availability_text, is_N_or_R_file)
            
            if current_category_in_df != new_category:
                df.loc[index, OUTPUT_COLUMN_NAME] = new_category
                applied_count += 1
                if new_category != "不明" and (current_category_in_df == "不明" or pd.isna(current_category_in_df)):
                    changed_to_specific_count +=1
                elif new_category != "不明" and current_category_in_df != "不明" and current_category_in_df != new_category :
                    changed_to_specific_count +=1

        try:
            df.to_csv(csv_filepath, index=False, encoding='utf-8-sig')
            print(f"  {csv_filename} を更新しました。{applied_count} 件のカテゴリが変更され、うち {changed_to_specific_count} 件が具体的なカテゴリに設定/更新されました。")
        except Exception as e:
            print(f"  CSVファイルへの書き込みエラー ({csv_filepath}): {e}")

    print("\n全てのCSVファイルのフィルターカテゴリ割り当て処理が完了しました。")

    print("\n--- カテゴリ別件数 (全CSV合計) ---")
    all_df_list = []
    for file_info in RARITY_CSV_FILES_INFO.values():
        csv_filepath = os.path.join(CSV_DIRECTORY, file_info["filename"])
        if os.path.exists(csv_filepath):
            try:
                df_temp = pd.read_csv(csv_filepath)
                if OUTPUT_COLUMN_NAME in df_temp.columns:
                    all_df_list.append(df_temp)
            except Exception as e:
                print(f"  集計用CSV読み込みエラー ({file_info['filename']}): {e}")
    
    if all_df_list:
        combined_df = pd.concat(all_df_list, ignore_index=True)
        print(combined_df[OUTPUT_COLUMN_NAME].value_counts(dropna=False))
        
        print("\n---「不明」カテゴリの詳細 (ID, 名前, 入手方法) ---")
        if 'availability' in combined_df.columns and 'id' in combined_df.columns and 'name' in combined_df.columns:
            unknown_cards_df = combined_df[combined_df[OUTPUT_COLUMN_NAME] == "不明"]
            if unknown_cards_df.empty:
                print("「不明」カテゴリのデータはありませんでした。")
            else:
                print(f"合計 {len(unknown_cards_df)} 件の「不明」カードがあります。")
                for index, row in unknown_cards_df.iterrows(): # 全件表示
                    card_id = row.get('id', 'N/A')
                    card_name = row.get('name', 'N/A')
                    availability_info = row.get('availability', 'N/A')
                    print(f"- ID: {card_id}, Name: {card_name}, Availability: {availability_info}")
        else:
            print("「不明」カテゴリの詳細表示に必要な列 (id, name, availability, filter_category) が揃っていません。")
            
        categories_to_list = ["イベント報酬(コラボ)", "期間限定ガシャ(コラボ)"]
        for category_to_show in categories_to_list:
            print(f"\n---「{category_to_show}」カテゴリの入手方法一覧 (ユニーク) ---")
            if 'availability' in combined_df.columns:
                category_examples_series = combined_df[combined_df[OUTPUT_COLUMN_NAME] == category_to_show]['availability']
                category_examples = category_examples_series.dropna().unique()
                if len(category_examples) == 0:
                    print(f"「{category_to_show}」カテゴリのデータはありませんでした。")
                else:
                    for ex in category_examples:
                        print(f"- {ex}")
            else:
                print("集計対象の 'availability' 列がありません。")
    else:
        print("集計できるCSVデータがありませんでした。")

if __name__ == "__main__":
    main()
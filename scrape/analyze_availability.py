import pandas as pd
import os
import re
from collections import Counter

# --- 設定項目 ---
CSV_DIRECTORY = '.'
# 分析対象のCSVファイルリスト (全レアリティ分)
RARITY_CSV_FILES = [
    "cgss_ssr_card_list.csv",
    "cgss_sr_card_list.csv",
    "cgss_r_card_list.csv",
    "cgss_n_card_list.csv",
]
# --- ここまで設定項目 ---

def normalize_text(text):
    """簡単なテキスト正規化（小文字化、余分なスペース削除など）"""
    if pd.isna(text):
        return ""
    text = str(text).lower() # 小文字化
    text = re.sub(r'\s+', ' ', text).strip() # 連続スペースを1つに、前後の空白削除
    # 日付や時間のフォーマットを統一するのはより複雑なので、ここでは省略
    # 例: 「プラチナガシャ」と「プラチナオーディションガシャ」を統一
    text = text.replace("プラチナオーディションガシャ", "プラチナガシャ")
    text = text.replace("ライブ", "live") # カタカナ英語の統一など
    return text

def main():
    all_availability_texts = []

    for csv_filename in RARITY_CSV_FILES:
        csv_filepath = os.path.join(CSV_DIRECTORY, csv_filename)
        if not os.path.exists(csv_filepath):
            print(f"CSVファイルが見つかりません: {csv_filepath}。スキップします。")
            continue

        print(f"\n--- {csv_filename} を読み込み中 ---")
        try:
            df = pd.read_csv(csv_filepath)
            if 'availability' in df.columns:
                # NaNや空でないものだけをリストに追加
                all_availability_texts.extend(df['availability'].dropna().astype(str).tolist())
            else:
                print(f"  警告: {csv_filename} に 'availability' 列がありません。")
        except Exception as e:
            print(f"  エラー: CSVファイルの読み込みに失敗 ({csv_filepath}): {e}")
            continue
    
    if not all_availability_texts:
        print("入手方法の情報がどのCSVからも取得できませんでした。")
        return

    print(f"\n--- 全 {len(all_availability_texts)} 件の入手方法情報を分析 ---")

    # 正規化したテキストのリストを作成
    normalized_texts = [normalize_text(text) for text in all_availability_texts if text.strip() and text.lower() not in ["情報なし", "取得失敗", "解析エラー", "url無効", "ページ取得失敗"]]

    # ユニークな入手方法とその出現回数
    print("\n--- ユニークな入手方法 (正規化後、トップ50) ---")
    unique_availability_counts = Counter(normalized_texts)
    for item, count in unique_availability_counts.most_common(50):
        print(f"- \"{item}\" ({count}回)")

    # キーワードによる分析
    print("\n--- 主要キーワードの出現回数 ---")
    keywords_to_check = {
        "ガシャ": ["ガシャ", "gacha"], # "ガシャ"を含むもの
        "フェス": ["フェス", "fes"],
        "限定": ["限定"], # "期間限定"も含む
        "恒常": ["恒常"], # これはおそらく "プラチナガシャ" のみなどで判断が必要
        "イベント": ["イベント", "event"],
        "報酬": ["報酬"],
        "ランキング": ["ランキング", "ranking"],
        "ポイント": ["ポイント", "pt"],
        "シンデレラキャラバン": ["シンデレラキャラバン", "キャラバン"],
        "live groove": ["live groove"],
        "live parade": ["live parade"],
        "live party": ["live party"],
        "live carnival": ["live carnival"],
        "ススメ！シンデレラロード": ["ススメ！シンデレラロード", "シンデレラロード"],
        "アイドルプロデュース": ["アイドルプロデュース"],
        "live infinity": ["live infinity"],
        "ローカル": ["ローカル"],
        "コラボ": ["コラボ"]
    }
    
    keyword_counts = Counter()
    for text in normalized_texts:
        for key, patterns in keywords_to_check.items():
            if any(pattern in text for pattern in patterns):
                keyword_counts[key] += 1
    
    for key, count in keyword_counts.most_common():
        print(f"- 「{key}」関連: {count}回")

    # 恒常/限定の簡易判定の試み
    print("\n--- 恒常/限定/期間限定の簡易判定試行 (キーワードベース) ---")
    limited_count = 0
    permanent_ish_count = 0 # 「恒常」と明記されていないが、そう思われるもの
    event_limited_count = 0
    unknown_type_count = 0
    
    # 判定用キーワード（優先度順に）
    # より詳細なルールが必要（例：「プラチナガシャ」だけなら恒常だが、「期間限定プラチナガシャ」なら限定）
    limited_keywords = ["限定", "シンデレラフェス", "フェス限定", "期間限定"] # 期間が書かれているものも限定
    event_keywords = ["イベント", "報酬", "ランキング", "ポイント", "シンデレラキャラバン", "live groove", "live parade", "live party", "live carnival", "シンデレラロード", "アイドルプロデュース", "live infinity"]
    # 恒常と判断できる明確なキーワードは少ないので、消去法で考える
    # 「プラチナガシャ」のみ、かつ上記限定/イベントキーワードを含まない、かつ日付情報が曖昧なもの
    
    categorized_examples = {"限定": [], "イベント限定": [], "恒常っぽい": [], "不明": []}

    for text in normalized_texts:
        text_lower = text.lower() # 判定用に小文字化
        is_limited = any(kw in text_lower for kw in limited_keywords)
        is_event = any(kw in text_lower for kw in event_keywords)
        has_date = bool(re.search(r'\d{4}年|\d{1,2}月\d{1,2}日|\d{1,2}/\d{1,2}', text)) # 簡単な日付判定

        if "復刻" in text_lower: # 復刻は元のカテゴリに準ずるが、ここでは一旦「限定」扱い
            is_limited = True

        if is_limited or (has_date and "プラチナガシャ" in text_lower and "シンデレラフェス" not in text_lower): # 日付付きガシャは限定とみなす
            limited_count += 1
            if len(categorized_examples["限定"]) < 5: categorized_examples["限定"].append(text)
        elif is_event:
            event_limited_count += 1
            if len(categorized_examples["イベント限定"]) < 5: categorized_examples["イベント限定"].append(text)
        elif "プラチナガシャ" in text_lower and not has_date and not is_limited and not is_event:
            permanent_ish_count += 1
            if len(categorized_examples["恒常っぽい"]) < 5: categorized_examples["恒常っぽい"].append(text)
        elif "ローカルガシャ" in text_lower or "初期選択" in text_lower:
             permanent_ish_count += 1
             if len(categorized_examples["恒常っぽい"]) < 5: categorized_examples["恒常っぽい"].append(text)
        else:
            unknown_type_count += 1
            if len(categorized_examples["不明"]) < 10: categorized_examples["不明"].append(text)


    print(f"  限定（ガシャ等）と判定される可能性: {limited_count} 件")
    for ex in categorized_examples["限定"]: print(f"    例: {ex}")
    print(f"  イベント限定/報酬と判定される可能性: {event_limited_count} 件")
    for ex in categorized_examples["イベント限定"]: print(f"    例: {ex}")
    print(f"  恒常ガシャ/その他と判定される可能性: {permanent_ish_count} 件")
    for ex in categorized_examples["恒常っぽい"]: print(f"    例: {ex}")
    print(f"  上記以外・分類不明: {unknown_type_count} 件")
    for ex in categorized_examples["不明"]: print(f"    例: {ex}")

    print("\n分析完了。上記を元にフィルター条件を検討してください。")

if __name__ == "__main__":
    main()
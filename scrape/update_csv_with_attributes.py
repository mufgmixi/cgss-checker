import pandas as pd
import json
import os

CSV_DIRECTORY = '.' # レアリティ別CSVがあるディレクトリ
ATTRIBUTE_ID_MAP_FILE = "attribute_card_ids.json"

# 処理対象のCSVファイル (画像ダウンロードスクリプトと合わせる)
RARITY_CSV_FILES = [
    "cgss_ssr_card_list.csv",
    "cgss_sr_card_list.csv",
    "cgss_r_card_list.csv",
    "cgss_n_card_list.csv",
]

def main():
    # 属性IDマップを読み込む
    try:
        with open(ATTRIBUTE_ID_MAP_FILE, "r", encoding="utf-8") as f:
            json_data = json.load(f)
            attribute_id_map = {k: set(v) for k, v in json_data.items()}
        print(f"属性カードIDマップを '{ATTRIBUTE_ID_MAP_FILE}' から読み込みました。")
    except FileNotFoundError:
        print(f"エラー: 属性カードIDマップファイル '{ATTRIBUTE_ID_MAP_FILE}' が見つかりません。")
        print("先にステップ1のスクリプトを実行して、このファイルを生成してください。")
        return
    except Exception as e:
        print(f"エラー: 属性カードIDマップファイルの読み込みに失敗しました: {e}")
        return

    for csv_filename in RARITY_CSV_FILES:
        csv_filepath = os.path.join(CSV_DIRECTORY, csv_filename)
        if not os.path.exists(csv_filepath):
            print(f"CSVファイルが見つかりません: {csv_filepath}。スキップします。")
            continue

        print(f"\n--- {csv_filename} の属性情報を更新中 ---")
        try:
            df = pd.read_csv(csv_filepath)
        except Exception as e:
            print(f"  エラー: CSVファイルの読み込みに失敗 ({csv_filepath}): {e}")
            continue
        
        if 'id' not in df.columns:
            print(f"  エラー: CSVファイルに 'id' 列が見つかりません: {csv_filename}。スキップします。")
            continue

        if 'attribute' not in df.columns:
            # dtypeを指定して 'object' にするか、後で pd.NA を使うならそのままでも良い
            df['attribute'] = pd.NA 
        else:
            # 既存の 'attribute' 列が数値型などになっていると pd.NA との比較で問題が起きうるので、
            # object型に変換しておくか、pd.NAを許容するStringDtypeなどに変換する。
            # ここでは、単純に pd.NA が入ることを許容する前提で進める。
            # もし既存列が 0 や空文字で埋まっているなら、それを pd.NA に置換する処理も検討。
            # 例: df['attribute'] = df['attribute'].replace('', pd.NA).replace(0, pd.NA)
            pass

        
        attributes_assigned_count = 0
        for index, row in df.iterrows():
            card_id = str(row['id']) 
            newly_assigned_attr = pd.NA 
            current_attr_in_df = df.loc[index, 'attribute'] 

            for attr_label, id_set in attribute_id_map.items():
                if card_id in id_set:
                    newly_assigned_attr = attr_label
                    break 
            
            update_needed = False
            if pd.notna(newly_assigned_attr): # 新しい属性が見つかった
                if pd.isna(current_attr_in_df) or current_attr_in_df != newly_assigned_attr:
                    df.loc[index, 'attribute'] = newly_assigned_attr
                    attributes_assigned_count += 1
                    update_needed = True
            elif pd.isna(newly_assigned_attr): # 新しい属性が見つからなかった
                # 現在がNAか"Unknown"でなければ、"Unknown"に設定する。
                # (つまり、以前Cu/Co/Paだったものが、今回見つからなかった場合も"Unknown"になる)
                # ポリシー: 属性情報が取得できない場合は"Unknown"にする
                if pd.isna(current_attr_in_df) or current_attr_in_df != "Unknown":
                    # ただし、既に具体的な属性(Cu/Co/Pa)が入っていて、今回見つからなかった場合はログを出しても良い
                    if pd.notna(current_attr_in_df) and current_attr_in_df not in ["Unknown", pd.NA]:
                         print(f"  Warning: ID {card_id} ({row.get('name', '')}) は以前属性 ({current_attr_in_df}) でしたが、今回属性が見つかりませんでした。'Unknown'に設定します。")
                    df.loc[index, 'attribute'] = "Unknown"
                    # attributes_assigned_count は具体的な属性が割り当てられた時だけカウントするなら、ここでは加算しない
                    if not update_needed and (pd.isna(current_attr_in_df) or current_attr_in_df != "Unknown"):
                        # "Unknown"への変更もカウントする場合
                        # attributes_assigned_count += 1 
                        pass


        try:
            df.to_csv(csv_filepath, index=False, encoding='utf-8-sig')
            print(f"  {csv_filename} を更新しました。{attributes_assigned_count} 件のカードに具体的な属性を新規/更新割り当てしました。")
        except Exception as e:
            print(f"  CSVファイルへの書き込みエラー ({csv_filepath}): {e}")

    print("\n全てのCSVファイルの属性情報更新処理が完了しました。")

if __name__ == "__main__":
    main()
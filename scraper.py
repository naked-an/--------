import requests
from bs4 import BeautifulSoup

def scrape_netkeiba_shutuba(race_id):
    """
    netkeibaの出馬表ページからデータをスクレイピングする (requests + BeautifulSoup版)
    """
    url = f"https://race.netkeiba.com/race/shutuba.html?race_id={race_id}"
    print(f"🌐 [取得中] {url} にアクセスしています...")

    # 一般的なブラウザを偽装するUser-Agent
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
    }

    try:
        # ページの取得
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # エラー（404, 403など）があれば例外を発生させる
        
        # エンコーディングの自動推測（文字化け防止）
        response.encoding = response.apparent_encoding
        
        soup = BeautifulSoup(response.content, 'html.parser')

        # レース名の取得
        race_name_elem = soup.select_one('.RaceName')
        if not race_name_elem:
            print("❌ レース名が見つかりませんでした。ページ構造が変わったか、アクセスがブロックされている可能性があります。")
            # デバッグ用にHTMLの一部を出力
            print(f"取得したHTMLの一部: {soup.prettify()[:500]}")
            return None
            
        race_name = race_name_elem.text.strip()
        print(f"✅ レース名: {race_name} のデータを解析します。")

        horses = []
        # 出馬表の行を取得（クラス名に 'HorseList' が含まれる行）
        horse_rows = soup.select('.HorseList')
        
        if not horse_rows:
            print("❌ 出走馬のデータが見つかりませんでした。")
            return None

        for row in horse_rows:
            horse_info = {}
            
            # 馬番 (枠色によって Umaban1, Umaban2... とクラスが変わるため前方一致で取得)
            umaban_elem = row.select_one('td[class^="Umaban"]')
            if umaban_elem:
                try:
                    horse_info["number"] = int(umaban_elem.text.strip())
                except ValueError:
                    continue # 馬番がない行(取消など)はスキップ
            else:
                 continue
                
            # 馬名
            name_elem = row.select_one('.HorseName a')
            if name_elem:
                horse_info["name"] = name_elem.text.strip()
            else:
                continue

            # 騎手
            jockey_elem = row.select_one('.Jockey a')
            if jockey_elem:
                horse_info["jockey"] = jockey_elem.text.strip()
            else:
                horse_info["jockey"] = "不明"

            # オッズ (Txt_R は右揃えのテキストクラス。オッズが入っていることが多い)
            odds_elem = row.select_one('.Txt_R span')
            if odds_elem:
                 try:
                     # '---' や取消などで数値に変換できない場合を考慮
                     odds_str = odds_elem.text.strip()
                     if odds_str == '---' or not odds_str:
                         horse_info["odds"] = 99.9
                     else:
                        horse_info["odds"] = float(odds_str)
                 except ValueError:
                     horse_info["odds"] = 99.9
            else:
                horse_info["odds"] = 99.9

            horses.append(horse_info)
            print(f"🐎 {horse_info.get('number', '?')}番 {horse_info.get('name', '不明')} (騎手: {horse_info.get('jockey', '不明')}) - オッズ: {horse_info.get('odds', 99.9)}")

        return {
            "raceName": race_name,
            "horses": horses
        }

    except requests.exceptions.RequestException as e:
        print(f"❌ ネットワークエラーまたはアクセス拒否: {e}")
        return None
    except Exception as e:
        print(f"❌ 解析エラー: {e}")
        return None

# テスト実行用 (このファイルを直接実行した時だけ動く)
if __name__ == "__main__":
    test_id = "202406030811" # 皐月賞
    scrape_netkeiba_shutuba(test_id)

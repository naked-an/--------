from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json
import time
from webdriver_manager.chrome import ChromeDriverManager

def scrape_netkeiba_shutuba(race_id):
    """
    netkeibaの出馬表ページから基本的なレース情報をスクレイピングする関数
    (Selenium + フルネーム抽出アップデート版)
    """
    url = f"https://race.netkeiba.com/race/shutuba.html?race_id={race_id}"
    
    # Chromeを裏側(ヘッドレス)で動かすための設定
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')

    print(f"🌐 [取得中] {url} に本物のブラウザ経由でアクセスしています...")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        driver.get(url)
        time.sleep(3) # JavaScriptの描画待ち
        
        html = driver.page_source
        driver.quit()
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # --- レース基本情報の取得 ---
        race_name = soup.select_one('.RaceName').text.strip() if soup.select_one('.RaceName') else "レース名不明"
        
        race_data = {
            "raceName": race_name,
            "horses": []
        }
        
        print(f"✅ レース名: {race_name} のデータを解析します。\n")

        # --- 出走馬データの取得 ---
        horse_rows = soup.select('.HorseList')
        
        for row in horse_rows:
            horse_info = {}
            
            # 馬番
            umaban_elem = row.select_one('td.Umaban')
            if umaban_elem:
                try:
                    horse_info["number"] = int(umaban_elem.text.strip())
                except ValueError:
                    continue
                
            # 馬名 (念のためtitle属性も確認)
            name_elem = row.select_one('.HorseName a')
            if name_elem:
                horse_info["name"] = name_elem.get('title') or name_elem.text.strip()
                
            # 騎手 (★ここを修正！表面の文字ではなくtitle属性からフルネームを狙い撃ち)
            jockey_elem = row.select_one('.Jockey a')
            if jockey_elem:
                full_name = jockey_elem.get('title')
                if full_name:
                    horse_info["jockey"] = full_name.strip()
                else:
                    horse_info["jockey"] = jockey_elem.text.strip()

            # オッズ
            odds_elem = row.select_one('td.Txt_R span')
            if odds_elem and odds_elem.text.strip() != '---':
                try:
                    horse_info["odds"] = float(odds_elem.text.strip())
                except ValueError:
                    horse_info["odds"] = 0.0
            else:
                horse_info["odds"] = 99.9 

            # EquiSense用ダミーパラメータ
            horse_info["baseScore"] = 70
            horse_info["jockeySkill"] = 7.0
            horse_info["variance"] = 10
            horse_info["runStyle"] = "先行"
            horse_info["tags"] = []
            
            if "name" in horse_info:
                race_data["horses"].append(horse_info)
                print(f"🐎 {horse_info.get('number', '?')}番 {horse_info['name']} (騎手: {horse_info.get('jockey', '?')})")

        return race_data

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return None

if __name__ == "__main__":
    # テストとして2024年 皐月賞のIDを指定
    test_race_id = "202406030811"
    
    print("🚀 スクレイピングを開始します...\n")
    
    result_data = scrape_netkeiba_shutuba(test_race_id)
    
    if result_data:
        print("\n✨ --- 取得完了・JSONフォーマット変換 --- ✨\n")
        json_output = json.dumps(result_data, ensure_ascii=False, indent=2)
        print(json_output)
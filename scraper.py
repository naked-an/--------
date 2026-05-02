import requests
from bs4 import BeautifulSoup

def scrape_netkeiba_shutuba(race_id):
    """
    出馬表の詳細データを取得する (既存の機能)
    """
    url = f"https://race.netkeiba.com/race/shutuba.html?race_id={race_id}"
    print(f"🌐 [取得中] {url} にアクセスしています...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.content, 'html.parser')

        race_name_elem = soup.select_one('.RaceName')
        if not race_name_elem: return None
        race_name = race_name_elem.text.strip()
        print(f"✅ レース名: {race_name} のデータを解析します。")

        horses = []
        horse_rows = soup.select('.HorseList')
        for row in horse_rows:
            horse_info = {}
            umaban_elem = row.select_one('td[class^="Umaban"]')
            if umaban_elem:
                try: horse_info["number"] = int(umaban_elem.text.strip())
                except ValueError: continue
            else: continue
                
            name_elem = row.select_one('.HorseName a')
            if name_elem: horse_info["name"] = name_elem.text.strip()
            else: continue

            jockey_elem = row.select_one('.Jockey a')
            horse_info["jockey"] = jockey_elem.text.strip() if jockey_elem else "不明"

            odds_elem = row.select_one('.Txt_R span')
            if odds_elem:
                 try:
                     odds_str = odds_elem.text.strip()
                     horse_info["odds"] = 99.9 if odds_str == '---' or not odds_str else float(odds_str)
                 except ValueError: horse_info["odds"] = 99.9
            else: horse_info["odds"] = 99.9

            horses.append(horse_info)
        return { "raceName": race_name, "horses": horses }
    except Exception as e:
        print(f"❌ 解析エラー: {e}")
        return None

def scrape_this_week_races():
    """
    🎯 【新規追加】 今週のレース一覧を取得する
    """
    url = "https://race.netkeiba.com/top/race_list.html"
    print(f"🌐 [取得中] {url} から今週のレース一覧を取得します...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.content, 'html.parser')
        
        race_list = []
        datalists = soup.select('.RaceList_DataList')
        
        for dl in datalists:
            place_text = dl.select_one('.RaceList_DataTitle').text if dl.select_one('.RaceList_DataTitle') else "JRA"
            location = "不明"
            for p in ["札幌", "函館", "福島", "新潟", "東京", "中山", "中京", "京都", "阪神", "小倉"]:
                if p in place_text:
                    location = p
                    break
                    
            items = dl.select('.RaceList_DataItem')
            for item in items:
                a_tag = item.select_one('a')
                if not a_tag or 'race_id=' not in a_tag.get('href', ''): continue
                    
                href = a_tag['href']
                race_id = href.split('race_id=')[1].split('&')[0]
                
                race_num_elem = item.select_one('.RaceList_Item01 .Race_Num')
                race_time_elem = item.select_one('.RaceList_Item02 .Race_Time')
                race_name_elem = item.select_one('.RaceList_Item02 .ItemTitle')
                
                if race_num_elem and race_name_elem:
                    is_heavy = bool(item.select_one('[class*="Type_G"]')) or bool(item.select_one('[class*="Type_J_G"]'))
                    num_str = race_num_elem.text.replace('R', '').strip()
                    
                    try:
                        r_num = int(num_str)
                        # 9R以降の特別戦・メインレースのみを抽出（画面が溢れるのを防ぐため）
                        if r_num < 9 and not is_heavy:
                            continue 
                    except ValueError: pass

                    race_list.append({
                        "id": race_id,
                        "location": location,
                        "raceNumber": race_num_elem.text.strip(),
                        "name": race_name_elem.text.strip(),
                        "time": race_time_elem.text.strip() if race_time_elem else "--:--",
                        "date": "本日"
                    })
                    
        print(f"✅ {len(race_list)}件の主要レース一覧を取得しました。")
        
        # もし平日等で取得できなかった場合はダミーを返す
        if not race_list: return get_mock_races()
        return race_list

    except Exception as e:
        print(f"❌ レース一覧取得エラー: {e}")
        return get_mock_races()

def get_mock_races():
    return [
        { "id": "202406030711", "location": "中山", "raceNumber": "11R", "name": "中山グランドJ (J-G1)", "time": "15:40", "date": "平日のため待機中" },
        { "id": "202406030811", "location": "中山", "raceNumber": "11R", "name": "皐月賞 (G1)", "time": "15:40", "date": "平日のため待機中" },
        { "id": "202409020811", "location": "阪神", "raceNumber": "11R", "name": "アンタレスS (G3)", "time": "15:30", "date": "平日のため待機中" }
    ]

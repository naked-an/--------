from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import google.generativeai as genai
from scraper import scrape_netkeiba_shutuba

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 【超重要】 ここにGemini APIキーを貼り付けます
GEMINI_API_KEY = "AIzaSyABKzRUKDJzwmraX9zuF9f2fA2KmxFTkgc"
genai.configure(api_key=GEMINI_API_KEY)
# ==========================================

print("=======================================")
print("📚 過去データベース(CSV)を読み込んでいます...")
try:
    history_df = pd.read_csv('results_light_50000.csv', encoding='utf-8-sig', low_memory=False)
    print(f"✅ DB接続成功！ {len(history_df):,} 件のレースデータをロードしました。")
except Exception as e:
    print(f"⚠️ 過去データCSVが見つからないか、エラーが発生しました: {e}")
    history_df = None
print("=======================================")

def get_past_results(horse_name):
    if history_df is None: return "データなし"
    past_races = history_df[history_df['horse_name'] == horse_name]
    if past_races.empty: return "過去データなし（新馬戦など）"
    recent = past_races.tail(3)
    results_list = []
    for _, row in recent.iterrows():
        date = str(row.get('date', ''))[:10]
        race_name = str(row.get('race_name', '不明'))
        rank = str(row.get('order', '不明'))
        if rank.endswith('.0'): rank = rank[:-2]
        results_list.append(f"[{date} {race_name}: {rank}着]")
    return " ➡ ".join(results_list)

def analyze_race_with_gemini(race_data):
    print("🧠 過去DBと連携し、Geminiによる高度なレース分析を開始します...")
    enhanced_horses = []
    for horse in race_data['horses']:
        past_history = get_past_results(horse['name'])
        enhanced_horses.append({
            "馬番": horse['number'], "馬名": horse['name'], "騎手": horse['jockey'], "オッズ": horse['odds'], "過去の戦績": past_history
        })

    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    あなたはプロの競馬予想AI「EquiSense」です。以下の出馬表と「過去の戦績」データを見て分析してください。
    データ: {json.dumps(enhanced_horses, ensure_ascii=False)}
    以下のJSONフォーマットのみで出力してください。（Markdownや不要なテキストは含めないこと）
    {{
        "analysis": [
            {{ "title": "AI 展開・過去データ分析", "content": "展開の予測と過去データからの傾向..." }},
            {{ "title": "有力馬評価", "content": "各馬の過去の成績を加味した評価..." }},
            {{ "title": "Gemini 総合推奨見解", "content": "推奨する買い目や総合的な見解..." }}
        ]
    }}
    """
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        if response_text.startswith("```json"): response_text = response_text[7:]
        if response_text.endswith("```"): response_text = response_text[:-3]
        ai_result = json.loads(response_text)
        print("✅ Geminiの高度分析が完了しました。")
        return ai_result.get("analysis", [])
    except Exception as e:
        print(f"❌ Gemini分析エラー: {e}")
        return [{"title": "エラー", "content": "AI分析中にエラーが発生しました。"}]

# 🎯 【新規追加】 今週のレース一覧を取得するAPIエンドポイント
@app.get("/api/races/this_week")
def get_this_week_races_api():
    print("\n📡 [API受信] 今週のレース一覧リクエストを受け付けました。")
    races = scrape_this_week_races()
    if races:
        return {"status": "success", "data": races}
    else:
        return {"status": "error", "message": "レース一覧が取得できませんでした"}

@app.get("/api/race/{race_id}")
def get_race_data(race_id: str):
    print(f"\n📡 [API受信] レースID '{race_id}' の詳細データリクエストを受け付けました。")
    result_data = scrape_netkeiba_shutuba(race_id)
    if result_data:
        analysis_data = analyze_race_with_gemini(result_data)
        result_data['analysis'] = analysis_data
        return {"status": "success", "data": result_data}
    else:
        return {"status": "error", "message": "スクレイピングに失敗しました。"}

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

def analyze_race_with_gemini(race_data):
    """
    スクレイピングした出馬表データをGeminiに渡し、AIの分析結果を生成する
    """
    print("🧠 Geminiによるレース分析を開始します...")
    
    # 使うモデルを指定（高速なFlashモデル）
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Geminiへの指示書（プロンプト）を作成
    prompt = f"""
    あなたはプロの競馬予想AI「EquiSense」です。
    以下の出馬表データを見て、レースの展開予測、有力馬の評価、そして総合的な推奨見解を作成してください。
    データ: {json.dumps(race_data['horses'], ensure_ascii=False)}

    以下のJSONフォーマットのみで出力してください。（Markdownや不要なテキストは含めないこと）
    {{
        "analysis": [
            {{ "title": "AI 展開予測", "content": "展開の予測文..." }},
            {{ "title": "有力馬評価", "content": "有力馬の評価文..." }},
            {{ "title": "Gemini 総合推奨見解", "content": "推奨する買い目や総合的な見解..." }}
        ]
    }}
    """
    
    try:
        # Geminiに推論を実行させる
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # ```json や ``` などの余分なマークダウンを削除
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        ai_result = json.loads(response_text)
        print("✅ Geminiの分析が完了しました。")
        return ai_result.get("analysis", [])
    except Exception as e:
        print(f"❌ Gemini分析エラー: {e}")
        # エラー時のダミーデータ
        return [{"title": "エラー", "content": "AI分析中にエラーが発生しました。"}]

@app.get("/api/race/{race_id}")
def get_race_data(race_id: str):
    print(f"\n📡 [API受信] レースID '{race_id}' のデータリクエストを受け付けました。")
    
    # 1. スクレイピングの実行
    result_data = scrape_netkeiba_shutuba(race_id)
    
    if result_data:
        # 2. 取得したデータをGeminiに渡して分析
        analysis_data = analyze_race_with_gemini(result_data)
        
        # 3. 分析結果をデータに結合
        result_data['analysis'] = analysis_data
        
        return {"status": "success", "data": result_data}
    else:
        return {"status": "error", "message": "スクレイピングに失敗しました。"}
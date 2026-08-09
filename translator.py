import os
import google.generativeai as genai
from deep_translator import GoogleTranslator

def translate_to_zh(text):
    """
    使用 Google Gemini API 將文字翻譯為繁體中文，並濾除特殊符號。
    如果尚未設定 API 金鑰或 Gemini 失敗，則使用免金鑰的 deep-translator 作為備用。
    """
    api_key = os.getenv("GEMINI_API_KEY")
    translated_text = text
    used_gemini = False
    
    if api_key and api_key != "your_gemini_api_key_here":
        try:
            genai.configure(api_key=api_key)
            
            prompt = f"""
            你是一個專業的社群媒體編輯。請將以下這段來自國外財經網紅的推文，翻譯成流暢、自然的台灣繁體中文。
            
            【嚴格規定】
            1. 絕對不要在翻譯結果中使用這些符號：*, 「, 」, $
            2. 請直接給出翻譯結果，不要加上任何解釋、問候語或註解。
            3. 如果遇到原本是美金的數字，請改用中文寫法 (例如：100萬美金)，不要保留 $ 符號。
            
            【待翻譯原文】
            {text}
            """
            
            # 嘗試使用一系列備用模型名稱，避免 404 錯誤
            models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro', 'gemini-pro']
            
            for model_name in models_to_try:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(prompt)
                    translated_text = response.text.strip()
                    used_gemini = True
                    break # 成功就跳出迴圈
                except Exception as e:
                    print(f"嘗試模型 {model_name} 失敗: {e}")
                    continue
        except Exception as e:
            print(f"Gemini API 初始化失敗: {e}")

    # 如果 Gemini 完全失敗，啟動終極備用方案：Google Translate (免金鑰)
    if not used_gemini or translated_text == text:
        print("⚠️ Gemini 翻譯失敗，啟動 Google Translate 終極備用方案...")
        try:
            translated_text = GoogleTranslator(source='auto', target='zh-TW').translate(text)
        except Exception as e:
            print(f"終極備用方案也失敗: {e}")
            return text
            
    # 雙重防線：程式碼層面強制移除不想要的符號
    for char in ['*', '「', '」', '$']:
        translated_text = translated_text.replace(char, '')
        
    return translated_text

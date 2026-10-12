"""Translate source X posts with Gemini."""

import os

import requests


TRANSLATION_INSTRUCTIONS = """
你是台灣財經社群的專業譯者。將使用者提供的 X 貼文翻成自然、精確的繁體中文（台灣用語）。

最重要規則：原文是唯一事實來源。不得根據圖片、常識、相似拼字或外部知識猜測、補充或改寫公司、人物、品牌、產品、股票代號、數字、職稱、地點或事件。

專有名詞規則：
- 人名、公司、品牌、產品、股票代號、縮寫，除非原文已經給出明確且通行的繁中名稱，否則保留原文。
- 不能因為縮寫相似就改成別的實體。例如原文的 Ant 必須保留 Ant；只有原文明寫 Ant Group 時，才能翻成螞蟻集團。Anthropic 必須保留 Anthropic。
- 原文已有中文名稱時逐字保留，不得改寫或校正為其他名稱；例如新日興必須維持新日興。
- 沒有把握時保留原文，絕不杜撰中文名稱。

文風規則：
- 使用台灣常用的財經詞，例如看多、看空、做多、做空、聯準會、財報、法說會、目標價、供應鏈。
- 可用短段落提升可讀性，但不得加入摘要、標題、免責聲明、來源標示、hashtag 或自己的評論。
- 忠實保留語氣、限定詞與不確定性；不得把推測寫成事實。
- 只輸出翻譯結果，不要解釋翻譯選擇。
- 不要使用 *、「、」、$ 字元；美元金額可改寫為「美元」。
""".strip()


def translate_to_zh(text: str):
    """Return a Taiwan Traditional Chinese translation, or None on failure.

    A failed Gemini call leaves the post unprocessed for a later retry rather
    than publishing a lower-quality machine translation.
    """
    if not text or not text.strip():
        return None

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("缺少 GEMINI_API_KEY，請在 GitHub Secrets 與工作流程設定金鑰。")
        return None

    model = os.getenv("GEMINI_TRANSLATION_MODEL") or "gemini-3.5-flash-lite"
    try:
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            headers={"x-goog-api-key": api_key},
            json={
                "systemInstruction": {"parts": [{"text": TRANSLATION_INSTRUCTIONS}]},
                "contents": [{"role": "user", "parts": [{"text": text}]}],
                "generationConfig": {"maxOutputTokens": 8192},
            },
            timeout=90,
        )
        if response.status_code != 200:
            # Do not log request URLs or exception messages containing secrets.
            print(f"Gemini 翻譯失敗（{model}），HTTP {response.status_code}。")
            return None
        candidates = response.json().get("candidates", [])
        if not candidates or candidates[0].get("finishReason") != "STOP":
            print("Gemini 未完成翻譯，保留貼文供下次重試。")
            return None
        translated_text = "".join(
            part.get("text", "")
            for part in candidates[0].get("content", {}).get("parts", [])
            if not part.get("thought")
        ).strip()
    except Exception as exc:
        print(f"Gemini 翻譯失敗（{model}）：{type(exc).__name__}")
        return None

    if not translated_text:
        print("Gemini 未回傳翻譯文字，保留貼文供下次重試。")
        return None

    for char in ("*", "「", "」", "$"):
        translated_text = translated_text.replace(char, "")

    print(f"✅ 已使用 Gemini {model} 完成翻譯。")
    return translated_text

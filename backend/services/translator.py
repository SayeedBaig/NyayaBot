from deep_translator import GoogleTranslator
from langdetect import detect

# 🔹 Detect language
def detect_language(text: str):
    try:
        return detect(text)
    except:
        return "en"


# 🔹 Translate to English
def translate_to_english(text: str):
    try:
        return GoogleTranslator(source="auto", target="en").translate(text)
    except:
        return text


# 🔹 Translate to target language
def translate_to_target(text: str, target_lang: str):
    try:
        if target_lang == "en":
            return text
        return GoogleTranslator(source="en", target=target_lang).translate(text)
    except:
        return text
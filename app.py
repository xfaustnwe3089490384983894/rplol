import streamlit as st
import os
import re
from google import genai
from google.genai import types

# Настройка страницы сайта (должна быть первой строчкой)
st.set_page_config(page_title="Душнила-Дефендер", page_icon="⚖️", layout="wide")

# Инициализация ИИ (берем ключ из секретов хостинга, об этом ниже)
# Для локального теста можно временно заменить на: API_KEY = "AQ.Ab8RN6L3tzjgtM1HB1aI3p81VpBeTy2HyoOjMVZpmS2dpoB9wA"
API_KEY = st.secrets.get("GEMINI_API_KEY", "AQ.Ab8RN6L3tzjgtM1HB1aI3p81VpBeTy2HyoOjMVZpmS2dpoB9wA")
client = genai.Client(api_key=API_KEY)

FILES_MAP = {
    "ук": "ук.txt",
    "ак": "ак.txt",
    "кс": "кс.txt",
    "пк": "пк.txt",
    "зоа": "зоа.txt",
    "зоо": "зоо.txt"
}

def load_all_files():
    full_context = ""
    for key, filename in FILES_MAP.items():
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                full_context += f"\n=== ДАННЫЕ ИЗ ФАЙЛА {filename.upper()} ===\n"
                full_context += f.read()
    return full_context

def direct_search(user_input):
    match = re.search(r'(\d+(?:\.\d+)*)\s*([а-яА-Яa-zA-Z]+)', user_input.lower())
    if match:
        article_num = match.group(1)
        file_key = match.group(2)
        
        if file_key in FILES_MAP:
            filename = FILES_MAP[file_key]
            if not os.path.exists(filename):
                return f"Файл {filename} не найден."
                
            with open(filename, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            found_lines = []
            start_saving = False
            for line in lines:
                if article_num in line and ("статья" in line.lower() or line.strip().startswith(article_num)):
                    start_saving = True
                    found_lines.append(line)
                    continue
                if start_saving:
                    if "статья" in line.lower() or re.match(r'^\d+(\.\d+)*', line.strip()):
                        break
                    found_lines.append(line)
            
            if found_lines:
                return "".join(found_lines)
    return None

# --- ИНТЕРФЕЙС САЙТА ---
st.title("⚖️ Юридический помощник «Душнила-Дефендер»")
st.caption("Быстрый поиск по кодексам и ИИ-анализ для жесткой защиты")

# Боковая панель со статусом файлов
with st.sidebar:
    st.header("📂 База данных")
    for key, filename in FILES_MAP.items():
        if os.path.exists(filename):
            st.success(f"Файл {filename} готов")
        else:
            st.error(f"Файл {filename} не найден")

# Разделение сайта на две удобные вкладки
tab1, tab2 = st.tabs(["🤖 ИИ-Адвокат (Анализ ситуации)", "📋 Быстрый поиск статьи"])

with tab1:
    st.subheader("Опиши ситуацию, и ИИ разложит её по законам")
    user_query = st.text_area(
        "Что натворил человек или как его задержали?", 
        placeholder="Пример: Чел ночью разбил витрину магазина и утащил ноут, при задержании жестко заломили руки...",
        height=150
    )
    
    # Красивая кнопка запуска
    if st.button("⚖️ Разобрать дело по закону", type="primary"):
        if not user_query.strip():
            st.warning("Сначала опиши ситуацию!")
        else:
            with st.spinner("Душный адвокат изучает материалы дела и ищет лазейки..."):
                knowledge_base = load_all_files()
                
                system_instruction = (
                    "Ты — самый дотошный, жесткий и душный адвокат в мире. Твоя цель — разносить в пух и прах обвинение, "
                    "используя исключительно предоставленные файлы нормативно-правовых актов (базу знаний).\n"
                    "1. Четко определи, под какие статьи из предоставленных файлов попадает действие.\n"
                    "2. Распиши пошагово, как вести себя при задержании, что говорить, какие права качать.\n"
                    "3. Найди любые лазейки, смягчающие обстоятельства или процессуальные ошибки в действиях силовиков, опираясь на статьи из файлов.\n"
                    "4. Пиши профессиональным, въедливым юридическим языком, оформляй текст списками, выделяй номера статей жирным шрифтом."
                )
                
                prompt = f"База знаний:\n{knowledge_base}\n\nСитуация: {user_query}"
                
                try:
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.3,
                        ),
                    )
                    st.markdown("### 🏛️ Стратегия защиты:")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"Ошибка ИИ: {e}")

with tab2:
    st.subheader("Мгновенное извлечение текста статьи")
    search_query = st.text_input("Введите номер и кодекс", placeholder="Пример: 17.1 УК или 5.1 АК")
    
    if st.button("🔍 Найти статью"):
        if search_query.strip():
            result = direct_search(search_query)
            if result:
                st.info(f"Текст найденной статьи по запросу {search_query}:")
                st.code(result, language="text")
            else:
                st.warning("Статья не найдена. Проверьте формат (Номер Название, например: 17.1 УК)")
        else:
            st.error("Введите запрос!")

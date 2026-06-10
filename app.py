import streamlit as st
import os
import re
import google.generativeai as genai

# 1. Настройка страницы сайта (Обязательно первая строка)
st.set_page_config(page_title="Душнила-Дефендер", page_icon="⚖️", layout="wide")

# 2. Настройка ИИ через старую стабильную библиотеку
API_KEY = "AQ.Ab8RN6L3tzjgtM1HB1aI3p81VpBeTy2HyoOjMVZpmS2dpoB9wA"
genai.configure(api_key=API_KEY)

# Карта твоих файлов
FILES_MAP = {
    "ук": "ук.txt",
    "ак": "ак.txt",
    "кс": "кс.txt",
    "пк": "пк.txt",
    "зоа": "зоа.txt",
    "зоо": "зоо.txt"
}

def load_all_files():
    """Считывает все файлы в одну базу для ИИ."""
    full_context = ""
    for key, filename in FILES_MAP.items():
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                full_context += f"\n=== ДАННЫЕ ИЗ ФАЙЛА {filename.upper()} ===\n"
                full_context += f.read()
    return full_context

def direct_search(user_input):
    """Прямой поиск по точной статье (например, 17.1 УК)"""
    match = re.search(r'(\d+(?:\.\d+)*)\s*([а-яА-Яa-zA-Z]+)', user_input.lower())
    if match:
        article_num = match.group(1)
        file_key = match.group(2)
        
        if file_key in FILES_MAP:
            filename = FILES_MAP[file_key]
            if not os.path.exists(filename):
                return f"Файл {filename} не найден в папке сайта."
                
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

# Боковая панель со статусом твоих файлов
with st.sidebar:
    st.header("📂 База данных")
    st.info("Убедись, что эти файлы лежат в той же папке на GitHub!")
    for key, filename in FILES_MAP.items():
        if os.path.exists(filename):
            st.success(f"✅ Файл {filename} обнаружен")
        else:
            st.error(f"❌ Файл {filename} НЕ найден")

# Вкладки на сайте
tab1, tab2 = st.tabs(["🤖 ИИ-Адвокат (Анализ ситуации)", "📋 Быстрый поиск статьи"])

with tab1:
    st.subheader("Опиши ситуацию, и ИИ разложит её по законам")
    user_query = st.text_area(
        "Что произошло? (Опиши действия человека или косяки при задержании)", 
        placeholder="Пример: Тип угнал машину ночью, закрылся в ней, при задержании ему заломили руки...",
        height=150
    )
    
    if st.button("⚖️ Разобрать дело по закону", type="primary"):
        if not user_query.strip():
            st.warning("Сначала опиши ситуацию в поле выше!")
        else:
            with st.spinner("Душный адвокат изучает материалы дела и ищет лазейки..."):
                knowledge_base = load_all_files()
                
                if not knowledge_base.strip():
                    st.error("Ошибка: Скрипт не нашёл ни одного .txt файла со статьями в твоей папке. Загрузи их на GitHub!")
                else:
                    system_instruction = (
                        "Ты — самый дотошный, жесткий и душный адвокат в мире. Твоя цель — разносить в пух и прах обвинение, "
                        "используя исключительно предоставленные файлы нормативно-правовых актов (базу знаний).\n"
                        "1. Четко определи, под какие статьи из предоставленных файлов попадает действие.\n"
                        "2. Распиши пошагово, как вести себя при задержании, что говорить, какие права качать.\n"
                        "3. Найди любые лазейки, смягчающие обстоятельства или процессуальные ошибки в действиях силовиков, опираясь на статьи из файлов.\n"
                        "4. Пиши профессиональным, въедливым юридическим языком, оформляй текст списками, выделяй номера статей жирным шрифтом."
                    )
                    
                    prompt = f"{system_instruction}\n\nВот твоя база знаний со статьями:\n{knowledge_base}\n\nСитуация подзащитного: {user_query}"
                    
                    try:
                        # Используем стабильную модель старого SDK
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        response = model.generate_content(prompt)
                        
                        st.markdown("### 🏛️ Стратегия защиты:")
                        st.markdown(response.text)
                    except Exception as e:
                        st.error(f"Ошибка при ответе ИИ: {e}")

with tab2:
    st.subheader("Мгновенное извлечение текста статьи без ИИ")
    search_query = st.text_input("Введите номер статьи и кодекс", placeholder="Пример: 17.1 УК или 5.1 АК")
    
    if st.button("🔍 Найти статью"):
        if search_query.strip():
            result = direct_search(search_query)
            if result:
                st.info(f"Текст найденной статьи по запросу {search_query}:")
                st.code(result, language="text")
            else:
                st.warning("Статья не найдена. Убедись, что пишешь формат как в примере (17.1 УК) и что этот файл загружен.")
        else:
            st.error("Введите поисковый запрос!")

import streamlit as st
import os
import re
from groq import Groq

# 1. Настройка страницы (Обязательно первая строка кода)
st.set_page_config(page_title="Душнила-Def", page_icon="⚖️", layout="wide")

# 2. Жестко вшитый API-ключ Groq (Больше никаких настроек секретов не нужно)
API_KEY = "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"
client = Groq(api_key=API_KEY)

# Твоя база файлов
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
                full_context += f"\n=== ДАННЫЕ ИЗ ФАЙЛА {filename.upper()} ===\n{f.read()}"
    return full_context

def direct_search(user_input):
    """Прямой поиск по конкретной статье (например, 17.1 УК) без ИИ."""
    match = re.search(r'(\d+(?:\.\d+)*)\s*([а-яА-Яa-zA-Z]+)', user_input.lower())
    if match:
        article_num = match.group(1)
        file_key = match.group(2)
        if file_key in FILES_MAP and os.path.exists(FILES_MAP[file_key]):
            with open(FILES_MAP[file_key], "r", encoding="utf-8") as f:
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
st.caption("Быстрый поиск по кодексам и ИИ-анализ на базе Llama 3.1")

# Боковая панель проверки файлов
with st.sidebar:
    st.header("📂 Твоя база данных")
    st.write("Эти файлы должны лежать на GitHub рядом с app.py:")
    for key, filename in FILES_MAP.items():
        if os.path.exists(filename):
            st.success(f"✅ {filename} на месте")
        else:
            st.error(f"❌ {filename} не найден")

# Вкладки
tab1, tab2 = st.tabs(["🤖 ИИ-Адвокат (Разбор дела)", "📋 Быстрый поиск статьи"])

with tab1:
    st.subheader("Опиши ситуацию, и ИИ разложит её по законам")
    user_query = st.text_area(
        "Что произошло? (Опиши действия человека или косяки силовиков при задержании)", 
        placeholder="Пример: Тип угнал машину ночью, закрылся в ней, при задержании ему заломили руки...",
        height=150
    )
    
    if st.button("⚖️ Разобрать дело по закону", type="primary"):
        if not user_query.strip():
            st.warning("Сначала опиши ситуацию в поле выше!")
        else:
            with st.spinner("Душный адвокат изучает предоставленные файлы кодексов..."):
                knowledge_base = load_all_files()
                
                if not knowledge_base.strip():
                    st.error("Ошибка: Скрипт не нашёл ни одного .txt файла в твоей папке на GitHub!")
                else:
                    system_instruction = (
                        "Ты — самый дотошный, жесткий и душный адвокат в мире. Твоя цель — разносить в пух и прах обвинение, "
                        "используя исключительно предоставленные файлы нормативно-правовых актов (базу знаний).\n"
                        "1. Четко определи, под какие статьи из предоставленных файлов попадает действие.\n"
                        "2. Распиши пошагово, как вести себя при задержании, что говорить, какие права качать.\n"
                        "3. Найди любые лазейки, смягчающие обстоятельства или процессуальные ошибки в действиях силовиков, опираясь на статьи из файлов.\n"
                        "4. Пиши профессиональным, въедливым юридическим языком на русском, оформляй текст списками, выделяй номера статей жирным шрифтом."
                    )
                    
                    try:
                        chat_completion = client.chat.completions.create(
                            messages=[
                                {"role": "system", "content": system_instruction},
                                {"role": "user", "content": f"Вот твоя нормативная база:\n{knowledge_base}\n\nЗапрос/Ситуация подзащитного: {user_query}"}
                            ],
                            model="llama-3.1-8b-instant",
                            temperature=0.3,
                        )
                        st.markdown("### 🏛️ Стратегия защиты:")
                        st.markdown(chat_completion.choices[0].message.content)
                    except Exception as e:
                        st.error(f"Ошибка ИИ (Groq): {e}")

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
                st.warning("Статья не найдена. Убедись, что формат совпадает с примером (17.1 УК) и файл загружен на GitHub.")
        else:
            st.error("Введите поисковый запрос!")

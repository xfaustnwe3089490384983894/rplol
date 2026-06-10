import streamlit as st
import os
import re
from groq import Groq

# 1. Настройка страницы (Обязательно первая строка кода)
st.set_page_config(page_title="Душнила-Def", page_icon="⚖️", layout="wide")

# 2. Твой API-ключ Groq
API_KEY = "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"
client = Groq(api_key=API_KEY)

FILES_MAP = {
    "ук": "ук.txt", 
    "ак": "ак.txt", 
    "кс": "кс.txt", 
    "пк": "пк.txt", 
    "зоа": "зоа.txt", 
    "зоо": "зоо.txt"
}

def get_keywords(text):
    """Вытаскивает ключевые слова из запроса для поиска по кодексам."""
    text = text.lower()
    # Чистим от мелкого мусора
    words = re.findall(r'[а-яё]{4,}', text) 
    # Исключаем стоп-слова, которые ломают поиск
    stop_words = {'меня', 'тебя', 'было', 'этого', 'если', 'когда', 'чтобы', 'человек', 'задержали'}
    return [w for w in words if w not in stop_words]

def load_relevant_context(user_query):
    """
    Ищет только релевантные статьи во всех файлах, чтобы не превысить лимит в 6000 токенов.
    """
    keywords = get_keywords(user_query)
    if not keywords:
        # Если ключевых слов нет, берем первые строчки файлов как заглушку
        keywords = ['статья', 'закон']
        
    relevant_context = ""
    total_found_articles = 0
    
    for key, filename in FILES_MAP.items():
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                # Разбиваем файл на блоки статей (обычно статьи начинаются со слова 'Статья' или цифр)
                content = f.read()
                articles = re.split(r'(?=Статья|\b\d+\.\s)', content)
                
                for article in articles:
                    # Если статья содержит хотя бы одно ключевое слово из запроса
                    if any(kw in article.lower() for kw in keywords):
                        # Проверяем, чтобы контекст не стал слишком гигантским для Groq
                        if len(relevant_context) + len(article) < 15000: # ~3500 токенов максимум
                            relevant_context += f"\n[ИЗ ФАЙЛА {filename.upper()}]:\n{article}\n"
                            total_found_articles += 1
                        else:
                            break
                            
    return relevant_context, total_found_articles

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
st.caption("Оптимизированная версия: умный подбор статей + Llama 3.1")

# Боковая панель
with st.sidebar:
    st.header("📂 Твоя база данных")
    for key, filename in FILES_MAP.items():
        if os.path.exists(filename):
            st.success(f"✅ {filename}")
        else:
            st.error(f"❌ {filename} не найден")

tab1, tab2 = st.tabs(["🤖 ИИ-Адвокат (Разбор дела)", "📋 Быстрый поиск статьи"])

with tab1:
    st.subheader("Опиши ситуацию, и ИИ разложит её по законам")
    user_query = st.text_area(
        "Что произошло?", 
        placeholder="Пример: Тип угнал машину ночью, закрылся в ней, при задержании ему заломили руки...",
        height=150
    )
    
    if st.button("⚖️ Разобрать дело по закону", type="primary"):
        if not user_query.strip():
            st.warning("Сначала опиши ситуацию в поле выше!")
        else:
            with st.spinner("Фильтруем статьи и подключаем адвоката..."):
                # Вытягиваем только нужные статьи, подходящие под текст
                knowledge_base, count = load_relevant_context(user_query)
                
                if not knowledge_base.strip():
                    st.error("По ключевым словам из твоего запроса ничего не найдено в твоих .txt файлах.")
                else:
                    st.info(f"ℹ️ Для анализа успешно отобрано {count} подходящих по смыслу статей.")
                    
                    system_instruction = (
                        "Ты — самый дотошный, жесткий и душный адвокат в мире. Твоя цель — разносить в пух и прах обвинение, "
                        "используя исключительно предоставленные файлы нормативно-правовых актов (базу знаний).\n"
                        "1. Четко определи, под какие статьи попадает действие.\n"
                        "2. Распиши пошагово, как вести себя при задержании, что говорить, какие права качать.\n"
                        "3. Найди любые лазейки, смягчающие обстоятельства или процессуальные ошибки в действиях силовиков.\n"
                        "4. Пиши профессиональным, въедливым юридическим языком на русском, оформляй текст списками, выделяй номера статей жирным шрифтом."
                    )
                    
                    try:
                        chat_completion = client.chat.completions.create(
                            messages=[
                                {"role": "system", "content": system_instruction},
                                {"role": "user", "content": f"Вот релевантные статьи из базы:\n{knowledge_base}\n\nСитуация: {user_query}"}
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
    search_query = st.text_input("Введите номер статьи и кодекс", placeholder="Пример: 17.1 УК")
    
    if st.button("🔍 Найти статью"):
        if search_query.strip():
            result = direct_search(search_query)
            if result:
                st.info(f"Текст статьи:")
                st.code(result, language="text")
            else:
                st.warning("Статья не найдена. Проверь формат.")
        else:
            st.error("Введите поисковый запрос!")

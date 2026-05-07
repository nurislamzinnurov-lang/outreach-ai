import streamlit as st
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
from datetime import datetime

# --- КОНФИГ СТРАНИЦЫ (Темная тема как ChatGPT) ---
st.set_page_config(
    page_title="Outreach Pro AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- КАСТОМНЫЙ CSS (Темная тема ChatGPT-style) ---
st.markdown("""
<style>
    * {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    }
    
    body {
        background-color: #0d0d0d;
        color: #ececec;
    }
    
    .stApp {
        background-color: #0d0d0d;
    }
    
    .stChatMessage {
        background-color: #1a1a1a;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
    }
    
    .stButton > button {
        background-color: #10a37f;
        color: white;
        border-radius: 8px;
        font-weight: 600;
        padding: 10px 20px;
        border: none;
    }
    
    .stButton > button:hover {
        background-color: #1a9970;
    }
    
    .stTextInput, .stTextArea, .stSelectbox {
        background-color: #1a1a1a;
        border-radius: 8px;
    }
    
    .stSidebar {
        background-color: #0d0d0d;
    }
    
    h1, h2, h3 {
        color: #ececec;
    }
    
    .extension-button {
        display: inline-block;
        background-color: #1a1a1a;
        border: 1px solid #404040;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 8px 8px 0;
        cursor: pointer;
        text-decoration: none;
        color: #ececec;
        transition: all 0.2s;
    }
    
    .extension-button:hover {
        background-color: #262626;
        border-color: #10a37f;
    }
</style>
""", unsafe_allow_html=True)

# --- ИНИЦИАЛИЗАЦИЯ SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "generated_email" not in st.session_state:
    st.session_state.generated_email = None
if "email_ready_for_send" not in st.session_state:
    st.session_state.email_ready_for_send = False

# --- ФУНКЦИИ ---
def get_secret(key, default=""):
    """Получить секрет из Streamlit Secrets"""
    if key in st.secrets:
        return st.secrets[key]
    return default

def generate_email_with_style(lead_name, lead_context, offer, api_key, style="expert"):
    """Генерирует письмо с учетом выбранного стиля"""
    
    style_prompts = {
        "expert": """Ты — элитный B2B-аутрич менеджер в стиле Евгения Кострова. 
        Твоя задача: превратить данные о лиде в письмо, которое невозможно проигнорировать.
        Правила:
        1. Начни с 'сигнала' (почему мы пишем именно сейчас).
        2. Используй конкретные факты о проекте лида.
        3. Предложи четкую выгоду или 'входной продукт'.
        4. Стиль: уверенный, лаконичный, экспертный. Никаких клише. 3-4 предложения.""",
        
        "aggressive": """Ты — дерзкий стартапер, который пишет как свой парень. 
        Письмо должно быть коротким, прямым и немного провокационным.
        Правила:
        1. Начни с неожиданного вопроса или наблюдения.
        2. Покажи, что ты знаешь их бизнес.
        3. Предложи что-то конкретное, без воды.
        4. Стиль: дружелюбный, уверенный, немного хамоват. 2-3 предложения.""",
        
        "analytical": """Ты — холодный аналитик, который говорит на языке цифр и ROI.
        Письмо должно быть логичным и убедительным.
        Правила:
        1. Начни с фактов и статистики.
        2. Покажи проблему лида через данные.
        3. Предложи решение с конкретными результатами.
        4. Стиль: профессиональный, точный, минимум эмоций. 3-4 предложения."""
    }
    
    prompt = style_prompts.get(style, style_prompts["expert"])
    
    full_prompt = f"""{prompt}
    
    Лид: {lead_name}
    Контекст: {lead_context}
    Наше предложение: {offer}
    
    Напиши письмо прямо сейчас:"""
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": full_prompt}],
        "temperature": 0.7,
        "max_tokens": 300
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"❌ Ошибка ИИ: {response.status_code}"
    except Exception as e:
        return f"❌ Ошибка подключения: {str(e)}"

def send_email(to_email, subject, body, from_email, smtp_password, smtp_server, smtp_port):
    """Отправляет письмо через SMTP"""
    try:
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=10) as server:
            server.login(from_email, smtp_password)
            server.send_message(msg)
        
        return True, "✅ Письмо успешно отправлено!"
    except smtplib.SMTPAuthenticationError:
        return False, "❌ Ошибка: неверный пароль приложения"
    except smtplib.SMTPException as e:
        return False, f"❌ Ошибка SMTP: {str(e)}"
    except Exception as e:
        return False, f"❌ Ошибка: {str(e)}"

# --- ГЛАВНЫЙ ИНТЕРФЕЙС ---
col_main, col_sidebar = st.columns([4, 1])

with col_main:
    st.markdown("# 🚀 Outreach Pro AI")
    st.markdown("*Элитный ассистент для холодного аутрича на основе методики Кострова*")
    
    # --- ИСТОРИЯ СООБЩЕНИЙ (как в ChatGPT) ---
    st.markdown("---")
    
    # Таб 1: Генератор писем
    tab1, tab2, tab3 = st.tabs(["✍️ Генератор", "📊 История", "🔗 Расширения"])
    
    with tab1:
        st.subheader("Данные лида")
        
        col_a, col_b = st.columns(2)
        with col_a:
            lead_name = st.text_input("👤 Имя лида", placeholder="Levan Asatiani")
            lead_email = st.text_input("📧 Email лида", placeholder="levan@orbi.ge")
        
        with col_b:
            style = st.selectbox(
                "🎨 Стиль письма",
                ["expert", "aggressive", "analytical"],
                format_func=lambda x: {
                    "expert": "🎓 Экспертный (Костров)",
                    "aggressive": "⚡ Дерзкий стартапер",
                    "analytical": "📈 Аналитик"
                }[x]
            )
        
        lead_context = st.text_area(
            "📝 Контекст о лиде (его проект, достижения, текущие задачи)",
            placeholder="Founder ORBI Group, строит ORBI Millennium в Батуми, агрессивная маркетинговая стратегия...",
            height=120
        )
        
        offer = st.text_area(
            "💡 Что предлагаем?",
            placeholder="Реклама на 1500 экранах Novikov TV в премиум-локациях для привлечения инвесторов...",
            height=100
        )
        
        # --- ГЕНЕРАЦИЯ ---
        if st.button("✨ Сгенерировать письмо", use_container_width=True):
            groq_key = get_secret("GROQ_API_KEY")
            if not groq_key:
                st.error("❌ Groq API Key не найден в Secrets!")
            elif not lead_name or not lead_context or not offer:
                st.warning("⚠️ Заполни все поля!")
            else:
                with st.spinner("🤖 ИИ генерирует письмо..."):
                    generated = generate_email_with_style(lead_name, lead_context, offer, groq_key, style)
                    st.session_state.generated_email = generated
                    st.session_state.email_ready_for_send = False
        
        # --- РЕЗУЛЬТАТ ---
        if st.session_state.generated_email:
            st.markdown("---")
            st.subheader("📧 Сгенерированное письмо")
            
            final_email = st.text_area(
                "Отредактируй, если нужно:",
                value=st.session_state.generated_email,
                height=200,
                key="email_editor"
            )
            
            st.session_state.generated_email = final_email
            
            # --- ЭТАП ПОДТВЕРЖДЕНИЯ ---
            st.markdown("---")
            st.subheader("📤 Готово к отправке?")
            
            col_send_a, col_send_b = st.columns(2)
            
            with col_send_a:
                from_email = st.text_input(
                    "📧 С какой почты отправить?",
                    value=get_secret("EMAIL_USER"),
                    placeholder="your-email@yandex.ru"
                )
            
            with col_send_b:
                smtp_service = st.selectbox(
                    "🔐 Почтовый сервис",
                    ["Yandex", "Mail.ru"],
                    key="smtp_select"
                )
            
            if smtp_service == "Yandex":
                smtp_server, smtp_port = "smtp.yandex.ru", 465
            else:
                smtp_server, smtp_port = "smtp.mail.ru", 465
            
            smtp_password = st.text_input(
                "🔑 Пароль приложения",
                value=get_secret("EMAIL_PASS"),
                type="password",
                placeholder="16-значный пароль"
            )
            
            # --- КНОПКА ОТПРАВКИ ---
            if st.button("🚀 ОТПРАВИТЬ ПИСЬМО", use_container_width=True, type="primary"):
                if not from_email or not smtp_password:
                    st.error("❌ Заполни email и пароль!")
                else:
                    with st.spinner("📤 Отправляем письмо..."):
                        success, message = send_email(
                            lead_email,
                            f"Quick question for {lead_name}",
                            final_email,
                            from_email,
                            smtp_password,
                            smtp_server,
                            smtp_port
                        )
                        
                        if success:
                            st.success(message)
                            st.session_state.messages.append({
                                "time": datetime.now().strftime("%H:%M"),
                                "to": lead_email,
                                "status": "✅ Отправлено"
                            })
                            st.session_state.generated_email = None
                        else:
                            st.error(message)
    
    with tab2:
        st.subheader("📊 История отправок")
        if st.session_state.messages:
            for msg in reversed(st.session_state.messages):
                st.info(f"⏰ {msg['time']} → {msg['to']} {msg['status']}")
        else:
            st.info("📭 История пуста")
    
    with tab3:
        st.subheader("🔗 Расширения и интеграции")
        st.markdown("""
        Быстрые ссылки на популярные инструменты для аутрича:
        """)
        
        col_ext1, col_ext2, col_ext3, col_ext4 = st.columns(4)
        
        with col_ext1:
            st.markdown("""
            <a href="https://coldy.ai" target="_blank" class="extension-button">
            🎯 Coldy.ai
            </a>
            """, unsafe_allow_html=True)
        
        with col_ext2:
            st.markdown("""
            <a href="https://trulyinbox.com" target="_blank" class="extension-button">
            📬 TrulyInbox
            </a>
            """, unsafe_allow_html=True)
        
        with col_ext3:
            st.markdown("""
            <a href="https://apify.com" target="_blank" class="extension-button">
            🤖 Apify
            </a>
            """, unsafe_allow_html=True)
        
        with col_ext4:
            st.markdown("""
            <a href="https://hunter.io" target="_blank" class="extension-button">
            🎣 Hunter.io
            </a>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("""
        **Как использовать:**
        1. Найди контакты в одном из этих сервисов
        2. Скопируй данные лида сюда
        3. Сгенерируй письмо
        4. Отправь прямо из приложения
        """)

with col_sidebar:
    st.markdown("### ⚙️ Настройки")
    
    if st.button("🔄 Очистить историю"):
        st.session_state.messages = []
        st.session_state.generated_email = None
        st.success("✅ История очищена")
    
    st.markdown("---")
    st.markdown("""
    **Версия:** Pro 1.0
    
    **Powered by:**
    - Groq LLM
    - Streamlit
    - Костров методика
    """)

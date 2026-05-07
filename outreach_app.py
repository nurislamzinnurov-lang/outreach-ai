import streamlit as st
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- КОНФИГ СТРАНИЦЫ ---
st.set_page_config(
    page_title="Outreach Pro by Nurislam",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- КАСТОМНЫЙ CSS (Стиль Manus) ---
st.markdown("""
<style>
    * { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; }
    body, .stApp { background-color: #0f0f0f; color: #e0e0e0; }
    .stSidebar { background-color: #1a1a1a; border-right: 1px solid #2a2a2a; }
    h1, h2, h3 { color: #ffffff; font-weight: 700; }
    .stButton > button { background-color: #10a37f; color: white; border: none; border-radius: 6px; font-weight: 600; padding: 10px 20px; width: 100%; }
    .stButton > button:hover { background-color: #0d9370; }
    .stTextInput > div > div > input, .stTextArea > div > div > textarea, .stSelectbox > div > div > select {
        background-color: #1a1a1a; color: #e0e0e0; border: 1px solid #2a2a2a; border-radius: 6px;
    }
    .info-box { background-color: #1a1a1a; border-left: 4px solid #10a37f; padding: 16px; border-radius: 6px; margin: 12px 0; }
    .contact-link { display: inline-block; background-color: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 6px; padding: 8px 12px; margin: 4px 4px 4px 0; text-decoration: none; color: #10a37f; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

# --- ИНИЦИАЛИЗАЦИЯ ---
if "messages" not in st.session_state: st.session_state.messages = []
if "generated_email" not in st.session_state: st.session_state.generated_email = None

def get_secret(key, default=""):
    return st.secrets[key] if key in st.secrets else default

# --- СУПЕР-ЛОГИКА (ВШИТАЯ МЕТОДОЛОГИЯ) ---
def generate_pro_email(lead_name, lead_context, offer, api_key, user_kb=""):
    system_instruction = """
    Ты — элитный B2B-аутрич менеджер. Твоя методология основана на 4 столпах:
    1. СИГНАЛ: Начни с причины, почему мы пишем (пост, проект, новость). Никакой воды.
    2. МЯСО: Используй конкретные факты о лиде. Покажи, что ты "в теме".
    3. ВЫГОДА: Предложи четкий результат или "входной продукт" (аудит/исследование).
    4. СТИЛЬ: Уверенный, лаконичный, экспертный. 3-4 предложения. Человечный язык.
    
    ПРАВИЛА:
    - Если продукт дорогой, предлагай не продажу, а знакомство через экспертный контент.
    - Используй ABM-подход: пиши так, чтобы заинтересовать группу ЛПР.
    - Никаких "Надеюсь, у вас все хорошо". Сразу к фактуре.
    """
    
    full_context = f"Данные о лиде: {lead_name}. {lead_context}\nНаш оффер: {offer}"
    if user_kb:
        full_context += f"\nДоп. база знаний: {user_kb}"
        
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": f"Напиши идеальное письмо по этой фактуре:\n{full_context}"}
        ],
        "temperature": 0.6
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        return response.json()['choices'][0]['message']['content']
    except:
        return "❌ Ошибка генерации. Проверь API ключ."

def send_mail(to, subject, body, user, pw, server, port):
    try:
        msg = MIMEMultipart(); msg['From'], msg['To'], msg['Subject'] = user, to, subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        with smtplib.SMTP_SSL(server, port, timeout=15) as s:
            s.login(user, pw); s.send_message(msg)
        return True
    except: return False

# --- ИНТЕРФЕЙС ---
with st.sidebar:
    st.markdown("# 🚀 Outreach Pro")
    st.markdown("### 📱 Автор: Нурислам")
    st.markdown(f"""
    <a href="https://t.me/nurislam_manager" class="contact-link">TG</a>
    <a href="https://tenchat.ru/nurislamzinnurov" class="contact-link">TenChat</a>
    <a href="https://www.linkedin.com/in/nurislam-zinnurov-2b799b408" class="contact-link">LinkedIn</a>
    """, unsafe_allow_html=True)
    st.markdown("---")
    api_key = st.text_input("Groq API Key", value=get_secret("GROQ_API_KEY"), type="password")
    st.markdown("---")
    mail_user = st.text_input("Email", value=get_secret("EMAIL_USER"))
    mail_pass = st.text_input("Пароль приложения", value=get_secret("EMAIL_PASS"), type="password")
    service = st.selectbox("Сервис", ["Yandex", "Mail.ru"])
    st.markdown("---")
    user_kb = st.text_area("🧠 Твоя база знаний (кейсы, цифры)", height=150)

st.markdown("# ✍️ Генератор писем")
tab1, tab2 = st.tabs(["📧 Создать", "📊 История"])

with tab1:
    c1, c2 = st.columns(2)
    with c1: l_name = st.text_input("Имя лида")
    with c2: l_email = st.text_input("Email лида")
    l_ctx = st.text_area("Контекст (почему пишем?)", height=100)
    my_offer = st.text_area("Твой оффер", height=100)
    
    if st.button("✨ СГЕНЕРИРОВАТЬ"):
        if not api_key: st.error("Введи API Key!")
        else:
            with st.spinner("Думаю..."):
                st.session_state.generated_email = generate_pro_email(l_name, l_ctx, my_offer, api_key, user_kb)

    if st.session_state.generated_email:
        st.markdown("---")
        final_body = st.text_area("Результат:", value=st.session_state.generated_email, height=200)
        if st.button("🚀 ОТПРАВИТЬ"):
            server = "smtp.yandex.ru" if service == "Yandex" else "smtp.mail.ru"
            if send_mail(l_email, f"Quick question for {l_name}", final_body, mail_user, mail_pass, server, 465):
                st.success("Улетело! 🎉")
                st.session_state.messages.append({"t": datetime.now().strftime("%H:%M"), "e": l_email})
                st.session_state.generated_email = None
            else: st.error("Ошибка отправки.")

with tab2:
    for m in reversed(st.session_state.messages):
        st.markdown(f"<div class='info-box'>⏰ {m['t']} → {m['e']} ✅</div>", unsafe_allow_html=True)

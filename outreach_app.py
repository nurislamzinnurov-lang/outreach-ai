import streamlit as st
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- НАСТРОЙКИ СТРАНИЦЫ ---
st.set_page_config(page_title="AI Outreach Assistant", page_icon="🚀")

st.title("🚀 AI Outreach Assistant")
st.markdown("Генерируй персонализированные письма и отправляй их в один клик.")

# --- БОКОВАЯ ПАНЕЛЬ (НАСТРОЙКИ) ---
with st.sidebar:
    st.header("⚙️ Настройки")
    groq_key = st.text_input("Groq API Key", type="password", help="Получи на console.groq.com")
    
    st.subheader("📧 Почта (SMTP)")
    smtp_service = st.selectbox("Сервис", ["Yandex", "Mail.ru", "Custom"])
    email_user = st.text_input("Твой Email")
    email_pass = st.text_input("Пароль приложения", type="password", help="Не обычный пароль, а пароль для внешних приложений!")
    
    if smtp_service == "Yandex":
        smtp_server, smtp_port = "smtp.yandex.ru", 465
    elif smtp_service == "Mail.ru":
        smtp_server, smtp_port = "smtp.mail.ru", 465
    else:
        smtp_server = st.text_input("SMTP Server")
        smtp_port = st.number_input("SMTP Port", value=465)

# --- ОСНОВНОЙ ИНТЕРФЕЙС ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📝 Данные лида")
    lead_name = st.text_input("Имя лида", placeholder="Например: Levan")
    lead_email = st.text_input("Email лида", placeholder="levan@example.com")
    lead_context = st.text_area("Контекст (инфо о лиде)", placeholder="Например: Founder ORBI Group, строит отель в Батуми...", height=150)

with col2:
    st.subheader("💡 Твой оффер")
    my_offer = st.text_area("Что предлагаем?", placeholder="Например: Реклама на 1500 экранах Novikov TV...", height=235)

# --- ЛОГИКА ---
def generate_email(context, offer, api_key):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    prompt = f"Напиши короткое холодное письмо (3-4 предложения). Лид: {context}. Оффер: {offer}. Без воды, фокус на выгоде."
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"Ошибка ИИ: {str(e)}"

def send_mail(to, subject, body, user, pw, server, port):
    try:
        msg = MIMEMultipart()
        msg['From'], msg['To'], msg['Subject'] = user, to, subject
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP_SSL(server, port) as s:
            s.login(user, pw)
            s.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Ошибка отправки: {str(e)}")
        return False

# --- КНОПКИ ---
if st.button("✨ Сгенерировать письмо"):
    if not groq_key:
        st.warning("Введи Groq API Key в настройках слева!")
    else:
        with st.spinner("ИИ думает..."):
            st.session_state.generated_email = generate_email(lead_context, my_offer, groq_key)

if "generated_email" in st.session_state:
    st.subheader("📧 Результат:")
    final_email = st.text_area("Отредактируй, если нужно:", value=st.session_state.generated_email, height=200)
    
    if st.button("🚀 Отправить письмо"):
        if not email_user or not email_pass:
            st.warning("Настрой почту в боковой панели!")
        else:
            with st.spinner("Отправка..."):
                if send_mail(lead_email, f"Quick question for {lead_name}", final_email, email_user, email_pass, smtp_server, smtp_port):
                    st.success("Письмо успешно улетело! 🎉")

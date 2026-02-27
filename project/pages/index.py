import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import os
from groq import Groq
from dotenv import load_dotenv




#PREVENTS UNAUTHORIZED ACCESS
# Protect page


# -------------------------
# LOAD API KEY (STREAMLIT CLOUD SAFE)
# -------------------------

try:
    groq_api_key = st.secrets["GROQ_API_KEY"]
except:
    st.error("Groq API key not found in Streamlit secrets.")
    st.stop()

client = Groq(api_key=groq_api_key)

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(page_title="MedSafe AI Pro", page_icon="🩺", layout="centered")

# -------------------------
# STYLING
# -------------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(-45deg, #0f172a, #1e293b, #111827, #0f172a);
    background-size: 400% 400%;
    animation: gradientMove 15s ease infinite;
}
@keyframes gradientMove {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
.block-container {
    padding-top: 5%;
    max-width: 650px;
}
.main-title {
    text-align: center;
    font-size: 46px;
    font-weight: 800;
    background: linear-gradient(90deg, #2EC4B6, #3ddad7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.stButton>button {
    background: linear-gradient(90deg, #2EC4B6, #3ddad7);
    color: white;
    border-radius: 12px;
    font-weight: bold;
}
h1, h2, h3 {
    color: #2EC4B6 !important;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# DATABASE SETUP
# -------------------------
conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS history (
    username TEXT,
    drug1 TEXT,
    drug2 TEXT,
    result TEXT
)
""")

conn.commit()

# -------------------------
# PASSWORD HASH
# -------------------------
def hash_password(password):
    return hashlib.sha256(password.strip().encode()).hexdigest()

# -------------------------
# AUTH FUNCTIONS
# -------------------------
def register_user(username, password):
    try:
        c.execute("INSERT INTO users VALUES (?, ?)",
                  (username.strip().lower(), hash_password(password)))
        conn.commit()
        return True
    except:
        return False

def login_user(username, password):
    c.execute("SELECT * FROM users WHERE username=?",
              (username.strip().lower(),))
    user = c.fetchone()
    if user and user[1] == hash_password(password):
        return True
    return False

def save_history(username, drug1, drug2, result):
    c.execute("INSERT INTO history VALUES (?, ?, ?, ?)",
              (username, drug1, drug2, result))
    conn.commit()

def get_history(username):
    c.execute("SELECT drug1, drug2, result FROM history WHERE username=?",
              (username,))
    return c.fetchall()

# -------------------------
# LOAD DRUG CSV
# -------------------------
if not os.path.exists("drug_interactions.csv"):
    st.error("drug_interactions.csv file not found.")
    st.stop()

df = pd.read_csv("drug_interactions.csv")

def check_interaction(d1, d2):
    for _, row in df.iterrows():
        if ((row['drug1'].lower() == d1.lower() and row['drug2'].lower() == d2.lower()) or
            (row['drug1'].lower() == d2.lower() and row['drug2'].lower() == d1.lower())):
            return f"{row['severity']} Risk: {row['reason']}"
    return "Safe: No known interaction found."

# -------------------------
# SESSION STATE
# -------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# -------------------------
# LOGIN / REGISTER
# -------------------------
if not st.session_state.logged_in:

    st.markdown('<div class="main-title">🩺 MedSafe AI Pro</div>', unsafe_allow_html=True)
    menu = st.radio("Select Option", ["Login", "Register"])

    if menu == "Register":
        st.subheader("Create Account")
        new_user = st.text_input("Username")
        new_pass = st.text_input("Password", type="password")

        if st.button("Register"):
            if register_user(new_user, new_pass):
                st.success("Account created successfully!")
            else:
                st.error("Username already exists.")

    if menu == "Login":
        st.subheader("Login")
        user = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("🚀 Login / Signup", key="landing_login_button"):
            
            if login_user(user, password):
                st.session_state.logged_in = True
                st.session_state.username = user.strip().lower()
                st.rerun()
            else:
                st.error("Wrong credentials.")

# -------------------------
# MAIN DASHBOARD
# -------------------------
else:

    st.sidebar.success(f"Welcome {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    st.title("🩺 MedSafe AI Dashboard")

    tabs = st.tabs(["💊 Drug Checker", "📊 History", "🤖 AI Chatbot"])

    # Drug Checker
    with tabs[0]:
        age = st.number_input("Patient Age", min_value=0, max_value=120)
        drug_list = sorted(set(df['drug1'].tolist() + df['drug2'].tolist()))
        drug1 = st.selectbox("Medicine 1", drug_list)
        drug2 = st.selectbox("Medicine 2", drug_list)

        if st.button("Analyze Interaction"):
            result = check_interaction(drug1, drug2)

            if "High" in result:
                st.error(result)
            elif "Moderate" in result:
                st.warning(result)
            else:
                st.success(result)

            if age < 12 and drug1.lower() == "aspirin":
                st.error("Aspirin not recommended under 12.")

            save_history(st.session_state.username, drug1, drug2, result)
            
    # History
    with tabs[1]:
        records = get_history(st.session_state.username)
        if records:
            for r in records:
                st.write(f"{r[0]} + {r[1]} → {r[2]}")
        else:
            st.info("No history yet.")

    # AI Chatbot
    with tabs[2]:

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        user_input = st.text_input("Ask a medical safety question")

        if st.button("Send"):
            if user_input:
                try:
                    response = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[
                            {"role": "system", "content": "You are a medical drug safety assistant. Do not diagnose or prescribe. Always recommend consulting a certified doctor."},
                            {"role": "user", "content": user_input}
                        ]
                    )

                    ai_reply = response.choices[0].message.content

                except Exception as e:
                    ai_reply = f"Error: {str(e)}"

                st.session_state.chat_history.append(("You", user_input))
                st.session_state.chat_history.append(("MedSafe AI", ai_reply))

        for speaker, message in st.session_state.chat_history:
            if speaker == "You":
                st.markdown(f"<div style='text-align:right;background:#1f6f78;color:white;padding:10px;border-radius:15px;margin:5px;max-width:75%;margin-left:auto;'><b>You:</b><br>{message}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align:left;background:#1b3a41;color:#2EC4B6;padding:10px;border-radius:15px;margin:5px;max-width:75%;'><b>MedSafe AI:</b><br>{message}</div>", unsafe_allow_html=True)


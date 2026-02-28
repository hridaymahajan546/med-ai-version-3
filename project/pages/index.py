import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import os
from groq import Groq
from datetime import date

# -------------------------
# LOAD API KEY
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
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0b1c2d, #102a43, #0b1c2d) !important;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# DATABASE SETUP
# -------------------------
conn = sqlite3.connect("database.db", check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS history (
    username TEXT,
    drug1 TEXT,
    drug2 TEXT,
    result TEXT
)""")

c.execute("""CREATE TABLE IF NOT EXISTS allergies (
    username TEXT,
    allergy TEXT
)""")

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
    return user and user[1] == hash_password(password)

# -------------------------
# ALLERGY FUNCTIONS
# -------------------------
def add_allergy(username, allergy):
    c.execute("INSERT INTO allergies VALUES (?, ?)", (username, allergy.lower()))
    conn.commit()

def get_allergies(username):
    c.execute("SELECT allergy FROM allergies WHERE username=?", (username,))
    return [row[0] for row in c.fetchall()]

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
            return row['severity'], row['reason']
    return "Low", "No known major interaction."

# -------------------------
# SESSION STATE
# -------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# -------------------------
# LOGIN / REGISTER
# -------------------------
if not st.session_state.logged_in:

    st.title("🩺 MedSafe AI Pro")
    menu = st.radio("Select Option", ["Login", "Register"])

    if menu == "Register":
        new_user = st.text_input("Username")
        new_pass = st.text_input("Password", type="password")
        if st.button("Register"):
            if register_user(new_user, new_pass):
                st.success("Account created!")
            else:
                st.error("Username exists.")

    if menu == "Login":
        user = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
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

    username = st.session_state.username

    st.sidebar.success(f"Welcome {username}")

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    tabs = st.tabs([
        "💊 Drug Checker",
        "⚠️ Allergies",
        "🩹 Side Effects",
        "🤖 AI Chat",
        "REMINDER",
        "TODAY'S REMINDER"
    ])

    # -------------------------
    # REMINDER TAB (FIXED ONLY THIS PART)
    # -------------------------
    with tabs[4]:

        conn2 = sqlite3.connect("reminders.db", check_same_thread=False)
        c2 = conn2.cursor()

        # Create table safely
        c2.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            medicine TEXT,
            dosage TEXT,
            reminder_date TEXT,
            reminder_time TEXT
        )
        """)
        conn2.commit()

        st.subheader("⏰ Add Medication Reminder")

        with st.form("reminder_form"):
            med_name = st.text_input("Medicine Name")
            dosage = st.text_input("Dosage")
            reminder_date = st.date_input("Select Date", value=date.today())
            reminder_time = st.time_input("Select Time")

            submit = st.form_submit_button("Save Reminder")

            if submit:
                if med_name and dosage:
                    c2.execute(
                        "INSERT INTO reminders (username, medicine, dosage, reminder_date, reminder_time) VALUES (?, ?, ?, ?, ?)",
                        (username, med_name, dosage, str(reminder_date), str(reminder_time))
                    )
                    conn2.commit()
                    st.success("✅ Reminder Saved Successfully!")
                else:
                    st.warning("Please fill all fields")

        conn2.close()

    # -------------------------
    # TODAY'S REMINDER TAB
    # -------------------------
    with tabs[5]:

        conn2 = sqlite3.connect("reminders.db", check_same_thread=False)
        c2 = conn2.cursor()

        st.subheader("📅 Today's Reminders")

        today = str(date.today())

        c2.execute(
            "SELECT * FROM reminders WHERE username=? AND reminder_date=?",
            (username, today)
        )
        rows = c2.fetchall()

        if rows:
            for row in rows:
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

                col1.write(f"💊 {row[2]}")
                col2.write(f"💉 {row[3]}")
                col3.write(f"🕒 {row[5]}")

                if col4.button("❌", key=f"delete_{row[0]}"):
                    c2.execute("DELETE FROM reminders WHERE id = ?", (row[0],))
                    conn2.commit()
                    st.rerun()
        else:
            st.info("No reminders for today.")

        conn2.close()

















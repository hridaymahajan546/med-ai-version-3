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
# MAIN DATABASE
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
# REMINDERS DATABASE (initialized once, safely)
# -------------------------
conn2 = sqlite3.connect("reminders.db", check_same_thread=False)
c2 = conn2.cursor()
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
conn2.close()

# -------------------------
# PASSWORD HASH
# -------------------------
def hash_password(password):
    return hashlib.sha256(password.strip().encode()).hexdigest()

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

def add_allergy(username, allergy):
    c.execute("INSERT INTO allergies VALUES (?, ?)", (username, allergy.lower()))
    conn.commit()

def get_allergies(username):
    c.execute("SELECT allergy FROM allergies WHERE username=?", (username,))
    return [row[0] for row in c.fetchall()]

# -------------------------
# LOAD CSV
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
# SESSION
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
        "⏰ REMINDER",
        "📅 TODAY'S REMINDER"
    ])

    # -------------------------
    # TAB 1: DRUG CHECKER
    # -------------------------
    with tabs[0]:
        st.subheader("💊 Drug Interaction Checker")

        drug1 = st.text_input("Enter First Drug", key="drug1")
        drug2 = st.text_input("Enter Second Drug", key="drug2")

        if st.button("Check Interaction"):
            if drug1 and drug2:
                severity, reason = check_interaction(drug1, drug2)

                if severity.lower() == "high":
                    st.error(f"⚠️ HIGH Severity Interaction\n\n{reason}")
                elif severity.lower() == "moderate":
                    st.warning(f"⚠️ MODERATE Severity Interaction\n\n{reason}")
                else:
                    st.success(f"✅ LOW / No Major Interaction\n\n{reason}")

                # Save to history
                c.execute("INSERT INTO history VALUES (?, ?, ?, ?)",
                          (username, drug1, drug2, f"{severity}: {reason}"))
                conn.commit()
            else:
                st.warning("Please enter both drug names.")

        st.markdown("---")
        st.subheader("📋 Check History")
        c.execute("SELECT drug1, drug2, result FROM history WHERE username=?", (username,))
        history_rows = c.fetchall()
        if history_rows:
            for h in history_rows:
                st.write(f"**{h[0]}** + **{h[1]}** → {h[2]}")
        else:
            st.info("No history yet.")

    # -------------------------
    # TAB 2: ALLERGIES
    # -------------------------
    with tabs[1]:
        st.subheader("⚠️ Manage Allergies")

        new_allergy = st.text_input("Add a new allergy (drug/substance name)")
        if st.button("Add Allergy"):
            if new_allergy.strip():
                add_allergy(username, new_allergy.strip())
                st.success(f"Allergy '{new_allergy}' added!")
            else:
                st.warning("Please enter an allergy name.")

        st.markdown("---")
        st.subheader("Your Allergies")
        allergies = get_allergies(username)
        if allergies:
            for a in allergies:
                st.write(f"🔴 {a.capitalize()}")
        else:
            st.info("No allergies recorded.")

    # -------------------------
    # TAB 3: SIDE EFFECTS
    # -------------------------
    with tabs[2]:
        st.subheader("🩹 Side Effects Lookup")

        drug_se = st.text_input("Enter Drug Name to look up side effects")
        if st.button("Look Up Side Effects"):
            if drug_se.strip():
                with st.spinner("Fetching side effects..."):
                    try:
                        response = client.chat.completions.create(
                            model="llama3-8b-8192",
                            messages=[
                                {"role": "system", "content": "You are a medical assistant. Provide clear, concise side effects of medications. Always advise consulting a doctor."},
                                {"role": "user", "content": f"What are the common and serious side effects of {drug_se}?"}
                            ]
                        )
                        result = response.choices[0].message.content
                        st.markdown(result)
                    except Exception as e:
                        st.error(f"Error fetching side effects: {e}")
            else:
                st.warning("Please enter a drug name.")

    # -------------------------
    # TAB 4: AI CHAT
    # -------------------------
    with tabs[3]:
        st.subheader("🤖 AI Medical Assistant")

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        user_msg = st.text_input("Ask a medical question...", key="chat_input")

        if st.button("Send"):
            if user_msg.strip():
                st.session_state.chat_history.append({"role": "user", "content": user_msg})

                with st.spinner("Thinking..."):
                    try:
                        messages = [
                            {"role": "system", "content": "You are MedSafe AI, a helpful medical assistant. Provide accurate health information and always remind users to consult a healthcare professional for medical decisions."}
                        ] + st.session_state.chat_history

                        response = client.chat.completions.create(
                            model="llama3-8b-8192",
                            messages=messages
                        )
                        reply = response.choices[0].message.content
                        st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    except Exception as e:
                        st.error(f"Error: {e}")

        # Display chat history
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f"**🧑 You:** {msg['content']}")
            else:
                st.markdown(f"**🤖 MedSafe AI:** {msg['content']}")

        if st.button("Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()

    # -------------------------
    # TAB 5: REMINDER
    # -------------------------
    with tabs[4]:
        conn2 = sqlite3.connect("reminders.db", check_same_thread=False)
        c2 = conn2.cursor()

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
                    st.warning("Please fill all fields.")

        conn2.close()

    # -------------------------
    # TAB 6: TODAY'S REMINDER
    # -------------------------
    with tabs[5]:
        conn2 = sqlite3.connect("reminders.db", check_same_thread=False)
        c2 = conn2.cursor()

        st.subheader("📅 Today's Reminders")

        today = str(date.today())

        c2.execute(
            "SELECT id, medicine, dosage, reminder_time FROM reminders WHERE username=? AND reminder_date=?",
            (username, today)
        )
        rows = c2.fetchall()

        if rows:
            for row in rows:
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

                col1.write(f"💊 {row[1]}")
                col2.write(f"💉 {row[2]}")
                col3.write(f"🕒 {row[3]}")

                if col4.button("❌", key=f"delete_{row[0]}"):
                    c2.execute("DELETE FROM reminders WHERE id = ?", (row[0],))
                    conn2.commit()
                    st.rerun()
        else:
            st.info("No reminders for today.")

        conn2.close()

















import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import os
from groq import Groq

# -------------------------
#LOAD API KEY
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

    tabs = st.tabs(["💊 Drug Checker", "⚠️ Allergies", "🩹 Side Effects", "🤖 AI Chat"])

    # -------------------------
    # DRUG CHECKER + RISK METER
    # -------------------------
    with tabs[0]:

        drug_list = sorted(set(df['drug1'].tolist() + df['drug2'].tolist()))
        drug1 = st.selectbox("Medicine 1", drug_list)
        drug2 = st.selectbox("Medicine 2", drug_list)

        if st.button("Analyze Interaction"):

            severity, reason = check_interaction(drug1, drug2)

            risk_score = {"Low": 25, "Moderate": 60, "High": 90}.get(severity, 20)

            st.progress(risk_score)

            if severity == "High":
                st.error(f"🔴 High Risk: {reason}")
            elif severity == "Moderate":
                st.warning(f"🟡 Moderate Risk: {reason}")
            else:
                st.success(f"🟢 Low Risk: {reason}")

            # Allergy Check
            allergies = get_allergies(username)
            if drug1.lower() in allergies or drug2.lower() in allergies:
                st.error("⚠️ ALERT: This drug matches your recorded allergy!")

    # -------------------------
    # ALLERGY TRACKER
    # -------------------------
    with tabs[1]:

        st.subheader("Your Recorded Allergies")

        new_allergy = st.text_input("Add Allergy (e.g., aspirin, penicillin)")

        if st.button("Add Allergy"):
            add_allergy(username, new_allergy)
            st.success("Allergy added.")

        allergies = get_allergies(username)

        if allergies:
            for a in allergies:
                st.write(f"• {a}")
        else:
            st.info("No allergies recorded.")

    # -------------------------
    # SIDE EFFECT ANALYZER
    # -------------------------
    with tabs[2]:

        selected_drug = st.selectbox("Select Drug", drug_list)

        if st.button("Analyze Side Effects"):
            try:
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": "You are a medical safety assistant. List common and serious side effects. Do not diagnose."},
                        {"role": "user", "content": f"List side effects of {selected_drug}"}
                    ]
                )
                st.write(response.choices[0].message.content)
            except Exception as e:
                st.error(str(e))

    # -------------------------
    # AI CHAT
    # -------------------------
    with tabs[3]:
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


    
    with tabs[4]:
        st.subheader("💊 Medication Reminder System")

    # ---------------------------
    # ADD REMINDER FORM
    # ---------------------------
    with st.form("add_reminder"):
        col1, col2 = st.columns(2)

        with col1:
            med_name = st.text_input("Medicine Name")
            dosage = st.text_input("Dosage")

        with col2:
            reminder_time = st.time_input("Reminder Time", value=time(9,0))
            frequency = st.selectbox("Frequency", ["Daily", "Weekly"])

        submit = st.form_submit_button("Add Reminder")

        if submit:
            if med_name and dosage:
                c.execute("""INSERT INTO reminders
                    (username, medicine, dosage, reminder_time, frequency, created_on)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (username,
                     med_name.strip(),
                     dosage.strip(),
                     reminder_time.strftime("%H:%M"),
                     frequency,
                     str(date.today())))
                conn.commit()
                st.success("✅ Reminder Saved Successfully!")
                st.rerun()
            else:
                st.error("Please fill all fields.")

    st.markdown("---")

    # ---------------------------
    # TODAY'S REMINDERS
    # ---------------------------
    st.subheader("📅 Today's Reminders")

    current_time = datetime.now().strftime("%H:%M")

    c.execute("""SELECT * FROM reminders
                 WHERE username=?""", (username,))
    reminders = c.fetchall()

    today_reminders = []
    all_reminders = []

    for r in reminders:
        all_reminders.append(r)
        if r[4] == current_time:
            today_reminders.append(r)

    if today_reminders:
        for r in today_reminders:
            st.success(f"🔔 Time to take {r[2]} ({r[3]})")
    else:
        st.info("No reminder at this moment.")

    st.markdown("---")

    # ---------------------------
    # ALL SAVED REMINDERS
    # ---------------------------
    st.subheader("💾 All Saved Reminders")

    if all_reminders:
        for r in all_reminders:
            col1, col2 = st.columns([5,1])

            with col1:
                st.markdown(f"""
                💊 **{r[2]}**  
                Dosage: {r[3]}  
                Time: {r[4]}  
                Frequency: {r[5]}
                """)

            with col2:
                if st.button("❌", key=f"delete_{r[0]}"):
                    c.execute("DELETE FROM reminders WHERE id=?", (r[0],))
                    conn.commit()
                    st.rerun()
    else:
        st.info("No saved reminders yet.")
        

    



       



              
             










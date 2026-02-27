import streamlit as st
import base64

st.set_page_config(page_title="MedSafe AI", layout="wide")

# ---- Redirect Function ----
if st.button("🚀 Login / Signup"):
    st.experimental_set_query_params(page="index")
    st.switch_page("pages/index.py")

# ---- CSS Styling ----
st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif;
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    color: white;
}

.main {
    background: transparent;
}

.hero-title {
    font-size: 65px;
    font-weight: 700;
    text-align: center;
    background: -webkit-linear-gradient(#00f5ff, #ff00c8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: glow 2s ease-in-out infinite alternate;
}

@keyframes glow {
    from { text-shadow: 0 0 10px #00f5ff; }
    to { text-shadow: 0 0 25px #ff00c8; }
}

.subtitle {
    text-align: center;
    font-size: 22px;
    opacity: 0.85;
    margin-bottom: 40px;
}

.section {
    padding: 40px;
    border-radius: 20px;
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(15px);
    margin-bottom: 40px;
    box-shadow: 0px 0px 30px rgba(255, 0, 200, 0.2);
    transition: 0.4s ease;
}

.section:hover {
    transform: scale(1.02);
    box-shadow: 0px 0px 40px rgba(0, 245, 255, 0.4);
}

.dev-card {
    padding: 20px;
    border-radius: 15px;
    background: rgba(255,255,255,0.07);
    text-align: center;
    transition: 0.3s;
}

.dev-card:hover {
    transform: translateY(-10px);
    box-shadow: 0px 0px 20px #ff00c8;
}

.footer {
    text-align: center;
    padding: 30px;
    font-size: 14px;
    opacity: 0.7;
}

.divider {
    height: 3px;
    width: 80%;
    margin: 60px auto;
    background: linear-gradient(to right, #00f5ff, #ff00c8);
    border-radius: 10px;
}

.legal-box {
    padding: 25px;
    border-radius: 15px;
    background: rgba(255,255,255,0.05);
    font-size: 13px;
    opacity: 0.75;
    line-height: 1.6;
    text-align: center;
}

.big-glow {
    text-align:center;
    font-size: 22px;
    margin-top: 40px;
    animation: glow 3s infinite alternate;
}

</style>
""", unsafe_allow_html=True)

# ---- HERO SECTION ----
st.markdown('<div class="hero-title">💊 MedSafe AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Smart • Secure • AI Powered Drug Interaction & Medical Safety Platform</div>', unsafe_allow_html=True)

st.write("")

col1, col2, col3 = st.columns([1,2,1])
with col2:
    if st.button("🚀 Login / Signup"):
        go_to_login()

# ---- ABOUT SECTION ----
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

st.markdown("""
<div class="section">
<h2>✨ About MedSafe AI</h2>
<p>
MedSafe AI is a next-generation AI-powered healthcare assistant designed to detect drug interactions,
enhance prescription safety, and provide intelligent health insights in seconds.
Built with advanced backend systems and aesthetic frontend innovation, it ensures
accuracy, security, and seamless user experience.
</p>
</div>
""", unsafe_allow_html=True)

# ---- FEATURES ----
st.markdown("""
<div class="section">
<h2>🚀 Features</h2>
<ul>
<li>⚡ AI-Based Drug Interaction Detection</li>
<li>🔒 Secure Authentication System</li>
<li>📊 Real-Time Medical Data Processing</li>
<li>🎨 Modern Gen-Z Aesthetic Interface</li>
<li>🧠 Smart Healthcare Insights</li>
</ul>
</div>
""", unsafe_allow_html=True)

# ---- DEVELOPERS ----
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

st.markdown("<h2 style='text-align:center;'>👨‍💻 Meet The Developers</h2>", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="dev-card">
    <h3>👩‍💻 AASHI</h3>
    <p><b>Role:</b> Backend Developer & System Tester</p>
    <p>Ensured database integrity, backend stability, and flawless testing execution.</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="dev-card">
    <h3>👩‍🎨 AMIKSHA</h3>
    <p><b>Role:</b> Frontend Developer & UI Designer</p>
    <p>Designed the Gen-Z aesthetic interface, colour pattern & interactive layout.</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="dev-card">
    <h3>👨‍💻 HRIDAY</h3>
    <p><b>Role:</b> Frontend Developer & Functional Architect</p>
    <p>Developed core system functions and ensured seamless feature integration.</p>
    </div>
    """, unsafe_allow_html=True)

# ---- X FACTOR GLOW MESSAGE ----
st.markdown("""
<div class="big-glow">
🌌 Built with Passion. Powered by Intelligence. Designed for the Future.
</div>
""", unsafe_allow_html=True)

# ---- LEGAL SECTION ----
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

st.markdown("""
<div class="legal-box">
<b>© 2026 MedSafe AI. All Rights Reserved.</b><br><br>
This platform, including its design, source code, AI models, database structure,
UI/UX elements, branding, and content are protected under applicable copyright laws.
Unauthorized reproduction, distribution, or modification of any part of this project
without written permission from the developers is strictly prohibited.
<br><br>
MedSafe AI is developed strictly for educational and healthcare assistance purposes.
It does not replace professional medical advice.
</div>
""", unsafe_allow_html=True)

# ---- FOOTER ----
st.markdown("""
<div class="footer">
Made with ❤️ using Streamlit | MedSafe AI Official Platform
</div>
""", unsafe_allow_html=True)

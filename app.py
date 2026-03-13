import streamlit as st
from audiorecorder import audiorecorder
import google.generativeai as genai
import urllib.parse
import tempfile
import os
import json

# --- 1. PAGE CONFIG & STYLING ---
st.set_page_config(page_title="PCA Smart Vault", page_icon="🌳", layout="wide")

# This CSS makes the app look like a professional dashboard instead of a basic website
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        height: 3em;
        background-color: #2e7d32;
        color: white;
        font-weight: bold;
    }
    .report-card {
        background-color: white;
        border-radius: 15px;
        padding: 25px;
        margin-bottom: 20px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .card-title {
        font-size: 1.3em;
        font-weight: 700;
        color: #1b5e20;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .task-box {
        background-color: #e8f5e9;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-left: 5px solid #2e7d32;
    }
    .event-box {
        background-color: #e3f2fd;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-left: 5px solid #1565c0;
    }
    .shortcut-btn {
        background-color: white;
        padding: 5px 12px;
        border-radius: 15px;
        text-decoration: none;
        color: #333;
        font-size: 0.8em;
        font-weight: bold;
        border: 1px solid #ccc;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR SETUP ---
with st.sidebar:
    st.header("Settings")
    API_KEY = st.text_input("Gemini API Key", type="password")
    st.info("Your keys are never stored on the server. They stay in your browser session.")

if not API_KEY:
    st.warning("Please enter your Gemini API Key in the sidebar to begin.")
    st.stop()

genai.configure(api_key=API_KEY)

# --- 3. THE HEADER & ORCHARD VIEW ---
# This displays your HD photo as the dashboard hero image
if os.path.exists("orchard.jpg"):
    st.image("orchard.jpg", use_container_width=True)
else:
    st.info("Add a photo named 'orchard.jpg' to your folder to see your custom header.")

st.markdown("<h1 style='text-align: center;'>🌳 PCA Smart Vault</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666;'>Automated Agronomy Intelligence</p>", unsafe_allow_html=True)

# --- 4. THE RECORDER INTERFACE ---
col_pad1, col_main, col_pad2 = st.columns([1, 2, 1])

with col_main:
    audio = audiorecorder("⏺️ Start New Recording", "⏹️ Stop & Analyze")

if len(audio) > 0:
    st.audio(audio.export().read())
    
    with st.spinner("Processing conversation..."):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            audio.export(tmp.name, format="mp3")
            
            # 5. UPLOAD & AI BRAIN
            audio_file = genai.upload_file(path=tmp.name)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = """
            Listen to this recording. You are an expert PCA/CCA assistant. 
            Output ONLY a JSON object with this exact structure:
            {
              "summary": "3-4 sentence high-level summary",
              "tasks": ["Task description 1", "Task description 2"],
              "events": [{"title": "Event Name", "time": "Time/Date"}]
            }
            """
            
            response = model.generate_content([prompt, audio_file])
            
            # Clean the JSON output (removes markdown backticks if Gemini adds them)
            clean_json = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_json)

            # --- 6. THE DASHBOARD VIEW ---
            st.divider()
            
            # Card 1: Executive Summary
            st.markdown(f"""
            <div class="report-card">
                <div class="card-title">📝 Executive Summary</div>
                <p style="color: #444; line-height: 1.6;">{data['summary']}</p>
            </div>
            """, unsafe_allow_html=True)

            # Card 2 & 3: Actionable Items
            col_left, col_right = st.columns(2)

            with col_left:
                st.markdown('<div class="report-card"><div class="card-title">✅ Tasks for Reminders</div>', unsafe_allow_html=True)
                for task in data['tasks']:
                    encoded_task = urllib.parse.quote(task)
                    url = f"shortcuts://run-shortcut?name=AddReminder&input=text&text={encoded_task}"
                    st.markdown(f"""
                    <div class="task-box">
                        <span>{task}</span>
                        <a href="{url}" class="shortcut-btn">➕ Add</a>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with col_right:
                st.markdown('<div class="report-card"><div class="card-title">📅 Calendar Events</div>', unsafe_allow_html=True)
                for event in data['events']:
                    event_str = f"{event['title']} at {event['time']}"
                    encoded_event = urllib.parse.quote(event_str)
                    url = f"shortcuts://run-shortcut?name=AddCalendar&input=text&text={encoded_event}"
                    st.markdown(f"""
                    <div class="event-box">
                        <span>{event['title']}<br><small>{event['time']}</small></span>
                        <a href="{url}" class="shortcut-btn">➕ Add</a>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

    # Cleanup temp audio
    os.remove(tmp.name)

# --- 7. FOOTER ---
st.markdown("<p style='text-align: center; font-size: 0.8em; color: #999; margin-top: 50px;'>Powered by Gemini 1.5 Flash • Optimized for Northern California Agriculture</p>", unsafe_allow_html=True)
import streamlit as st
from streamlit_mic_recorder import mic_recorder
import google.generativeai as genai
import urllib.parse
import tempfile
import os
import json
import time

# --- 1. PAGE CONFIG & STYLING ---
st.set_page_config(page_title="PCA Smart Vault", page_icon="🌳", layout="wide")

# Custom CSS for the "Otter Dashboard" look
st.markdown("""
<style>
    .report-card { background-color: white; border-radius: 15px; padding: 25px; margin-bottom: 20px; border: 1px solid #e0e0e0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .card-title { font-size: 1.3em; font-weight: 700; color: #1b5e20; margin-bottom: 15px; }
    .task-box { background-color: #e8f5e9; padding: 12px; border-radius: 10px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; border-left: 5px solid #2e7d32; }
    .event-box { background-color: #e3f2fd; padding: 12px; border-radius: 10px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; border-left: 5px solid #1565c0; }
    .shortcut-btn { background-color: white; padding: 5px 12px; border-radius: 15px; text-decoration: none; color: #333; font-size: 0.8em; font-weight: bold; border: 1px solid #ccc; }
</style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    API_KEY = st.text_input("Gemini API Key", type="password")
    if API_KEY:
        genai.configure(api_key=API_KEY)

# --- 3. HEADER ---
# Displays your HD orchard photo
if os.path.exists("orchard.jpg"):
    st.image("orchard.jpg", use_container_width=True)

st.markdown("<h1 style='text-align: center;'>🌳 PCA Smart Vault</h1>", unsafe_allow_html=True)

# --- 4. THE RECORDER ---
if not API_KEY:
    st.warning("Please enter your Gemini API Key in the sidebar to start.")
else:
    st.write("Click the mic to start/stop recording your call or scouting note:")
    audio_data = mic_recorder(start_prompt="⏺️ Record Note", stop_prompt="⏹️ Stop & Analyze", key='recorder')

    if audio_data:
        st.audio(audio_data['bytes'])
        
        with st.spinner("Gemini is analyzing the audio..."):
            # Create temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(audio_data['bytes'])
                tmp_path = tmp.name
            
            try:
                # 5. UPLOAD & WAIT FOR PROCESSING
                audio_file = genai.upload_file(path=tmp_path)
                
                # Loop until file is ready (prevents 'NotFound' errors)
                while audio_file.state.name == "PROCESSING":
                    time.sleep(1)
                    audio_file = genai.get_file(audio_file.name)

                model = genai.GenerativeModel('gemini-1.5-flash-latest')
                
                prompt = """
                You are a PCA/CCA assistant. Analyze this recording and return ONLY a JSON object:
                {
                  "summary": "3-sentence executive summary",
                  "tasks": ["Task 1", "Task 2"],
                  "events": [{"title": "Event Name", "time": "Date/Time"}]
                }
                """
                
                response = model.generate_content([prompt, audio_file])
                
                # Cleaning and Parsing
                clean_json = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(clean_json)

                # --- 6. DASHBOARD VIEW ---
                st.divider()
                st.markdown(f'<div class="report-card"><div class="card-title">📝 Summary</div><p>{data["summary"]}</p></div>', unsafe_allow_html=True)

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown('<div class="report-card"><div class="card-title">✅ Reminders</div>', unsafe_allow_html=True)
                    for task in data.get('tasks', []):
                        url = f"shortcuts://run-shortcut?name=AddReminder&input=text&text={urllib.parse.quote(task)}"
                        st.markdown(f'<div class="task-box"><span>{task}</span><a href="{url}" class="shortcut-btn">➕</a></div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                with col2:
                    st.markdown('<div class="report-card"><div class="card-title">📅 Calendar</div>', unsafe_allow_html=True)
                    for event in data.get('events', []):
                        e_str = f"{event['title']} at {event['time']}"
                        url = f"shortcuts://run-shortcut?name=AddCalendar&input=text&text={urllib.parse.quote(e_str)}"
                        st.markdown(f'<div class="event-box"><span>{event["title"]}<br><small>{event["time"]}</small></span><a href="{url}" class="shortcut-btn">➕</a></div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error: {e}")
                st.write("Raw Output from AI:")
                st.write(response.text)
            
            finally:
                # Clean up local file
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

st.markdown("<p style='text-align: center; font-size: 0.8em; color: #999; margin-top: 50px;'>Woodland PCA Intelligence Dashboard</p>", unsafe_allow_html=True)
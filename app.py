import streamlit as st
from streamlit_mic_recorder import mic_recorder
import google.generativeai as genai
import urllib.parse
import tempfile
import os
import json
import time
import datetime

def create_ics(title, time_str):
    now = datetime.datetime.now()
    dtstamp = now.strftime('%Y%m%dT%H%M%SZ')
    dtstart = now.strftime('%Y%m%dT%H%M%SZ')
    dtend = (now + datetime.timedelta(hours=1)).strftime('%Y%m%dT%H%M%SZ')
    
    return f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//PCA Smart Vault//EN
BEGIN:VEVENT
UID:{dtstamp}-{id(title)}@pcasmartvault.com
DTSTAMP:{dtstamp}
DTSTART:{dtstart}
DTEND:{dtend}
SUMMARY:{title}
DESCRIPTION:{time_str}
END:VEVENT
END:VCALENDAR"""

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
            # Create temp file with .webm to match typical browser mic output
            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
                tmp.write(audio_data['bytes'])
                tmp_path = tmp.name
            
            try:
                # 5. UPLOAD & WAIT FOR PROCESSING
                audio_file = genai.upload_file(path=tmp_path, mime_type="audio/webm")
                
                # Loop until file is ready (prevents 'NotFound' errors)
                while audio_file.state.name == "PROCESSING":
                    time.sleep(1)
                    audio_file = genai.get_file(audio_file.name)
                    
                if audio_file.state.name == "FAILED":
                    raise ValueError("Google Gemini failed to process the audio file. Please try recording again.")

                # Force Structured Output to prevent parsing hallucinations
                model = genai.GenerativeModel('gemini-1.5-flash-latest', generation_config={"response_mime_type": "application/json"})
                
                prompt = """
                You are a PCA/CCA assistant. Analyze this recording and return ONLY a JSON object:
                {
                  "summary": "3-sentence executive summary",
                  "tasks": ["Task 1", "Task 2"],
                  "events": [{"title": "Event Name", "time": "Date/Time"}]
                }
                """
                
                response = model.generate_content([prompt, audio_file])
                
                # Cleaning and strict parsing with fallback
                try:
                    clean_json = response.text.replace("```json", "").replace("```", "").strip()
                    data = json.loads(clean_json)
                except json.JSONDecodeError as e:
                    st.error("⚠️ AI returned malformed data. Attempted parsing failed.")
                    st.write("Raw Transcribed Details (unformatted):", response.text)
                    raise e # Bubble up to the main exception block to stop dashboard rendering

                # --- 6. DASHBOARD VIEW ---
                st.divider()
                st.markdown(f'<div class="report-card"><div class="card-title">📝 Summary</div><p>{data.get("summary", "No summary provided.")}</p></div>', unsafe_allow_html=True)

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown('<div class="report-card"><div class="card-title">✅ Reminders</div>', unsafe_allow_html=True)
                    for task in data.get('tasks', []):
                        # Ensure tasks are strings
                        task_str = str(task)
                        url = f"shortcuts://run-shortcut?name=AddReminder&input=text&text={urllib.parse.quote(task_str)}"
                        st.markdown(f'<div class="task-box"><span>{task}</span><a href="{url}" class="shortcut-btn">➕</a></div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                with col2:
                    st.markdown('<div class="report-card"><div class="card-title">📅 Calendar</div>', unsafe_allow_html=True)
                    events_list = data.get('events', [])
                    if events_list:
                        for i, event in enumerate(events_list):
                            # Ensure event format is a dictionary with title and time
                            if isinstance(event, dict) and 'title' in event and 'time' in event:
                                e_str = str(f"{event['title']} at {event['time']}")
                                url = f"shortcuts://run-shortcut?name=AddCalendar&input=text&text={urllib.parse.quote(e_str)}"
                                st.markdown(f'<div class="event-box"><span>{event["title"]}<br><small>{event["time"]}</small></span><a href="{url}" class="shortcut-btn" title="iOS Native">🍎 iOS</a></div>', unsafe_allow_html=True)
                                
                                # Cross-platform fallback ICS
                                ics_data = create_ics(event['title'], event['time'])
                                st.download_button(label="📥 Download .ics (Android/PC)", data=ics_data, file_name=f"event_{i}.ics", mime="text/calendar", key=f"dl_ics_{i}")
                    else:
                        st.write("No events scheduled from this recording.")
                    st.markdown('</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error Processing Request: {e}")
                st.info("Ensure your API Key is correct and the audio recording was successful.")
                try:
                    st.write("Raw Output from AI:", response.text)
                except:
                    pass
            
            finally:
                # Clean up local file
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

st.markdown("<p style='text-align: center; font-size: 0.8em; color: #999; margin-top: 50px;'>Woodland PCA Intelligence Dashboard</p>", unsafe_allow_html=True)
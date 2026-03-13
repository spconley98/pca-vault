import streamlit as st
from streamlit_mic_recorder import mic_recorder
import google.generativeai as genai
import urllib.parse
import tempfile
import os
import json
import time
import datetime
import base64

def img_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()
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
st.set_page_config(page_title="PCA Smart Vault", page_icon="🌳", layout="centered")

# Custom CSS for the "Vibe Coding" Premium Dashboard look
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Outfit', sans-serif;
        background-color: #f7f9fc;
    }
    
    .hero-container {
        position: relative;
        width: 100%;
        height: 300px;
        border-radius: 20px;
        overflow: hidden;
        margin-bottom: 30px;
        box-shadow: 0 12px 24px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        justify-content: center;
        background-position: center;
        background-size: cover;
    }
    
    .hero-overlay {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background: linear-gradient(135deg, rgba(27,94,32,0.8) 0%, rgba(0,0,0,0.2) 100%);
        z-index: 1;
    }
    
    .hero-content {
        position: relative;
        z-index: 2;
        text-align: center;
        color: white;
        text-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    
    .hero-title {
        font-size: 3.5rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -1px;
    }
    
    .hero-subtitle {
        font-size: 1.2rem;
        font-weight: 300;
        opacity: 0.9;
        margin-top: 5px;
    }

    .report-card { 
        background-color: #ffffff; 
        border-radius: 20px; 
        padding: 30px; 
        margin-bottom: 25px; 
        border: 1px solid rgba(0,0,0,0.04); 
        box-shadow: 0 8px 32px rgba(0,0,0,0.06); 
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .card-title { 
        font-size: 1.4em; 
        font-weight: 600; 
        color: #1b5e20; 
        margin-bottom: 20px; 
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .task-box { 
        background-color: #f1f8e9; 
        padding: 16px 20px; 
        border-radius: 12px; 
        margin-bottom: 12px; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        border-left: 5px solid #4caf50; 
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .task-box:hover, .event-box:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.08);
    }

    .event-box { 
        background-color: #e3f2fd; 
        padding: 16px 20px; 
        border-radius: 12px; 
        margin-bottom: 12px; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        border-left: 5px solid #1e88e5; 
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .shortcut-btn { 
        background-color: white; 
        padding: 8px 16px; 
        border-radius: 20px; 
        text-decoration: none !important; 
        color: #333 !important; 
        font-size: 0.85em; 
        font-weight: 600; 
        border: 1px solid #e0e0e0; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        transition: all 0.2s ease;
        white-space: nowrap;
    }
    
    .shortcut-btn:hover {
        background-color: #f5f5f5;
        border-color: #ccc;
    }
    
    p { line-height: 1.6; color: #444; font-size: 1.05rem; }
    
</style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    API_KEY = st.text_input("Gemini API Key", type="password")
    if API_KEY:
        genai.configure(api_key=API_KEY)

# --- 3. DYNAMIC HERO HEADER ---
if os.path.exists("orchard.jpg"):
    img_b64 = img_to_base64("orchard.jpg")
    hero_html = f"""
    <div class="hero-container" style="background-image: url('data:image/jpeg;base64,{img_b64}');">
        <div class="hero-overlay"></div>
        <div class="hero-content">
            <h1 class="hero-title">PCA Smart Vault</h1>
            <p class="hero-subtitle">Woodland Agricultural Intelligence</p>
        </div>
    </div>
    """
    st.markdown(hero_html, unsafe_allow_html=True)
else:
    st.markdown("<h1 class='hero-title' style='text-align: center; color: #1b5e20; padding: 40px 0;'>🌳 PCA Smart Vault</h1>", unsafe_allow_html=True)

# --- Initialize Session State ---
if 'dashboard_data' not in st.session_state:
    st.session_state.dashboard_data = None

# --- 4. THE RECORDER ---
if not API_KEY:
    st.warning("Please enter your Gemini API Key in the sidebar to start.")
else:
    st.markdown("<h3 style='font-weight: 400; color: #555; margin-bottom: 20px;'>Intelligence Upload</h3>", unsafe_allow_html=True)
    audio_data = mic_recorder(start_prompt="⏺️ Record Field Note", stop_prompt="⏹️ Analyze & Synthesize", key='recorder')

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
                    parsed_data = json.loads(clean_json)
                    st.session_state.dashboard_data = parsed_data # Save to persistent session state
                except json.JSONDecodeError as e:
                    st.error("⚠️ AI returned malformed data. Attempted parsing failed.")
                    st.write("Raw Transcribed Details (unformatted):", response.text)
                    raise e # Bubble up to the main exception block to stop dashboard rendering

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

# --- 6. DASHBOARD VIEW (Persisted via Session State) ---
if st.session_state.dashboard_data:
    data = st.session_state.dashboard_data
    
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

st.markdown("<p style='text-align: center; font-size: 0.85em; color: #a0aabf; margin-top: 60px; font-weight: 300;'>Powered by Gemini 1.5 Flash • Vibe Coded UI</p>", unsafe_allow_html=True)
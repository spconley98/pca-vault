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
import uuid

# --- 1. UTILITY FUNCTIONS ---
def img_to_base64(image_path):
    """Converts local image to base64 for the Hero Header background."""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

def create_ics(title, time_str, summary=""):
    """Generates a cross-platform calendar file (.ics)."""
    now = datetime.datetime.now()
    dtstamp = now.strftime('%Y%m%dT%H%M%SZ')
    # Defaulting to tomorrow at 10 AM for the event start
    dtstart = (now + datetime.timedelta(days=1)).strftime('%Y%m%dT100000Z')
    dtend = (now + datetime.timedelta(days=1, hours=1)).strftime('%Y%m%dT110000Z')
    
    return f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//PCA Smart Vault//EN
BEGIN:VEVENT
UID:{uuid.uuid4()}
DTSTAMP:{dtstamp}
DTSTART:{dtstart}
DTEND:{dtend}
SUMMARY:{title}
DESCRIPTION:{summary} (Original Time Mentioned: {time_str})
END:VEVENT
END:VCALENDAR"""

# --- 2. PAGE CONFIG & STYLING ---
st.set_page_config(page_title="PCA Smart Vault", page_icon="🌳", layout="centered")

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
        height: 250px;
        border-radius: 20px;
        overflow: hidden;
        margin-bottom: 30px;
        box-shadow: 0 12px 24px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        justify-content: center;
        background-size: cover;
        background-position: center;
    }
    
    .hero-overlay {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background: linear-gradient(135deg, rgba(27,94,32,0.85) 0%, rgba(0,0,0,0.3) 100%);
        z-index: 1;
    }
    
    .hero-content {
        position: relative;
        z-index: 2;
        text-align: center;
        color: white;
    }
    
    .hero-title { font-size: 3rem; font-weight: 700; margin: 0; }
    .hero-subtitle { font-size: 1.1rem; font-weight: 300; opacity: 0.9; }

    .report-card { 
        background-color: #ffffff; 
        border-radius: 20px; 
        padding: 25px; 
        margin-bottom: 20px; 
        border: 1px solid rgba(0,0,0,0.05); 
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    
    .card-title { font-size: 1.3em; font-weight: 600; color: #1b5e20; margin-bottom: 15px; }
    
    .task-box { 
        background-color: #f1f8e9; 
        padding: 15px; 
        border-radius: 12px; 
        margin-bottom: 10px; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        border-left: 5px solid #4caf50; 
    }

    .event-box { 
        background-color: #e3f2fd; 
        padding: 15px; 
        border-radius: 12px; 
        margin-bottom: 10px; 
        display: flex; 
        justify-content: space-between; 
        align-items: center; 
        border-left: 5px solid #1e88e5; 
    }
    
    .shortcut-btn { 
        background-color: white; 
        padding: 6px 12px; 
        border-radius: 15px; 
        text-decoration: none !important; 
        color: #333 !important; 
        font-size: 0.8em; 
        font-weight: 600; 
        border: 1px solid #ddd;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    API_KEY = st.text_input("Gemini API Key", type="password")
    if API_KEY:
        genai.configure(api_key=API_KEY)
        with st.expander("🛠️ Debug: Available Models"):
            try:
                models = [m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
                st.write(models)
            except Exception as e:
                st.write("Error fetching models.")

# --- 4. HERO HEADER ---
if os.path.exists("orchard.jpg"):
    img_b64 = img_to_base64("orchard.jpg")
    st.markdown(f"""
    <div class="hero-container" style="background-image: url('data:image/jpeg;base64,{img_b64}');">
        <div class="hero-overlay"></div>
        <div class="hero-content">
            <h1 class="hero-title">PCA Smart Vault</h1>
            <p class="hero-subtitle">Woodland Agricultural Intelligence</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("<h1 style='text-align: center; color: #1b5e20;'>🌳 PCA Smart Vault</h1>", unsafe_allow_html=True)

# Initialize Session State for data persistence
if 'dashboard_data' not in st.session_state:
    st.session_state.dashboard_data = None

# --- 5. THE RECORDER ---
if not API_KEY:
    st.warning("Please enter your Gemini API Key in the sidebar to start.")
else:
    st.write("Record your scouting notes or field observations:")
    audio_data = mic_recorder(start_prompt="⏺️ Record Field Note", stop_prompt="⏹️ Analyze & Synthesize", key='recorder')

    if audio_data:
        st.audio(audio_data['bytes'])
        
        with st.spinner("Gemini is analyzing the audio..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
                tmp.write(audio_data['bytes'])
                tmp_path = tmp.name
            
            try:
                # 5. UPLOAD & WAIT FOR PROCESSING
                audio_file = genai.upload_file(path=tmp_path, mime_type="audio/webm")
                
                while audio_file.state.name == "PROCESSING":
                    time.sleep(1)
                    audio_file = genai.get_file(audio_file.name)
                
                # FIX: Using 'gemini-2.5-flash' based on the API key's available models
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                prompt = """
                You are a senior PCA/CCA assistant. Analyze this recording and return ONLY a JSON object:
                {
                  "summary": "3-sentence executive summary focusing on crop status and treatment recommendations.",
                  "tasks": ["Specific action item for grower or crew"],
                  "events": [{"title": "Event Name", "time": "Date/Time mentioned"}]
                }
                """
                
                response = model.generate_content([prompt, audio_file])
                
                # Cleaning and Parsing
                clean_json = response.text.replace("```json", "").replace("```", "").strip()
                st.session_state.dashboard_data = json.loads(clean_json)

            except Exception as e:
                st.error(f"Analysis Error: {e}")
                if 'response' in locals():
                    st.write("AI Debug Info:")
                    st.code(response.text)
                else:
                    st.info("Technical Tip: Ensure your 'google-generativeai' library is updated.")
            
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

# --- 6. DASHBOARD VIEW ---
if st.session_state.dashboard_data:
    data = st.session_state.dashboard_data
    
    st.divider()
    st.markdown(f'<div class="report-card"><div class="card-title">📝 Summary</div><p>{data.get("summary")}</p></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="report-card"><div class="card-title">✅ Tasks</div>', unsafe_allow_html=True)
        for task in data.get('tasks', []):
            url = f"shortcuts://run-shortcut?name=AddReminder&input=text&text={urllib.parse.quote(str(task))}"
            st.markdown(f'<div class="task-box"><span>{task}</span><a href="{url}" class="shortcut-btn">➕</a></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="report-card"><div class="card-title">📅 Calendar</div>', unsafe_allow_html=True)
        for i, event in enumerate(data.get('events', [])):
            e_str = f"{event['title']} at {event['time']}"
            url = f"shortcuts://run-shortcut?name=AddCalendar&input=text&text={urllib.parse.quote(e_str)}"
            ics_data = create_ics(event['title'], event['time'], data.get("summary", ""))
            
            st.markdown(f'<div class="event-box"><span>{event["title"]}<br><small>{event["time"]}</small></span><a href="{url}" class="shortcut-btn" style="margin-right:5px;">🍎 iOS</a></div>', unsafe_allow_html=True)
            st.download_button(label="📥 .ics (Android/PC)", data=ics_data, file_name=f"event_{i}.ics", mime="text/calendar", key=f"dl_{uuid.uuid4()}")
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<p style='text-align: center; font-size: 0.8em; color: #a0aabf; margin-top: 50px;'>Woodland PCA Dashboard • Powered by Gemini 1.5 Flash</p>", unsafe_allow_html=True)
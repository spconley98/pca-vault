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
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

def create_ics(title, time_str, summary=""):
    now = datetime.datetime.now()
    dtstamp = now.strftime('%Y%m%dT%H%M%SZ')
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
# Shifting from "centered" to "wide" for the Otter 3-pane architecture
st.set_page_config(page_title="PCA Smart Vault", page_icon="🌳", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Outfit', sans-serif;
        background-color: #ffffff;
    }
    
    /* Otter-like clean layout adjustments */
    .stApp {
        background-color: #ffffff;
    }
    
    .main-header {
        font-size: 2.2rem;
        font-weight: 600;
        color: #1e1e1e;
        margin-bottom: 5px;
    }
    
    .meta-text {
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 30px;
        display: flex;
        gap: 15px;
        align-items: center;
    }
    
    .section-header {
        font-size: 1.2rem;
        font-weight: 600;
        color: #333;
        margin-top: 30px;
        margin-bottom: 15px;
        border-bottom: 1px solid #eee;
        padding-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .overview-text {
        font-size: 1.05rem;
        line-height: 1.6;
        color: #444;
    }
    
    .outline-list {
        padding-left: 20px;
    }
    
    .outline-list li {
        margin-bottom: 10px;
        color: #333;
        font-size: 1.05rem;
    }

    .ai-chat-header {
        font-weight: 600;
        margin-bottom: 20px;
        font-size: 1.1rem;
        border-bottom: 1px solid #eee;
        padding-bottom: 10px;
    }
    
    /* Sidebar styling to mimic navigation */
    .css-1544g2n {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. SECRETS & SIDEBAR ---
# Silently load the API Key from Streamlit Secrets or local Environment Variables
API_KEY = None
try:
    API_KEY = st.secrets.get("GEMINI_API_KEY")
except:
    pass

if not API_KEY:
    API_KEY = os.environ.get("GEMINI_API_KEY")

with st.sidebar:
    st.markdown("<h2 style='font-weight: 700; color: #1b5e20;'>🌳 PCA Vault</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Navigation style to mimic Otter
    st.button("🏠 Home", use_container_width=True)
    st.button("🤖 AI Chat", use_container_width=True)
    st.button("🔗 Integrations", use_container_width=True)
    
    st.markdown("---")
    st.markdown("**📁 Folders**")
    st.button("🌱 Spring Scouting", use_container_width=True)
    st.button("💧 Nutrient Reports", use_container_width=True)

    # Fallback to manual input if no secret is found
    if not API_KEY:
        st.warning("Key not found in `.streamlit/secrets.toml`.")
        API_KEY = st.text_input("Gemini API Key", type="password")
    
    if API_KEY:
        genai.configure(api_key=API_KEY)

# Initialize Session States
if 'dashboard_data' not in st.session_state:
    st.session_state.dashboard_data = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = [{"role": "assistant", "content": "Ask me anything about your field notes..."}]

# --- 4. MAIN LAYOUT (Wide Split) ---
# If no data yet, show a clean, centered recorder interface
if not st.session_state.dashboard_data:
    st.markdown("<div style='max-width: 600px; margin: 10vh auto; text-align: center;'>", unsafe_allow_html=True)
    st.markdown("<h1 class='main-header'>Record New Field Note</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #666; margin-bottom: 40px;'>Capture your scouting observations for automated synthesis.</p>", unsafe_allow_html=True)
    
    if not API_KEY:
        st.error("Please configure your Gemini API Key via Streamlit Secrets or the sidebar.")
    else:
        audio_data = mic_recorder(start_prompt="⏺️ Start Recording", stop_prompt="⏹️ Analyze Audio", key='recorder')

        if audio_data:
            with st.spinner("Synthesizing field data..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
                    tmp.write(audio_data['bytes'])
                    tmp_path = tmp.name
                
                try:
                    audio_file = genai.upload_file(path=tmp_path, mime_type="audio/webm")
                    
                    while audio_file.state.name == "PROCESSING":
                        time.sleep(1)
                        audio_file = genai.get_file(audio_file.name)
                    
                    # Target advanced model
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    
                    # Upgraded Prompt to align with the Otter.ai data hierarchy
                    prompt = """
                    You are a senior PCA/CCA assistant. Analyze this recording and return ONLY a JSON object:
                    {
                      "title": "A short, professional title for the recording",
                      "overview": "A flowing paragraph summarizing the core discussion, crop status, and any observations.",
                      "action_items": ["Specific action 1", "Specific action 2"],
                      "outline": [
                         {"heading": "Main point 1", "details": ["Point 1 detail A", "Point 1 detail B"]},
                         {"heading": "Main point 2", "details": ["Point 2 detail A"]}
                      ]
                    }
                    """
                    
                    response = model.generate_content([prompt, audio_file])
                    clean_json = response.text.replace("```json", "").replace("```", "").strip()
                    st.session_state.dashboard_data = json.loads(clean_json)
                    st.rerun()

                except Exception as e:
                    st.error(f"Analysis Error: {e}")
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
    st.markdown("</div>", unsafe_allow_html=True)

else:
    # --- OTTER DASHBOARD VIEW ---
    # Establishing the 75 / 25 column split for the UI
    col_main, col_chat = st.columns([3, 1], gap="large")
    data = st.session_state.dashboard_data
    
    with col_main:
        # Title & Context Meta
        st.markdown(f"<h1 class='main-header'>{data.get('title', 'Field Observation')}</h1>", unsafe_allow_html=True)
        date_str = datetime.datetime.now().strftime("%b %d at %I:%M %p")
        st.markdown(f"""
        <div class='meta-text'>
            <span>👤 Sean C</span>
            <span>📅 {date_str}</span>
            <span>⏱️ Synthesized</span>
            <span style='color: #1b5e20; cursor: pointer;'>📋 Copy Summary</span>
        </div>
        """, unsafe_allow_html=True)
        
        tab_summary, tab_transcript = st.tabs(["Summary", "Transcript"])
        
        with tab_summary:
            # Overview block
            st.markdown("<div class='section-header'>📝 Overview</div>", unsafe_allow_html=True)
            st.markdown(f"<p class='overview-text'>{data.get('overview', '')}</p>", unsafe_allow_html=True)
            
            # Action Items mapped as native Checkboxes
            st.markdown("<div class='section-header'>☑️ Action Items</div>", unsafe_allow_html=True)
            for i, task in enumerate(data.get('action_items', [])):
                st.checkbox(task, key=f"task_{i}")
                
            # Deep Outline mapping
            st.markdown("<div class='section-header'>📋 Outline</div>", unsafe_allow_html=True)
            for item in data.get('outline', []):
                st.markdown(f"**{item.get('heading', '')}**")
                for detail in item.get('details', []):
                    st.markdown(f"-<span style='margin-left:5px; color:#444;'>{detail}</span>", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
        
        with tab_transcript:
            st.info("Transcript view is currently hidden. Configure the LLM to output word-for-word transcript blocks to populate this tab.")

    with col_chat:
        st.markdown("<div class='ai-chat-header'>💬 AI Chat</div>", unsafe_allow_html=True)
        
        # Display chat history iteratively
        chat_container = st.container(height=500)
        with chat_container:
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.write(message["content"])
        
        # Quick interactive demo prompts under the chat
        st.button("What treatments run best here?", key="q1", use_container_width=True)
        st.button("Extract all compound names.", key="q2", use_container_width=True)
        
        # Chat text input behavior
        if prompt := st.chat_input("Ask PCA assistant about your notes..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with chat_container:
                with st.chat_message("user"):
                    st.write(prompt)
                with st.chat_message("assistant"):
                    st.write("This is a simulated AI response. Hook this up to `model.generate_content()` to query against the dashboard context!")
            st.session_state.chat_history.append({"role": "assistant", "content": "This is a simulated AI response. Hook this up to `model.generate_content()` to query against the dashboard context!"})
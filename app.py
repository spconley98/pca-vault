import streamlit as st
from audiorecorder import audiorecorder
import google.generativeai as genai
import urllib.parse
import tempfile
import os
import json # New tool for processing structured data

st.set_page_config(page_title="PCA Smart Vault", page_icon="🌳", layout="wide") # Use wide layout for dashboard feel

# --- 1. SETUP ---
# You'll enter this key once the app is running
API_KEY = st.sidebar.text_input("Gemini API Key", type="password")
if API_KEY:
    genai.configure(api_key=API_KEY)

# --- 2. MAIN HEADER (WITH ALMOND ORCHARD IMAGE) ---
# Add the high-definition orchard image
st.markdown("<h1 style='text-align: center; color: white; background-color: rgba(0,0,0,0.5); padding: 10px; border-radius: 10px;'>🌳 PCA Smart Vault Dashboard</h1>", unsafe_allow_html=True)
st.image("path/to/your/almond_orchard.jpg", caption="Your Almond Orchard Analysis Hub", use_column_width=True) # <<< ADD YOUR ORCHARD PHOTO PATH HERE

# Introduce custom CSS to style the conversation 'cards'
st.markdown("""
<style>
    .report-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .card-title {
        font-size: 1.5em;
        font-weight: bold;
        color: #1f77b4;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .task-item, .event-item {
        margin-left: 20px;
        font-weight: 500;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .shortcut-icon {
        color: #1f77b4;
        text-decoration: none;
        margin-left: 10px;
        font-size: 1.2em;
    }
    .audio-player {
        margin-top: 20px;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. THE RECORDER ---
st.write("Start a new call or scouting note:")
audio = audiorecorder("⏺️ Start Call Recording", "Stop & Generate Insights", key="recorder_main")

if len(audio) > 0:
    # Display the player immediately
    st.markdown("<div class='audio-player'>", unsafe_allow_html=True)
    st.audio(audio.export().read())
    st.markdown("</div>", unsafe_allow_html=True)
    
    with st.spinner("Analyzing call and generating custom insights..."):
        # Save audio to a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            audio.export(tmp.name, format="mp3")
            
            # Send to Gemini
            audio_file = genai.upload_file(path=tmp.name)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # 4. THE PROMPT (Revised for structured JSON output)
            # This is key for the Otter look. We demand JSON.
            prompt = """
            Analyze this phone conversation and output a structured JSON object with the following schema:
            
            {
              "summary": "A 3-sentence summary of the conversation.",
              "tasks": [
                {
                  "description": "Short description of the task.",
                  "shortcut_url": "Encoded URL for the Apple Shortcut: shortcuts://run-shortcut?name=AddReminder&input=text&text=[encoded_description]"
                },
                ...
              ],
              "events": [
                {
                  "title": "Title of the event.",
                  "date": "Date and Time of the event.",
                  "shortcut_url": "Encoded URL for the Apple Shortcut: shortcuts://run-shortcut?name=AddCalendar&input=text&text=[encoded_title] at [encoded_date]"
                },
                ...
              ]
            }
            """
            
            response = model.generate_content([prompt, audio_file])
            raw_text = response.text
            st.markdown("### Processed Insights (Draft)")
            st.markdown(raw_text) # Show raw text for validation

            try:
                # Parse the JSON output
                # Use json.loads to clean up common formatting issues from Gemini
                data = json.loads(raw_text.strip('` \n'))
                
                # --- 5. VISUALIZING THE "CONVERSATION DASHBOARD" ---
                st.markdown("<h2 style='text-align: center; color: #1f77b4;'>Conversation Dashboard</h2>", unsafe_allow_html=True)
                
                # Card 1: Summary (Wide card)
                st.markdown(f"""
                <div class='report-card'>
                    <div class='card-title'>📝 Conversation Summary</div>
                    <p>{data['summary']}</p>
                </div>
                """, unsafe_allow_html=True)

                # Card 2 & 3: Tasks and Events (Two-column layout)
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                    <div class='report-card'>
                        <div class='card-title'>🗓️ Key Action Items</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if not data['tasks']:
                        st.markdown("<p>No tasks identified.</p>", unsafe_allow_html=True)
                    for task in data['tasks']:
                        st.markdown(f"""
                        <div class='task-item'>
                            <span>• {task['description']}</span>
                            <a href='{task['shortcut_url']}' class='shortcut-icon' target='_self'>🗓️+</a>
                        </div>
                        """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                    <div class='report-card'>
                        <div class='card-title'>📅 Upcoming Events</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if not data['events']:
                        st.markdown("<p>No events identified.</p>", unsafe_allow_html=True)
                    for event in data['events']:
                        st.markdown(f"""
                        <div class='event-item'>
                            <span>• {event['title']} ({event['date']})</span>
                            <a href='{event['shortcut_url']}' class='shortcut-icon' target='_self'>📅+</a>
                        </div>
                        """, unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Failed to process conversation dashboard: {e}. Raw analysis is above.")
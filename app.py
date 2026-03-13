import streamlit as st
from audiorecorder import audiorecorder
import google.generativeai as genai
import urllib.parse
import tempfile
import os

st.set_page_config(page_title="PCA Smart Vault", page_icon="🌳")
st.title("🌳 PCA Smart Vault")

# --- 1. SETUP ---
# You'll enter this key once the app is running
API_KEY = st.sidebar.text_input("Gemini API Key", type="password")
if API_KEY:
    genai.configure(api_key=API_KEY)

# --- 2. THE RECORDER ---
audio = audiorecorder("⏺️ Start Call Recording", "Stop & Extract Tasks")

if len(audio) > 0:
    with st.spinner("Analyzing call for tasks and events..."):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            audio.export(tmp.name, format="mp3")
            
            # Send to Gemini
            audio_file = genai.upload_file(path=tmp.name)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = """
            Listen to this call. Provide:
            1. A 3-sentence summary.
            2. Any TASK (e.g. "Spray the north block"). Format: TASK: [Description]
            3. Any EVENT (e.g. "Grower meeting"). Format: EVENT: [Title] | DATE: [Date/Time]
            """
            
            response = model.generate_content([prompt, audio_file])
            text = response.text
            st.markdown(text)

            # --- 3. APPLE BUTTONS ---
            for line in text.split('\n'):
                if "TASK:" in line:
                    task = line.split("TASK:")[1].strip()
                    url = f"shortcuts://run-shortcut?name=AddReminder&input=text&text={urllib.parse.quote(task)}"
                    st.link_button(f"🗓️ Add Reminder: {task[:25]}...", url)

                if "EVENT:" in line:
                    event = line.split("|")[0].replace("EVENT:", "").strip()
                    url = f"shortcuts://run-shortcut?name=AddCalendar&input=text&text={urllib.parse.quote(event)}"
                    st.link_button(f"📅 Add Calendar: {event[:25]}...", url)
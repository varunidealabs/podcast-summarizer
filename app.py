import streamlit as st
import tempfile
import os
from pytube import YouTube
import requests
from gtts import gTTS
import shutil
import traceback
from azure_openai import transcribe_audio, summarize_text

# Audio extraction from YouTube
from yt_dlp import YoutubeDL
import traceback

def extract_audio_from_youtube(url):
    try:
        # Remove unnecessary URL parameters
        url = url.split('&')[0]  

        temp_dir = tempfile.mkdtemp()
        audio_file_path = os.path.join(temp_dir, '%(title)s.%(ext)s')

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': audio_file_path,
            'quiet': True,
            'no_warnings': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            downloaded_file = ydl.prepare_filename(info_dict).rsplit('.', 1)[0] + ".mp3"

        if os.path.exists(downloaded_file):
            return downloaded_file
        else:
            st.error("Audio extraction failed. File not found.")
            return None
    except Exception as e:
        st.error(f"Error extracting audio: {str(e)}")
        st.error(traceback.format_exc())
        return None


# Text-to-Speech using gTTS
def text_to_speech(text):
    try:
        with st.spinner("Converting summary to audio..."):
            audio_path = tempfile.mktemp(suffix=".mp3")
            tts = gTTS(text=text, lang="en", slow=False)
            tts.save(audio_path)
            return audio_path
    except Exception as e:
        st.error(f"Error converting summary to audio: {str(e)}")
        st.error(traceback.format_exc())
        return None

# Streamlit Interface
st.title("🎧 Podcast Summarizer")

option = st.radio("Choose Input Type:", ["Upload Audio File", "YouTube URL"])

audio_file_path = None

if option == "Upload Audio File":
    uploaded_file = st.file_uploader("Upload Podcast Audio", type=["mp3", "wav"])
    if uploaded_file:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_file.write(uploaded_file.getvalue())
        audio_file_path = temp_file.name


elif option == "YouTube URL":
    youtube_url = st.text_input("Enter YouTube URL")
    if st.button("Extract Audio") and youtube_url:
        audio_file_path = extract_audio_from_youtube(youtube_url)

if audio_file_path:
    try:
        with st.spinner("Transcribing audio..."):
            transcript = transcribe_audio(audio_file_path)
        with st.spinner("Summarizing transcript..."):
            summary = summarize_text(transcript)
        
        st.success("Summary generated!")
        st.subheader("Podcast Summary")
        st.write(summary)

        audio_summary_path = text_to_speech(summary)

        if audio_summary_path:
            audio_file = open(audio_summary_path, "rb")
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format="audio/mp3")
            st.download_button("Download Summary Audio", audio_bytes, file_name="summary.mp3", mime="audio/mp3")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.error(traceback.format_exc())

    finally:
        # Cleanup
        if audio_file_path and os.path.exists(audio_file_path):
            os.remove(audio_file_path)

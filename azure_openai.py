import os
from dotenv import load_dotenv
import requests
import streamlit as st

ENDPOINT = st.secrets["AZURE_OPENAI_ENDPOINT"]
API_KEY = st.secrets["AZURE_OPENAI_API_KEY"]
DEPLOYMENT = st.secrets["AZURE_OPENAI_DEPLOYMENT"]
API_VERSION = st.secrets["AZURE_OPENAI_API_VERSION"]


headers = {
    "Content-Type": "application/json",
    "api-key": API_KEY
}

# GPT-4o Summarization
def summarize_text(transcript):
    url = f"{ENDPOINT}openai/deployments/{DEPLOYMENT}/chat/completions?api-version={API_VERSION}"
    
    payload = {
        "messages": [
            {"role": "system", "content": "Summarize the following podcast transcript into key points suitable for a 6-minute audio summary."},
            {"role": "user", "content": transcript}
        ],
        "max_tokens": 800,
        "temperature": 0.3
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    summary = response.json()["choices"][0]["message"]["content"]
    return summary

# Whisper Premium Speech-to-Text (Azure-hosted OpenAI)
def transcribe_audio(audio_file_path):
    whisper_endpoint = f"{ENDPOINT}openai/deployments/whisper/audio/transcriptions?api-version={API_VERSION}"
    
    with open(audio_file_path, "rb") as audio_file:
        files = {'file': audio_file}
        data = {'model': 'whisper'}

        response = requests.post(whisper_endpoint, headers={"api-key": API_KEY}, files=files, data=data)
        response.raise_for_status()

        transcript = response.json()["text"]
        return transcript

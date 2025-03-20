
import os
from dotenv import load_dotenv
import requests
import streamlit as st
import re
from pydub import AudioSegment

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

def detect_mood(summary_text):
    """
    Analyze the summary and classify the tone as joyful, serious, or neutral.
    """
    url = f"{ENDPOINT}openai/deployments/{DEPLOYMENT}/chat/completions?api-version={API_VERSION}"

    payload = {
        "messages": [
            {"role": "system", "content": "Analyze the tone of the following podcast summary and classify it as one of: 'joyful', 'serious', or 'neutral'."},
            {"role": "user", "content": summary_text}
        ],
        "max_tokens": 10,
        "temperature": 0.3
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    mood = response.json()["choices"][0]["message"]["content"].strip().lower()
    
    # Ensure mood is one of the expected values
    if mood not in ["joyful", "serious", "neutral"]:
        mood = "neutral"

    return mood


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
    


def format_ssml_text(text):
    """
    Convert plain text into SSML by adding pauses and formatting sentences.
    """
    # Add a 1-second pause after each sentence for natural flow
    text = re.sub(r'(\.|\?|!) ', r'\1 <break time="1s"/> ', text)

    # Add slight pauses at commas for better pacing
    text = text.replace(",", "<break time='500ms'/>")

    # Add emphasis on important words (optional)
    text = re.sub(r'\b(important|key|critical|note)\b', r'<emphasis level="strong">\1</emphasis>', text)

    return text


# Azure Text-to-Speech (TTS) 

def azure_text_to_speech(text, output_audio_path="summary.mp3"):
    tts_endpoint = f"{ENDPOINT}openai/deployments/tts/audio/speech?api-version={API_VERSION}"

    headers = {
        "Content-Type": "application/json",
        "api-key": API_KEY
    }

    # Detect mood and set expressive voice
    mood = detect_mood(text)
    if mood == "joyful":
        voice = "shimmer"
        style = "cheerful"
    elif mood == "serious":
        voice = "onyx"
        style = "serious"
    else:
        voice = "nova"
        style = "neutral"

    # Convert text to SSML
    ssml = f"""<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
        <voice name='{voice}'>
            <mstts:express-as style='{style}'>
                <prosody rate="medium">
                    {format_ssml_text(text)}
                </prosody>
            </mstts:express-as>
        </voice>
    </speak>"""

    payload = {
        "input": ssml,
        "text_type": "ssml",
        "voice": voice,
        "response_format": "mp3"
    }

    response = requests.post(tts_endpoint, headers=headers, json=payload)

    if response.status_code != 200:
        raise Exception(f"Azure TTS API Error: {response.status_code} - {response.text}")

    # Save the original audio file
    raw_audio_path = "raw_summary.mp3"
    with open(raw_audio_path, "wb") as audio_file:
        audio_file.write(response.content)

    # Trim the first 10 seconds
    audio = AudioSegment.from_file(raw_audio_path, format="mp3")
    trimmed_audio = audio[10000:]  # Trim first 10,000 milliseconds (10 sec)

    # Save the trimmed audio file
    trimmed_audio.export(output_audio_path, format="mp3")

    return output_audio_path







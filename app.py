import streamlit as st
import tempfile
import os
from pytube import YouTube
import requests
import traceback
import time
from azure_openai import transcribe_audio, summarize_text, azure_text_to_speech
import base64
from yt_dlp import YoutubeDL
import random
from components import render_key_features, render_how_it_works

# Set page configuration
st.set_page_config(
    page_title="PodSnapper - AI Podcast Summarizer",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Audio extraction from YouTube with progress indicator
def extract_audio_from_youtube(url, progress_bar=None):
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

        # Update progress
        if progress_bar:
            progress_bar.progress(0.2, text="Fetching video information...")

        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            title = info_dict.get('title', 'Unknown Title')
            
            if progress_bar:
                progress_bar.progress(0.3, text=f"Downloading audio from '{title}'...")
            
            info_dict = ydl.extract_info(url, download=True)
            downloaded_file = ydl.prepare_filename(info_dict).rsplit('.', 1)[0] + ".mp3"

            if progress_bar:
                progress_bar.progress(0.6, text="Audio extraction complete")

        if os.path.exists(downloaded_file):
            return downloaded_file, title
        else:
            st.error("Audio extraction failed. File not found.")
            return None, None
    except Exception as e:
        st.error(f"Error extracting audio: {str(e)}")
        st.error(traceback.format_exc())
        return None, None


# Force delete files (for cleanup)
def force_delete_file(file_path, retries=5):
    """
    Tries to delete the file multiple times, waiting between attempts.
    """
    for attempt in range(retries):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            break  # Exit loop if successful
        except PermissionError:
            time.sleep(1)  # Wait 1 second before retrying
    else:
        st.warning("Could not delete the file after multiple attempts. It may still be in use.")


# Create loading animation with audio waves
def show_loading_animation(message="Processing your podcast..."):
    loading_html = f"""
    <style>
        .audio-wave-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100px;
            margin: 30px auto;
            width: 80%;
        }}
        
        .audio-wave {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            height: 100%;
            width: 100%;
            max-width: 400px;
        }}
        
        .audio-wave-bar {{
            background-color: #0d6efd;
            height: 100%;
            width: 8px;
            border-radius: 4px;
            animation: audio-wave-animation 1.2s ease-in-out infinite;
            transform-origin: bottom;
        }}
        
        @keyframes audio-wave-animation {{
            0%, 100% {{
                transform: scaleY(0.3);
            }}
            50% {{
                transform: scaleY(1);
            }}
        }}
        
        .audio-wave-bar:nth-child(2) {{
            animation-delay: 0.1s;
        }}
        .audio-wave-bar:nth-child(3) {{
            animation-delay: 0.2s;
        }}
        .audio-wave-bar:nth-child(4) {{
            animation-delay: 0.3s;
        }}
        .audio-wave-bar:nth-child(5) {{
            animation-delay: 0.4s;
        }}
        .audio-wave-bar:nth-child(6) {{
            animation-delay: 0.5s;
        }}
        .audio-wave-bar:nth-child(7) {{
            animation-delay: 0.6s;
        }}
        .audio-wave-bar:nth-child(8) {{
            animation-delay: 0.7s;
        }}
        .audio-wave-bar:nth-child(9) {{
            animation-delay: 0.8s;
        }}
        .audio-wave-bar:nth-child(10) {{
            animation-delay: 0.9s;
        }}
    </style>
    
    <div class="loading-container">
        <h3 class="centered">{message}</h3>
        <div class="audio-wave-container">
            <div class="audio-wave">
                <div class="audio-wave-bar"></div>
                <div class="audio-wave-bar"></div>
                <div class="audio-wave-bar"></div>
                <div class="audio-wave-bar"></div>
                <div class="audio-wave-bar"></div>
                <div class="audio-wave-bar"></div>
                <div class="audio-wave-bar"></div>
                <div class="audio-wave-bar"></div>
                <div class="audio-wave-bar"></div>
                <div class="audio-wave-bar"></div>
            </div>
        </div>
        <p class="centered">This might take a few minutes depending on the length of your podcast</p>
    </div>
    """
    return st.markdown(loading_html, unsafe_allow_html=True)


# Get a file download link
def get_download_link(file_path, file_name="summary.mp3"):
    with open(file_path, "rb") as file:
        file_bytes = file.read()
    
    b64 = base64.b64encode(file_bytes).decode()
    # Created a proper link that will be styled by our CSS
    href = f'<a href="data:audio/mp3;base64,{b64}" download="{file_name}" class="podcast-button">Download MP3</a>'
    
    return href


# Modern upload card UI
def render_upload_card():
    # Create the card header
    st.markdown("""
    <div class="card">
        <h2 class="centered" style="font-weight: bold;">Upload your podcast</h2>
        <p class="centered" style="color: #6c757d; font-weight: bold; margin-bottom: 2rem;">Drop an audio file or paste a YouTube link to get started</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Custom CSS for file uploader
    st.markdown("""
    <style>
        [data-testid="stFileUploader"] {
            width: 100%;
        }
        
        [data-testid="stFileUploader"] section {
            border: 2px dashed #0d6efd !important;
            border-radius: 12px !important;
            padding: 30px !important;
            background-color: rgba(13, 110, 253, 0.03) !important;
            text-align: center !important;
            transition: all 0.3s ease !important;
            position: relative;
        }
        
        [data-testid="stFileUploader"] section:hover {
            background-color: rgba(13, 110, 253, 0.08) !important;
            border-color: #0a58ca !important;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(13, 110, 253, 0.15);
        }
        
        /* FIX: Change button color highlight to blue */
        [data-testid="baseButton-secondary"] {
            background-color: #0d6efd !important;
            color: white !important;
        }
        
        [data-testid="baseButton-secondary"]:hover {
            background-color: #0a58ca !important;
        }
        
        /* Make clicked button more prominent */
        .active-tab {
            background-color: #0d6efd !important;
            color: white !important;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(13, 110, 253, 0.2);
        }
        
        /* Styling for download and reset buttons */
        .button-container {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin: 20px 0;
        }
        .podcast-button {
            background-color: #0d6efd;
            color: white !important;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: 500;
            text-decoration: none;
            display: inline-block;
            text-align: center;
            min-width: 180px;
            font-size: 16px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            transition: background-color 0.2s ease;
        }
        .podcast-button:hover {
            background-color: #0a58ca;
            text-decoration: none;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state for upload mode if not exists
    if 'upload_mode' not in st.session_state:
        st.session_state.upload_mode = None
    
    # Create tabs with proper styling
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Use two columns within the center column to make buttons narrower
        btn_col1, btn_col2 = st.columns(2)
        
        with btn_col1:
            audio_tab_button = st.button("🎵 Audio File", 
                                         use_container_width=True, 
                                         key="audio_tab_button")
        
        with btn_col2:
            youtube_tab_button = st.button("🔗 YouTube Link", 
                                           use_container_width=True, 
                                           key="youtube_tab_button")
    
    # Handle button clicks to set upload mode
    if audio_tab_button:
        st.session_state.upload_mode = "audio"
    elif youtube_tab_button:
        st.session_state.upload_mode = "youtube"
    
    audio_file_path = None
    podcast_title = None
    
    # Audio File Upload Tab
    if st.session_state.upload_mode == "audio":
        # Create columns to control width
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div style="text-align: center; margin-bottom: 25px; margin-top: 10px;">
                <div style="display: inline-block; background-color: rgba(13, 110, 253, 0.1); padding: 8px 16px; border-radius: 20px;">
                    <span style="color: #0d6efd; font-weight: 500;">Upload your podcast audio</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            uploaded_file = st.file_uploader(
                "Drag and drop or choose an audio file", 
                type=["mp3", "wav", "m4a"],
                accept_multiple_files=False,
                label_visibility="collapsed"
            )
            
            if uploaded_file:
                # Show file info in a custom format
                file_size_kb = uploaded_file.size / 1024
                
                st.markdown(f"""
                <div style="background-color: #f8f9fa; border-radius: 10px; padding: 15px; margin: 15px 0; display: flex; align-items: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
                    <div style="background: #0d6efd; width: 50px; height: 50px; border-radius: 10px; display: flex; align-items: center; justify-content: center; margin-right: 15px;">
                        <span style="color: white; font-size: 24px;">🎵</span>
                    </div>
                    <div style="flex-grow: 1;">
                        <div style="font-weight: 600; color: #2c3e50; font-size: 16px; margin-bottom: 4px;">
                            {uploaded_file.name}
                        </div>
                        <div style="display: flex; align-items: center; justify-content: space-between;">
                            <div style="font-size: 13px; color: #6c757d;">{uploaded_file.type}</div>
                            <div style="font-size: 13px; color: #0d6efd; font-weight: 500;">{file_size_kb:.1f} KB</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Save uploaded file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                temp_file.write(uploaded_file.getvalue())
                audio_file_path = temp_file.name
                podcast_title = uploaded_file.name.split('.')[0]
                
                if st.button("Generate Summary", key="generate_file_summary", use_container_width=True):
                    st.session_state.audio_path = audio_file_path
                    st.session_state.podcast_title = podcast_title
                    st.session_state.start_processing = True
                    st.rerun()
    
    # YouTube Link Upload Tab
    elif st.session_state.upload_mode == "youtube":
        # Create columns to control width
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div style="text-align: center; margin-bottom: 25px; margin-top: 10px;">
                <div style="display: inline-block; background-color: rgba(13, 110, 253, 0.1); padding: 8px 16px; border-radius: 20px;">
                    <span style="color: #0d6efd; font-weight: 500;">Enter YouTube Podcast URL</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # YouTube URL input with custom styling
            st.markdown("""
            <style>
                [data-testid="stTextInput"] input {
                    border: 2px solid #0d6efd !important;
                    border-radius: 8px !important;
                    padding: 10px 15px !important;
                    font-size: 16px !important;
                    transition: all 0.3s ease !important;
                }
                [data-testid="stTextInput"] input:focus {
                    border-color: #0a58ca !important;
                    box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.2) !important;
                }
            </style>
            """, unsafe_allow_html=True)
            st.markdown("Works with any public YouTube video containing podcast-like content")
            youtube_url = st.text_input(
                "YouTube URL",
                placeholder="https://www.youtube.com/watch?v=...",
                label_visibility="collapsed"
            )
            
            if youtube_url:
                # Display YouTube thumbnail if possible
                if "youtube.com" in youtube_url or "youtu.be" in youtube_url:
                    try:
                        video_id = youtube_url.split("v=")[1].split("&")[0] if "v=" in youtube_url else youtube_url.split("/")[-1]
                        st.image(f"https://img.youtube.com/vi/{video_id}/0.jpg", use_container_width=True)
                    except:
                        pass
                
                if st.button("Generate Summary", key="generate_youtube_summary", use_container_width=True):
                    with st.spinner("Extracting audio from YouTube..."):
                        progress_bar = st.progress(0.1, text="Starting audio extraction...")
                        audio_file_path, podcast_title = extract_audio_from_youtube(youtube_url, progress_bar)
                        progress_bar.progress(1.0, text="Ready for processing")
                        
                        if audio_file_path:
                            st.session_state.audio_path = audio_file_path
                            st.session_state.podcast_title = podcast_title
                            st.session_state.start_processing = True
                            st.rerun()
    
    return audio_file_path, podcast_title


# Main App Layout
def main():
    # Header Section
    st.markdown("<h1 class='centered' style='margin-bottom: 0.5rem; font-family: \"San Francisco\", -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, Helvetica, Arial, sans-serif; font-weight: bold;'><span style='color: #0d6efd;'>Pod</span>Snapper</h1>", unsafe_allow_html=True)
    st.markdown("<p class='centered' style='font-size: 1.2rem; margin-bottom: 2rem; color: #6c757d;'>Save time by turning hour-long podcasts into minutes summaries that capture only the essential points.</p>", unsafe_allow_html=True)
    
    # Check if we should render the upload card or processing/results
    if not st.session_state.get("audio_path"):
        # Render the upload card interface
        audio_file_path, podcast_title = render_upload_card()
    
    elif st.session_state.get("start_processing") and not st.session_state.get("summary_text"):
        # Show processing animation with audio waves
        show_loading_animation("AI is processing your podcast...")
        
        # Start the actual processing
        try:
            with st.spinner("Transcribing audio..."):
                transcript = transcribe_audio(st.session_state.audio_path)
            
            with st.spinner("Summarizing transcript..."):
                summary = summarize_text(transcript)
                st.session_state.summary_text = summary
            
            with st.spinner("Converting summary to speech..."):
                audio_summary_path = azure_text_to_speech(summary)
                st.session_state.audio_summary_path = audio_summary_path
            
            st.session_state.start_processing = False
            st.rerun()
            
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.error(traceback.format_exc())
            st.session_state.start_processing = False
    
    elif st.session_state.get("summary_text") and st.session_state.get("audio_summary_path"):
        # Show results section with minimal UI
        st.markdown("<h2 class='centered' style='margin: 2rem 0;'>Your Podcast Summary</h2>", unsafe_allow_html=True)
        
        # Title only
        st.markdown(f"<h3 style='text-align: center; color: #0d6efd;'>{st.session_state.podcast_title}</h3>", unsafe_allow_html=True)
        
        # Use Streamlit's built-in audio player - this is the only player we need
        with open(st.session_state.audio_summary_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
        st.audio(audio_bytes, format="audio/mp3")
        
        # Simple button for downloading
        st.markdown(get_download_link(st.session_state.audio_summary_path, 
                    f"{st.session_state.podcast_title.replace(' ', '_')}_summary.mp3"), 
                    unsafe_allow_html=True)
        
        # Simple reset button
        if st.button("Summarize Another Podcast"):
            # Clean up files
            if st.session_state.get("audio_path"):
                force_delete_file(st.session_state.audio_path)
            if st.session_state.get("audio_summary_path"):
                force_delete_file(st.session_state.audio_summary_path)
            
            # Reset session state
            for key in ["audio_path", "podcast_title", "summary_text", "audio_summary_path", "start_processing"]:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.rerun()
    
    # Call the components to render Key Features and How It Works
    render_key_features()
    render_how_it_works()


if __name__ == "__main__":
    # Initialize session state
    if "start_processing" not in st.session_state:
        st.session_state.start_processing = False
    
    # Make sure all required state variables are initialized
    for key in ["audio_path", "podcast_title", "summary_text", "audio_summary_path"]:
        if key not in st.session_state:
            st.session_state[key] = None
    
    main()

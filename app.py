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


# Generate a random waveform SVG
def generate_waveform_svg():
    # Create random bar heights for waveform visualization
    bars = 60
    bar_width = 4
    gap = 2
    heights = [random.randint(5, 80) for _ in range(bars)]
    
    svg = f'<svg viewBox="0 0 {bars * (bar_width + gap)} 100" class="waveform-svg">'
    
    for i, height in enumerate(heights):
        x = i * (bar_width + gap)
        y = (100 - height) / 2
        svg += f'<rect x="{x}" y="{y}" width="{bar_width}" height="{height}" rx="1" fill="#91c0ff" />'
    
    svg += '</svg>'
    return svg


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


# Modern audio player UI with enhanced controls
def render_audio_player(audio_path, title="The Future of AI Technologies", duration="6:00"):
    """
    Renders a custom audio player in Streamlit
    
    Parameters:
    audio_path (str): Path to the audio file
    title (str): Title of the audio
    duration (str): Duration of the audio in format "MM:SS"
    """
    import streamlit as st
    import os
    import hashlib
    import base64
    
    # Check if file exists
    if not os.path.exists(audio_path):
        st.error(f"Audio file not found: {audio_path}")
        return
    
    try:
        # Read audio file and create base64 encoded version (crucial fix)
        with open(audio_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
            audio_b64 = base64.b64encode(audio_bytes).decode()
        
        # Create a unique ID for this audio player
        player_id = hashlib.md5(audio_path.encode()).hexdigest()[:8]
        
        # Display standard Streamlit audio player (will be hidden)
        st.audio(audio_bytes, format="audio/mp3")
        
        # Encode the title and duration to prevent JS injection
        title_safe = title.replace("'", "\\'").replace('"', '\\"')
        duration_safe = duration.replace("'", "\\'").replace('"', '\\"')
        
        # Create the HTML content
        audio_player_html = f"""
        <style>
            /* Container styling */
            .enhanced-audio-player-{player_id} {{
                width: 100%;
                max-width: 800px;
                margin: 20px auto;
                padding: 15px;
                border-radius: 8px;
                background-color: #f8f9fa;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            
            /* Header styling */
            .player-header-{player_id} {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }}
            
            /* Control buttons container */
            .player-controls-{player_id} {{
                display: flex;
                justify-content: center;
                align-items: center;
                margin-top: 15px;
                gap: 15px;
            }}
            
            /* Individual button styling */
            .control-button-{player_id} {{
                background-color: #0d6efd;
                color: white;
                border: none;
                width: 40px;
                height: 40px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                font-size: 18px;
                transition: background-color 0.2s;
            }}
            
            .control-button-{player_id}:hover {{
                background-color: #0a58ca;
            }}
            
            /* Playback speed selector */
            .speed-selector-{player_id} {{
                background-color: #e9ecef;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 5px 10px;
                cursor: pointer;
                font-size: 14px;
            }}
            
            /* Player area */
            #custom-player-{player_id} {{
                margin-top: 15px;
            }}
            
            /* Progress bar container */
            #progress-container-{player_id} {{
                width: 100%;
                height: 6px;
                background-color: #e9ecef;
                border-radius: 3px;
                cursor: pointer;
                margin-bottom: 5px;
            }}
            
            /* Progress bar */
            #progress-bar-{player_id} {{
                height: 100%;
                background-color: #0d6efd;
                border-radius: 3px;
                width: 0%;
            }}
            
            /* Time display */
            #time-display-{player_id} {{
                display: flex;
                justify-content: space-between;
                font-size: 12px;
                color: #6c757d;
            }}

            /* Hide default Streamlit audio player */
            div[data-testid="stAudio"] {{
                display: none !important;
            }}
        </style>
        
        <div class="enhanced-audio-player-{player_id}">
            <div class="player-header-{player_id}">
                <div>
                    <h3 style="margin: 0; font-size: 18px;">{title_safe}</h3>
                    <p style="margin: 5px 0 0 0; font-size: 14px; color: #6c757d;">⏱️ {duration_safe} summary</p>
                </div>
            </div>
            
            <!-- Direct embedding of audio source with base64 - CRITICAL FIX -->
            <audio id="podcast-audio-{player_id}" src="data:audio/mp3;base64,{audio_b64}" preload="metadata" style="display:none;"></audio>
            
            <div id="custom-player-{player_id}">
                <div id="progress-container-{player_id}">
                    <div id="progress-bar-{player_id}"></div>
                </div>
                <div id="time-display-{player_id}">
                    <span id="current-time-{player_id}">0:00</span>
                    <span id="duration-{player_id}">{duration_safe}</span>
                </div>
            </div>
            
            <div class="player-controls-{player_id}" style="display: flex; align-items: center; justify-content: center;">
                <button class="control-button-{player_id}" id="skip-backward-{player_id}" type="button" style="display: flex; align-items: center; justify-content: center;">⏪</button>
                <button class="control-button-{player_id}" id="play-pause-{player_id}" type="button" style="display: flex; align-items: center; justify-content: center;">▶️</button>
                <button class="control-button-{player_id}" id="skip-forward-{player_id}" type="button" style="display: flex; align-items: center; justify-content: center;">⏩</button>
                <select class="speed-selector-{player_id}" id="speed-selector-{player_id}">
                    <option value="0.5">0.5x</option>
                    <option value="0.75">0.75x</option>
                    <option value="1" selected>1x</option>
                    <option value="1.25">1.25x</option>
                    <option value="1.5">1.5x</option>
                    <option value="2">2x</option>
                </select>
            </div>
        </div>
        
        <script>
            (function() {{
                // Wait for DOM to fully load
                window.addEventListener('DOMContentLoaded', initializePlayer);
                
                // Also try with timeout as fallback
                setTimeout(initializePlayer, 1000);
                
                function initializePlayer() {{
                    const audioElement = document.getElementById('podcast-audio-{player_id}');
                    const playPauseButton = document.getElementById('play-pause-{player_id}');
                    const progressBar = document.getElementById('progress-bar-{player_id}');
                    const progressContainer = document.getElementById('progress-container-{player_id}');
                    const currentTimeDisplay = document.getElementById('current-time-{player_id}');
                    const durationDisplay = document.getElementById('duration-{player_id}');
                    const skipBackwardButton = document.getElementById('skip-backward-{player_id}');
                    const skipForwardButton = document.getElementById('skip-forward-{player_id}');
                    const speedSelector = document.getElementById('speed-selector-{player_id}');
                    
                    // Check if all elements exist
                    if (!audioElement || !playPauseButton || !progressBar || !progressContainer || 
                        !currentTimeDisplay || !skipBackwardButton || !skipForwardButton || !speedSelector) {{
                        console.error('Missing player elements');
                        return;
                    }}
                    
                    // Debug audio element
                    console.log('Audio element found:', audioElement);
                    
                    // Try to load metadata
                    audioElement.addEventListener('loadedmetadata', function() {{
                        console.log('Audio metadata loaded');
                        if (audioElement.duration && !isNaN(audioElement.duration) && audioElement.duration !== Infinity) {{
                            const min = Math.floor(audioElement.duration / 60);
                            const sec = Math.floor(audioElement.duration % 60);
                            durationDisplay.textContent = min + ':' + (sec < 10 ? '0' : '') + sec;
                        }}
                    }});
                    
                    // Error handling for audio
                    audioElement.addEventListener('error', function(e) {{
                        console.error('Audio error:', e);
                    }});
                    
                    // Update progress as audio plays
                    audioElement.addEventListener('timeupdate', function() {{
                        if (audioElement.duration && !isNaN(audioElement.duration)) {{
                            const percentage = (audioElement.currentTime / audioElement.duration) * 100;
                            progressBar.style.width = percentage + '%';
                            
                            // Update current time display
                            const minutes = Math.floor(audioElement.currentTime / 60);
                            const seconds = Math.floor(audioElement.currentTime % 60);
                            currentTimeDisplay.textContent = minutes + ':' + (seconds < 10 ? '0' : '') + seconds;
                        }}
                    }});
                    
                    // Play/pause button
                    playPauseButton.addEventListener('click', function() {{
                        if (audioElement.paused) {{
                            console.log('Attempting to play audio');
                            const playPromise = audioElement.play();
                            if (playPromise !== undefined) {{
                                playPromise
                                    .then(() => {{
                                        console.log('Audio playing successfully');
                                        playPauseButton.textContent = '⏸️';
                                    }})
                                    .catch(error => {{
                                        console.error('Error playing audio:', error);
                                    }});
                            }}
                        }} else {{
                            console.log('Pausing audio');
                            audioElement.pause();
                            playPauseButton.textContent = '▶️';
                        }}
                    }});
                    
                    // Skip forward 10 seconds
                    skipForwardButton.addEventListener('click', function() {{
                        if (!audioElement.duration) return;
                        audioElement.currentTime = Math.min(audioElement.currentTime + 10, audioElement.duration);
                    }});
                    
                    // Skip backward 10 seconds
                    skipBackwardButton.addEventListener('click', function() {{
                        audioElement.currentTime = Math.max(audioElement.currentTime - 10, 0);
                    }});
                    
                    // Playback speed selector
                    speedSelector.addEventListener('change', function() {{
                        audioElement.playbackRate = parseFloat(this.value);
                    }});
                    
                    // Progress bar click to seek
                    progressContainer.addEventListener('click', function(event) {{
                        if (!audioElement.duration) return;
                        
                        const rect = progressContainer.getBoundingClientRect();
                        const percent = (event.clientX - rect.left) / rect.width;
                        audioElement.currentTime = percent * audioElement.duration;
                    }});
                    
                    // Handle audio ending
                    audioElement.addEventListener('ended', function() {{
                        playPauseButton.textContent = '▶️';
                    }});
                }}
            }})();
        </script>
        """
        
        # Display custom player UI
        st.markdown(audio_player_html, unsafe_allow_html=True)
        
        # Display a debug message for testing
        st.markdown(f"""
        <div style="background-color: #e7f3fe; padding: 10px; border-radius: 5px; margin-top: 10px; font-size: 12px; display: none;">
            <strong>Debug:</strong> Audio player initialized with ID: {player_id}
        </div>
        """, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Error rendering audio player: {str(e)}")
        import traceback
        st.error(traceback.format_exc())


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
        
        /* Hide default text */
        [data-testid="stFileUploader"] section p {
            display: none !important;
        }
        
        /* Hide the default button and file preview */
        [data-testid="stFileUploader"] section button,
        .uploadedFile {
            display: none !important;
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
    st.markdown("<p class='centered' style='font-size: 1.2rem; margin-bottom: 2rem; color: #6c757d;'>Save time by turning hour-long podcasts into 6-minute summaries that capture only the essential points.</p>", unsafe_allow_html=True)
    
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
        # Show results with modern audio player - but don't show the text summary
        st.markdown("<h2 class='centered' style='margin: 2rem 0;'>Your Podcast Summary</h2>", unsafe_allow_html=True)
        
        # Display audio player
        render_audio_player(
            st.session_state.audio_summary_path, 
            title=st.session_state.podcast_title,
            duration="6:00"
        )
        
        # Create two buttons side by side in a container
        download_btn = get_download_link(st.session_state.audio_summary_path, 
                                        f"{st.session_state.podcast_title.replace(' ', '_')}_summary.mp3")
        
        st.markdown("""
        <style>
        .button-container {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin: 20px 0;
        }
        .podcast-button {
            background-color: #0d6efd;
            color: white !important; /* Force white text color even for links */
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: 500;
            text-decoration: none;
            display: inline-block;
            text-align: center;
            min-width: 180px;
            font-size: 16px; /* Ensure consistent font size */
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; /* Consistent font */
            transition: background-color 0.2s ease;
        }
        .podcast-button:hover {
            background-color: #0a58ca;
            text-decoration: none; /* Prevent underline on hover for links */
        }
        </style>

        <div class="button-container">
            """ + get_download_link(st.session_state.audio_summary_path, 
                                f"{st.session_state.podcast_title.replace(' ', '_')}_summary.mp3") + """
            <button class="podcast-button" id="summarize-another" onclick="summaryReset()">Summarize Another Podcast</button>
        </div>

        <script>
        function summaryReset() {
            const buttons = window.parent.document.querySelectorAll('button[kind=secondary]');
            for (const button of buttons) {
                if (button.innerText.includes('Summarize Another Podcast')) {
                    if st.session_state.get("audio_path"):
                force_delete_file(st.session_state.audio_path)
            if st.session_state.get("audio_summary_path"):
                force_delete_file(st.session_state.audio_summary_path)
            
            # Reset session state
            for key in ["audio_path", "podcast_title", "summary_text", "audio_summary_path", "start_processing"]:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.rerun()
                }
            }
        }
        </script>
        """, unsafe_allow_html=True)
        
            
    
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

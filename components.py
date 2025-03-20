import streamlit as st

def render_key_features():
    """Render the Key Features section"""
    st.markdown("---")
    st.markdown("<h2 style='text-align: center; margin: 3rem 0 2rem 0;'>Key Features</h2>", unsafe_allow_html=True)    
    
    # Row 1 of features
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="background-color: #e6f3ff; width: 60px; height: 60px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto;">
                <span style="color: #0d6efd; font-size: 24px;">⏲</span>
            </div>
            <h3 style="margin-top: 1rem;">Save Time</h3>
            <p style="color: #6c757d; font-size: 14px;">Convert hour-long podcasts into 6-minute summaries without losing key insights.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="background-color: #e6f3ff; width: 60px; height: 60px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto;">
                <span style="color: #0d6efd; font-size: 24px;">֎</span>
            </div>
            <h3 style="margin-top: 1rem;">AI-Powered</h3>
            <p style="color: #6c757d; font-size: 14px;">Utilizes GPT-4o to intelligently extract and summarize the most important content.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="background-color: #e6f3ff; width: 60px; height: 60px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto;">
                <span style="color: #0d6efd; font-size: 24px;">ϟ</span>
            </div>
            <h3 style="margin-top: 1rem;">Fast Processing</h3>
            <p style="color: #6c757d; font-size: 14px;">Get your summarized podcast in minutes, regardless of the original length.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="background-color: #e6f3ff; width: 60px; height: 60px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto;">
                <span style="color: #0d6efd; font-size: 24px;">☊</span>
            </div>
            <h3 style="margin-top: 1rem;">Easy Playback</h3>
            <p style="color: #6c757d; font-size: 14px;">Listen to summaries with adjustable playback speeds and convenient controls.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Row 2 of features
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="background-color: #e6f3ff; width: 60px; height: 60px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto;">
                <span style="color: #0d6efd; font-size: 24px;">☰</span>
            </div>
            <h3 style="margin-top: 1rem;">Key Points Focus</h3>
            <p style="color: #6c757d; font-size: 14px;">Focus only on what matters with AI that identifies the core messages.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="background-color: #e6f3ff; width: 60px; height: 60px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto;">
                <span style="color: #0d6efd; font-size: 24px;">၊၊||၊</span>
            </div>
            <h3 style="margin-top: 1rem;">Voice Preservation</h3>
            <p style="color: #6c757d; font-size: 14px;">Maintains the original speaking style and tone of the podcast hosts.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="background-color: #e6f3ff; width: 60px; height: 60px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto;">
                <span style="color: #0d6efd; font-size: 24px;">⤓</span>
            </div>
            <h3 style="margin-top: 1rem;">Download Options</h3>
            <p style="color: #6c757d; font-size: 14px;">Save summaries as MP3 files to listen offline on any device.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <div style="background-color: #e6f3ff; width: 60px; height: 60px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto;">
                <span style="color: #0d6efd; font-size: 24px;">✴</span>
            </div>
            <h3 style="margin-top: 1rem;">Perfect Fidelity</h3>
            <p style="color: #6c757d; font-size: 14px;">Enjoy high-quality audio that preserves the essence of the original content.</p>
        </div>
        """, unsafe_allow_html=True)

def render_how_it_works():
    """Render the How It Works section"""
    st.markdown("---")
    st.markdown("<h2 style='text-align: center; margin-bottom: 2rem; font-weight: bold;'>How PodSnapper Works</h2>", unsafe_allow_html=True)
    
    # Process Steps as shown in Image 2
    st.markdown("""
    <div style="display: flex; margin-bottom: 3rem;">
        <div style="width: 50px; margin-right: 20px;">
            <div style="background-color: #0d6efd; color: white; width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 20px;">01</div>
            <div style="height: 100px; width: 2px; background-color: #e0e0e0; margin-left: 24px; margin-top: 10px;"></div>
        </div>
        <div style="background-color: white; border-radius: 10px; padding: 25px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); flex-grow: 1; margin-bottom: 20px;">
            <h3>Upload Your Podcast</h3>
            <p style="color: #6c757d;">Choose an audio file or paste a YouTube link to a podcast episode you want to summarize.</p>
        </div>
    </div>
    
    <div style="display: flex; margin-bottom: 3rem;">
        <div style="width: 50px; margin-right: 20px;">
            <div style="background-color: #0d6efd; color: white; width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 20px;">02</div>
            <div style="height: 100px; width: 2px; background-color: #e0e0e0; margin-left: 24px; margin-top: 10px;"></div>
        </div>
        <div style="background-color: white; border-radius: 10px; padding: 25px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); flex-grow: 1; margin-bottom: 20px;">
            <h3>AI-Powered Processing</h3>
            <p style="color: #6c757d;">Our advanced GPT-4o model processes the content, identifying key points and meaningful insights.</p>
        </div>
    </div>
    
    <div style="display: flex; margin-bottom: 3rem;">
        <div style="width: 50px; margin-right: 20px;">
            <div style="background-color: #0d6efd; color: white; width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 20px;">03</div>
        </div>
        <div style="background-color: white; border-radius: 10px; padding: 25px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); flex-grow: 1; margin-bottom: 20px;">
            <h3>Listen & Save</h3>
            <p style="color: #6c757d;">Enjoy your summarized podcast in just minutes, with the option to download it for offline listening.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
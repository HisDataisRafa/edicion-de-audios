import streamlit as st
from pydub import AudioSegment
import speech_recognition as sr
from datetime import datetime
import tempfile
import os

class AudioCombiner:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        
    def load_and_transcribe(self, audio_file):
        """Load audio file and return transcription"""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                # Save uploaded file to temporary file
                tmp_file.write(audio_file.getvalue())
                tmp_path = tmp_file.name

            # Convert audio to WAV format
            audio = AudioSegment.from_file(tmp_path)
            audio.export(tmp_path, format="wav")
            
            # Transcribe
            with sr.AudioFile(tmp_path) as source:
                audio_data = self.recognizer.record(source)
            text = self.recognizer.recognize_google(audio_data)
            
            # Clean up
            os.unlink(tmp_path)
            
            return text
        except Exception as e:
            st.error(f"Error processing audio: {str(e)}")
            return None

    def combine_segments(self, audio1_file, audio2_file, selected_segments):
        """Combine selected audio segments"""
        try:
            # Create temporary files
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp1, \
                 tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp2:
                
                # Save uploaded files
                tmp1.write(audio1_file.getvalue())
                tmp2.write(audio2_file.getvalue())
                
                # Load audio files
                audio1 = AudioSegment.from_file(tmp1.name)
                audio2 = AudioSegment.from_file(tmp2.name)
                
                # Combine segments
                combined = AudioSegment.empty()
                for segment in selected_segments:
                    source_audio = audio1 if segment['source'] == 'audio1' else audio2
                    start_ms = int(segment['start'] * 1000)  # Convert to milliseconds
                    end_ms = int(segment['end'] * 1000)
                    audio_segment = source_audio[start_ms:end_ms]
                    combined += audio_segment
                
                # Clean up temp files
                os.unlink(tmp1.name)
                os.unlink(tmp2.name)
                
                # Export combined audio
                output_path = "combined_audio.wav"
                combined.export(output_path, format="wav")
                return output_path
        except Exception as e:
            st.error(f"Error combining audio: {str(e)}")
            return None

def main():
    st.title("Audio Analysis Combiner")
    
    # Initialize session state
    if 'transcriptions' not in st.session_state:
        st.session_state.transcriptions = {'audio1': None, 'audio2': None}
    if 'segments' not in st.session_state:
        st.session_state.segments = []
    
    combiner = AudioCombiner()
    
    # File uploaders
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Audio 1")
        audio1_file = st.file_uploader("Upload first audio", type=['wav', 'mp3'])
        if audio1_file and st.button("Transcribe Audio 1"):
            with st.spinner("Transcribing Audio 1..."):
                text = combiner.load_and_transcribe(audio1_file)
                if text:
                    st.session_state.transcriptions['audio1'] = text
                    st.success("Audio 1 transcribed successfully!")
    
    with col2:
        st.subheader("Audio 2")
        audio2_file = st.file_uploader("Upload second audio", type=['wav', 'mp3'])
        if audio2_file and st.button("Transcribe Audio 2"):
            with st.spinner("Transcribing Audio 2..."):
                text = combiner.load_and_transcribe(audio2_file)
                if text:
                    st.session_state.transcriptions['audio2'] = text
                    st.success("Audio 2 transcribed successfully!")
    
    # Display transcriptions
    if st.session_state.transcriptions['audio1']:
        st.subheader("Audio 1 Transcription")
        st.text_area("", st.session_state.transcriptions['audio1'], height=200, key="text1")
    
    if st.session_state.transcriptions['audio2']:
        st.subheader("Audio 2 Transcription")
        st.text_area("", st.session_state.transcriptions['audio2'], height=200, key="text2")
    
    # Segment selection
    if st.session_state.transcriptions['audio1'] and st.session_state.transcriptions['audio2']:
        st.subheader("Select Segments")
        
        # Add new segment
        with st.expander("Add New Segment"):
            source = st.selectbox("Select Audio Source", ['audio1', 'audio2'], key="source")
            text = st.text_area("Enter text segment to match", key="text_segment")
            start_time = st.number_input("Start time (seconds)", min_value=0.0, key="start")
            end_time = st.number_input("End time (seconds)", 
                                     min_value=start_time, 
                                     value=start_time+1.0,
                                     key="end")
            
            if st.button("Add Segment"):
                new_segment = {
                    'source': source,
                    'text': text,
                    'start': start_time,
                    'end': end_time
                }
                st.session_state.segments.append(new_segment)
                st.success("Segment added!")
        
        # Display and manage segments
        if st.session_state.segments:
            st.subheader("Selected Segments")
            for i, segment in enumerate(st.session_state.segments):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"Segment {i+1}: {segment['text'][:50]}...")
                with col2:
                    st.write(f"Source: {segment['source']}")
                with col3:
                    if st.button(f"Remove {i+1}", key=f"remove_{i}"):
                        st.session_state.segments.pop(i)
                        st.experimental_rerun()
        
        # Combine audio
        if st.session_state.segments and st.button("Combine Selected Segments"):
            if audio1_file and audio2_file:
                with st.spinner("Combining audio segments..."):
                    output_path = combiner.combine_segments(
                        audio1_file,
                        audio2_file,
                        st.session_state.segments
                    )
                    if output_path:
                        st.success("Audio combined successfully!")
                        
                        # Display combined audio
                        with open(output_path, 'rb') as audio_file:
                            audio_bytes = audio_file.read()
                            st.audio(audio_bytes, format='audio/wav')
                        
                        # Provide download button
                        st.download_button(
                            label="Download Combined Audio",
                            data=audio_bytes,
                            file_name="combined_audio.wav",
                            mime="audio/wav"
                        )
            else:
                st.error("Please upload both audio files first!")

if __name__ == "__main__":
    main()

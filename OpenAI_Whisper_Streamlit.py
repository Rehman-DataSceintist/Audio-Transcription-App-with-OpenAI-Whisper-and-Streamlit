import streamlit as st
import whisper
import tempfile
import os
from docx import Document


# Title of the Streamlit app
st.title("Audio Transcription and Summarization App with OpenAI Whisper")

# Upload audio file
audio_file = st.file_uploader("Upload audio", type=['wav', 'mp3', 'm4a', 'mp4'])

# Function to load the Whisper model
@st.cache_resource
def load_model():
    return whisper.load_model("base")

# Initialize the Whisper model in session state if not already loaded
if 'model' not in st.session_state:
    st.session_state.model = None

# Load the model when the button is pressed
if st.sidebar.button("Load Whisper Model"):
    st.session_state.model = load_model()
    st.sidebar.success("Model loaded successfully")

# Function to load the summarization pipeline
@st.cache_resource
def load_summarizer():
    return pipeline("summarization")

# Initialize the summarization pipeline in session state if not already loaded
if 'summarizer' not in st.session_state:
    st.session_state.summarizer = load_summarizer()

# Transcribe audio when the button is pressed
if st.sidebar.button("Transcribe Audio"):
    if st.session_state.model is None:
        st.sidebar.error("Please load the model first")
    elif audio_file is None:
        st.sidebar.error("Please upload an audio file")
    else:
        st.sidebar.info('Transcribing audio...')

        # Save the uploaded audio file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(audio_file.read())
            temp_filename = temp_file.name

        # Transcribe the audio file
        transcription = st.session_state.model.transcribe(temp_filename)

        # Remove the temporary file
        os.remove(temp_filename)

        # Store the transcription text in session state
        st.session_state.transcription_text = transcription['text']

        # Display the transcription
        st.sidebar.success("Transcription complete")
        st.text_area("Transcription", st.session_state.transcription_text, height=300)

        # Check if transcription is successful
        if st.session_state.transcription_text:
            # Save transcription to a text file
            text_filename = "transcription.txt"
            with open(text_filename, "w") as text_file:
                text_file.write(st.session_state.transcription_text)

            # Save transcription to a Word document
            doc = Document()
            doc.add_paragraph(st.session_state.transcription_text)
            word_filename = "transcription.docx"
            doc.save(word_filename)

            # Provide download buttons for the transcription files
            with open(text_filename, "rb") as text_file:
                st.download_button(
                    label="Download Transcription as Text",
                    data=text_file,
                    file_name=text_filename,
                    mime="text/plain"
                )

            with open(word_filename, "rb") as word_file:
                st.download_button(
                    label="Download Transcription as Word",
                    data=word_file,
                    file_name=word_filename,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

# Summarize transcription when the button is pressed
if st.sidebar.button("Summarize Transcription"):
    if 'transcription_text' not in st.session_state:
        st.sidebar.error("Please transcribe the audio first")
    else:
        # Log the transcription text and length
        transcription_text = st.session_state.transcription_text
        transcription_length = len(transcription_text.split())
        st.sidebar.info(f'Transcription length: {transcription_length} words')

        if transcription_length < 50:
            st.sidebar.error("Transcription is too short for summarization. Please provide a longer audio.")
        else:
            try:
                # Summarize the transcription text
                st.sidebar.info('Summarizing transcription...')
                summary = st.session_state.summarizer(
                    transcription_text,
                    max_length=min(150, transcription_length // 2),  # Ensure max_length is appropriate
                    min_length=30,
                    do_sample=False
                )[0]['summary_text']
                # Display the summary
                st.text_area("Summary", summary, height=150)
            except IndexError:
                st.sidebar.error("Summarization failed. The input might be too short or not suitable for summarization.")
            except Exception as e:
                st.sidebar.error(f"An unexpected error occurred: {e}")

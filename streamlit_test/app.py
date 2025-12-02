# CRITICAL: Import opencv_fix FIRST to ensure headless version is used
# This must happen before any other imports that might use cv2
import opencv_fix  # noqa: F401

import os
import sys
import tempfile
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main import run_pipeline


def run_streamlit_app():
    st.set_page_config(page_title="Football Analytics", layout="wide")

    st.title("Football Tracking & Analytics")
    st.write(
        "Upload a football match clip and this app will run the tracking/analysis "
        "pipeline and generate an annotated output video."
    )

    # Initialize session state for tracking temp files
    if 'temp_files' not in st.session_state:
        st.session_state.temp_files = []

    # Clean up old temp files from previous runs
    for temp_file in st.session_state.temp_files:
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass  # Ignore errors if file is already deleted
    st.session_state.temp_files = []

    st.sidebar.header("Settings")
    use_stubs = st.sidebar.checkbox(
        "Use precomputed stubs (fast, only works for sample video)",
        value=False,
        help=(
            "When enabled, the app will use precomputed tracking/camera-movement data. "
            "This is only valid for the bundled sample video; disable it for your own videos."
        ),
    )

    uploaded_file = st.file_uploader(
        "Upload a video file", type=["mp4", "avi", "mov", "mkv"]
    )

    if uploaded_file is not None:
        st.video(uploaded_file)

        if st.button("Run analysis"):
            with st.spinner("Processing video, this may take a while..."):
                # Use a temporary file in system temp directory (not project directory)
                with tempfile.NamedTemporaryFile(
                    suffix=".mp4", delete=False
                ) as tmp_in:
                    tmp_in.write(uploaded_file.read())
                    input_path = tmp_in.name
                    st.session_state.temp_files.append(input_path)

                # Use a temporary file for output as well
                with tempfile.NamedTemporaryFile(
                    suffix=".mp4", delete=False
                ) as tmp_out:
                    output_path = tmp_out.name
                    st.session_state.temp_files.append(output_path)

                try:
                    final_path = run_pipeline(
                        input_video_path=input_path,
                        output_video_path=output_path,
                        use_stubs=use_stubs,
                    )
                    
                    # Clean up the temporary input file immediately after processing
                    if os.path.exists(input_path):
                        try:
                            os.remove(input_path)
                            if input_path in st.session_state.temp_files:
                                st.session_state.temp_files.remove(input_path)
                        except Exception:
                            pass
                            
                except Exception as e:
                    # Clean up temp files even if there's an error
                    for temp_file in [input_path, output_path]:
                        if os.path.exists(temp_file):
                            try:
                                os.remove(temp_file)
                                if temp_file in st.session_state.temp_files:
                                    st.session_state.temp_files.remove(temp_file)
                            except Exception:
                                pass
                    st.error(f"Error while running pipeline: {e}")
                    return

                st.success("Processing complete!")
                
                if os.path.exists(final_path):
                    st.subheader("Annotated output video")
                    with open(final_path, "rb") as f:
                        video_bytes = f.read()
                    st.video(video_bytes)

                    st.download_button(
                        label="Download output video",
                        data=video_bytes,
                        file_name="output_video.mp4",
                        mime="video/mp4",
                    )
                    # Output file will be cleaned up on next run or session end
                else:
                    st.warning("Output video was not found. Please check the logs.")


if __name__ == "__main__":
    run_streamlit_app()

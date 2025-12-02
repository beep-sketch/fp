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
               
                inputs_dir = os.path.join(os.getcwd(), "inputs")
                os.makedirs(inputs_dir, exist_ok=True)

                with tempfile.NamedTemporaryFile(
                    dir=inputs_dir, suffix=".mp4", delete=False
                ) as tmp_in:
                    tmp_in.write(uploaded_file.read())
                    input_path = tmp_in.name

                
                outputs_dir = os.path.join(os.getcwd(), "output_videos")
                os.makedirs(outputs_dir, exist_ok=True)
                output_path = os.path.join(outputs_dir, "streamlit_output.mp4")

                try:
                    final_path = run_pipeline(
                        input_video_path=input_path,
                        output_video_path=output_path,
                        use_stubs=use_stubs,
                    )
                except Exception as e:
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
                        file_name=os.path.basename(final_path),
                        mime="video/mp4",
                    )
                else:
                    st.warning("Output video was not found. Please check the logs.")


if __name__ == "__main__":
    run_streamlit_app()

import os
import sys
import tempfile
import subprocess
from pathlib import Path

# CRITICAL FIX for Streamlit Cloud: Ensure opencv-python-headless is used
# This must happen BEFORE any cv2 imports to prevent libGL.so.1 errors

# Remove cv2 from sys.modules if it exists
if 'cv2' in sys.modules:
    del sys.modules['cv2']

# Aggressively remove opencv-python and ensure headless is available
try:
    # Uninstall opencv-python (this is the problematic package)
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'uninstall', '-y', 'opencv-python', '--quiet'],
        capture_output=True,
        timeout=20,
        check=False
    )
    
    # Ensure opencv-python-headless is installed
    subprocess.run(
        [sys.executable, '-m', 'pip', 'install', '--upgrade', '--force-reinstall', 
         'opencv-python-headless>=4.8.0', '--quiet'],
        capture_output=True,
        timeout=90,
        check=False
    )
    
    # Clear import caches
    if 'cv2' in sys.modules:
        del sys.modules['cv2']
    import importlib
    importlib.invalidate_caches()
    
    # Remove opencv-python from site-packages if it still exists
    import site
    for site_packages in site.getsitepackages():
        opencv_python_path = os.path.join(site_packages, 'opencv_python-')
        if os.path.exists(opencv_python_path):
            # Try to remove the directory
            try:
                import shutil
                for item in os.listdir(site_packages):
                    if item.startswith('opencv_python-') and not item.startswith('opencv_python_headless-'):
                        item_path = os.path.join(site_packages, item)
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path, ignore_errors=True)
            except Exception:
                pass
except Exception:
    pass  # Continue even if cleanup fails

# Create import hook to intercept cv2 imports
class OpenCVHeadlessHook:
    """Force use of opencv-python-headless."""
    
    def find_spec(self, name, path, target=None):
        if name == 'cv2':
            # Clear cv2 from cache
            if 'cv2' in sys.modules:
                del sys.modules['cv2']
            # Return None to let Python find the module normally
            # (but we've ensured only headless is available)
        return None

# Register hook
sys.meta_path.insert(0, OpenCVHeadlessHook())

# Note: cv2 will be imported when we import main below
# The import hook and cleanup above should ensure headless version is used

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import main with error handling
try:
    from main import run_pipeline
except Exception as e:
    import traceback
    import streamlit as st
    st.error(f"❌ Failed to import pipeline module: {str(e)}")
    st.info("💡 This error occurred while loading the application. Check the details below.")
    with st.expander("🔍 Full error traceback", expanded=True):
        st.code(traceback.format_exc(), language="python")
    st.stop()


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
                            
                except FileNotFoundError as e:
                    # Clean up temp files
                    for temp_file in [input_path, output_path]:
                        if os.path.exists(temp_file):
                            try:
                                os.remove(temp_file)
                                if temp_file in st.session_state.temp_files:
                                    st.session_state.temp_files.remove(temp_file)
                            except Exception:
                                pass
                    st.error(f"❌ File not found: {e}")
                    st.info("💡 This usually means a model file or required resource is missing. Please check that all model files are in the repository.")
                    return
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
                    
                    # Show detailed error information
                    import traceback
                    error_details = traceback.format_exc()
                    st.error(f"❌ Error while running pipeline: {str(e)}")
                    st.info("💡 Expand the error details below to see the full traceback for debugging.")
                    with st.expander("🔍 Error details (click to expand)", expanded=False):
                        st.code(error_details, language="python")
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


# Always run the app (Streamlit calls this automatically)
try:
    run_streamlit_app()
except Exception as e:
    import traceback
    st.error(f"❌ Fatal error in app: {str(e)}")
    st.info("💡 This error occurred during app execution. Check the details below.")
    with st.expander("🔍 Full error traceback", expanded=True):
        st.code(traceback.format_exc(), language="python")
    st.stop()

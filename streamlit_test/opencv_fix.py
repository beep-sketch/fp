"""
Fix for Streamlit Cloud: Ensure opencv-python-headless is used instead of opencv-python.
This must be imported BEFORE any cv2 imports to prevent libGL.so.1 errors.
"""
import sys
import subprocess
import importlib.util
from importlib import import_module

# Remove cv2 from sys.modules if it exists (wrong version might be loaded)
if 'cv2' in sys.modules:
    del sys.modules['cv2']

# Try to uninstall opencv-python if it exists (it conflicts with headless version)
try:
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'uninstall', '-y', 'opencv-python', '--quiet'],
        capture_output=True,
        timeout=10,
        check=False
    )
    # If uninstall was successful, we need to clear any cached imports
    if result.returncode == 0:
        # Clear cv2 from sys.modules again after uninstall
        if 'cv2' in sys.modules:
            del sys.modules['cv2']
except Exception:
    pass  # Ignore errors, continue

# Install opencv-python-headless if not already installed
try:
    import cv2
except ImportError:
    # If cv2 import fails, try installing headless version
    try:
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', 'opencv-python-headless>=4.8.0', '--quiet'],
            capture_output=True,
            timeout=60,
            check=False
        )
        # Clear sys.modules to force reimport
        if 'cv2' in sys.modules:
            del sys.modules['cv2']
        import cv2
    except Exception as e:
        raise ImportError(
            f"Could not import cv2. Please ensure opencv-python-headless is installed. "
            f"Error: {e}"
        )

# Install import hook to intercept cv2 imports and ensure headless version
class OpenCVImportHook:
    """Import hook to ensure opencv-python-headless is used instead of opencv-python."""
    
    def find_spec(self, name, path, target=None):
        if name == 'cv2':
            # Clear cv2 from sys.modules to force reimport
            if 'cv2' in sys.modules:
                del sys.modules['cv2']
            # Try to uninstall opencv-python one more time
            try:
                subprocess.run(
                    [sys.executable, '-m', 'pip', 'uninstall', '-y', 'opencv-python', '--quiet'],
                    capture_output=True,
                    timeout=5,
                    check=False
                )
            except Exception:
                pass
        return None

# Register the import hook
sys.meta_path.insert(0, OpenCVImportHook())


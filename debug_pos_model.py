from pathlib import Path
import cv2
from ultralytics import YOLO

MODEL_PATH = "pos_model/best.pt"
VIDEO_PATH = "inputs/video1.mp4"  # or any frame where the pitch is clearly visible

def main():
    if not Path(MODEL_PATH).exists():
        print(f"Model not found at {MODEL_PATH}")
        return

    cap = cv2.VideoCapture(VIDEO_PATH)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        print("Could not read first frame from video")
        return

    model = YOLO(MODEL_PATH)
    results = model(frame, verbose=False)
    if not results:
        print("No results from model")
        return

    res = results[0]
    if res.keypoints is None:
        print("No keypoints in result")
        return

    kpts = res.keypoints.xy  # (num_dets, num_kpts, 2)
    print("keypoints shape:", kpts.shape)
    print("first detection keypoints:")
    print(kpts[0])

if __name__ == "__main__":
    main()
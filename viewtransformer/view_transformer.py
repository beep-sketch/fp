import numpy as np
import cv2

from pos_model import PitchKeypointDetector


class ViewTransformer:
    def __init__(self, reference_frame=None, use_keypoint_model: bool = True):
        """
        If use_keypoint_model is True and a reference_frame is provided, use the
        YOLO keypoint model in `pos_model/best.pt` to automatically estimate the
        pitch corners. Otherwise, fall back to the original hard-coded vertices.
        """
        # Real-world pitch dimensions in meters (approximate)
        court_width = 68       # width of the pitch
        court_length = 105     # length of the pitch

        pixel_vertices = None

        if use_keypoint_model and reference_frame is not None:
            try:
                detector = PitchKeypointDetector()
                detected_vertices = detector.detect_pitch_vertices(reference_frame)
                if (
                    detected_vertices is not None
                    and detected_vertices.shape == (4, 2)
                ):
                    pixel_vertices = detected_vertices
            except Exception:
                # If anything goes wrong, we silently fall back to the manual vertices
                pixel_vertices = None

        # Fallback to the original manually-tuned vertices if the model failed
        if pixel_vertices is None:
            pixel_vertices = np.array(
                [
                    [110, 1035],
                    [265, 275],
                    [910, 260],
                    [1640, 915],
                ]
            )

        self.pixel_vertices = pixel_vertices.astype(np.float32)

        self.target_vertices = np.array(
            [
                [0, court_width],
                [0, 0],
                [court_length, court_length],
                [court_length, 0],
            ],
            dtype=np.float32,
        )

        self.perspective_transformer = cv2.getPerspectiveTransform(
            self.pixel_vertices, self.target_vertices
        )

    def transform_point(self, point):
        """
        Transform a single image point into pitch coordinates.

        We no longer strictly require the point to be inside the detected polygon,
        so players slightly outside the estimated area still get a transformed
        coordinate and therefore speed/distance.
        """
        reshaped_point = point.reshape(-1, 1, 2).astype(np.float32)
        transform_point = cv2.perspectiveTransform(reshaped_point, self.perspective_transformer)

        return transform_point.reshape(-1, 2)


    def add_transformed_position_to_tracks(self, tracks):
        for obj, object_tracks in tracks.items():
            for frame_num, track in enumerate(object_tracks):
                for track_id, track_info in track.items():
                    position = track_info.get("position_adjusted")
                    if position is None:
                        continue
                    position = np.array(position)
                    position_transformed = self.transform_point(position)
                    if position_transformed is not None:
                        position_transformed = position_transformed.squeeze().tolist()
                    tracks[obj][frame_num][track_id]["position_transformed"] = position_transformed

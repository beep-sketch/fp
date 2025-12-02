import cv2
from utils import measure_distance, get_foot_position

class Speed_and_Distance_Estimator:
    def __init__(self):
        self.frame_window = 5
        self.frame_rate = 24

    def add_speed_and_distance_to_tracks(self,tracks):

        total_distance = {}
        last_speed = {}  # Track last known speed for each player
        last_distance = {}  # Track last known distance for each player

        for object, object_tracks in tracks.items():
            if object =='ball' or object == 'referees':
                continue
            number_of_frames = len(object_tracks)
            
            # Initialize tracking dictionaries
            if object not in total_distance:
                total_distance[object] = {}
            if object not in last_speed:
                last_speed[object] = {}
            if object not in last_distance:
                last_distance[object] = {}
            
            # Calculate speed using consecutive frames for smoother results
            for frame_num in range(number_of_frames - 1):
                next_frame = frame_num + 1
                
                # Get all track IDs present in current frame
                track_ids = set(object_tracks[frame_num].keys())
                # Also check next frame
                if next_frame < number_of_frames:
                    track_ids.update(object_tracks[next_frame].keys())
                
                for track_id in track_ids:
                    if track_id not in object_tracks[frame_num]:
                        continue
                    if track_id not in object_tracks[next_frame]:
                        continue

                    # Use transformed positions (in meters) for accurate speed calculation.
                    start_position = object_tracks[frame_num][track_id].get('position_transformed')
                    end_position = object_tracks[next_frame][track_id].get('position_transformed')

                    # Skip if we don't have both positions for this step
                    if start_position is None or end_position is None:
                        continue

                    distance_covered = measure_distance(start_position, end_position)
                    time_elapsed = 1.0 / self.frame_rate  # One frame difference
                    
                    if time_elapsed == 0:
                        continue
                    
                    speed_meters_per_second = distance_covered / time_elapsed
                    speed_km_per_hour = speed_meters_per_second * 3.6

                    # Basic physical plausibility filter:
                    # Ignore unrealistically low or high speeds caused by noisy detections.
                    # Typical sprinting speeds are < 36 km/h; we allow a bit of margin.
                    if speed_km_per_hour < 0.5 or speed_km_per_hour > 40:
                        continue

                    if track_id not in total_distance[object]:
                        total_distance[object][track_id] = 0

                    total_distance[object][track_id] += distance_covered

                    # Store last known values
                    last_speed[object][track_id] = speed_km_per_hour
                    last_distance[object][track_id] = total_distance[object][track_id]

                    # Assign to current frame
                    object_tracks[frame_num][track_id]['speed'] = speed_km_per_hour
                    object_tracks[frame_num][track_id]['distance'] = total_distance[object][track_id]

            # Propagate last known speed/distance forward so players keep labels
            # even when a frame is missing a new measurement.
            for frame_num in range(1, number_of_frames):
                prev_tracks = object_tracks[frame_num - 1]
                curr_tracks = object_tracks[frame_num]
                for track_id, track_info in curr_tracks.items():
                    if 'speed' in track_info and 'distance' in track_info:
                        continue
                    prev_info = prev_tracks.get(track_id)
                    if prev_info is None:
                        continue
                    prev_speed = prev_info.get('speed')
                    prev_distance = prev_info.get('distance')
                    if prev_speed is None or prev_distance is None:
                        continue
                    track_info['speed'] = prev_speed
                    track_info['distance'] = prev_distance


    def draw_speed_and_distance(self,tracks,frames):
        output_frames = []
        total_drawn = 0
        for frame_num, frame in enumerate(frames):
            frame_drawn_count = 0
            for object, object_tracks in tracks.items():
                if object == "ball" or object == "referees":
                    continue
                if frame_num >= len(object_tracks):
                    continue
                for track_id, track_info in object_tracks[frame_num].items():
                    if "speed" in track_info:
                        speed = track_info.get('speed', None)
                        distance = track_info.get('distance', None)
                        if speed is None or distance is None:
                            continue

                        bbox = track_info.get('bbox')
                        if bbox is None:
                            continue
                        
                        position = get_foot_position(bbox)
                        if position is None:
                            continue
                            
                        position = list(position)
                        position[1] += 40

                        # Make sure position is within frame bounds
                        height, width = frame.shape[:2]
                        if position[0] < 0 or position[0] >= width or position[1] < 0 or position[1] >= height:
                            continue

                        position = tuple(map(int, position))
                        # Draw white text with black outline for better visibility
                        text = f"{speed:.2f} km/h"
                        cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3)
                        cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                        
                        text2 = f"{distance:.2f} m"
                        pos2 = (position[0], position[1] + 25)
                        if pos2[1] < height:  # Make sure second line is also in bounds
                            cv2.putText(frame, text2, pos2, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 3)
                            cv2.putText(frame, text2, pos2, cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                        frame_drawn_count += 1
            total_drawn += frame_drawn_count
            output_frames.append(frame)
        
        return output_frames



from utils.bbox_utils import get_center_of_bbox, measure_distance, is_valid_bbox

class PlayerBallAssigner:
    def __init__(self):
        self.max_player_ball_distance = 70

    def assign_ball_to_player(self, players, ball_bbox):
        if not is_valid_bbox(ball_bbox):
            return -1

        ball_position = get_center_of_bbox(ball_bbox)
        if ball_position is None:
            return -1
        minimum_distance = 9999999
        assigned_player = -1
        for player_id, player, in players.items():
            player_bbox = player['bbox']
            if not is_valid_bbox(player_bbox):
                continue

            distance_left = measure_distance((player_bbox[0], player_bbox[-1]), ball_position)
            distance_right = measure_distance((player_bbox[2], player_bbox[-1]), ball_position)
            distance = min(distance_left, distance_right)

            if distance < self.max_player_ball_distance - distance:
                if distance < minimum_distance:
                    minimum_distance = distance
                    assigned_player = player_id

        return assigned_player

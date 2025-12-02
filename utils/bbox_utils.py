import math


def _is_invalid_coordinate(value):
    return value is None or (isinstance(value, float) and math.isnan(value))


def is_valid_bbox(bbox):
    if not bbox or len(bbox) != 4:
        return False
    return not any(_is_invalid_coordinate(coord) for coord in bbox)


def get_center_of_bbox(bbox):
    if not is_valid_bbox(bbox):
        return None

    x1, y1, x2, y2 = bbox
    return int((x1 + x2) / 2), int((y1 + y2) / 2)

def get_bbox_width(bbox):
    return bbox[2]-bbox[0]

def measure_distance(p1,p2):
    return ((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)**0.5

def measure_xy_distance(p1,p2):
    return p1[0]-p2[0],p1[1]-p2[1]

def get_foot_position(bbox):
    x1,y1,x2,y2 = bbox
    return int((x1+x2)/2),int(y2)
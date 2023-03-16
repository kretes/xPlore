import json
import requests
from more_itertools import chunked
import math
import tqdm
from geopy.distance import distance
from itertools import product
from pathlib import Path

from typing import Collection, Tuple, Dict


def generate_grid_points_in_radius(center: Tuple[float, float], radius_km: float, grid_spacing_m: int) -> list[Tuple[float, float]]:
    """
    generates grid points in a circle defined by `center` and `radius_km` using spacing `grid_spacing_m`
    :param center:
    :param radius_km:
    :param grid_spacing_m:
    :return: list of points
    """
    n = math.ceil(1000 * radius_km / grid_spacing_m)

    lats = []
    longs = []
    for i in range(-n, n + 1):
        angle = 0 if i > 0 else 180
        destination = distance(meters=abs(i) * grid_spacing_m).destination(center, angle)
        lats.append(destination.latitude)
        angle = 90 if i > 0 else 270
        destination = distance(meters=abs(i) * grid_spacing_m).destination(center, angle)
        longs.append(destination.longitude)

    points = list(product(lats, longs))
    points = [p for p in points if distance(p, center).kilometers <= radius_km]
    return points


def get_roads(points: str, GOOGLE_API_KEY: str):
    """
    calls google roads api for nearestRoads and returns the response
    :param points:
    :param GOOGLE_API_KEY:
    :return:
    """
    nearest = f"https://roads.googleapis.com/v1/nearestRoads?points={points}&key={GOOGLE_API_KEY}"
    return requests.get(nearest)

def get_points_strings_from_tuple(points: list[Tuple[float, float]]) -> str:
    """
    formats `points` as google api parameter
    :param points:
    :return:
    """
    points_data = [",".join([str(i) for i in e]) for e in points]
    points_data = "|".join(points_data)
    return points_data

def get_road_points(grid_points: Collection[tuple[float]], MAX_REQUESTS: int, GOOGLE_API_KEY: str) -> dict[tuple[float, float], tuple[float, float]]:
    """
    Calls Google API in a chunked mode (to minimize the price) and converts the response by mapping the road point to a query point
    :param grid_points:
    :param MAX_REQUESTS:
    :param GOOGLE_API_KEY:
    :return:
    """
    groups = list(chunked(grid_points, 100))
    all_grid_to_road_points = {}
    assert len(groups) <= MAX_REQUESTS, len(groups)
    if len(groups) > 0:
        for group in tqdm.tqdm(groups):
            roads_grid = get_roads(get_points_strings_from_tuple(group), GOOGLE_API_KEY)
            roads_response_data = json.loads(roads_grid.text)
            roads_grid_points = roads_response_data.get("snappedPoints", [])
            for road_point in roads_grid_points:
                originalIndex = road_point["originalIndex"]
                originalPoint = group[originalIndex]
                all_grid_to_road_points[originalPoint] = (road_point["location"]["latitude"], road_point["location"]["longitude"])
    return all_grid_to_road_points


def get_grid_and_road_points(center_point: Tuple[float, float], radius_size_km: int, grid_spacing_m: int, data_dir: str, max_requests: int, GOOGLE_API_KEY: str) -> Dict[str, list[Tuple[float, float]]]:
    """
    Creates a grid of points around given `center_point` and reads a cached Google API data for mapping to roads.
    For each missing point - Google API is called and cached file is updated.

    grid points are stored as E7 in json since a directo comparison is needed to work reliably after serialization/deserialization

    :param center_point:
    :param radius_size_km:
    :param grid_spacing_m:
    :param data_dir:
    :param max_requests:
    :param GOOGLE_API_KEY:
    :return:
    """
    grid_to_road_file_name = f"grid_to_road_cache_center_{center_point[0]}_{center_point[1]}_radius_{radius_size_km}_spacing_{grid_spacing_m}.json"
    grid_to_road_path = Path(data_dir) / "grid_to_road_cache" / grid_to_road_file_name
    grid_points_in_scope = generate_grid_points_in_radius(center_point, radius_size_km, grid_spacing_m)
    print(
        f"grid from {center_point} with radius {radius_size_km} km and spacing {grid_spacing_m} m has {len(grid_points_in_scope)} points")

    grid_and_road_points = {"grid_points_E7": [], "road_points": []}
    if grid_to_road_path.exists():
        with open(grid_to_road_path) as f:
            grid_and_road_points = json.load(f)

    print(
        f'have cached grid points ({len(grid_and_road_points["grid_points_E7"])}) and cached road points ({len(grid_and_road_points["road_points"])})')

    def to_E7(point):
        return (int(point[0] * 1e7), int(point[1] * 1e7))

    grid_points_to_map = []
    for p in grid_points_in_scope:
        if list(to_E7(p)) not in grid_and_road_points["grid_points_E7"]:
            grid_points_to_map.append(p)

    print(f"needs {len(grid_points_to_map)} points to be mapped to roads")

    grid_and_road_points["road_points"] = grid_and_road_points["road_points"] + list(get_road_points(grid_points_to_map, max_requests, GOOGLE_API_KEY).values())
    grid_and_road_points["grid_points_E7"] = grid_and_road_points["grid_points_E7"] + [to_E7(p) for p in
                                                                                       grid_points_to_map]
    print(
        f'after mapping have grid points ({len(grid_and_road_points["grid_points_E7"])}) and road points ({len(grid_and_road_points["road_points"])})')

    with open(grid_to_road_path, "w") as f:
        json.dump(grid_and_road_points, f)

    return grid_and_road_points
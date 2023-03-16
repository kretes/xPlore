import zipfile
import json
from typing import Tuple

import numpy as np
import pandas as pd
from pathlib import Path
from geopy.distance import distance
from itertools import product


def read_location_history_dir(data_dir: str) -> np.array:
    """
    reads Google Location History data by taking any zip from given `data_dir`
    :param data_dir:
    :return: 2D Array [N_Points, 2] with unique points' coordinates
    """

    zip_path = list((Path(data_dir) / "takeouts").glob("*.zip"))[0]
    return read_location_history_zip(zip_path)


def read_location_history_zip(zip_path: str) -> np.array:
    """
    reads Google Location History from `zip_path`
    :param zip_path:
    :return: 2D Array [N_Points, 2] with unique points' coordinates
    """
    with zipfile.ZipFile(zip_path) as z:
        for name in z.namelist():
            if name.endswith("json"):
                with z.open(name) as f:
                    data = json.loads(f.read())
                    if "locations" in data:
                        print("json loaded...")
                        df = pd.DataFrame(data["locations"])

                        all_unique_coords = df[["latitudeE7", "longitudeE7"]].drop_duplicates().reset_index(drop=True)

                        X = all_unique_coords.values / 1e7

                        print(f"read {len(X)} unique locations")

                        return X

    return None


def generate_points_in_areas(areas: list[Tuple[Tuple[float, float], Tuple[float, float]]], grid_spacing_m: int) -> list[Tuple[float, float]]:
    """
    Generates points in given areas by following a grid with given spacing
    :param areas:
    :param grid_spacing_m:
    :return: list of points inside given `areas`
    """
    all_points = []
    for area in areas:

        lats = []
        longs = []
        start_point = (min([area[0][0], area[1][0]]), min([area[0][1], area[1][1]]))
        end_point = (max([area[0][0], area[1][0]]), max([area[0][1], area[1][1]]))
        curr_lat, curr_long = start_point
        i = 1
        while curr_lat < end_point[0]:
            destination = distance(meters=abs(i) * grid_spacing_m).destination(start_point, 0)
            lats.append(curr_lat := destination.latitude)
            i += 1
            assert i < 1000, f"this area looks to large : {area}"

        i = 1
        while curr_long < end_point[1]:
            destination = distance(meters=abs(i) * grid_spacing_m).destination(start_point, 90)
            longs.append(curr_long := destination.longitude)
            i += 1
            assert i < 1000, f"this area looks to large : {area}"

        points = list(product(lats, longs))
        all_points.extend(points)
    return all_points


def read_points_excluded_from_exploration(data_dir: str, grid_spacing_m: int) -> list[Tuple[float, float]]:
    """
    Reads from `data_dir / excluded_from_exploration.json` and generates a list of points that are excluded from exploration.
    The result is a concatenation of:
        `private_points` collection read from the file
        points generated from both `private_areas` and `manual_visited_areas`
            - generation is just creating a point in grid with spacing equal to `grid_spacing_m // 2`
    :param data_dir:
    :param grid_spacing_m:
    :return: list of points that should be excluded from exploration
    """

    excluded_from_exploration_path = Path(data_dir) / "excluded_from_exploration.json"
    if excluded_from_exploration_path.exists():
        with open(excluded_from_exploration_path) as f:
            data = json.load(f)
        return data.get("private_points", []) + generate_points_in_areas(data.get("private_areas", []) + data.get("manual_visited_areas", []), grid_spacing_m // 2)
    return []
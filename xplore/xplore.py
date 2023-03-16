from operator import itemgetter
from typing import Tuple

from sklearn.neighbors import NearestNeighbors
import numpy as np

from haversine import haversine, haversine_vector, Unit

import folium


def create_knn(visited_points: list[Tuple[float, float]], points_excluded_from_exploration: list[Tuple[float, float]]) -> NearestNeighbors:
    """
    Creates and fits a KNN model to a concatenation of visited points and excluded from exploration.
    Both sets of files are treated in the same way, since we want them to mean 'this point is not a candidate for exploration'
    :param visited_points:
    :param points_excluded_from_exploration:
    :return:
    """
    X = np.vstack([visited_points, points_excluded_from_exploration * 2])

    knn = NearestNeighbors(n_neighbors=30)

    knn.fit(X)

    return knn



def closest_point(road_point: Tuple[float, float], knn: NearestNeighbors) -> Tuple[float, list[int]]:
    """
    Runs knn using given `road_point`

    NOTE:
    As an approximation of a geodesic distance I use an euclidean knn in the space of geodesic coordinates,
        and we search for a group of 30 closest points
    Next, to do the proper calculation - find a minimum haversine distance from all points

    This is the approximation and should work roughly properly, especially for coordinates far from the poles.

    :param road_point:
    :param knn:
    :return: tuple of:
     - haversine distance to the closest points in kNN
     - list of indices of K nearest neighbours
    """

    indices = knn.kneighbors([road_point], n_neighbors=30, return_distance=False)

    return np.min([haversine(road_point, knn._fit_X[idx, :], Unit.KILOMETERS) for idx in indices[0]]), indices[0]


def get_non_visited_road_points(knn: NearestNeighbors, road_points: list[Tuple[float, float]], center_point: Tuple[float, float], radius_size_km: int, grid_spacing_m: int) -> list[Tuple[float, float]]:
    """
    Runs the main algorithm - for each of the road point - check if there is any visited point(in knn) that is less than `grid_spacing_m`.
    If not - the point is returned.


    :param knn:
    :param road_points:
    :param center_point:
    :param radius_size_km:
    :param grid_spacing_m:
    :return: road points to which there is no visited point within `grid_spacing_m` - sorted by the ascending distance to `center_point`.
    """
    dist_threshold_km = grid_spacing_m / 1000

    road_points_with_dist = []
    for road_point in set([tuple(x) for x in road_points]):
        if haversine(road_point, center_point, unit=Unit.KILOMETERS) < radius_size_km:
            road_points_with_dist.append((road_point, *closest_point(road_point, knn)))

    road_points_with_dist.sort(key=lambda a: -a[1])

    road_points_with_dist_above = [e for e in road_points_with_dist if e[1] > dist_threshold_km]

    print(f"have {len(road_points_with_dist_above)} non-visited points")

    points_to_display_with_distance_from_center = [(x[0], haversine(x[0], center_point, unit=Unit.METERS)) for x in
                                                   road_points_with_dist_above]
    points_to_display_with_distance_from_center = sorted(points_to_display_with_distance_from_center, key=itemgetter(1))
    points_to_display = [x[0] for x in points_to_display_with_distance_from_center]

    return points_to_display


def show_map_with_points(center_point: Tuple[float, float], points: list[Tuple[float, float]]) -> folium.Map:
    """
    Shows Folium Map with `points`
    :param center_point:
    :param points:
    :return:
    """
    m = folium.Map(location=center_point, zoom_start=12)
    folium.Marker(center_point, icon=folium.Icon(color="green")).add_to(m)

    for point in points:
        folium.Marker(point).add_to(m)

    min_point = np.array(points).min(axis=0).tolist()
    max_point = np.array(points).max(axis=0).tolist()

    m.fit_bounds([min_point, max_point])

    return m
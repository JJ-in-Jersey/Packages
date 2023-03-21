from GPX import Waypoint
from Navigation import Navigation as nav
import numpy as np
from scipy.interpolate import Rbf as RBF
from matplotlib import pyplot as plt
from math import dist

class MinimalSurface:

    @staticmethod
    def new_point(start, end, dist_from_start):
        scale = dist_from_start/nav.distance(start, end)
        return [start[i] * (1 - scale) + start[i] * scale for i in range(0, 3)]

    def step_size(pts):
        dists = []
        points = pts + [pts[0]]
        for i, pt in enumerate(points[:-1]):
            dists.append(dist(pt, points[i + 1]))
        return np.array(dists).min() / 10

    def new_edge(a, b, ss):
        new_points = []
        for step in range(0, int(round(dist(a, b) / ss, 0))): new_points.append(new_point(a, b, step * ss / dist(a, b)))
        return new_points

    def __init__(self, waypoints):
        self.points= []
        for pt in waypoints:
            self.points.append(pt.coords)

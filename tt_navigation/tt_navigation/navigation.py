from haversine import haversine as hvs, Unit
import numpy as np


def sign(value): return value/abs(value)


def distance(start_coords, end_coords): return hvs(start_coords, end_coords, unit=Unit.NAUTICAL_MILES)


def directions(compass_heading: int):
    dir_names = None
    if compass_heading > 337.5 or compass_heading < 22.5:
        dir_names = tuple(['north', 'south'])
    elif 67.5 > compass_heading > 22.5:
        dir_names = tuple(['northeast', 'southwest'])
    elif 112.5 > compass_heading > 67.5:
        dir_names = tuple(['east', 'west'])
    elif 157.5 > compass_heading > 112.5:
        dir_names = tuple(['southeast', 'northwest'])
    elif 202.5 > compass_heading > 157.5:
        dir_names = tuple(['south', 'north'])
    elif 247.5 > compass_heading > 202.5:
        dir_names = tuple(['southwest', 'northeast'])
    elif 292.5 > compass_heading > 247.5:
        dir_names = tuple(['west', 'east'])
    elif 337.5 > compass_heading > 292.5:
        dir_names = tuple(['northwest', 'southeast'])

    return dir_names


def dir_abbrevs(compass_heading: int):
    dir_names = None
    if compass_heading > 337.5 or compass_heading < 22.5:
        dir_names = tuple(['N', 'S'])
    elif 67.5 > compass_heading > 22.5:
        dir_names = tuple(['NE', 'SW'])
    elif 112.5 > compass_heading > 67.5:
        dir_names = tuple(['E', 'W'])
    elif 157.5 > compass_heading > 112.5:
        dir_names = tuple(['SE', 'NW'])
    elif 202.5 > compass_heading > 157.5:
        dir_names = tuple(['S', 'N'])
    elif 247.5 > compass_heading > 202.5:
        dir_names = tuple(['SW', 'NE'])
    elif 292.5 > compass_heading > 247.5:
        dir_names = tuple(['W', 'E'])
    elif 337.5 > compass_heading > 292.5:
        dir_names = tuple(['NW', 'SE'])

    return dir_names


class Heading:

    def quadrant(self):
        if self.lat_sign > 0 and self.lon_sign > 0:
            return 1
        elif self.lat_sign < 0 < self.lon_sign:
            return 2
        elif self.lat_sign < 0 and self.lon_sign < 0:
            return 3
        elif self.lon_sign < 0 < self.lat_sign:
            return 4
        else:
            raise NotImplementedError


    def __init__(self, start_coords, end_coords):
        self.lat_sign = np.sign(end_coords[0] - start_coords[0])
        self.lon_sign = np.sign(end_coords[1] - start_coords[1])
        corner = (end_coords[0], start_coords[1])
        self.lat_dist = distance(corner, start_coords)
        self.lon_dist = distance(end_coords, corner)
        self.angle = int(round(np.rad2deg(np.arctan(self.lon_dist/self.lat_dist)), 0))

        if self.quadrant() == 2:
            self.angle = 180 - self.angle
        elif self.quadrant() == 3:
            self.angle = self.angle + 180
        elif self.quadrant() == 4:
            self.angle = 360 - self.angle

from haversine import haversine as hvs, Unit
import numpy as np


def sign(value): return value/abs(value)


def distance(start_coords, end_coords): return hvs(start_coords, end_coords, unit=Unit.NAUTICAL_MILES)


def direction(compass_heading: int):
    if compass_heading > 337.5 or compass_heading < 22.5:
        dir_name = 'north'
    elif 62.5 > compass_heading > 22.5:
        dir_name = 'northeast'
    elif 112.5 > compass_heading > 62.5:
        dir_name = 'east'
    elif 157.5> compass_heading > 112.5:
        dir_name = 'southeast'
    elif 202.5 > compass_heading > 157.5:
        dir_name = 'south'
    elif 247.5 > compass_heading > 202.5:
        dir_name = 'southwest'
    elif 292.5 > compass_heading > 247.5:
        dir_name = 'west'
    elif 337.5 > compass_heading > 202.5:
        dir_name = 'northwest'

    return dir_name


def heading(start_coords, end_coords):
    corner = (end_coords[0], start_coords[1])
    lat_dist = distance(corner, start_coords)
    lon_dist = distance(end_coords, corner)
    return int(round(np.rad2deg(np.arctan(lon_dist/lat_dist)), 0))

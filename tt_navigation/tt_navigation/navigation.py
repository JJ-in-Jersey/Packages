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


def heading(start_coords, end_coords):
    corner = (end_coords[0], start_coords[1])
    lat_dist = distance(corner, start_coords)
    lon_dist = distance(end_coords, corner)
    return int(round(np.rad2deg(np.arctan(lon_dist/lat_dist)), 0))

from haversine import haversine as hvs, Unit
import numpy as np

def sign(value): return value/abs(value)

class Navigation:

    directionLookup = {'SN': 'South to North', 'NS': 'North to South', 'EW': 'East to West', 'WE': 'West to East'}

    @staticmethod
    def distance(start_coords, end_coords): return hvs(start_coords, end_coords, unit=Unit.NAUTICAL_MILES)

    @staticmethod
    def direction(start_coords, end_coords):
        #                                  (y,x)
        # corner(e lat,s lon)---------end(lat,lon)
        # ----------------------------------------
        # ----------------------------------------
        # ----------------------------------------
        # start(lat,lon)--------------------------
        #        (y,x)

        corner = (end_coords[0], start_coords[1])
        lat_sign = sign(end_coords[0] - start_coords[0])
        lon_sign = sign(end_coords[1] - start_coords[1])

        lat_dist = Navigation.distance(corner, start_coords)
        lon_dist = Navigation.distance(end_coords, corner)

        if lon_dist > lat_dist:
            if lon_sign > 0: code = 'WE'
            else: code = 'EW'
        else:
            if lat_sign > 0: code = 'SN'
            else: code = 'NS'

        return Navigation.directionLookup[code]

    @staticmethod
    def heading(start_coords, end_coords):
        corner = (end_coords[0], start_coords[1])
        lat_dist = Navigation.distance(corner, start_coords)
        lon_dist = Navigation.distance(end_coords, corner)
        return int(round(np.rad2deg(np.arctan(lon_dist/lat_dist)), 0))

    def __init__(self):
        pass

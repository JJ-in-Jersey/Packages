import numpy as np
from scipy.differentiate import derivative
from scipy.interpolate import CubicSpline


def cubic_inflection_points(x_values, y_values):

    # define the function
    cs = CubicSpline(x_values, y_values)
    second_derivative = derivative(cs, x_values)

    # Find the sign changes in the second derivative
    inflection_indices = np.where(np.diff(np.sign(second_derivative)))[0]
    inflection_points = x_values[inflection_indices]

    return inflection_points

import numpy as np
from pandas import Series
from sympy.geometry import Point3D, Line, Segment, Plane
from sympy import symbols

from scipy.interpolate import Rbf, CubicSpline
from matplotlib import pyplot as plot

from tt_exceptions.exceptions import DuplicateValues, LengthMismatch, NonMonotonic
from tt_dataframe.dataframe import DataFrame


def step_size(segments): return np.array([s.length for s in segments]).min() / Interpolator.num_edge_points


def edge_points(segments, ss):
    t = symbols('t')
    edge_pts = []
    for segment in segments:
        num_pts = range(1, int(round(segment.length / ss, 0)))
        edge_pts += [segment.arbitrary_point(t).evalf(subs={t: pt*ss/segment.length}) for pt in num_pts]
    return np.array(edge_pts).astype(float)


# noinspection PyPep8Naming
class Interpolator:

    scale = 10000
    num_edge_points = 10
    mesh_density = 300
    LINE = 'LINE'
    SURFACE = 'SURFACE'
    XY_PLANE = Plane(Point3D(0, 0, 0), normal_vector=[0, 0, 1])

    def plot_segment(self, segment: Segment, color: str, style: str, weight: float):
        if segment.length == 0:
            return
        points = np.array(segment.points).astype(float)
        self.ax.plot3D(points[:, 0], points[:, 1], points[:, 2], c=color, linestyle=style, linewidth=weight)

    def plot_point(self, pt: Point3D, color: str, mark: str):
        self.ax.scatter(pt.x, pt.y, pt.z, c=color, marker=mark)

    def show_axes(self):
        if self.ax is None:
            self.ax = plot.axes(projection="3d")
        xi = np.linspace(min(self.x_limits), max(self.x_limits), Interpolator.mesh_density)
        yi = np.linspace(min(self.y_limits), max(self.y_limits), Interpolator.mesh_density)
        XI, YI = np.meshgrid(xi, yi)

        self.ax.scatter(self.edge_plot_points[0], self.edge_plot_points[1], self.edge_plot_points[2], c='orange', marker='.')
        self.ax.scatter(self.input_plot_points[0], self.input_plot_points[1], self.input_plot_points[2], c='black', marker='.')

        if self.shape == Interpolator.LINE:
            z_intercept = Interpolator.XY_PLANE.intersection(Line(self.linear_range))[0]
            self.plot_point(z_intercept, 'black', '.')
            self.plot_segment(Segment(z_intercept, self.linear_range.p2), 'grey', '--', 0.5)
            self.plot_segment(Segment(z_intercept, self.input_point), 'grey', '--', 0.5)
        if self.shape == Interpolator.SURFACE:
            self.ax.plot_wireframe(XI, YI, self.surface(XI, YI), rstride=10, cstride=10, color='grey', linewidth=0.25)
            self.plot_point(self.output_point, 'red', 'o')
        plot.show(block=True)

    def show_interpolation_point(self):
        if self.input_point is None:
            return ValueError
        if self.ax is None:
            self.ax = plot.axes(projection="3d")
        self.plot_point(self.input_point, 'black', 'o')
        plot.show(block=False)
        plot.pause(0.001)
        return None

    def show_interpolated_point(self):
        if self.output_point is None:
            return ValueError
        if self.ax is None:
            self.ax = plot.axes(projection="3d")
        self.plot_point(self.output_point, 'red', 'o')
        self.plot_segment(Segment(self.input_point, self.output_point), 'black', '--', 0.25)
        plot.show(block=False)
        plot.pause(0.001)
        return None

    @staticmethod
    def close_plot():
        plot.close('all')

    def set_interpolation_point(self, pt: Point3D):
        if not isinstance(pt, Point3D):
            raise TypeError
        self.input_point = pt.scale(Interpolator.scale, Interpolator.scale, 1)

    def get_interpolated_point(self):
        if self.shape == Interpolator.SURFACE:
            self.output_point = Point3D(self.input_point.x, self.input_point.y, self.surface(self.input_point.x, self.input_point.y).tolist())
        elif self.shape == Interpolator.LINE:
            self.output_point = Line(self.linear_range).projection(self.input_point)
        return self.output_point.scale(1/Interpolator.scale, 1/Interpolator.scale, 1)

    def __init__(self, *points):
        self.input_point = self.output_point = self.shape = self.linear_range = None
        self.input_plot_points = self.edge_plot_points = self.x_limits = self.y_limits = None
        self.ax = self.surface = None
        self.initialize([*points][0])

    def initialize(self, pts: Point3D):
        if len(pts) < 2:
            raise ValueError
        for pt in pts:
            if not isinstance(pt, Point3D):
                raise TypeError

        if len(pts) == 2:
            self.shape = Interpolator.LINE
        else:
            self.shape = Interpolator.SURFACE

        scaled_point_list = [pt.scale(Interpolator.scale, Interpolator.scale, 1) for pt in pts]
        closed_figure = scaled_point_list + [scaled_point_list[0]]
        segments = [Segment(pt, closed_figure[index+1]) for index, pt in enumerate(closed_figure[:-1])]
        self.linear_range = segments[0]
        ss = step_size(segments)
        edge_point_array = edge_points(segments, ss)

        figure_point_array = np.array(scaled_point_list).astype(float)
        self.input_plot_points = [figure_point_array[:, 0], figure_point_array[:, 1], figure_point_array[:, 2]]
        self.edge_plot_points = [edge_point_array[:, 0], edge_point_array[:, 1], edge_point_array[:, 2]]
        self.x_limits = [int(round(self.input_plot_points[0].min(), 0)), int(round(self.input_plot_points[0].max(), 0))]
        self.y_limits = [int(round(self.input_plot_points[1].min(), 0)), int(round(self.input_plot_points[1].max(), 0))]

        if self.shape == Interpolator.SURFACE:
            self.surface = Rbf(self.edge_plot_points[0], self.edge_plot_points[1], self.edge_plot_points[2], function='thin_plate', smooth=100.0)


class CubicSplineFrame(DataFrame):
    def __init__(self, x: Series | np.ndarray | list, y: Series | np.ndarray | list, spline_x: Series | np.ndarray | list):

        if not x.is_unique:
            raise DuplicateValues(f'Duplicate x values')
        if not x.is_monotonic_increasing:
            raise NonMonotonic(f'x values not monotonic')
        if len(x) != len(y):
            raise LengthMismatch(f'x series and y series have different lengths')

        cs = CubicSpline(x, y)
        super().__init__(DataFrame({x.name: spline_x, y.name: cs(spline_x)}))

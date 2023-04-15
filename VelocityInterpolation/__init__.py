import numpy as np
from sympy.geometry import Point, Line, Segment, Plane
from sympy import symbols

from scipy.interpolate import RBFInterpolator, Rbf
from matplotlib import pyplot as plot

# noinspection PyArgumentList
class Interpolator:

    scale = 1000
    mesh_density = 300
    LINE = 'LINE'
    SURFACE = 'SURFACE'
    XY_PLANE = Plane(Point(0, 0, 0), normal_vector=[0, 0, 1])

    @staticmethod
    def __step_size(segments): return np.array([s.length for s in segments]).min()/10

    @staticmethod
    def __edge_points(segments, ss):
        t = symbols('t')
        edge_points = []
        for segment in segments:
            num_pts = range(1, int(round(segment.length / ss, 0)))
            edge_points += [segment.arbitrary_point(t).evalf(subs={t: pt*ss/segment.length}) for pt in num_pts]
        return np.array(edge_points).astype(float)

    def __plot_segment(self, segment: Segment, color: str, style: str, weight: float):
        points = np.array(segment.points).astype(float)
        self.ax.plot3D(points[:, 0], points[:, 1], points[:, 2], c=color, linestyle=style, linewidth=weight)

    def __plot_point(self, point: Point, color: str, mark: str):
        self.ax.scatter(point.x, point.y, point.z, c=color, marker=mark)

    def show_plot(self):
        xi = np.linspace(min(self.x_limits), max(self.x_limits), Interpolator.mesh_density)
        yi = np.linspace(min(self.y_limits), max(self.y_limits), Interpolator.mesh_density)
        XI, YI = np.meshgrid(xi, yi)

        self.ax = plot.axes(projection="3d")
        self.ax.scatter(self.edge_plot_points[0], self.edge_plot_points[1], self.edge_plot_points[2], c='orange', marker='.')
        self.ax.scatter(self.input_plot_points[0], self.input_plot_points[1], self.input_plot_points[2], c='black', marker='.')

        if self.shape == Interpolator.LINE:
            z_intercept = Interpolator.XY_PLANE.intersection(Line(self.linear_range))[0]
            self.__plot_point(z_intercept, 'black', '.')
            self.__plot_segment(Segment(z_intercept, self.linear_range.p2), 'grey', '--', 0.5)
            self.__plot_segment(Segment(z_intercept, self.input_point), 'grey', '--', 0.5)
        if self.shape == Interpolator.SURFACE:
            self.ax.plot_wireframe(XI, YI, self.surface(XI, YI), rstride=10, cstride=10, color='grey', linewidth=0.25)

        self.__plot_segment(Segment(self.input_point, self.output_point), 'grey', '--', 0.5)
        self.__plot_point(self.output_point, 'red', 'o')
        plot.show(block=False)
        plot.pause(0.001)

    def get_velocity(self, point: Point):
        if not isinstance(point, Point): raise TypeError
        self.input_point = point
        if self.shape == Interpolator.SURFACE:
            self.output_point = Point(point.x, point.y, self.surface(point.x, point.y).tolist()).evalf()
        elif self.shape == Interpolator.LINE:
            self.output_point = Line(self.linear_range).projection(point)
        return self.output_point

    def __init__(self, *points):
        self.input_point = self.output_point = self.shape = self.linear_range = None
        self.input_plot_points = self.edge_plot_points = self.x_limits = self.y_limits = None
        self.ax = self.surface = None
        self.initialize(points)

    def initialize(self, points):
        if len(points) < 2: raise ValueError
        for pt in points:
            if not isinstance(pt, Point): raise TypeError

        if len(points) == 2:
            self.shape = Interpolator.LINE
        else:
            self.shape = Interpolator.SURFACE

        scaled_point_list = [pt.scale(Interpolator.scale, Interpolator.scale, 1) for pt in points]
        closed_figure = scaled_point_list + [scaled_point_list[0]]
        segments = [Segment(pt, closed_figure[index+1]) for index, pt in enumerate(closed_figure[:-1])]
        self.linear_range = segments[0]
        ss = self.__step_size(segments)
        edge_point_array = self.__edge_points(segments, ss)

        figure_point_array = np.array(scaled_point_list).astype(float)
        self.input_plot_points = [figure_point_array[:, 0], figure_point_array[:, 1], figure_point_array[:, 2]]
        self.edge_plot_points = [edge_point_array[:, 0], edge_point_array[:, 1], edge_point_array[:, 2]]
        self.x_limits = [int(round(self.input_plot_points[0].min(), 0)), int(round(self.input_plot_points[0].max(), 0))]
        self.y_limits = [int(round(self.input_plot_points[1].min(), 0)), int(round(self.input_plot_points[1].max(), 0))]

        if self.shape == Interpolator.SURFACE:
            self.surface = Rbf(self.edge_plot_points[0], self.edge_plot_points[1], self.edge_plot_points[2], function='thin_plate', smooth=100.0)

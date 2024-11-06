from sympy import Point
from tt_interpolation.velocity_interpolation import Interpolator as VInt
from tt_job_manager.job_manager import Job


class InterpolatedPoint:

    def __init__(self, interpolation_pt_data, surface_points, date_index):
        interpolator = VInt(surface_points)
        interpolator.set_interpolation_point(Point(interpolation_pt_data[1], interpolation_pt_data[2], 0))
        self.date_velocity = tuple([date_index, round(interpolator.get_interpolated_point().z.evalf(), 4)])


class InterpolatePointJob(Job):

    def execute(self): return super().execute()
    def execute_callback(self, result): return super().execute_callback(result)
    def error_callback(self, result): return super().error_callback(result)

    def __init__(self, interpolation_pt, velocity_data, index):

        date_indices = velocity_data[0]['date_index']

        result_key = str(id(interpolation_pt)) + '_' + str(index)
        interpolation_pt_data = tuple([interpolation_pt.unique_name, interpolation_pt.lat, interpolation_pt.lon])
        surface_points = tuple([Point(frame.at[index, 'lat'], frame.at[index, 'lon'], frame.at[index, 'velocity']) for frame in velocity_data])
        arguments = tuple([interpolation_pt_data, surface_points, date_indices[index]])
        super().__init__(str(index) + ' ' + interpolation_pt.unique_name, result_key, InterpolatedPoint, arguments)

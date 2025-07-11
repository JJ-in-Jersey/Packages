import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from scipy.signal import savgol_filter
from sympy import Point

from tt_dataframe.dataframe import DataFrame
from tt_gpx.gpx import Route, Waypoint, Segment
from tt_job_manager.job_manager import Job
from tt_globals.globals import PresetGlobals as pg
from tt_date_time_tools.date_time_tools import hours_mins
from tt_geometry.geometry import Arc, StartArc, EndArc
from tt_interpolation.interpolation import Interpolator as VInt


class InterpolatedPoint:

    def __init__(self, interpolation_pt_data, lats, lons, vels):
        num_points = range(len(vels))
        surface_points = tuple([Point(lats[i], lons[i], vels[i]) for i in num_points])
        interpolator = VInt(surface_points)
        interpolator.set_interpolation_point(Point(interpolation_pt_data[1], interpolation_pt_data[2], 0))
        interpolated_velocity = np.round(float(interpolator.get_interpolated_point().z.evalf()), 2)
        self.velocity = interpolated_velocity


class InterpolatePointJob(Job):

    def execute(self): return super().execute()

    def execute_callback(self, result): return super().execute_callback(result)
    def error_callback(self, result): return super().error_callback(result)

    def __init__(self, interpolated_pt: Waypoint, lats: list, lons: list, velos: list, timestamp: int, index: int):
        interpolated_pt_data = tuple([interpolated_pt.name, interpolated_pt.lat, interpolated_pt.lon])
        arguments = tuple([interpolated_pt_data, lats, lons, velos])
        super().__init__(str(index) + ' ' + str(timestamp), timestamp, InterpolatedPoint, arguments)


class ElapsedTimeFrame(DataFrame):

    @staticmethod
    def distance(water_vf, water_vi, boat_speed, ts_in_hr):
        dist = ((water_vf + water_vi) / 2 + boat_speed) * ts_in_hr  # distance is nm
        return dist

    #  Elapsed times are reported in number of timesteps
    @staticmethod
    def elapsed_time(distances, length):
        csum = 0
        index = 0
        while csum < length and index < len(distances):
            csum += distances[index]
            index += 1
        if index > len(distances):
            return None
        else:
            return index - 1

    def __init__(self, start_path: Path, end_path: Path, length: float, speed: int, name: str):

        if not start_path.exists() or not end_path.exists():
            raise FileExistsError

        start_frame = DataFrame(csv_source=start_path)
        end_frame = DataFrame(csv_source=end_path)

        if not len(start_frame) == len(end_frame):
            raise ValueError
        if not start_frame.stamp.equals(end_frame.stamp):
            raise ValueError
        if not start_frame.Time.equals(end_frame.Time):
            raise ValueError

        dist = self.distance(end_frame.Velocity_Major.to_numpy()[1:], start_frame.Velocity_Major.to_numpy()[:-1], speed, pg.timestep / 3600)
        dist = dist * np.sign(speed)  # make sure distances are positive in the direction of the current
        timesteps = [timestep for timestep in [self.elapsed_time(dist[i:], length) for i in range(len(dist))] if timestep is not None]
        timesteps.insert(0, 0)  # initial time 0 has no displacement

        frame = DataFrame(data={'stamp': start_frame.stamp, 'Time': pd.to_datetime(start_frame.Time, utc=True)})
        frame[name] = timesteps
        super().__init__(data=frame)


class ElapsedTimeJob(Job):  # super -> job name, result key, function/object, arguments

    def execute(self): return super().execute()
    def execute_callback(self, result): return super().execute_callback(result)
    def error_callback(self, result): return super().error_callback(result)

    def __init__(self, seg: Segment, speed: int):

        node = seg.start
        node_path = node.folder.joinpath(Waypoint.velocity_csv_name)
        while not node_path.exists():
            node = node.next_edge.end
            node_path = node.folder.joinpath(Waypoint.velocity_csv_name)
        start_path = node_path

        node = seg.end
        node_path = node.folder.joinpath(Waypoint.velocity_csv_name)
        while not node_path.exists():
            node = node.prev_edge.start
            node_path = node.folder.joinpath(Waypoint.velocity_csv_name)
        end_path = node_path

        job_name = f'{speed} {seg.name}'
        result_key = job_name
        arguments = tuple([start_path, end_path, seg.length, speed, seg.name])
        super().__init__(job_name, result_key, ElapsedTimeFrame, arguments)


class TimeStepsFrame(DataFrame):

    @staticmethod
    def total_transit_timesteps(init_row: int, ets_values: np.ndarray, array_indices: list):
        max_row = len(ets_values) - 1
        transit_time = 0
        for idx in array_indices:
            row = int(transit_time) + init_row
            if row > max_row:
                break
            transit_time += ets_values[row, idx]
        return transit_time

    def __init__(self, elapsed_timesteps_frame: DataFrame, time_steps_path: Path):

        if time_steps_path.exists():
            super().__init__(data=DataFrame(csv_source=time_steps_path))
            self.Time = pd.to_datetime(self.Time, utc=True)
        else:
            indices = [elapsed_timesteps_frame.columns.get_loc(c) for c in elapsed_timesteps_frame.columns.to_list() if Segment.prefix in c]
            values = elapsed_timesteps_frame.values
            transit_timesteps_arr = [self.total_transit_timesteps(row, values, indices) for row in range(len(elapsed_timesteps_frame))]

            elapsed_timesteps_frame.drop(elapsed_timesteps_frame.columns[indices], axis=1, inplace=True)
            elapsed_timesteps_frame['t_time'] = pd.Series(transit_timesteps_arr)
            elapsed_timesteps_frame.write(time_steps_path)

            super().__init__(data=elapsed_timesteps_frame)


class TimeStepsJob(Job):

    def execute(self): return super().execute()
    def execute_callback(self, result): return super().execute_callback(result)
    def error_callback(self, result): return super().error_callback(result)

    def __init__(self, elapsed_times_frame: DataFrame, speed: int, route: Route):
        job_name = 'transit timesteps' + ' ' + str(speed)
        result_key = speed
        arguments = tuple([elapsed_times_frame, route.filepath('transit timesteps', speed)])
        super().__init__(job_name, result_key, TimeStepsFrame, arguments)


class SavGolFrame(DataFrame):

    savgol_size = 1100
    savgol_order = 1

    def __init__(self, timesteps_frame: DataFrame, savgol_path: Path):

        if savgol_path.exists():
            super().__init__(data=DataFrame(csv_source=savgol_path))
            self.Time = pd.to_datetime(self.Time, utc=True)
        else:
            # timesteps_frame['midline'] = savgol_filter(timesteps_frame.t_time, self.savgol_size, self.savgol_order).round().astype('int')
            timesteps_frame['midline'] = np.round(savgol_filter(timesteps_frame.t_time, self.savgol_size, self.savgol_order)).astype('int')

            timesteps_frame = timesteps_frame[timesteps_frame.t_time.ne(timesteps_frame.midline)].copy()  # remove values that equal the midline
            timesteps_frame.loc[timesteps_frame.t_time.lt(timesteps_frame.midline), 'GL'] = True  # less than midline = false
            timesteps_frame.loc[timesteps_frame.t_time.gt(timesteps_frame.midline), 'GL'] = False  # greater than midline => true
            timesteps_frame['block'] = (timesteps_frame['GL'] != timesteps_frame['GL'].shift(1)).cumsum()  # index the blocks of True and False
            timesteps_frame.write(savgol_path)
            super().__init__(data=timesteps_frame)


class SavGolJob(Job):

    def execute(self): return super().execute()
    def execute_callback(self, result): return super().execute_callback(result)
    def error_callback(self, result): return super().error_callback(result)

    def __init__(self, timesteps_frame: DataFrame, speed: int, route: Route):
        job_name = 'savitzky-golay midlines' + ' ' + str(speed)
        result_key = speed
        arguments = tuple([timesteps_frame, route.filepath('savgol', speed)])
        super().__init__(job_name, result_key, SavGolFrame, arguments)


class MinimaFrame(DataFrame):

    noise_threshold = 100

    # def __init__(self, transit_timesteps_path: Path, savgol_path: Path):
    def __init__(self, savgol_frame: DataFrame, minima_path: Path):

        if minima_path.exists():
            super().__init__(data=DataFrame(csv_source=minima_path))
            for col in [c for c in self.columns if 'time' in c]:
                self[col] = self[col].apply(pd.to_datetime)
        else:
            # create a list of minima frames (TF = True, below midline) and larger than the noise threshold
            blocks = [df.reset_index(drop=True).drop(labels=['GL', 'block', 'midline'], axis=1) for index, df in savgol_frame.groupby('block') if df['GL'].any() and len(df) > MinimaFrame.noise_threshold]

            frame = DataFrame(columns=['start_datetime', 'min_datetime', 'end_datetime', 'start_duration', 'min_duration', 'end_duration'])
            for i, df in enumerate(blocks):
                median_stamp = int(df[df.t_time == df.min().t_time]['stamp'].median())
                frame.at[i, 'start_utc'] = df.iloc[0].Time
                frame.at[i, 'min_utc'] = df.iloc[abs(df.stamp - median_stamp).idxmin()].Time
                frame.at[i, 'end_utc'] = df.iloc[-1].Time
                frame.at[i, 'start_duration'] = hours_mins(df.iloc[0].t_time * pg.timestep)
                frame.at[i, 'min_duration'] = hours_mins(df.iloc[abs(df.stamp - median_stamp).idxmin()].t_time * pg.timestep)
                frame.at[i, 'end_duration'] = hours_mins(df.iloc[-1].t_time * pg.timestep)

            # all eastern timezone rounded to 15 minutes
            frame.start_datetime = pd.to_datetime(frame.start_utc, utc=True).dt.tz_convert('US/Eastern').round('15min')  # type: ignore
            frame.min_datetime = pd.to_datetime(frame.min_utc, utc=True).dt.tz_convert('US/Eastern').round('15min')  # type: ignore
            frame.end_datetime = pd.to_datetime(frame.end_utc, utc=True).dt.tz_convert('US/Eastern').round('15min')  # type: ignore

            frame.drop(['start_utc', 'min_utc', 'end_utc'], axis=1, inplace=True)
            frame.write(minima_path)
            super().__init__(data=frame)


class MinimaJob(Job):  # super -> job name, result key, function/object, arguments

    def execute(self): return super().execute()
    def execute_callback(self, result): return super().execute_callback(result)
    def error_callback(self, result): return super().error_callback(result)

    def __init__(self, savgol_frame: DataFrame, speed: int, route: Route):
        job_name = 'minima' + ' ' + str(speed)
        result_key = speed
        arguments = tuple([savgol_frame, route.filepath('minima', speed)])
        super().__init__(job_name, result_key, MinimaFrame, arguments)


class ArcsFrame(DataFrame):

    def __init__(self, minima_frame: DataFrame, arc_path: Path, speed: int, first_day: datetime.date, last_day: datetime.date):

        if arc_path.exists():
            super().__init__(DataFrame(csv_source=arc_path))
            for col in [c for c in self.columns if 'time' in c]:
                self[col] = self[col].apply(pd.to_datetime)
        else:
            arcs = []
            for i, row in minima_frame.iterrows():
                row_dict = row.to_dict()
                try:
                    arc = Arc(**row_dict)
                    if arc.start_datetime.date() == arc.end_datetime.date():
                        if arc.total_angle != 0.0:
                            arcs.append(arc)
                    else:
                        arc = StartArc(**row_dict)
                        if arc.total_angle != 0.0:
                            arcs.append(arc)
                        arc = EndArc(**row_dict)
                        if arc.total_angle != 0.0:
                            arcs.append(arc)
                except Exception as err:
                    print(f'{err}')

            frame = DataFrame([arc.arc_dict for arc in arcs])
            frame.insert(0, 'date', frame.start_datetime.apply(lambda timestamp: timestamp.date()))
            frame.insert(0, 'start_time', frame.start_datetime.apply(lambda timestamp: timestamp.time()))
            frame.insert(0, 'min_time', frame.min_datetime.apply(lambda timestamp: timestamp.time()))
            frame.insert(0, 'end_time', frame.end_datetime.apply(lambda timestamp: timestamp.time()))
            frame = frame.sort_values(by=['date', 'start_datetime']).reset_index(drop=True)
            frame.insert(0, 'idx', frame.groupby('date').cumcount() + 1)
            frame.insert(1, 'speed', speed)

            eligible_dates = frame.groupby('date').filter(lambda x: len(x) >= 3)['date'].unique()
            start_mask = (frame['date'].isin(eligible_dates)) & (frame['start_angle'] == 0)
            end_mask = (frame['date'].isin(eligible_dates)) & (frame['end_angle'] == 0)
            frame.loc[start_mask, 'start_duration_display'] = False
            frame.loc[end_mask, 'end_duration_display'] = False

            min_mask = ((frame['start_angle'] == 0) & (frame['min_angle'] == 0)) | (
                        (frame['end_angle'] == 0) & (frame['min_angle'] == 0))
            frame.loc[min_mask, 'min_duration_display'] = False

            frame = frame[(frame['date'] >= first_day) & (frame['date'] <= last_day)]
            frame.reset_index(drop=True, inplace=True)

            frame.write(arc_path)
            super().__init__(frame)


class ArcsJob(Job):  # super -> job name, result key, function/object, arguments

    def execute(self): return super().execute()
    def execute_callback(self, result): return super().execute_callback(result)
    def error_callback(self, result): return super().error_callback(result)

    def __init__(self, minima_frame: DataFrame, route: Route, speed: int):
        job_name = 'arcs' + ' ' + str(speed)
        result_key = speed
        year = minima_frame.loc[0]['start_datetime'].year
        first_day_string = str(Route.template_dict['first_day'].substitute({'year': year}))
        last_day_string = str(Route.template_dict['last_day'].substitute({'year': year+2}))
        first_day = pd.to_datetime(first_day_string).date()
        last_day = pd.to_datetime(last_day_string).date()
        arguments = tuple([minima_frame, route.filepath('arcs', speed), speed, first_day, last_day])
        super().__init__(job_name, result_key, ArcsFrame, arguments)

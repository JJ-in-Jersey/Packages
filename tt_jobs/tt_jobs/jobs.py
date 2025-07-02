from numpy import sign, where, cumsum, ndarray
from pandas import to_datetime, Series
from pathlib import Path
from datetime import datetime
from scipy.signal import savgol_filter

from tt_dataframe.dataframe import DataFrame
from tt_gpx.gpx import Route, Waypoint, Segment
from tt_job_manager.job_manager import Job
from tt_globals.globals import PresetGlobals as pg
from tt_file_tools.file_tools import print_file_exists
from tt_date_time_tools.date_time_tools import hours_mins
from tt_geometry.geometry import Arc, StartArc, EndArc


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
        return index - 1

    def __init__(self, start_path: Path, end_path: Path, length: float, speed: int, name: str):

        if not start_path.exists() or not end_path.exists():
            raise FileExistsError

        start_frame = DataFrame(csv_source=start_path)
        end_frame = DataFrame(csv_source=end_path)

        if not len(start_frame) == len(end_frame):
            raise ValueError
        if not (start_frame.stamp == end_frame.stamp).all():
            raise ValueError
        if not (start_frame.Time == end_frame.Time).all():
            raise ValueError

        dist = self.distance(end_frame.Velocity_Major.to_numpy()[1:], start_frame.Velocity_Major.to_numpy()[:-1], speed, pg.timestep / 3600)
        dist = dist * sign(speed)  # make sure distances are positive in the direction of the current
        timesteps = [self.elapsed_time(dist[i:], length) for i in range(len(dist))]
        timesteps.insert(0,0)  # initial time 0 has no displacement

        frame = DataFrame(data={'stamp': start_frame.stamp, 'Time': to_datetime(start_frame.Time, utc=True)})
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
    def total_transit_timesteps(init_row: int, ets_values: ndarray, array_indices: list):
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
            self.Time = to_datetime(self.Time, utc=True)
        else:
            indices = [elapsed_timesteps_frame.columns.get_loc(c) for c in elapsed_timesteps_frame.columns.to_list() if Segment.prefix in c]
            values = elapsed_timesteps_frame.values
            transit_timesteps_arr = [self.total_transit_timesteps(row, values, indices) for row in range(len(elapsed_timesteps_frame))]

            elapsed_timesteps_frame.drop(elapsed_timesteps_frame.columns[indices], axis=1, inplace=True)
            elapsed_timesteps_frame['t_time'] = Series(transit_timesteps_arr)
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
            self.Time = to_datetime(self.Time, utc=True)
        else:
            timesteps_frame['midline'] = savgol_filter(timesteps_frame.t_time, self.savgol_size, self.savgol_order).round().astype('int')
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
                self[col] = self[col].apply(to_datetime)
        else:
            # create a list of minima frames (TF = True, below midline) and larger than the noise threshold
            blocks = [df.reset_index(drop=True).drop(labels=['GL', 'block', 'midline'], axis=1)
                  for index, df in savgol_frame.groupby('block') if df['GL'].any() and len(df) > MinimaFrame.noise_threshold]

            frame = DataFrame(columns=['start_time', 'min_time', 'end_time', 'start_duration', 'min_duration', 'end_duration'])
            for i, df in enumerate(blocks):
                median_stamp = df[df.t_time == df.min().t_time]['stamp'].median().astype(int)
                frame.at[i, 'start_utc'] = df.iloc[0].Time
                frame.at[i, 'min_utc'] = df.iloc[abs(df.stamp - median_stamp).idxmin()].Time
                frame.at[i, 'end_utc'] = df.iloc[-1].Time
                frame.at[i, 'start_duration'] = hours_mins(df.iloc[0].t_time * pg.timestep)
                frame.at[i, 'min_duration'] = hours_mins(df.iloc[abs(df.stamp - median_stamp).idxmin()].t_time * pg.timestep)
                frame.at[i, 'end_duration'] = hours_mins(df.iloc[-1].t_time * pg.timestep)

            # all eastern timezone rounded to 15 minutes, for now!
            frame.start_time =  to_datetime(frame.start_utc, utc=True).dt.tz_convert('US/Eastern').round('15min')
            frame.min_time = to_datetime(frame.min_utc, utc=True).dt.tz_convert('US/Eastern').round('15min')
            frame.end_time = to_datetime(frame.end_utc, utc=True).dt.tz_convert('US/Eastern').round('15min')

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
                self[col] = self[col].apply(to_datetime)
        else:
            arcs = []
            for i, row in minima_frame.iterrows():
                row_dict = row.to_dict()
                try:
                    arc = Arc(**row_dict)
                    if arc.start_time.date() == arc.end_time.date():
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
            frame.insert(0, 'date', frame.start_time.apply(lambda timestamp: timestamp.date()))
            frame = frame.sort_values(by=['date', 'start_time']).reset_index(drop=True)
            frame.insert(0, 'idx', frame.groupby('date').cumcount() + 1)
            frame.insert(1, 'speed', speed)

            frame = frame[(frame['date'] >= first_day) & (frame['date'] <= last_day)]
            frame.reset_index(drop=True, inplace=True)

            frame.write(arc_path)
            super().__init__(frame)

    # for col in ['start_round', 'min_round', 'end_round']:
    #     arcs_df['str_' + col] = None
    #     for row in range(len(arcs_df)):
    #         arcs_df.loc[row, 'str_' + col] = arcs_df.loc[row, col].strftime("%I:%M %p") if arcs_df.loc[row, col] is not None else None


class ArcsJob(Job):  # super -> job name, result key, function/object, arguments

    def execute(self): return super().execute()
    def execute_callback(self, result): return super().execute_callback(result)
    def error_callback(self, result): return super().error_callback(result)

    def __init__(self, minima_frame: DataFrame, route: Route, speed: int):
        job_name = 'arcs' + ' ' + str(speed)
        result_key = speed
        year = minima_frame.loc[0]['start_time'].year
        first_day = to_datetime(Route.template_dict['first_day'].substitute({'year': year})).date()
        last_day = to_datetime(Route.template_dict['last_day'].substitute({'year': year+2})).date()
        arguments = tuple([minima_frame, route.filepath('arcs', speed), speed, first_day, last_day])
        super().__init__(job_name, result_key, ArcsFrame, arguments)

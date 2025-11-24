import pandas as pd
import numpy as np
from pathlib import Path
from datetime import date, datetime
from os import remove
from scipy.signal import savgol_filter
from sympy import Point

from tt_dataframe.dataframe import DataFrame
from tt_gpx.gpx import Route, Waypoint, Segment
from tt_job_manager.job_manager import Job
import tt_globals.globals as fc_globals
from tt_date_time_tools.date_time_tools import hours_mins
from tt_geometry.geometry import Arc, StartArc, EndArc
from tt_interpolation.interpolation import Interpolator as VInt, CubicSplineFrame
from tt_noaa_data.noaa_data import SixteenMonths

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
        arguments = [interpolated_pt_data, lats, lons, velos]
        super().__init__(str(index) + ' ' + str(timestamp), timestamp, InterpolatedPoint, arguments, {})

class SplineCSV:

    _metadata = ['message']

    def __init__(self, year: int, waypoint: Waypoint):
        self.id = waypoint.id

        try:
            stamp_step = 60  # timestamps in seconds so steps of one minute is 60
            start_stamp = int(datetime(year=year - 1, month=11, day=1).timestamp())
            end_stamp = int(datetime(year=year + 1, month=3, day=1).timestamp())
            stamps = [start_stamp + i * stamp_step for i in range(int((end_stamp - start_stamp)/stamp_step))]

            input_frame = DataFrame(csv_source=waypoint.adjusted_csv_path)
            cs_frame = CubicSplineFrame(input_frame.stamp, input_frame.Velocity_Major, stamps)
            cs_frame['Time'] = pd.to_datetime(cs_frame.stamp, unit='s').dt.tz_localize('UTC')
            cs_frame['Velocity_Major'] = cs_frame.Velocity_Major.round(2)
            cs_frame.write(waypoint.velocity_csv_path)
            remove(waypoint.adjusted_csv_path)
        except Exception as e:
            self.message = f'<!> {waypoint.id} {type(e).__name__}'

class SplineJob(Job):  # super -> job name, result key, function/object, arguments

    def execute(self): return super().execute()
    def execute_callback(self, result): return super().execute_callback(result)
    def error_callback(self, result): return super().error_callback(result)

    def __init__(self, year: int, waypoint: Waypoint):
        result_key = id(waypoint.id)
        arguments = tuple([year, waypoint])
        super().__init__(waypoint.id + ' ' + waypoint.name, result_key, SplineCSV, arguments, {})

class RequestVelocityCSV:

    _metadata = ['message']

    def __init__(self, year: int, waypoint: Waypoint):
        self.id = waypoint.id

        if waypoint.type == "H":
            path = waypoint.velocity_csv_path
        elif waypoint.type == 'S':
            path = waypoint.adjusted_csv_path
        else:
            raise TypeError

        if not path.exists():
            sixteen_months = SixteenMonths(year, waypoint)
            sixteen_months.write(path)

class RequestVelocityJob(Job):  # super -> job name, result key, function/object, arguments
    def execute(self): return super().execute()
    def execute_callback(self, result): return super().execute_callback(result)
    def error_callback(self, result): return super().error_callback(result)

    def __init__(self, year, waypoint: Waypoint):
        result_key = waypoint.id
        arguments = tuple([year, waypoint])
        super().__init__(waypoint.id + ' ' + waypoint.name, result_key, RequestVelocityCSV, arguments, {})

class ElapsedTimeFrame(DataFrame):
    # Create a dataframe of elapsed time, in timesteps, to get from the begining to the end of the segment at the starting time
    # departure_time, number of timesteps to end of segment

    _metadata = ['message']

    @staticmethod
    def distance(water_vf, water_vi, boat_speed, ts_in_hr):
        dist = ((water_vf + water_vi) / 2 + boat_speed) * ts_in_hr  # distance is nm
        return dist

    @staticmethod
    def average_velocity(water_vf, water_vi):
        return (water_vf + water_vi) / 2

    #  Elapsed times are reported in number of timesteps
    @staticmethod
    def elapsed_time(distances, length):
        cum_sum = 0
        index = 0
        while cum_sum < length and index < len(distances):
            cum_sum += distances[index]
            index += 1
        if index > len(distances):
            return None
        else:
            return [index - 1, cum_sum - length]

    @classmethod
    def frame(cls, start_path: Path, end_path: Path, length: float, speed: int, name: str):

        if not start_path.exists() or not end_path.exists():
            raise FileExistsError

        sf = DataFrame(csv_source=start_path)
        ef = DataFrame(csv_source=end_path)

        if not len(sf) == len(ef) or not sf.stamp.equals(ef.stamp) or not sf.Time.equals(ef.Time):
            raise ValueError

        dist = ElapsedTimeFrame.distance(ef.Velocity_Major.to_numpy()[1:], sf.Velocity_Major.to_numpy()[:-1], speed, fc_globals.TIMESTEP / 3600)
        dist = dist * np.sign(speed)  # if the sign(dist) == sign(speed), dist+, else dist-
        av = ElapsedTimeFrame.average_velocity(ef.Velocity_Major.to_numpy()[1:], sf.Velocity_Major.to_numpy()[:-1])
        fair_current_flag = (av * speed) > 0  # no opposing current flag, all average current directions match speed direction
        fair_current_flag = fair_current_flag.tolist()
        timestep_and_error = [ElapsedTimeFrame.elapsed_time(dist[i:], length) for i in range(len(dist))]

        frame = DataFrame(data={'stamp': sf.stamp[:-1], 'Time': pd.to_datetime(sf.Time[:-1], utc=True)})
        frame['date'] = frame['Time'].dt.date
        frame[name + ' timesteps'] = [t[0] for t in timestep_and_error]
        frame[name + ' error'] = [round(t[1], 4) for t in timestep_and_error]
        frame[name + ' faircurrent'] = fair_current_flag

        return cls(frame, num_dates=frame.date.nunique())

    def __init__(self, *args, **kwargs):
        num_dates = kwargs.pop('num_dates', None)
        super().__init__(*args, **kwargs)
        if num_dates is None:
            num_dates = self.date.nunique()
        self.message = f'# utc dates: {num_dates}'

class ElapsedTimeJob(Job):  # super -> job name, result key, function/object, arguments

    def execute(self): return super().execute()
    def execute_callback(self, result): return super().execute_callback(result)
    def error_callback(self, result): return super().error_callback(result)

    def __init__(self, seg: Segment, speed: int):

        filepath = Route.filepath(ElapsedTimeFrame, speed)
        job_name = f'{speed} {seg.name}'
        result_key = seg.name

        if filepath.exists():
            super().__init__(job_name, result_key, ElapsedTimeFrame, [], {'csv_source': filepath})
        else:
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
    
            arguments = [start_path, end_path, seg.length, speed, seg.name]
            super().__init__(job_name, result_key, ElapsedTimeFrame.frame, arguments, {})

# noinspection PyTypeChecker
class TimeStepsFrame(DataFrame):

    write_flag = True
    _metadata = ['message']

    @classmethod
    def frame(cls, et_frame: DataFrame) -> DataFrame:

        frame = DataFrame()
        frame['stamp'] = et_frame['stamp']
        frame['Time'] = et_frame['Time']
        frame['Time'] = pd.to_datetime(frame.Time, utc=True)
        frame['date'] = frame['Time'].dt.date

        # simple_frame = DataFrame()
        # simple_frame['stamp'] = et_frame['stamp']
        # simple_frame['Time'] = et_frame['Time']

        seg_cols = [c for c in et_frame.columns.to_list() if Segment.prefix in c]
        timestep_cols = [c for c in seg_cols if 'timesteps' in c]
        error_cols = [c for c in seg_cols if 'error' in c]
        faircurrent_cols = [c for c in seg_cols if 'faircurrent' in c]
        triple_column = list(zip(timestep_cols, error_cols, faircurrent_cols))

        for c in seg_cols:
            frame[c] = pd.NA

        for stamp_index in range(len(frame)):
            row_index = stamp_index
            for ts_col, err_col, fc_col in triple_column:
                if pd.isna(row_index) or row_index < 0 or row_index >= len(et_frame):
                    ts = err = fc = pd.NA
                else:
                    ts = et_frame.at[int(row_index), ts_col]
                    err = et_frame.at[int(row_index), err_col]
                    fc = et_frame.at[int(row_index), fc_col]
                frame.at[stamp_index, ts_col] = ts
                frame.at[stamp_index, err_col] = err
                frame.at[stamp_index, fc_col] = fc
                row_index += int(ts) if pd.notna(ts) else pd.NA

        frame['t_time'] = frame[timestep_cols].sum(axis=1)
        frame['error'] = frame[error_cols].sum(axis=1)
        frame['faircurrent'] = frame[faircurrent_cols].all(axis=1)

        # simple_frame['t_time'] = frame[timestep_cols].sum(axis=1)
        # simple_frame['error'] = frame[error_cols].sum(axis=1)
        # simple_frame['faircurrent'] = frame[faircurrent_cols].all(axis=1)

        return cls(frame, num_dates=frame.date.nunique())

    def __init__(self, *args, **kwargs):
        num_dates = kwargs.pop('num_dates', None)
        super().__init__(*args, **kwargs)
        if num_dates is None:
            num_dates = self.date.nunique()
        self.message = f'# utc dates: {num_dates}'

class TimeStepsJob(Job):

    def execute(self): return super().execute()
    def execute_callback(self, result): return super().execute_callback(result)
    def error_callback(self, result): return super().error_callback(result)

    def __init__(self, frame: DataFrame, speed: int):

        filepath = Route.filepath(TimeStepsFrame, speed)
        job_name = f'{TimeStepsFrame.__name__} {speed}'
        result_key = tuple([speed, filepath])

        if filepath.exists():
            super().__init__(job_name, result_key, ElapsedTimeFrame, [], {'csv_source': filepath})
        else:
            super().__init__(job_name, result_key, TimeStepsFrame.frame, [frame], {})

class SavGolFrame(DataFrame):

    savgol_size = 500
    savgol_order = 1
    write_flag = True
    _metadata = ['message']

    @classmethod
    def frame(cls, tt_frame: DataFrame):
        frame = tt_frame.copy()
        frame['midline'] = np.round(savgol_filter(frame.t_time, SavGolFrame.savgol_size, SavGolFrame.savgol_order)).astype('int')
        frame = frame[frame.t_time.ne(frame.midline)].copy()  # remove values that equal the midline
        frame.loc[frame.t_time.lt(frame.midline), 'GL'] = True  # less than midline = false
        frame.loc[frame.t_time.ge(frame.midline), 'GL'] = False  # greater than midline => true
        frame['block'] = (frame['GL'] != frame['GL'].shift(1)).cumsum()  # index the blocks of True and False
        frame['block_size'] = frame.groupby('block').transform('size')
        return cls(frame, num_blocks=frame.block.nunique(), num_dates=frame.date.nunique(), min_size=frame.block_size.min(), max_size=frame.block_size.max())


    def __init__(self, *args, **kwargs):
        num_blocks = kwargs.pop('num_blocks', None)
        num_dates = kwargs.pop('num_dates', None)
        min_size = kwargs.pop('min_size', None)
        max_size = kwargs.pop('max_size', None)
        super().__init__(*args, **kwargs)
        if num_dates is None:
            num_dates = self.date.nunique()
        if num_blocks is None:
            num_blocks = self.block.nunique()
        if min_size is None:
            min_size = self.block_size.min()
        if max_size is None:
            max_size = self.block_size.max()
        self.message = f'# utc dates: {num_dates},  # blocks: {num_blocks},  min_size: {min_size},  max_size: {max_size}'

class SavGolJob(Job):

    def execute(self): return super().execute()
    def execute_callback(self, result): return super().execute_callback(result)
    def error_callback(self, result): return super().error_callback(result)

    def __init__(self, frame: DataFrame, speed: int):
        filepath = Route.filepath(SavGolFrame, speed)
        job_name = f'{SavGolFrame.__name__} {speed}'
        result_key = tuple([speed, filepath])

        if filepath.exists():
            super().__init__(job_name, result_key, SavGolFrame, [], {'csv_source': filepath})
        else:
            super().__init__(job_name, result_key, SavGolFrame.frame, [frame], {})

class FairCurrentFrame(DataFrame):

    write_flag = True
    _metadata = ['message']

    @classmethod
    def frame(cls, ts_frame: DataFrame):
        frame = ts_frame.copy()
        frame['block'] = (frame['faircurrent'] != frame['faircurrent'].shift(1)).cumsum()
        frame['block_size'] = frame.groupby('block').transform('size')
        return cls(frame, num_blocks=frame.block.nunique(), num_dates=frame.date.nunique(), min_size=frame.block_size.min(), max_size=frame.block_size.max())

    def __init__(self, *args, **kwargs):
        num_blocks = kwargs.pop('num_blocks', None)
        num_dates = kwargs.pop('num_dates', None)
        min_size = kwargs.pop('min_size', None)
        max_size = kwargs.pop('max_size', None)
        super().__init__(*args, **kwargs)
        if num_dates is None:
            num_dates = self.date.nunique()
        if num_blocks is None:
            num_blocks = self.block.nunique()
        if min_size is None:
            min_size = self.block_size.min()
        if max_size is None:
            max_size = self.block_size.max()
        self.message = f'# utc dates: {num_dates},  # blocks: {num_blocks}, min_size: {min_size},  max_size: {max_size}'

class FairCurrentJob(Job):

    def execute(self): return super().execute()
    def execute_callback(self, result): return super().execute_callback(result)
    def error_callback(self, result): return super().error_callback(result)

    def __init__(self, frame: DataFrame, speed: int):
        filepath = Route.filepath(FairCurrentFrame, speed)
        job_name = f'{FairCurrentFrame.__name__} {speed}'
        result_key = tuple([speed, filepath])

        if filepath.exists():
            super().__init__(job_name, result_key, FairCurrentFrame, [], {'csv_source': filepath})
        else:
            super().__init__(job_name, result_key, FairCurrentFrame.frame, [frame], {})

class SavGolMinimaFrame(DataFrame):

    noise_threshold = 100
    write_flag = True
    _metadata = ['message']

    @classmethod
    def frame(cls, sg_frame: DataFrame):

        # create a list of minima frames (TF = True, below midline) and larger than the noise threshold
        blocks = [df.reset_index(drop=True).drop(labels=['GL', 'midline'], axis=1) for index, df in sg_frame.groupby('block') if df['GL'].any() and len(df) > SavGolMinimaFrame.noise_threshold]
        frame = DataFrame(columns=['start_datetime', 'min_datetime', 'end_datetime', 'start_duration', 'min_duration', 'end_duration', 'block_size'])
        for i, df in enumerate(blocks):
            median_stamp = int(df[df.t_time == df.min().t_time]['stamp'].median())
            frame.at[i, 'start_utc'] = df.iloc[0].Time
            frame.at[i, 'min_utc'] = df.iloc[abs(df.stamp - median_stamp).idxmin()].Time
            frame.at[i, 'end_utc'] = df.iloc[-1].Time
            frame.at[i, 'start_duration'] = hours_mins(df.iloc[0].t_time * fc_globals.TIMESTEP)
            frame.at[i, 'min_duration'] = hours_mins(
                df.iloc[abs(df.stamp - median_stamp).idxmin()].t_time * fc_globals.TIMESTEP)
            frame.at[i, 'end_duration'] = hours_mins(df.iloc[-1].t_time * fc_globals.TIMESTEP)
            frame.at[i, 'block_size'] = len(df)

        frame['utc date'] = pd.to_datetime(frame.start_utc, utc=True).dt.date

        # round to 15 minutes, then convert to eastern time
        frame.start_datetime = pd.to_datetime(frame.start_utc, utc=True).dt.round('15min').dt.tz_convert('US/Eastern')
        frame.min_datetime = pd.to_datetime(frame.min_utc, utc=True).dt.round('15min').dt.tz_convert('US/Eastern')
        frame.end_datetime = pd.to_datetime(frame.end_utc, utc=True).dt.round('15min').dt.tz_convert('US/Eastern')
        frame.drop(['start_utc', 'min_utc', 'end_utc'], axis=1, inplace=True)
        frame['type'] = 'sg'
        return cls(frame, num_blocks=len(frame), num_dates=frame['utc date'].nunique(), min_size=frame.block_size.min(), max_size=frame.block_size.max())

    def __init__(self, *args, **kwargs):
        num_blocks = kwargs.pop('num_blocks', None)
        num_dates = kwargs.pop('num_dates', None)
        min_size = kwargs.pop('min_size', None)
        max_size = kwargs.pop('max_size', None)
        super().__init__(*args, **kwargs)
        if num_dates is None:
            num_dates = self['utc date'].nunique()
        if num_blocks is None:
            num_blocks = len(self)
        if min_size is None:
            min_size = self.block_size.min()
        if max_size is None:
            max_size = self.block_size.max()
        self.message = f'# utc dates: {num_dates},  # blocks: {num_blocks}, min_size: {min_size},  max_size: {max_size}'

class SavGolMinimaJob(Job):  # super -> job name, result key, function/object, arguments

    def execute(self): return super().execute()
    def execute_callback(self, result): return super().execute_callback(result)
    def error_callback(self, result): return super().error_callback(result)

    def __init__(self, frame: DataFrame, speed: int):
        filepath = Route.filepath(SavGolMinimaFrame, speed)
        job_name = f'{SavGolMinimaFrame.__name__} {speed}'
        result_key = tuple([speed, filepath])

        if filepath.exists():
            super().__init__(job_name, result_key, SavGolMinimaFrame, [], {'csv_source': filepath})
        else:
            super().__init__(job_name, result_key, SavGolMinimaFrame.frame, [frame], {})

class FairCurrentMinimaFrame(DataFrame):

    noise_threshold = 100
    write_flag = True
    _metadata = ['message']

    @classmethod
    def frame(cls, fc_frame: DataFrame):

        blocks = [df.reset_index(drop=True).drop(labels=['faircurrent'], axis=1) for index, df in fc_frame.groupby('block') if df['faircurrent'].any() and len(df) > FairCurrentMinimaFrame.noise_threshold]
        frame = DataFrame(columns=['start_datetime', 'min_datetime', 'end_datetime', 'start_duration', 'min_duration', 'end_duration', 'block_size'])
        for i, df in enumerate(blocks):
            median_stamp = int(df[df.t_time == df.min().t_time]['stamp'].median())
            frame.at[i, 'start_utc'] = df.iloc[0].Time
            frame.at[i, 'min_utc'] = df.iloc[abs(df.stamp - median_stamp).idxmin()].Time
            frame.at[i, 'end_utc'] = df.iloc[-1].Time
            frame.at[i, 'start_duration'] = hours_mins(df.iloc[0].t_time * fc_globals.TIMESTEP)
            frame.at[i, 'min_duration'] = hours_mins(
                df.iloc[abs(df.stamp - median_stamp).idxmin()].t_time * fc_globals.TIMESTEP)
            frame.at[i, 'end_duration'] = hours_mins(df.iloc[-1].t_time * fc_globals.TIMESTEP)
            frame.at[i, 'block_size'] = len(df)
        frame['utc date'] = pd.to_datetime(frame.start_utc, utc=True).dt.date

        # round to 15 minutes, then convert to eastern time
        frame.start_datetime = pd.to_datetime(frame.start_utc, utc=True).dt.round('15min').dt.tz_convert('US/Eastern')
        frame.min_datetime = pd.to_datetime(frame.min_utc, utc=True).dt.round('15min').dt.tz_convert('US/Eastern')
        frame.end_datetime = pd.to_datetime(frame.end_utc, utc=True).dt.round('15min').dt.tz_convert('US/Eastern')
        frame.drop(['start_utc', 'min_utc', 'end_utc'], axis=1, inplace=True)
        frame['type'] = 'fc'
        return cls(frame, num_blocks=len(frame), num_dates=frame['utc date'].nunique(), min_size=frame.block_size.min(), max_size=frame.block_size.max())

    def __init__(self, *args, **kwargs):
        num_blocks = kwargs.pop('num_blocks', None)
        num_dates = kwargs.pop('num_dates', None)
        min_size = kwargs.pop('min_size', None)
        max_size = kwargs.pop('max_size', None)
        super().__init__(*args, **kwargs)
        if num_dates is None:
            num_dates = self['utc date'].nunique()
        if num_blocks is None:
            num_blocks = len(self)
        if min_size is None:
            min_size = self.block_size.min()
        if max_size is None:
            max_size = self.block_size.max()
        self.message = f'# utc dates: {num_dates},  # blocks: {num_blocks},  min_size: {min_size},  max_size: {max_size}'

class FairCurrentMinimaJob(Job):  # super -> job name, result key, function/object, arguments

    def execute(self): return super().execute()
    def execute_callback(self, result): return super().execute_callback(result)
    def error_callback(self, result): return super().error_callback(result)

    def __init__(self, frame: DataFrame, speed: int):
            filepath = Route.filepath(FairCurrentMinimaFrame, speed)
            job_name = f'{FairCurrentMinimaFrame.__name__} {speed}'
            result_key = tuple([speed, filepath])

            if filepath.exists():
                super().__init__(job_name, result_key, FairCurrentMinimaFrame, [], {'csv_source': filepath})
            else:
                super().__init__(job_name, result_key, FairCurrentMinimaFrame.frame, [frame], {})

class ArcsFrame(DataFrame):
    write_flag = True
    _metadata = ['message']

    @staticmethod
    def hide_overlapping_durations(frame: DataFrame):

        threshold = 7.5
        frame['duplicate_suppressed'] = False
        grouped = frame.groupby('date')
        suppress_start_indices = {}
        suppress_end_indices = {}

        for date, group in grouped:
            # Get the 'fc' angles (both start and end) for the current date
            fc_angles = group[group['type'] == 'fc'][['start_angle', 'end_angle']].values.flatten().tolist()
            # Get the 'sg' rows (index and angles) for the current date
            sg_rows = group[group['type'] == 'sg']

            for fc_angle in fc_angles:
                for index, row in sg_rows.iterrows():
                    sg_angle_start = row['start_angle']
                    sg_angle_end = row['end_angle']
                    if row['start_duration_display']:
                        if abs(fc_angle - sg_angle_start) <= threshold:
                            suppress_start_indices[index] = True
                    if row['end_duration_display']:
                        if abs(fc_angle - sg_angle_end) <= threshold:
                            suppress_end_indices[index] = True
        start_indices = list(suppress_start_indices.keys())
        if start_indices:
            frame.loc[start_indices, 'start_duration_display'] = False
        end_indices = list(suppress_end_indices.keys())
        if end_indices:
            frame.loc[end_indices, 'end_duration_display'] = False
        final_suppression_mask = (frame['start_duration_display'] == False) | (frame['end_duration_display'] == False)
        frame.loc[final_suppression_mask, 'duplicate_suppressed'] = True

        return frame

    @classmethod
    def frame(cls, min_frame: DataFrame, speed: int, first_day: date, last_day: date):

        min_frame = min_frame.drop(labels=['block_size', 'utc date'], axis=1)
        arcs = []
        for i, row in min_frame.iterrows():
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
        frame.insert(0, 'min_time', frame.min_datetime.apply(lambda timestamp: timestamp.time() if not pd.isna(timestamp) else timestamp))
        frame.insert(0, 'end_time', frame.end_datetime.apply(lambda timestamp: timestamp.time()))
        frame = frame.sort_values(by=['date', 'type', 'start_datetime']).reset_index(drop=True)
        frame.insert(0, 'idx', frame.groupby(['date', 'type']).cumcount() + 1)
        frame['idx'] = frame['idx'].astype(str) + ' ' + frame['type']
        frame.insert(1, 'speed', speed)

        eligible_dates = frame.groupby('date').filter(lambda x: len(x) >= 3)['date'].unique()
        start_mask = (frame['date'].isin(eligible_dates)) & (frame['start_angle'] == 0)
        end_mask = (frame['date'].isin(eligible_dates)) & (frame['end_angle'] == 0)
        frame.loc[start_mask, 'start_duration_display'] = False
        frame.loc[end_mask, 'end_duration_display'] = False

        min_mask = ((frame['start_angle'] == 0) & (frame['min_angle'] == 0)) | (
                (frame['end_angle'] == 0) & (frame['min_angle'] == 0)) | (frame['type'] == 'sg')
        frame.loc[min_mask, 'min_duration_display'] = False
        frame = frame[(frame['date'] >= first_day) & (frame['date'] <= last_day)]
        frame.reset_index(drop=True, inplace=True)

        frame = ArcsFrame.hide_overlapping_durations(frame)

        return cls(frame, num_dates=frame['date'].nunique())

    def __init__(self, *args, **kwargs):
        num_dates = kwargs.pop('num_dates', None)
        super().__init__(*args, **kwargs)
        if num_dates is None:
            num_dates = self['date'].nunique()
        self.message = f'# dates: {num_dates}'
        
class ArcsJob(Job):  # super -> job name, result key, function/object, arguments

    def execute(self): return super().execute()
    def execute_callback(self, result): return super().execute_callback(result)
    def error_callback(self, result): return super().error_callback(result)

    def __init__(self, frame: DataFrame, speed: int):
            filepath = Route.filepath(ArcsFrame, speed)
            job_name = f'{ArcsFrame.__name__} {speed}'
            result_key = tuple([speed, filepath])

            year = pd.to_datetime(frame.loc[0]['start_datetime']).year
            first_day_string = str(fc_globals.TEMPLATES['first_day'].substitute({'year': year}))
            last_day_string = str(fc_globals.TEMPLATES['last_day'].substitute({'year': year + 2}))

            first_day = pd.to_datetime(first_day_string).date()
            last_day = pd.to_datetime(last_day_string).date()

            if filepath.exists():
                super().__init__(job_name, result_key, ArcsFrame, [], {'csv_source': filepath})
            else:
                super().__init__(job_name, result_key, ArcsFrame.frame, [frame, speed, first_day, last_day], {})

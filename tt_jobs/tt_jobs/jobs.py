import pandas as pd
import numpy as np
from pathlib import Path
from datetime import date
from scipy.signal import savgol_filter
from sympy import Point

from tt_dataframe.dataframe import DataFrame
from tt_gpx.gpx import Route, Waypoint, Segment
from tt_job_manager.job_manager import Job
import tt_globals.globals as fc_globals
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
        arguments = [interpolated_pt_data, lats, lons, velos]
        super().__init__(str(index) + ' ' + str(timestamp), timestamp, InterpolatedPoint, arguments, {})

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
        self.message = f'# of unique dates: {num_dates}'

class ElapsedTimeJob(Job):  # super -> job name, result key, function/object, arguments

    def execute(self): return super().execute()
    def execute_callback(self, result): return super().execute_callback(result)
    def error_callback(self, result): return super().error_callback(result)

    def __init__(self, seg: Segment, speed: int):

        filepath = Route.filepath(ElapsedTimeFrame, speed)
        job_name = f'{speed} {seg.name}'
        result_key = job_name

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

    _metadata = ['message']

    @classmethod
    def frame(cls, et_frame: DataFrame):

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
        self.message = f'# of unique dates: {num_dates}'

class TimeStepsJob(Job):

    def execute(self): return super().execute()
    def execute_callback(self, result): return super().execute_callback(result)
    def error_callback(self, result): return super().error_callback(result)

    def __init__(self, elapsed_times_frame: DataFrame, speed: int):

        filepath = Route.filepath(TimeStepsFrame, speed)
        job_name = f'{TimeStepsFrame.__name__}  {speed}'
        result_key = speed

        if filepath.exists():
            super().__init__(job_name, result_key, ElapsedTimeFrame, [], {'csv_source': filepath})
        else:
            super().__init__(job_name, result_key, TimeStepsFrame.frame, [elapsed_times_frame], {})


class SavGolFrame(DataFrame):

    savgol_size = 500
    savgol_order = 1

    def __init__(self, timesteps_frame: DataFrame, file_path: Path):

        if file_path.exists():
            super().__init__(csv_source=file_path)
        else:
            savgol_frame = timesteps_frame.copy()
            savgol_frame['midline'] = np.round(savgol_filter(savgol_frame.t_time, self.savgol_size, self.savgol_order)).astype('int')
            savgol_frame = savgol_frame[savgol_frame.t_time.ne(savgol_frame.midline)].copy()  # remove values that equal the midline
            savgol_frame.loc[savgol_frame.t_time.lt(savgol_frame.midline), 'GL'] = True  # less than midline = false
            savgol_frame.loc[savgol_frame.t_time.ge(savgol_frame.midline), 'GL'] = False  # greater than midline => true
            savgol_frame['sg_block'] = (savgol_frame['GL'] != savgol_frame['GL'].shift(1)).cumsum()  # index the blocks of True and False
            savgol_frame.write(file_path)
            super().__init__(data=savgol_frame)

class SavGolJob(Job):

    def execute(self): return super().execute()
    def execute_callback(self, result): return super().execute_callback(result)
    def error_callback(self, result): return super().error_callback(result)

    def __init__(self, timesteps_frame: DataFrame, speed: int, route: Route):
        job_name = SavGolFrame.__name__ + ' ' + str(speed)
        result_key = speed
        arguments = [timesteps_frame, route.filepath(SavGolFrame.__name__, speed)]
        super().__init__(job_name, result_key, SavGolFrame, arguments, [])

class FairCurrentFrame(DataFrame):

    def __init__(self, timesteps_frame: DataFrame, file_path: Path):

        if file_path.exists():
            super().__init__(csv_source=file_path)
        else:
            fc_frame = timesteps_frame.copy()
            fc_frame['fc_block'] = (fc_frame['faircurrent'] != fc_frame['faircurrent'].shift(1)).cumsum()  # index the blocks of True and False
            fc_frame.write(file_path)
            super().__init__(data=fc_frame)

class FairCurrentJob(Job):

    def execute(self): return super().execute()
    def execute_callback(self, result): return super().execute_callback(result)
    def error_callback(self, result): return super().error_callback(result)

    def __init__(self, timesteps_frame: DataFrame, speed: int, route: Route):
        job_name = FairCurrentFrame.__name__ + ' ' + str(speed)
        result_key = speed
        arguments = [timesteps_frame, route.filepath(FairCurrentFrame.__name__, speed)]
        super().__init__(job_name, result_key, FairCurrentFrame, arguments, [])

class SavGolMinimaFrame(DataFrame):

    noise_threshold = 100

    def __init__(self, sg_frame: DataFrame, file_path: Path):

        if file_path.exists():
            super().__init__(csv_source=file_path)
        else:
            # create a list of minima frames (TF = True, below midline) and larger than the noise threshold
            blocks = [df.reset_index(drop=True).drop(labels=['GL', 'sg_block', 'midline'], axis=1) for index, df in sg_frame.groupby('sg_block') if df['GL'].any() and len(df) > SavGolMinimaFrame.noise_threshold]

            frame = DataFrame(columns=['start_datetime', 'min_datetime', 'end_datetime', 'start_duration', 'min_duration',
                                       'end_duration'])
            for i, df in enumerate(blocks):
                median_stamp = int(df[df.t_time == df.min().t_time]['stamp'].median())
                frame.at[i, 'start_utc'] = df.iloc[0].Time
                frame.at[i, 'min_utc'] = df.iloc[abs(df.stamp - median_stamp).idxmin()].Time
                frame.at[i, 'end_utc'] = df.iloc[-1].Time
                frame.at[i, 'start_duration'] = hours_mins(df.iloc[0].t_time * fc_globals.TIMESTEP)
                frame.at[i, 'min_duration'] = hours_mins(
                    df.iloc[abs(df.stamp - median_stamp).idxmin()].t_time * fc_globals.TIMESTEP)
                frame.at[i, 'end_duration'] = hours_mins(df.iloc[-1].t_time * fc_globals.TIMESTEP)

            # round to 15 minutes, then convert to eastern time
            frame.start_datetime = pd.to_datetime(frame.start_utc, utc=True).dt.round('15min').dt.tz_convert('US/Eastern')
            frame.min_datetime = pd.to_datetime(frame.min_utc, utc=True).dt.round('15min').dt.tz_convert('US/Eastern')
            frame.end_datetime = pd.to_datetime(frame.end_utc, utc=True).dt.round('15min').dt.tz_convert('US/Eastern')

            frame.drop(['start_utc', 'min_utc', 'end_utc'], axis=1, inplace=True)
            frame['type'] = 'sg'
            frame.write(file_path)
            super().__init__(data=frame)

class SavGolMinimaJob(Job):  # super -> job name, result key, function/object, arguments

    def execute(self): return super().execute()
    def execute_callback(self, result): return super().execute_callback(result)
    def error_callback(self, result): return super().error_callback(result)

    def __init__(self, savgol_frame: DataFrame, speed: int, route: Route):
        job_name = SavGolMinimaFrame.__name__ + ' ' + str(speed)
        result_key = speed
        arguments = [savgol_frame, route.filepath(SavGolMinimaFrame.__name__, speed)]
        super().__init__(job_name, result_key, SavGolMinimaFrame, arguments, [])

class FairCurrentMinimaFrame(DataFrame):

    def __init__(self, fc_frame: DataFrame, file_path: Path):

        if file_path.exists():
            super().__init__(csv_source=file_path)
        else:
            # create a list of dataframe blocks for only those with a no opposing current (fair_current == True)
            blocks = [df.reset_index(drop=True).drop(labels=['faircurrent'], axis=1) for index, df in fc_frame.groupby('fc_block') if df['faircurrent'].all()]

            if len(blocks) > 0:
                frame = DataFrame(columns=['start_datetime', 'min_datetime', 'end_datetime', 'start_duration', 'min_duration', 'end_duration'])
                for i, df in enumerate(blocks):
                    median_stamp = int(df[df.t_time == df.min().t_time]['stamp'].median())
                    frame.at[i, 'start_utc'] = df.iloc[0].Time
                    frame.at[i, 'min_utc'] = df.iloc[abs(df.stamp - median_stamp).idxmin()].Time
                    frame.at[i, 'end_utc'] = df.iloc[-1].Time
                    frame.at[i, 'start_duration'] = hours_mins(df.iloc[0].t_time * fc_globals.TIMESTEP)
                    frame.at[i, 'min_duration'] = hours_mins(df.iloc[abs(df.stamp - median_stamp).idxmin()].t_time * fc_globals.TIMESTEP)
                    frame.at[i, 'end_duration'] = hours_mins(df.iloc[-1].t_time * fc_globals.TIMESTEP)

                # round to 15 minutes, then convert to eastern time
                frame.start_datetime = pd.to_datetime(frame.start_utc, utc=True).dt.round('15min').dt.tz_convert('US/Eastern')
                frame.min_datetime = pd.to_datetime(frame.min_utc, utc=True).dt.round('15min').dt.tz_convert('US/Eastern')
                frame.end_datetime = pd.to_datetime(frame.end_utc, utc=True).dt.round('15min').dt.tz_convert('US/Eastern')

                frame.drop(['start_utc', 'min_utc', 'end_utc'], axis=1, inplace=True)
                frame['type'] = 'fc'
                frame.write(file_path)
                super().__init__(data=frame)
            else:
                no_faircurrents = file_path.with_suffix('.no_faircurrents')
                no_faircurrents.touch()
                super().__init__()

class FairCurrentMinimaJob(Job):  # super -> job name, result key, function/object, arguments

    def execute(self): return super().execute()
    def execute_callback(self, result): return super().execute_callback(result)
    def error_callback(self, result): return super().error_callback(result)

    def __init__(self, fair_current_frame: DataFrame, speed: int, route: Route):
        job_name = FairCurrentMinimaFrame.__name__ + ' ' + str(speed)
        result_key = speed
        arguments = [fair_current_frame, route.filepath(FairCurrentMinimaFrame.__name__, speed)]
        super().__init__(job_name, result_key, FairCurrentMinimaFrame, arguments, [])

class ArcsFrame(DataFrame):

    def __init__(self, minima_frame: DataFrame, file_path: Path, speed: int, first_day: date, last_day: date):

        if file_path.exists():
            super().__init__(DataFrame(csv_source=file_path))
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
                        (frame['end_angle'] == 0) & (frame['min_angle'] == 0)) | (frame['type'] =='sg')
            frame.loc[min_mask, 'min_duration_display'] = False
            frame = frame[(frame['date'] >= first_day) & (frame['date'] <= last_day)]
            frame.reset_index(drop=True, inplace=True)
            frame.write(file_path)

            super().__init__(data=frame)

class ArcsJob(Job):  # super -> job name, result key, function/object, arguments

    def execute(self): return super().execute()
    def execute_callback(self, result): return super().execute_callback(result)
    def error_callback(self, result): return super().error_callback(result)

    def __init__(self, minima_frame: DataFrame, route: Route, speed: int):
        job_name = ArcsFrame.__name__ + ' ' + str(speed)
        result_key = speed
        year = pd.to_datetime(minima_frame.loc[0]['start_datetime']).year
        first_day_string = str(fc_globals.TEMPLATES['first_day'].substitute({'year': year}))
        last_day_string = str(fc_globals.TEMPLATES['last_day'].substitute({'year': year+2}))
        first_day = pd.to_datetime(first_day_string).date()
        last_day = pd.to_datetime(last_day_string).date()
        arguments = [minima_frame, route.filepath(ArcsFrame.__name__, speed), speed, first_day, last_day]
        super().__init__(job_name, result_key, ArcsFrame, arguments, [])

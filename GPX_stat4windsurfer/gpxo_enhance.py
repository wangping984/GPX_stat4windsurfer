import gpxo
import pandas as pd
import numpy as np
import pathlib
from timezonefinder import TimezoneFinder
from datetime import datetime
import pytz

def list_files_with_extension(directory_path, extension):
    """List all files with a specific extension in a given directory, including their full paths.

    Args:
        directory_path (str): The path to the directory to search.
        extension (str): The file extension to search for (e.g., 'gpx', 'txt').

    Returns:
        list: A list of full paths to files with the specified extension.
    """
    path = pathlib.Path(directory_path)
    return [str(f) for f in path.rglob(f'*.{extension}')]

class track_enhance(gpxo.Track):
    def __init__(self, track, planing_threshold=18, sample_time_interval_warn_threshold=3, sample_distance_warn_threshold = 15):
        super().__init__(track)
        self.planing_threshold = planing_threshold  # 滑行速度阈值，单位km/h
        self.sample_time_interval_warn_threshold = sample_time_interval_warn_threshold  # 采样间隔警告阈值，单位秒
        self.sample_distance_warn_threshold = sample_distance_warn_threshold # 采样距离间隔警告阈值，单位m
    
    def get_interpolated_data_1s(self):
        """返回1秒间隔线性插值后的DataFrame，索引为DatetimeIndex"""
        df = self.data.copy()
        # 确保索引为DatetimeIndex
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("数据索引不是DatetimeIndex，无法插值")
        # 1秒重采样并线性插值
        df_interp = df.resample('1s').interpolate('linear')
        return df_interp

    def fastest_in_window(self, seconds):
        """Calculate the maximum average speed over a specified time window.
        
        Args:
            seconds (int): The time window in seconds.
            
        Returns:
            float: Maximum average speed in km/h over the specified time window in the track.
        """
        # 用插值后的数据计算最大平均速度
        data = self.get_interpolated_data_1s()
        distances = data['distance (km)'].values
        time_index = data.index
        max_avg_speed = 0
        end_idx_previous = 1
        for start_idx in range(len(distances)):
            for end_idx in range(end_idx_previous, len(distances)):
                t0 = time_index[start_idx]
                t1 = time_index[end_idx]
                segment_time = (t1 - t0).total_seconds()
                if segment_time >= seconds:
                    segment_distance = distances[end_idx] - distances[start_idx]
                    segment_time_hr = segment_time / 3600
                    if segment_time_hr > 0:
                        avg_speed = segment_distance / segment_time_hr
                    else:
                        avg_speed = 0
                    if avg_speed > max_avg_speed:
                        max_avg_speed = avg_speed
                    end_idx_previous = end_idx
                    break
        return max_avg_speed
    
    def fastest_in_distance_window(self, dist_window):
        """Calculate the maximum average speed over a specified distance window.
        
        This function slides a distance window of specified length over the track and
        finds the segment with the highest average speed.
        
        Args:
            dist_window (float): The distance window in kilometers.
            
        Returns:
            float: Maximum average speed in km/h over the specified distance window in the track.
        """
        # 用插值后的数据计算最大平均速度
        data = self.get_interpolated_data_1s()
        distances = data['distance (km)'].values
        time_index = data.index
        max_avg_speed = 0
        end_idx_previous = 1
        for start_idx in range(len(distances)):
            for end_idx in range(end_idx_previous, len(distances)):
                segment_distance = distances[end_idx] - distances[start_idx]
                if segment_distance >= dist_window:
                    t0 = time_index[start_idx]
                    t1 = time_index[end_idx]
                    segment_time = (t1 - t0).total_seconds() / 3600
                    if segment_time > 0:
                        avg_speed = segment_distance / segment_time
                    else:
                        avg_speed = 0
                    if avg_speed > max_avg_speed:
                        max_avg_speed = avg_speed
                    end_idx_previous = end_idx
                    break
        return max_avg_speed
    
    def get_timezone(self):
        """根据GPS坐标获取时区
        
        Returns:
            str: 时区名称（如 'Asia/Shanghai'）
        """
        try:
            # 获取轨迹的第一个点的经纬度
            first_point = self.data.iloc[0]
            lat = first_point['latitude (°)']
            lon = first_point['longitude (°)']
            
            if pd.isna(lat) or pd.isna(lon):
                print("经纬度数据为空")
                return None
                
            # 使用TimezoneFinder获取时区
            tf = TimezoneFinder()
            timezone_str = tf.timezone_at(lat=float(lat), lng=float(lon))
            return timezone_str
        except Exception as e:
            print(f"获取时区时出错: {e}")
            return None

    def get_planing_stats(self):
        """计算滑行统计数据
        
        Returns:
            dict: 包含以下滑行统计信息：
                - planing_time_ratio: 滑行时间占比
                - planing_duration: 滑行总时长（秒）
                - planing_duration_formatted: 格式化的滑行时长
                - planing_distance: 滑行总距离（公里）
                - planing_distance_ratio: 滑行距离占比
                - planing_avg_speed: 滑行平均速度（km/h）
                - max_planing_distance: 最长滑行距离（公里）
        """
        try:
            # 获取速度数据和时间索引
            velocities = self.data['velocity (km/h)'].values
            distances = self.data['distance (km)'].values
            time_index = self.data.axes[0]
            
            if not hasattr(time_index, 'name') or time_index.name != 'time':
                raise ValueError("无法获取时间索引")
            
            # 计算实际时间间隔（秒）
            time_diffs = np.diff(time_index).astype('timedelta64[s]').astype(float)
            
            # 计算滑行时间
            planing_mask = velocities >= self.planing_threshold
            # 使用实际时间间隔计算滑行时间
            planing_duration = np.sum(time_diffs[planing_mask[:-1]])  # 使用[:-1]因为diff会减少一个元素
            total_duration = (time_index[-1] - time_index[0]).total_seconds()
            planing_time_ratio = planing_duration / total_duration if total_duration > 0 else 0
            
            # 格式化滑行时长
            hours, remainder = divmod(planing_duration, 3600)
            minutes, seconds = divmod(remainder, 60)
            duration_str = f"{int(hours)}h{int(minutes)}min{int(seconds)}s"
            
            # 计算滑行距离
            planing_distances = np.diff(distances)[planing_mask[:-1]]  # 使用[:-1]因为diff会减少一个元素
            planing_distance = np.sum(planing_distances)
            total_distance = distances[-1] - distances[0]
            planing_distance_ratio = planing_distance / total_distance if total_distance > 0 else 0
            
            # 计算滑行平均速度
            planing_avg_speed = np.mean(velocities[planing_mask]) if np.any(planing_mask) else 0
            
            # 计算最长滑行距离
            # 找到连续的滑行段
            planing_segments = []
            current_segment = []
            for i, is_planing in enumerate(planing_mask[:-1]):  # 使用[:-1]因为我们要看下一个点
                if is_planing:
                    current_segment.append(i)
                elif current_segment:
                    planing_segments.append(current_segment)
                    current_segment = []
            if current_segment:
                planing_segments.append(current_segment)
            
            # 计算每个滑行段的距离
            segment_distances = []
            for segment in planing_segments:
                if segment:
                    start_idx = segment[0]
                    end_idx = segment[-1] + 1  # +1 因为要包含最后一个点
                    segment_distance = distances[end_idx] - distances[start_idx]
                    segment_distances.append(segment_distance)
            
            max_planing_distance = max(segment_distances) if segment_distances else 0
            
            return {
                'planing_time_ratio': round(planing_time_ratio * 100, 2),  # 转换为百分比
                'planing_duration': round(planing_duration, 2),
                'planing_duration_formatted': duration_str,
                'planing_distance': round(planing_distance, 2),
                'planing_distance_ratio': round(planing_distance_ratio * 100, 2),  # 转换为百分比
                'planing_avg_speed': round(planing_avg_speed, 2),
                'max_planing_distance': round(max_planing_distance, 2)
            }
        except Exception as e:
            print(f"计算滑行统计时出错: {e}")
            return None

    def get_GPS_sample_stats(self):
        """分析轨迹采样点的时间间隔和距离间隔
        
        Returns:
            dict: 包含以下采样统计信息：
                - avg_interval: 平均采样时间间隔（秒）
                - min_interval: 最小采样时间间隔（秒）
                - max_interval: 最大采样时间间隔（秒）
                - avg_distance: 平均采样距离间隔（米）
                - min_distance: 最小采样距离间隔（米）
                - max_distance: 最大采样距离间隔（米）
        """
        try:
            # 从data.axes中获取时间索引
            time_index = self.data.axes[0]
            if hasattr(time_index, 'name') and time_index.name == 'time':
                # 计算相邻点之间的时间间隔（秒）
                time_diffs = np.diff(time_index).astype('timedelta64[s]').astype(float)
                
                # 使用现有的distance数据计算相邻点之间的距离间隔（米）
                distances_km = self.data['distance (km)'].values
                distance_diffs = np.diff(distances_km)  # 相邻点间的距离差（公里）
                distance_diffs_m = distance_diffs * 1000  # 转换为米
                
                return {
                    'avg_interval': round(np.mean(time_diffs), 2),
                    'min_interval': round(np.min(time_diffs), 2),
                    'max_interval': round(np.max(time_diffs), 2),
                    'avg_distance': round(np.mean(distance_diffs_m), 2),
                    'min_distance': round(np.min(distance_diffs_m), 2),
                    'max_distance': round(np.max(distance_diffs_m), 2)
                }
        except Exception as e:
            print(f"计算GPS采样统计时出错: {e}")
            return None

    @property
    def results(self):
        """获取轨迹的性能数据
        
        Returns:
            dict: 包含以下信息的字典：
                - basic_info: 基本信息（开始时间、总距离、总时长、最大速度、平均速度）
                - maxspeed_in_time_window: 基于时间窗口的最快速度
                - maxspeed_in_distance_window: 基于距离窗口的最快速度
                - speed_in_segments: 每公里段的平均速度
                - planing_stat: 滑行统计数据
                - GPS_sample_stats: 采样时间统计
                - warning: 警告信息
        """
        # 初始化basic_info字典
        basic_info = {}
        
        # 获取轨迹开始时间
        try:
            # 从data.axes中获取时间索引
            time_index = self.data.axes[0]
            if hasattr(time_index, 'name') and time_index.name == 'time':
                start_time = time_index[0]
                # 获取时区
                timezone_str = self.get_timezone()
                if timezone_str:
                    # 将UTC时间转换为当地时间
                    utc_time = start_time.replace(tzinfo=pytz.UTC)
                    local_tz = pytz.timezone(timezone_str)
                    local_time = utc_time.astimezone(local_tz)
                    formatted_start_time = local_time.strftime('%Y-%m-%d %H:%M:%S')
                    basic_info['start_time'] = {
                        'local_time': formatted_start_time,
                        'timezone': timezone_str
                    }
                else:
                    # 如果无法获取时区，则显示UTC时间
                    formatted_start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
                    basic_info['start_time'] = {
                        'utc_time': formatted_start_time
                    }
        except Exception as e:
            print(f"无法获取轨迹开始时间: {e}")
        
        # 获取总距离
        total_distance = self.data['distance (km)'].iloc[-1]
        basic_info['total_distance'] = round(total_distance, 2)
        
        # 获取总时长
        try:
            # 从data.axes中获取时间索引
            time_index = self.data.axes[0]
            if hasattr(time_index, 'name') and time_index.name == 'time':
                total_duration_seconds = (time_index[-1] - time_index[0]).total_seconds()
                hours, remainder = divmod(total_duration_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                duration_str = f"{int(hours)}h{int(minutes)}min{int(seconds)}s"
                basic_info['total_duration'] = {
                    'hours': int(hours),
                    'minutes': int(minutes),
                    'seconds': int(seconds),
                    'total_seconds': total_duration_seconds,
                    'formatted': duration_str
                }
        except Exception as e:
            print(f"无法计算总时长: {e}")
        
        # 获取最快速度
        max_speed = self.data['velocity (km/h)'].max()
        basic_info['max_speed'] = round(max_speed, 2)
        
        # 计算平均速度
        avg_speed = self.data['velocity (km/h)'].mean()
        basic_info['avg_speed'] = round(avg_speed, 2)
        
        # Calculate all the maximum average speeds for time windows
        maxspeed_in_time_window = {
            '2秒': self.fastest2s,
            '5秒': self.fastest5s,
            '10秒': self.fastest10s,
            '20秒': self.fastest20s,
            '30秒': self.fastest30s,
            '1分钟': self.fastest1min,
            '2分钟': self.fastest2min,
            '5分钟': self.fastest5min
        }
        
        # Calculate all the maximum average speeds for distance windows
        maxspeed_in_distance_window = {
            '50米': self.fastest_in_distance_window(0.05),
            '100米': self.fastest_in_distance_window(0.1),
            '200米': self.fastest_in_distance_window(0.2),
            '250米': self.fastest_in_distance_window(0.25),
            '500米': self.fastest_in_distance_window(0.5),
            '1公里': self.fastest_in_distance_window(1.0),
            '2公里': self.fastest_in_distance_window(2.0),
            '5公里': self.fastest_in_distance_window(5.0)
        }
        
        # Calculate average speed for each 1km segment
        speed_in_segments = self.avg_speed_in_segment(1.0)
        
        # 获取滑行统计数据
        planing_stat = self.get_planing_stats()
        
        # 获取采样时间统计
        GPS_sample_stats = self.get_GPS_sample_stats()
        
        # 检查是否需要添加警告
        warning = ''
        if GPS_sample_stats and GPS_sample_stats['max_interval'] > self.sample_time_interval_warn_threshold:
            warning = 'GPS采样时间间隔过长'
        if GPS_sample_stats and GPS_sample_stats['max_distance'] > self.sample_distance_warn_threshold:
            warning += ',GPS采样距离间隔过长'
        
        warning += '\n 请谨慎看待分析结果'
        
        # Combine results
        return {
            'basic_info': basic_info,
            'maxspeed_in_time_window': maxspeed_in_time_window,
            'maxspeed_in_distance_window': maxspeed_in_distance_window,
            'speed_in_segments': speed_in_segments,
            'planing_stat': planing_stat,
            'GPS_sample_stats': GPS_sample_stats,
            'warning': warning
        }
    
    def print_results(self):
        """打印轨迹的性能报告"""
        results = self.results
        basic_info = results['basic_info']
        
        print('--------------------------------')
        print('--------------------------------')
        
        # 打印基本信息
        if 'start_time' in basic_info:
            if 'local_time' in basic_info['start_time']:
                print(f"{basic_info['start_time']['local_time']}")
            else:
                print(f"{basic_info['start_time']['utc_time']}")
        
        print(f"Total Distance(km): {basic_info['total_distance']:.2f}")
        
        if 'total_duration' in basic_info:
            print(f"Total Duration: {basic_info['total_duration']['formatted']}")
        
        print(f"Max Speed(km/h): {basic_info['max_speed']:.2f}")
        print(f"Average Speed(km/h): {basic_info['avg_speed']:.2f}")
        
        # 打印采样时间统计
        if results['GPS_sample_stats']:
            stats = results['GPS_sample_stats']
            print(f"GPS采样时间间隔: 平均={stats['avg_interval']}s, 最小={stats['min_interval']}s, 最大={stats['max_interval']}s")
            print(f"GPS采样距离间隔: 平均={stats['avg_distance']}m, 最小={stats['min_distance']}m, 最大={stats['max_distance']}m")
        
        # 打印警告信息
        if results['warning']:
            print(f"警告: {results['warning']}")
            
        print("=======================")
        
        # 打印滑行统计信息
        planing_stat = results['planing_stat']
        print("滑行统计 (速度 >= {:.1f} km/h)".format(self.planing_threshold))
        print("-----------------------")
        print(f"滑行时间占比: {planing_stat['planing_time_ratio']}%")
        print(f"滑行总时长: {planing_stat['planing_duration_formatted']}")
        print(f"滑行总距离: {planing_stat['planing_distance']:.2f}公里")
        print(f"滑行距离占比: {planing_stat['planing_distance_ratio']}%")
        print(f"滑行平均速度: {planing_stat['planing_avg_speed']:.2f} km/h")
        print(f"最长滑行距离: {planing_stat['max_planing_distance']:.2f}公里")
        print("=======================")
        
        # 打印性能报告
        print("性能报告 - 最快平均速度")
        print("=======================")
        print("基于时间窗口:")
        for window, speed in results['maxspeed_in_time_window'].items():
            print(f"{window}:\t{speed:.2f} km/h")
        
        print("\n基于距离窗口:")
        for window, speed in results['maxspeed_in_distance_window'].items():
            print(f"{window}:\t{speed:.2f} km/h")
        
        print("\n每公里段平均速度:")
        for i, speed in enumerate(results['speed_in_segments']):
            print(f"第{i+1}公里:\t{speed:.2f} km/h")
        print("=======================")
    
    @property
    def fastest2s(self):
        """Calculate the maximum average speed over a 2-second window.
        
        Returns:
            float: Maximum average speed in km/h over any 2-second window in the track.
        """
        return self.fastest_in_window(2)
    
    @property
    def fastest5s(self):
        """Calculate the maximum average speed over a 5-second window.
        
        Returns:
            float: Maximum average speed in km/h over any 5-second window in the track.
        """
        return self.fastest_in_window(5)
    
    @property
    def fastest10s(self):
        """Calculate the maximum average speed over a 10-second window.
        
        Returns:
            float: Maximum average speed in km/h over any 10-second window in the track.
        """
        return self.fastest_in_window(10)
    
    @property
    def fastest20s(self):
        """Calculate the maximum average speed over a 20-second window.
        
        Returns:
            float: Maximum average speed in km/h over any 20-second window in the track.
        """
        return self.fastest_in_window(20)
    
    @property
    def fastest30s(self):
        """Calculate the maximum average speed over a 30-second window.
        
        Returns:
            float: Maximum average speed in km/h over any 30-second window in the track.
        """
        return self.fastest_in_window(30)
    
    @property
    def fastest1min(self):
        """Calculate the maximum average speed over a 1-minute window.
        
        Returns:
            float: Maximum average speed in km/h over any 1-minute window in the track.
        """
        return self.fastest_in_window(60)
    
    @property
    def fastest2min(self):
        """Calculate the maximum average speed over a 2-minute window.
        
        Returns:
            float: Maximum average speed in km/h over any 2-minute window in the track.
        """
        return self.fastest_in_window(120)
    
    @property
    def fastest5min(self):
        """Calculate the maximum average speed over a 5-minute window.
        
        Returns:
            float: Maximum average speed in km/h over any 5-minute window in the track.
        """
        return self.fastest_in_window(300)
        
    def avg_speed_in_segment(self, distance):
        """Calculate average speed for each segment of specified distance along the track.
        
        This function divides the track into segments of specified distance and calculates
        the average speed within each segment. The last segment may be shorter than the
        specified distance if the track length is not an exact multiple of the segment distance.
        
        Args:
            distance (float): The segment distance in kilometers.
            
        Returns:
            list: A list of average speeds (km/h) for each segment.
        """
        # Get the distance, velocity, and time data
        data = self.data[['distance (km)', 'velocity (km/h)']].copy()
        distances = data['distance (km)'].values
        velocities = data['velocity (km/h)'].values
        # 获取时间索引
        time_index = self.data.axes[0]
        
        speed_in_segments = []
        start_idx = 0
        total_distance = distances[-1]
        segment_count = int(np.ceil(total_distance / distance))
        
        for segment in range(segment_count):
            target_distance = min((segment + 1) * distance, total_distance)
            end_idx = start_idx
            while end_idx < len(distances) - 1 and distances[end_idx] < target_distance:
                end_idx += 1
            if end_idx >= start_idx:
                # 计算该段距离和时间
                segment_distance = distances[end_idx] - distances[start_idx]
                # 获取对应的时间（假设time_index为DatetimeIndex）
                t0 = time_index[start_idx]
                t1 = time_index[end_idx]
                segment_time = (t1 - t0).total_seconds() / 3600  # 小时
                if segment_time > 0:
                    avg_speed = segment_distance / segment_time  # km/h
                else:
                    avg_speed = 0
                speed_in_segments.append(avg_speed)
                start_idx = end_idx
            else:
                break
        return speed_in_segments
        
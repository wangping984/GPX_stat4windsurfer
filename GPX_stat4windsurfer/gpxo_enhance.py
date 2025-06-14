import gpxo
import pandas as pd
import numpy as np

class track_enhance(gpxo.Track):
    def __init__(self, track):
        super().__init__(track)
    
    def fastest_in_window(self, seconds):
        """Calculate the maximum average speed over a specified time window.
        
        Args:
            seconds (int): The time window in seconds.
            
        Returns:
            float: Maximum average speed in km/h over the specified time window in the track.
        """
        velocity_data = self.data['velocity (km/h)']
        # The window size is seconds+1 because we need to include both endpoints
        # (e.g., points at t=0s through t=seconds make a 'seconds' second window)
        window_size = seconds + 1
        rolling_mean = velocity_data.rolling(window=window_size, min_periods=window_size).mean()
        return rolling_mean.max()
    
    def fastest_in_distance_window(self, dist_window):
        """Calculate the maximum average speed over a specified distance window.
        
        This function slides a distance window of specified length over the track and
        finds the segment with the highest average speed.
        
        Args:
            dist_window (float): The distance window in kilometers.
            
        Returns:
            float: Maximum average speed in km/h over the specified distance window in the track.
        """
        # Get the distance and velocity data
        data = self.data[['distance (km)', 'velocity (km/h)']].copy()
        
        # Calculate the cumulative distance for each point
        distances = data['distance (km)'].values
        velocities = data['velocity (km/h)'].values
        
        # Initialize variables to track the maximum average speed
        max_avg_speed = 0
        
        # For each starting point
        for start_idx in range(len(distances)):
            # Find the end point that is approximately dist_window away
            for end_idx in range(start_idx + 1, len(distances)):
                # Calculate the distance between start and end points
                segment_distance = distances[end_idx] - distances[start_idx]
                
                # If we've reached or exceeded the desired window distance
                if segment_distance >= dist_window:
                    # Calculate the average speed for this segment
                    segment_velocities = velocities[start_idx:end_idx+1]
                    avg_speed = np.mean(segment_velocities)
                    
                    # Update the maximum average speed if this segment is faster
                    if avg_speed > max_avg_speed:
                        max_avg_speed = avg_speed
                    
                    # No need to check larger windows from this starting point
                    break
        
        return max_avg_speed
    
    def performance_report(self):
        """Generate a performance report showing the maximum average speeds for various time and distance windows.
        
        This function prints the maximum average speeds for:
        - Time windows: 2s, 5s, 10s, 20s, 30s, 1min, 2min, and 5min
        - Distance windows: 50m, 100m, 200m, 250m, 500m, 1km, 2km, and 5km
        - Average speed for each 1km segment
        
        Returns:
            dict: A dictionary containing the performance data.
        """
        # Calculate all the maximum average speeds for time windows
        time_results = {
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
        distance_results = {
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
        segment_speeds = self.avg_speed_in_segment(1.0)
        
        # Combine results
        results = {
            'time_windows': time_results,
            'distance_windows': distance_results,
            'km_segments': segment_speeds
        }
        
        # Print the performance report
        print("性能报告 - 最快平均速度")
        print("=======================")
        print("基于时间窗口:")
        for window, speed in time_results.items():
            print(f"{window}:\t{speed:.2f} km/h")
        print("\n基于距离窗口:")
        for window, speed in distance_results.items():
            print(f"{window}:\t{speed:.2f} km/h")
        
        print("\n每公里段平均速度:")
        for i, speed in enumerate(segment_speeds):
            print(f"第{i+1}公里:\t{speed:.2f} km/h")
        print("=======================")
        
        return results
    
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
        # Get the distance and velocity data
        data = self.data[['distance (km)', 'velocity (km/h)']].copy()
        
        # Calculate the cumulative distance for each point
        distances = data['distance (km)'].values
        velocities = data['velocity (km/h)'].values
        
        # Initialize variables
        segment_speeds = []
        start_idx = 0
        total_distance = distances[-1]  # Total track distance
        segment_count = int(np.ceil(total_distance / distance))  # Number of segments
        
        # Process each segment
        for segment in range(segment_count):
            # Calculate target distance for this segment
            target_distance = min((segment + 1) * distance, total_distance)
            
            # Find the end index for this segment
            end_idx = start_idx
            while end_idx < len(distances) - 1 and distances[end_idx] < target_distance:
                end_idx += 1
            
            # Calculate average speed for this segment
            if end_idx >= start_idx:
                segment_velocities = velocities[start_idx:end_idx+1]
                avg_speed = np.mean(segment_velocities)
                segment_speeds.append(avg_speed)
                
                # Set start index for next segment
                start_idx = end_idx
            else:
                # This should not happen, but just in case
                break
        
        return segment_speeds
        
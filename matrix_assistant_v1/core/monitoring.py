import psutil
import time

class SystemMonitor:
    def __init__(self):
        self.health_score = 100  # Setting initial health score to 100

    def compute_health_score(self):
        # Example logic to compute health score based on CPU and memory usage
        cpu_usage = psutil.cpu_percent()
        memory_info = psutil.virtual_memory()
        memory_usage = memory_info.percent

        # Simple scoring: health score decreases based on usage
        self.health_score = 100 - (cpu_usage + memory_usage) / 2
        return self.health_score

    def track_system_metrics(self):
        while True:
            cpu_usage = psutil.cpu_percent()
            memory_info = psutil.virtual_memory()
            print(f"CPU Usage: {cpu_usage}% | Memory Usage: {memory_info.percent}%")
            time.sleep(5)  # Track metrics every 5 seconds

    def analyze_episode(self, episode_data):
        # Example analysis function
        average_score = sum(episode_data) / len(episode_data)
        return average_score  # Returns average score from episode data

if __name__ == '__main__':
    monitor = SystemMonitor()
    print(f'Health Score: {monitor.compute_health_score()}')
    monitor.track_system_metrics() # This can be run in a separate thread for live tracking

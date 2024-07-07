import subprocess
import time
def get_hardware_data():
    # Get CPU usage
    def get_cpu_usage():
        with open('/proc/stat', 'r') as f:
            lines = f.readlines()
        cpu_line = lines[0]
        cpu_times = list(map(int, cpu_line.split()[1:]))
        idle_time = cpu_times[3]
        total_time = sum(cpu_times)
        return idle_time, total_time

    idle_time1, total_time1 = get_cpu_usage()
    time.sleep(1)
    idle_time2, total_time2 = get_cpu_usage()
    idle_delta = idle_time2 - idle_time1
    total_delta = total_time2 - total_time1
    cpu_usage = 100 * (1.0 - idle_delta / total_delta)

    # Get memory usage
    with open('/proc/meminfo', 'r') as f:
        lines = f.readlines()
    meminfo = {line.split(':')[0]: int(line.split()[1]) for line in lines}
    total_memory = meminfo['MemTotal'] * 1024
    available_memory = meminfo['MemAvailable'] * 1024
    used_memory = total_memory - available_memory
    memory_percent = (used_memory / total_memory) * 100

    # Get disk usage
    disk_usage = subprocess.check_output(['df', '/']).decode().split('\n')[1].split()
    total_disk = int(disk_usage[1]) * 1024
    used_disk = int(disk_usage[2]) * 1024
    free_disk = int(disk_usage[3]) * 1024
    disk_percent = (used_disk / total_disk) * 100

    def get_cpu_temperature():
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = int(f.read().strip()) / 1000.0  # Convert from millidegree Celsius
                return temp
        except Exception:
            return None

    cpu_temperature = get_cpu_temperature()

    # hardware_data = {
    #     'cpu_usage_percent': cpu_usage,
    #     # 'total_memory': total_memory,
    #     # 'available_memory': available_memory,
    #     # 'used_memory': used_memory,
    #     'memory_percent': memory_percent,
    #     # 'total_disk': total_disk,
    #     # 'used_disk': used_disk,
    #     # 'free_disk': free_disk,
    #     'disk_percent': disk_percent,
    #     'cpu_temperature': cpu_temperature
    # }

    hardware_data = {
        'cpu_usage_percent': round(cpu_usage, 1),
        'memory_percent': round(memory_percent, 1),
        'disk_percent': round(disk_percent, 1),
        'cpu_temperature': cpu_temperature
    }

    return hardware_data



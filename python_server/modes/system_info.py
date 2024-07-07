from python_server.shared.controller.matrix_controller import stop_scrolling_text, display_on_matrix
from python_server.shared.constants import BLUE, GREEN, ORANGE, RED, GREY, YELLOW
from python_server.shared.service.system_info_service import get_hardware_data

# Define thresholds for each metric
thresholds = {
    'cpu_usage_percent': {'very_high': 90, 'high': 75, 'medium': 50, 'low': 25, 'very_low': 0},
    'memory_percent': {'very_high': 90, 'high': 75, 'medium': 50, 'low': 25, 'very_low': 0},
    'disk_percent': {'very_high': 90, 'high': 75, 'medium': 50, 'low': 25, 'very_low': 0},
    'cpu_temperature': {'very_high': 80, 'high': 70, 'medium': 60, 'low': 50, 'very_low': 0}
}


display_names = {
    'cpu_usage_percent': 'CPU Usage',
    'memory_percent': 'Memory Usage ',
    'disk_percent': 'Disk Usage ',
    'cpu_temperature': 'CPU Temperature'
}



def run(stop_event):
    stop_scrolling_text()
    data = get_hardware_data()
    for key, value in data.items():
        color = get_color(value, key)
        display_name = display_names.get(key, key)
        symbol = "%" if display_name != 'CPU Temperature' else "°C"
        display_on_matrix(f"{display_name}: {value} " + symbol , color, stop_event)
        print(f"{key}: {value}", color, stop_event)


# Function to determine color based on value and thresholds
def get_color(value, key):
    if value is None:
        return GREY
    if key in thresholds:
        if value >= thresholds[key]['very_high']:
            return RED
        elif value >= thresholds[key]['high']:
            return ORANGE
        elif value >= thresholds[key]['medium']:
            return YELLOW
        elif value >= thresholds[key]['low']:
            return BLUE
    return GREEN



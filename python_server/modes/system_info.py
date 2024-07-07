from python_server.shared.controller.matrix_controller import stop_scrolling_text, display_on_matrix
from python_server.shared.constants import BLUE, GREEN, ORANGE, RED, GREY, YELLOW
from python_server.shared.service.system_info_service import get_hardware_data, get_system_info





def run(stop_event):
    stop_scrolling_text()
    info_list = get_system_info()
    for info, color in info_list:
        display_on_matrix(info, color, stop_event)





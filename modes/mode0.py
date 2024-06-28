import subprocess
import threading
import os
from python_server.scrolling_text_controller import start_scrolling_text, stop_scrolling_text


def run(text, cpp_binary_folder):
    stop_scrolling_text()
    print("text :" + text)
    print("text :" + cpp_binary_folder)

    cpp_binary = os.path.join(cpp_binary_folder, 'text-scroller')
    args = [cpp_binary, '-f', os.path.join(cpp_binary_folder, '../fonts/9x18.bdf'), text,
            '--led-no-hardware-pulse', '--led-cols=64', '--led-gpio-mapping=adafruit-hat',
            '--led-slowdown-gpio=4']

    try:
        print("Calling C++ Library")
        threading.Thread(target=start_scrolling_text, args=(args,)).start()
        print("C++ called successfully")
        return {"message": "OK"}
    except subprocess.CalledProcessError as e:
        return {"message": f"Error executing program: {str(e)}"}

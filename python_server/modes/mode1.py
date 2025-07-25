import subprocess
import threading
import os
import logging
from python_server.shared.controller.matrix_controller import start_scrolling_text


def run(text, cpp_binary_folder):
    logging.info("text :" + text)
    logging.info("text :" + cpp_binary_folder)

    cpp_binary = os.path.join(cpp_binary_folder, 'text-fixed')
    args = [cpp_binary, '-f', os.path.join(cpp_binary_folder, '../fonts/9x18.bdf'), text,
            '--led-no-hardware-pulse', '--led-cols=64', '--led-gpio-mapping=adafruit-hat',
            '--led-slowdown-gpio=4']

    try:
        logging.info("Calling C++ Library")
        threading.Thread(target=start_scrolling_text, args=(args,)).start()
        logging.info("C++ called successfully")
        return {"message": "OK"}
    except subprocess.CalledProcessError as e:
        return {"message": f"Error executing program: {str(e)}"}

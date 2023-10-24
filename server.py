from flask import Flask, request, jsonify
import importlib
from config import MODE_MAPPING  # Import the MODE_MAPPING constant

app = Flask(__name__)

# Initialize the current_mode to a default mode ID (e.g., 0)
current_mode = 0

@app.route('/changeMode', methods=['POST'])
def change_mode():
    global current_mode

    data = request.json

    mode_id = data.get('modeId', None)
    next_mode = data.get('nextMode', False)
    previous_mode = data.get('previousMode', False)

    num_modes = len(MODE_MAPPING)  # Get the number of modes

    if mode_id is not None:
        if 0 <= mode_id <= num_modes:
            current_mode = mode_id
        else:
            return jsonify({"message": "Invalid mode ID"}), 400
    elif next_mode:
        current_mode = (current_mode + 1) % num_modes
    elif previous_mode:
        current_mode = (current_mode - 1) % num_modes
    else:
        return jsonify({"message": "No valid parameters provided"}), 400

    # Import the selected mode script
    mode_name = next(key for key, value in MODE_MAPPING.items() if value == current_mode)
    mode_module = importlib.import_module(f"modes.{mode_name}")

    return jsonify({"message": "OK"})

if __name__ == '__main__':
    app.run(debug=True)

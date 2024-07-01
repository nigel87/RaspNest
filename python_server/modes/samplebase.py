import argparse
import time
import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))
from rgbmatrix import RGBMatrix, RGBMatrixOptions

class SampleBase(object):
    def __init__(self, *args, **kwargs):
        self.parser = argparse.ArgumentParser()

        self.parser.add_argument("-t", "--text", help="The text to scroll on the RGB LED panel", default="Hello world!")
        self.parser.add_argument("--rows", type=int, default=32, help="Number of rows in the LED matrix")
        self.parser.add_argument("--cols", type=int, default=64, help="Number of columns in the LED matrix")
        self.parser.add_argument("--chain-length", type=int, default=1, help="Number of daisy-chained boards")
        self.parser.add_argument("--parallel", type=int, default=1, help="Number of parallel chains")
        self.parser.add_argument("--hardware-mapping", type=str, default="adafruit-hat", help="Hardware mapping")

    # Other methods and properties...

    def process(self):
        self.args = self.parser.parse_args()

        options = RGBMatrixOptions()

        options.rows = self.args.rows
        options.cols = self.args.cols
        options.chain_length = self.args.chain_length
        options.parallel = self.args.parallel
        options.hardware_mapping = self.args.hardware_mapping

        # Other configuration options...

        self.matrix = RGBMatrix(options=options)

        try:
            # Start the RunText sample
            run_text = RunText(matrix=self.matrix, text=self.args.text)
            run_text.run()
        except KeyboardInterrupt:
            print("Exiting\n")
            sys.exit(0)

        return True

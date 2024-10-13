#include "led-matrix.h"
#include "graphics.h"
#include <string>
#include <iostream>
#include <ctime>

using namespace rgb_matrix;

int main(int argc, char *argv[]) {
  // Initialize matrix options
  RGBMatrix::Options matrix_options;
  matrix_options.hardware_mapping = "regular";  // or your specific mapping
  matrix_options.rows = 32;
  matrix_options.cols = 64;

  // Initialize the matrix
  RGBMatrix *matrix = RGBMatrix::CreateFromOptions(matrix_options, runtime_options);
  if (matrix == nullptr) {
    std::cerr << "Couldn't initialize the RGBMatrix." << std::endl;
    return 1;
  }

  FrameCanvas *offscreen_canvas = matrix->CreateFrameCanvas();

  while (true) {
    // Drawing the current time
    time_t t = time(nullptr);
    struct tm *now = localtime(&t);
    char time_str[100];
    strftime(time_str, sizeof(time_str), "%H:%M:%S", now);

    offscreen_canvas->Clear();
    offscreen_canvas->DrawText(1, 10, Color(255, 255, 255), "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 10, time_str);
    offscreen_canvas = matrix->SwapOnVSync(offscreen_canvas);

    sleep(1);  // Sleep for 1 second
  }

  delete matrix;
  return 0;
}

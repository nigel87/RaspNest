#include "led-matrix.h"
#include "graphics.h"
#include <string>
#include <iostream>
#include <ctime>
#include <unistd.h>  // For sleep

using namespace rgb_matrix;

int main(int argc, char *argv[]) {
  if (argc < 2) {
    std::cerr << "Usage: " << argv[0] << " <text_to_scroll>" << std::endl;
    return 1;
  }

  // Get the scrolling text from arguments
  std::string scrolling_text = argv[1];

  // Initialize matrix options
  RGBMatrix::Options matrix_options;
  matrix_options.hardware_mapping = "regular";  // Adjust as needed
  matrix_options.rows = 32;
  matrix_options.cols = 64;

  // Initialize runtime options
  RuntimeOptions runtime_options;

  // Initialize the matrix
  RGBMatrix *matrix = CreateMatrixFromOptions(matrix_options, runtime_options);
  if (matrix == nullptr) {
    std::cerr << "Couldn't initialize the RGBMatrix." << std::endl;
    return 1;
  }

  FrameCanvas *offscreen_canvas = matrix->CreateFrameCanvas();

  // Load font for clock
  rgb_matrix::Font clock_font;
  if (!clock_font.LoadFont("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")) {
    std::cerr << "Couldn't load font for clock." << std::endl;
    return 1;
  }

  // Load font for scrolling text (could be the same or different)
  rgb_matrix::Font text_font;
  if (!text_font.LoadFont("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")) {
    std::cerr << "Couldn't load font for scrolling text." << std::endl;
    return 1;
  }

  rgb_matrix::Color white(255, 255, 255);
  rgb_matrix::Color red(255, 0, 0);

  int text_position = offscreen_canvas->width();  // Start text off-screen

  while (true) {
    // Drawing the current time (Fixed at top)
    time_t t = time(nullptr);
    struct tm *now = localtime(&t);
    char time_str[100];
    strftime(time_str, sizeof(time_str), "%H:%M:%S", now);

    offscreen_canvas->Clear();

    // Display the clock at the top (Y position: 10 for 32x64 matrix)
    rgb_matrix::DrawText(offscreen_canvas, clock_font, 1, 10, white, time_str);

    // Scrolling text at the bottom (Y position: 30 for 32x64 matrix)
    rgb_matrix::DrawText(offscreen_canvas, text_font, text_position, 30, red, scrolling_text.c_str());

    // Scroll text
    --text_position;

    // If the text has scrolled off the screen, reset its position
    int text_width = rgb_matrix::DrawText(offscreen_canvas, text_font, text_position, 30, red, scrolling_text.c_str());
    if (text_position + text_width < 0) {
      text_position = offscreen_canvas->width();
    }

    offscreen_canvas = matrix->SwapOnVSync(offscreen_canvas);

    usleep(30 * 1000);  // 30ms delay for smoother scrolling (adjust as needed)
  }

  delete matrix;
  return 0;
}

#include <iostream>
#include <signal.h>
#include <thread>
#include <chrono>
#include <Magick++.h>
#include "led-matrix.h"

using namespace std;

// Function to handle interruptions (Ctrl+C)
volatile bool interrupt_received = false;
static void InterruptHandler(int signo) {
  interrupt_received = true;
}

int main(int argc, char *argv[]) {
  // Initialize the Matrix
  RGBMatrix::Options matrix_options;
  matrix_options.hardware_mapping = "regular";
  matrix_options.rows = 32;
  matrix_options.cols = 64;
  matrix_options.chain_length = 1;
  matrix_options.parallel = 1;

  RGBMatrix *matrix = RGBMatrix::CreateFromOptions(matrix_options);

  if (matrix == NULL) {
    cout << "Error initializing matrix" << endl;
    return 1;
  }

  FrameCanvas *offscreen_canvas = matrix->CreateFrameCanvas();

  // Initialize ImageMagick
  Magick::InitializeMagick(*argv);

  // Set up interruption handler
  signal(SIGTERM, InterruptHandler);
  signal(SIGINT, InterruptHandler);

  // Load the image (replace "sun.jpg" with your image file)
  string image_path = "sun.jpg";
  Magick::Image image;
  try {
    image.read(image_path);
  } catch (Magick::Exception &error) {
    cerr << "Error loading image: " << error.what() << endl;
    return 1;
  }

  // Main loop
  while (!interrupt_received) {
    // Get the current time
    auto current_time = chrono::system_clock::to_time_t(chrono::system_clock::now());
    string time_str = ctime(&current_time);
    time_str.pop_back();  // Remove the newline character

    // Clear the canvas
    offscreen_canvas->Clear();

    // Draw the time at the top of the screen
    offscreen_canvas->DrawText(1, 10, RGB(255, 255, 255), "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 10, time_str.c_str());

    // Draw the image below the time
    int x_offset = (offscreen_canvas->width() - image.columns()) / 2;
    int y_offset = 20;  // Adjust this value to change the vertical position
    for (size_t y = 0; y < image.rows(); ++y) {
      for (size_t x = 0; x < image.columns(); ++x) {
        const Magick::Color &c = image.pixelColor(x, y);
        offscreen_canvas->SetPixel(x + x_offset, y + y_offset,
                                   ScaleQuantumToChar(c.redQuantum()),
                                   ScaleQuantumToChar(c.greenQuantum()),
                                   ScaleQuantumToChar(c.blueQuantum()));
      }
    }

    // Swap the canvas to the display
    matrix->SwapOnVSync(offscreen_canvas);

    // Sleep for a short duration (adjust as needed)
    this_thread::sleep_for(chrono::seconds(1));
  }

  // Clean up
  matrix->Clear();
  delete matrix;

  return 0;
}

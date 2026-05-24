// -*- mode: c++; c-basic-offset: 2; indent-tabs-mode: nil; -*-
#include "led-matrix.h"
#include "graphics.h"

#include <getopt.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <fstream>
#include <string>

using namespace rgb_matrix;

volatile bool interrupt_received = false;
static void InterruptHandler(int signo) {
  interrupt_received = true;
}

static int usage(const char *progname) {
  fprintf(stderr, "usage: %s [options]\n", progname);
  fprintf(stderr, "Options:\n"
          "\t-f <font-file>    : Font for the clock (e.g. 9x18.bdf)\n"
          "\t-s <font-file>    : Font for the widgets (e.g. 5x8.bdf or 4x6.bdf)\n"
          "\t-i <input-file>   : Input file path for dashboard data (Default: /var/weather/dashboard_data.txt)\n"
          );
  rgb_matrix::PrintMatrixFlags(stderr);
  return 1;
}

static bool parseColor(Color *c, const std::string& str) {
  return sscanf(str.c_str(), "%hhu,%hhu,%hhu", &c->r, &c->g, &c->b) == 3;
}

int main(int argc, char *argv[]) {
  RGBMatrix::Options matrix_options;
  rgb_matrix::RuntimeOptions runtime_opt;
  
  // Safe privilege dropping if running as root
  runtime_opt.drop_priv_user = getenv("SUDO_UID");
  runtime_opt.drop_priv_group = getenv("SUDO_GID");
  
  if (!rgb_matrix::ParseOptionsFromFlags(&argc, &argv, &matrix_options, &runtime_opt)) {
    return usage(argv[0]);
  }

  const char *clock_font_file = NULL;
  const char *widget_font_file = NULL;
  const char *input_file = "/var/weather/dashboard_data.txt";

  int opt;
  while ((opt = getopt(argc, argv, "f:s:i:")) != -1) {
    switch (opt) {
    case 'f': clock_font_file = strdup(optarg); break;
    case 's': widget_font_file = strdup(optarg); break;
    case 'i': input_file = strdup(optarg); break;
    default: return usage(argv[0]);
    }
  }

  if (clock_font_file == NULL || widget_font_file == NULL) {
    fprintf(stderr, "Need to specify clock BDF font-file with -f and widget BDF font-file with -s\n");
    return usage(argv[0]);
  }

  // Load fonts
  rgb_matrix::Font clock_font;
  if (!clock_font.LoadFont(clock_font_file)) {
    fprintf(stderr, "Couldn't load clock font '%s'\n", clock_font_file);
    return 1;
  }

  rgb_matrix::Font widget_font;
  if (!widget_font.LoadFont(widget_font_file)) {
    fprintf(stderr, "Couldn't load widget font '%s'\n", widget_font_file);
    return 1;
  }

  RGBMatrix *matrix = RGBMatrix::CreateFromOptions(matrix_options, runtime_opt);
  if (matrix == NULL) return 1;

  FrameCanvas *offscreen = matrix->CreateFrameCanvas();

  signal(SIGTERM, InterruptHandler);
  signal(SIGINT, InterruptHandler);

  // Layout baselines/positions
  // clock: Y = 13 (typical for 9x18 font or 6x13 on 32-row screen)
  // divider: Y = 16 (horizontal separator line)
  // widgets: Y = 28 (typical for 5x8 or 4x6 font on 32-row screen)
  int clock_y = 13;
  int divider_y = 16;
  int widget_y = 28;

  Color clock_color(0, 255, 255);    // Cyan
  Color divider_color(60, 60, 60);   // Dark Slate Grey
  Color temp_color(255, 215, 0);     // Gold

  std::string temp = "24C";
  std::string bottom_left = "14:00 Std";
  Color bl_color(0, 255, 255);       // Cyan
  std::string bottom_right = "BTC +2.4%";
  Color br_color(0, 255, 0);         // Green

  time_t last_file_read = 0;

  while (!interrupt_received) {
    offscreen->Fill(0, 0, 0); // Clear black

    // 1. Read input file if it was modified (check every 1 second to avoid file read overhead)
    time_t now_time = time(NULL);
    if (now_time - last_file_read >= 1) {
      std::ifstream file(input_file);
      if (file.is_open()) {
        std::string line_temp, line_bl, line_bl_col, line_br, line_br_col;
        if (std::getline(file, line_temp)) temp = line_temp;
        if (std::getline(file, line_bl)) bottom_left = line_bl;
        if (std::getline(file, line_bl_col)) parseColor(&bl_color, line_bl_col);
        if (std::getline(file, line_br)) bottom_right = line_br;
        if (std::getline(file, line_br_col)) parseColor(&br_color, line_br_col);
      }
      last_file_read = now_time;
    }

    // 2. Render Clock (HH:MM) at top-left
    struct tm tm;
    localtime_r(&now_time, &tm);
    char time_text[6];
    strftime(time_text, sizeof(time_text), "%H:%M", &tm);
    rgb_matrix::DrawText(offscreen, clock_font, 2, clock_y, clock_color, NULL, time_text, 0);

    // 3. Render Temp/Weather at top-right
    // Align right: matrix->width() - text_width - margin
    int temp_width = 0;
    for (const char* c = temp.c_str(); *c; ++c) {
      temp_width += widget_font.CharacterWidth(*c);
    }
    int temp_x = matrix->width() - temp_width - 2;
    rgb_matrix::DrawText(offscreen, widget_font, temp_x, clock_y - 2, temp_color, NULL, temp.c_str(), 0);

    // 4. Render Dotted Separator Line
    for (int x = 1; x < matrix->width() - 1; x += 2) {
      offscreen->SetPixel(x, divider_y, divider_color.r, divider_color.g, divider_color.b);
    }

    // 5. Render Bottom-Left Widget
    rgb_matrix::DrawText(offscreen, widget_font, 2, widget_y, bl_color, NULL, bottom_left.c_str(), 0);

    // 6. Render Bottom-Right Widget
    int br_width = 0;
    for (const char* c = bottom_right.c_str(); *c; ++c) {
      br_width += widget_font.CharacterWidth(*c);
    }
    int br_x = matrix->width() - br_width - 2;
    rgb_matrix::DrawText(offscreen, widget_font, br_x, widget_y, br_color, NULL, bottom_right.c_str(), 0);

    // Wait a bit, and swap to the next buffer.
    usleep(100 * 1000);  // 100ms loop is perfect for time updates and uses very low CPU
    offscreen = matrix->SwapOnVSync(offscreen);
  }

  // Clear display and cleanup
  matrix->Clear();
  delete matrix;

  write(STDOUT_FILENO, "\n", 1);
  return 0;
}

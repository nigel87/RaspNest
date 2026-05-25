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

  // Load a dedicated larger font for the weather (5x8) for better legibility
  rgb_matrix::Font weather_font;
  bool has_weather_font = weather_font.LoadFont("../fonts/5x8.bdf");
  if (!has_weather_font) {
    fprintf(stderr, "Warning: Couldn't load weather font '../fonts/5x8.bdf', falling back to widget font\n");
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
  std::string bus_pred = "ND";
  Color bus_color(150, 150, 150);     // Grey

  std::string last_bottom_right = "";
  int br_scroll_pos = 0;

  std::string music_active = "0";
  std::string music_text = "";
  std::string last_music_text = "";
  int music_scroll_pos = 32;

  time_t last_file_read = 0;

  while (!interrupt_received) {
    offscreen->Fill(0, 0, 0); // Clear black

    // 1. Read input file if it was modified (check every 1 second to avoid file read overhead)
    time_t now_time = time(NULL);
    if (now_time - last_file_read >= 1) {
      std::ifstream file(input_file);
      if (file.is_open()) {
        std::string line_temp, line_bl, line_bl_col, line_br, line_br_col, line_bus_pred, line_bus_col;
        std::string line_music_active, line_music_text;
        if (std::getline(file, line_temp)) temp = line_temp;
        if (std::getline(file, line_bl)) bottom_left = line_bl;
        if (std::getline(file, line_bl_col)) parseColor(&bl_color, line_bl_col);
        if (std::getline(file, line_br)) {
          bottom_right = line_br;
          if (bottom_right != last_bottom_right) {
            br_scroll_pos = matrix->width();
            last_bottom_right = bottom_right;
          }
        }
        if (std::getline(file, line_br_col)) parseColor(&br_color, line_br_col);
        if (std::getline(file, line_bus_pred)) bus_pred = line_bus_pred;
        if (std::getline(file, line_bus_col)) parseColor(&bus_color, line_bus_col);
        if (std::getline(file, line_music_active)) music_active = line_music_active;
        if (std::getline(file, line_music_text)) {
          music_text = line_music_text;
          if (music_text != last_music_text) {
            music_scroll_pos = 32;
            last_music_text = music_text;
          }
        }
      }
      last_file_read = now_time;
    }

    if (music_active == "1") {
      // --- Render Music Layout ---

      // 1. Draw Clock (HH:MM) at top-left
      struct tm tm;
      localtime_r(&now_time, &tm);
      char time_text[6];
      strftime(time_text, sizeof(time_text), "%H:%M", &tm);
      rgb_matrix::DrawText(offscreen, clock_font, 1, clock_y, clock_color, NULL, time_text, 0);

      // 2. Draw Scrolling Music Info in bottom-left
      int music_width = 0;
      for (const char* c = music_text.c_str(); *c; ++c) {
        music_width += widget_font.CharacterWidth(*c);
      }

      music_scroll_pos--;
      if (music_scroll_pos + music_width < 0) {
        music_scroll_pos = 32; // Scroll from the right edge of the left side (x = 32)
      }

      // Draw scrolling text in the bottom left area (Vibrant Green)
      Color music_text_color(0, 255, 0);
      rgb_matrix::DrawText(offscreen, widget_font, music_scroll_pos, widget_y, music_text_color, NULL, music_text.c_str(), 0);

      // 3. Draw 32x32 Album Artwork on the right half (cols 32-63, rows 0-31)
      bool img_drawn = false;
      std::ifstream raw_file("/var/weather/album_art_raw.bin", std::ios::binary);
      if (raw_file.is_open()) {
        char buffer[3072]; // 32 * 32 * 3 = 3072 bytes
        raw_file.read(buffer, sizeof(buffer));
        if (raw_file.gcount() == sizeof(buffer)) {
          int index = 0;
          for (int y = 0; y < 32; ++y) {
            for (int x = 32; x < 64; ++x) {
              unsigned char r = buffer[index++];
              unsigned char g = buffer[index++];
              unsigned char b = buffer[index++];
              offscreen->SetPixel(x, y, r, g, b);
            }
          }
          img_drawn = true;
        }
        raw_file.close();
      }

      if (!img_drawn) {
        // If image file is missing or has error, clear the right square to black (overwrites overlapping scroller text)
        for (int y = 0; y < 32; ++y) {
          for (int x = 32; x < 64; ++x) {
            offscreen->SetPixel(x, y, 0, 0, 0);
          }
        }
        // Draw standard fallback label
        rgb_matrix::DrawText(offscreen, widget_font, 36, 18, Color(100, 100, 100), NULL, "MUSIC", 0);
      }

    } else {
      // --- Render Standard Dashboard Layout ---

      // 2. Render Clock (HH:MM) at top-left
      struct tm tm;
      localtime_r(&now_time, &tm);
      char time_text[6];
      strftime(time_text, sizeof(time_text), "%H:%M", &tm);
      rgb_matrix::DrawText(offscreen, clock_font, 2, clock_y, clock_color, NULL, time_text, 0);

      // 3. Render Temp/Weather at top-right
      rgb_matrix::Font &w_font = has_weather_font ? weather_font : widget_font;
      int temp_width = 0;
      for (const char* c = temp.c_str(); *c; ++c) {
        temp_width += w_font.CharacterWidth(*c);
      }
      int temp_x = matrix->width() - temp_width - 2;
      rgb_matrix::DrawText(offscreen, w_font, temp_x, clock_y - 2, temp_color, NULL, temp.c_str(), 0);

      // 4. Render Dotted Separator Line
      for (int x = 1; x < matrix->width() - 1; x += 2) {
        offscreen->SetPixel(x, divider_y, divider_color.r, divider_color.g, divider_color.b);
      }

      // 4.5. Render Bus 409 top widget aligned with weather
      if (!bus_pred.empty()) {
        int clock_width = 0;
        for (const char* c = time_text; *c; ++c) {
          clock_width += clock_font.CharacterWidth(*c);
        }
        int start_x = 2 + clock_width;

        int end_x = temp_x;
        int mid_x = start_x + (end_x - start_x) / 2;

        int pred_width = 0;
        for (const char* c = bus_pred.c_str(); *c; ++c) {
          pred_width += widget_font.CharacterWidth(*c);
        }
        int x_pred = mid_x - pred_width / 2;
        if (x_pred < start_x + 1) x_pred = start_x + 1;
        
        rgb_matrix::DrawText(offscreen, widget_font, x_pred, clock_y - 2, bus_color, NULL, bus_pred.c_str(), 0);
      }

      // 5. Render Bottom-Left & Bottom-Right Widgets with dynamic overlap and scrolling guard
      int br_width = 0;
      for (const char* c = bottom_right.c_str(); *c; ++c) {
        br_width += widget_font.CharacterWidth(*c);
      }

      int bl_width = 0;
      for (const char* c = bottom_left.c_str(); *c; ++c) {
        bl_width += widget_font.CharacterWidth(*c);
      }

      int clipping_boundary = 2 + bl_width + 2; // 2px margin + bl_width + 2px gap
      int max_br_width = matrix->width() - clipping_boundary - 2;

      int br_x = matrix->width() - br_width - 2;

      if (br_width <= max_br_width) {
        // It fits! Draw statically
        br_scroll_pos = br_x;
      } else {
        // It is too long! Scroll it
        br_scroll_pos--;
        if (br_scroll_pos + br_width < clipping_boundary) {
          br_scroll_pos = matrix->width();
        }
      }

      // 1. Draw the bottom-right text (either statically or scrolling)
      rgb_matrix::DrawText(offscreen, widget_font, br_scroll_pos, widget_y, br_color, NULL, bottom_right.c_str(), 0);

      // 2. Clear the left region on the bottom row to prevent the scrolling text from overlapping
      for (int x = 0; x < clipping_boundary; ++x) {
        for (int y = widget_y - 6; y <= widget_y + 1; ++y) {
          offscreen->SetPixel(x, y, 0, 0, 0);
        }
      }

      // 3. Draw the bottom-left text statically
      rgb_matrix::DrawText(offscreen, widget_font, 2, widget_y, bl_color, NULL, bottom_left.c_str(), 0);
    }

    // Wait a bit, and swap to the next buffer.
    usleep(60 * 1000);  // 60ms loop is perfect for smooth text scrolling and time updates
    offscreen = matrix->SwapOnVSync(offscreen);
  }

  // Clear display and cleanup
  matrix->Clear();
  delete matrix;

  write(STDOUT_FILENO, "\n", 1);
  return 0;
}

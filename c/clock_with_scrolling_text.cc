  // -*- mode: c++; c-basic-offset: 2; indent-tabs-mode: nil; -*-
  // Example of a clock. This is very similar to the text-example,
  // except that it shows the time :)
  //
  // This code is public domain
  // (but note, that the led-matrix library this depends on is GPL v2)

  #include "led-matrix.h"
  #include "graphics.h"

  #include <getopt.h>
  #include <signal.h>
  #include <stdio.h>
  #include <stdlib.h>
  #include <string.h>
  #include <time.h>
  #include <unistd.h>

  #include <vector>
  #include <string>
  #include <fstream>

  using namespace rgb_matrix;

  volatile bool interrupt_received = false;
  static void InterruptHandler(int signo) {
    interrupt_received = true;
  }

  static int usage(const char *progname) {
    fprintf(stderr, "usage: %s [options] <text>\n", progname);
    fprintf(stderr, "Reads text from stdin and displays it. "
            "Empty string: clear screen\n");
    fprintf(stderr, "Options:\n");
    fprintf(stderr,
            "\t-d <time-format>  : Default '%%H:%%M'. See strftime()\n"
            "\t                    Can be provided multiple times for multiple "
            "lines\n"
            "\t-f <font-file>    : Use given font.\n"
            "\t-x <x-origin>     : X-Origin of displaying text (Default: 0)\n"
            "\t-y <y-origin>     : Y-Origin of displaying text (Default: 0)\n"
            "\t-s <line-spacing> : Extra spacing between lines when multiple -d given\n"
            "\t-S <spacing>      : Extra spacing between letters (Default: 0)\n"
            "\t-C <r,g,b>        : Color. Default 255,255,0\n"
            "\t-B <r,g,b>        : Background-Color. Default 0,0,0\n"
            "\t-O <r,g,b>        : Outline-Color, e.g. to increase contrast.\n"
            "\n"
            );
    rgb_matrix::PrintMatrixFlags(stderr);
    return 1;
  }

  static bool parseColor(Color *c, const char *str) {
    return sscanf(str, "%hhu,%hhu,%hhu", &c->r, &c->g, &c->b) == 3;
  }

  static bool FullSaturation(const Color &c) {
    return (c.r == 0 || c.r == 255)
      && (c.g == 0 || c.g == 255)
      && (c.b == 0 || c.b == 255);
  }

std::string readTemperatureFromFile(const char *filename) {
  std::ifstream file(filename);
  printf("Reading from file: %s\n", filename);  // Debugging print
  if (!file) {
    printf("File not found or not accessible\n");  // Debugging print
    return "N/A";
  }
  std::string temp;
  std::getline(file, temp);
  printf("Read temperature: %s\n", temp.c_str());  // Debugging print
  return temp;
}

int main(int argc, char *argv[]) {
  RGBMatrix::Options matrix_options;
  rgb_matrix::RuntimeOptions runtime_opt;
  if (!rgb_matrix::ParseOptionsFromFlags(&argc, &argv, &matrix_options, &runtime_opt)) {
    return usage(argv[0]);
  }

  const char *bdf_font_file = NULL;
  const char *scroll_text = NULL;
  int letter_spacing = 0;
  Color color(255, 255, 0);
  Color bg_color(0, 0, 0);

  int opt;
  while ((opt = getopt(argc, argv, "f:S:C:B:t:")) != -1) {
    switch (opt) {
    case 'f': bdf_font_file = strdup(optarg); break;
    case 'S': letter_spacing = atoi(optarg); break;
    case 'C': if (!parseColor(&color, optarg)) return usage(argv[0]); break;
    case 'B': if (!parseColor(&bg_color, optarg)) return usage(argv[0]); break;
    case 't': scroll_text = strdup(optarg); break;
    default: return usage(argv[0]);
    }
  }

  if (bdf_font_file == NULL || scroll_text == NULL) {
    fprintf(stderr, "Need to specify BDF font-file with -f and scroll text with -t\n");
    return usage(argv[0]);
  }

  rgb_matrix::Font font;
  if (!font.LoadFont(bdf_font_file)) {
    fprintf(stderr, "Couldn't load font '%s'\n", bdf_font_file);
    return 1;
  }

  RGBMatrix *matrix = RGBMatrix::CreateFromOptions(matrix_options, runtime_opt);
  if (matrix == NULL) return 1;

  FrameCanvas *offscreen = matrix->CreateFrameCanvas();

  signal(SIGTERM, InterruptHandler);
  signal(SIGINT, InterruptHandler);

  int scroll_pos = matrix->width();

  // Calculate positions
  int clock_y = font.baseline();
  int scroll_y = matrix->height() - 1;  // Position at the very bottom

  while (!interrupt_received) {
    offscreen->Fill(bg_color.r, bg_color.g, bg_color.b);

    // Display clock at the top
    time_t now = time(NULL);
    struct tm tm;
    localtime_r(&now, &tm);
    char time_text[9];
    //strftime(time_text, sizeof(time_text), "%H:%M:%S", &tm);
    strftime(time_text, sizeof(time_text), "%H:%M", &tm);

    // Calculate the width of the time string
    int time_width = 0;
    for (const char* c = time_text; *c; ++c) {
      time_width += font.CharacterWidth(*c) + letter_spacing;
    }
    time_width -= letter_spacing;  // Remove extra spacing after last character

    int clock_x = (matrix->width() - time_width) / 2;
    rgb_matrix::DrawText(offscreen, font,
                         clock_x, clock_y,
                         color, NULL, time_text, letter_spacing);

    // Display scrolling text at the bottom
    int scroll_width = rgb_matrix::DrawText(offscreen, font,
                                            scroll_pos,
                                            scroll_y,
                                            color, NULL, scroll_text,
                                            letter_spacing);

    --scroll_pos;
    if (scroll_pos + scroll_width < 0) {
      scroll_pos = matrix->width();
    }

    // Wait a bit, and swap to the next buffer.
    usleep(30 * 1000);  // 30ms
    offscreen = matrix->SwapOnVSync(offscreen);
  }

  // Finished. Shut down the RGB matrix.
  delete matrix;

  write(STDOUT_FILENO, "\n", 1);  // Create a fresh new line after ^C on screen
  return 0;
}

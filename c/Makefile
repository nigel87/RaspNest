CXXFLAGS=-O3 -W -Wall -Wextra -Wno-unused-parameter -D_FILE_OFFSET_BITS=64
OBJECTS=led-image-viewer.o text-scroller.o clock.o
BINARIES=led-image-viewer text-scroller clock clock_with_scrolling_text

OPTIONAL_OBJECTS=video-viewer.o
OPTIONAL_BINARIES=video-viewer

# Where our library resides. You mostly only need to change the
# RGB_LIB_DISTRIBUTION, this is where the library is checked out.
RGB_LIB_DISTRIBUTION=..
RGB_INCDIR=$(RGB_LIB_DISTRIBUTION)/include
RGB_LIBDIR=$(RGB_LIB_DISTRIBUTION)/lib
RGB_LIBRARY_NAME=rgbmatrix
RGB_LIBRARY=$(RGB_LIBDIR)/lib$(RGB_LIBRARY_NAME).a
RGB_LDFLAGS+=-L$(RGB_LIBDIR) -l$(RGB_LIBRARY_NAME) -lrt -lm -lpthread

# Imagemagic flags, only needed if actually compiled.
MAGICK_CXXFLAGS?=$(shell GraphicsMagick++-config --cppflags --cxxflags)
MAGICK_LDFLAGS?=$(shell GraphicsMagick++-config --ldflags --libs)
AV_CXXFLAGS=$(shell pkg-config --cflags libavcodec libavformat libswscale libavutil)
AV_LDFLAGS=$(shell pkg-config --libs libavcodec libavformat libswscale libavutil)

# Default target
all: $(BINARIES) $(OPTIONAL_BINARIES)

# Rule to ensure RGB matrix library is built
$(RGB_LIBRARY): FORCE
	$(MAKE) -C $(RGB_LIBDIR)

# Rule for text-scroller
text-scroller: text-scroller.o $(RGB_LIBRARY)
	$(CXX) $(CXXFLAGS) text-scroller.o -o $@ $(LDFLAGS) $(RGB_LDFLAGS)

# Rule for led-image-viewer
led-image-viewer: led-image-viewer.o $(RGB_LIBRARY)
	$(CXX) $(CXXFLAGS) led-image-viewer.o -o $@ $(LDFLAGS) $(RGB_LDFLAGS) $(MAGICK_LDFLAGS)

# Rule for video-viewer
video-viewer: video-viewer.o $(RGB_LIBRARY)
	$(CXX) $(CXXFLAGS) video-viewer.o -o $@ $(LDFLAGS) $(RGB_LDFLAGS) $(AV_LDFLAGS)

# Rule for clock_with_scrolling_text
clock_with_scrolling_text: clock_with_scrolling_text.o $(RGB_LIBRARY)
	$(CXX) $(CXXFLAGS) clock_with_scrolling_text.o -o $@ $(LDFLAGS) $(RGB_LDFLAGS)

# Rule for display_time_and_image
display_time_and_image: display_time_and_image.o $(RGB_LIBRARY)
	$(CXX) $(CXXFLAGS) display_time_and_image.o -o $@ $(LDFLAGS) $(RGB_LDFLAGS) $(MAGICK_LDFLAGS)

# Rule for clock
clock: clock.o $(RGB_LIBRARY)
	$(CXX) $(CXXFLAGS) clock.o -o $@ $(LDFLAGS) $(RGB_LDFLAGS)

# Compilation rule for source files
%.o : %.cc
	$(CXX) -I$(RGB_INCDIR) $(CXXFLAGS) -c -o $@ $<

# Specific object file rules for special files
led-image-viewer.o: led-image-viewer.cc
	$(CXX) -I$(RGB_INCDIR) $(CXXFLAGS) $(MAGICK_CXXFLAGS) -c -o $@ $<

# clock_with_scrolling_text.o: clock_with_scrolling_text.cc
#	$(CXX) -I$(RGB_INCDIR) $(CXXFLAGS) -c -o $@ $<

#display_time_and_image.o: display_time_and_image.cpp
#	$(CXX) -I$(RGB_INCDIR) $(CXXFLAGS) $(MAGICK_CXXFLAGS) -c -o $@ $<

clock.o: clock.cc
	$(CXX) -I$(RGB_INCDIR) $(CXXFLAGS) -c -o $@ $<

# Clean rule
clean:
	rm -f $(OBJECTS) $(BINARIES) $(OPTIONAL_OBJECTS) $(OPTIONAL_BINARIES)

# Force target to rebuild library
FORCE:
.PHONY: FORCE

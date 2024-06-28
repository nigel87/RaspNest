# mode0.py

from led_display import display_text

if __name__ == '__main__':
    import sys
    print("mode0 start")
    if len(sys.argv) != 2:
        print("Usage: mode0.py <text>")
        sys.exit(1)
    print("text")
    text = sys.argv[1]

    print(text)
    display_text(text)


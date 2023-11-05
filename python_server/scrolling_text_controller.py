import subprocess

def stop_scrolling_text():
    try:
        # Send SIGINT signal to stop the scrolling text
        subprocess.run(["pkill", "-2", "text-scroller"])
    except subprocess.CalledProcessError:
        pass  # Handle any errors if needed


def start_scrolling_text(args):
    try:
        subprocess.Popen(args)
    except Exception as e:
        print(f"Error starting scrolling text: {str(e)}")

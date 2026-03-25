"""
ITC Form Generator - Web Application Launcher
Launches the web server and opens the browser automatically.

This module serves as the entry point for the PyInstaller-built executable.
"""

import os
import sys
import time
import webbrowser
import threading
from http.server import HTTPServer

# Determine base paths for frozen (exe) vs development modes
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    BASE_PATH = sys._MEIPASS
    SRC_PATH = BASE_PATH
else:
    # Running as script
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))
    SRC_PATH = os.path.join(BASE_PATH, 'src')

# Add paths for imports
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)
if BASE_PATH not in sys.path:
    sys.path.insert(0, BASE_PATH)

# Set working directory to base path for file operations
os.chdir(BASE_PATH)

PORT = 8080


def open_browser():
    """Open the browser after a short delay."""
    time.sleep(1.5)
    try:
        webbrowser.open(f'http://localhost:{PORT}')
    except Exception as e:
        print(f"Could not open browser automatically: {e}")
        print(f"Please open http://localhost:{PORT} manually.")


def main():
    """Start the web server and open browser."""
    # Import here after paths are set up
    from webapp import ITCHandler

    print(f"""
+--------------------------------------------------------------+
|                    ITC Form Generator                        |
|                     Web Application                          |
+--------------------------------------------------------------+
|                                                              |
|  Server running at: http://localhost:{PORT}                    |
|                                                              |
|  Your browser will open automatically.                       |
|                                                              |
|  Keep this window open while using the app.                  |
|  Press Ctrl+C or close this window to stop.                  |
|                                                              |
+--------------------------------------------------------------+
""")

    # Open browser in a separate thread
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    # Start the server
    server_address = ('localhost', PORT)
    httpd = HTTPServer(server_address, ITCHandler)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        httpd.server_close()
    except Exception as e:
        print(f"\nError: {e}")
        input("Press Enter to exit...")


if __name__ == '__main__':
    main()

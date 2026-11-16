"""
run_website.py
--------------
One-click execution script for the CPU Scheduling Simulator website.

Starts the FastAPI server (which hosts both the scheduling API and
the compiled React/TypeScript frontend), and automatically opens
the web application in the default web browser.

Usage:
    python run_website.py
"""

import os
import sys
import subprocess
import webbrowser
import time

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(base_dir, "frontend", "dist")

    # If the production build is missing, build it first
    if not os.path.exists(dist_dir):
        print("Production frontend build not found. Running npm build...")
        frontend_dir = os.path.join(base_dir, "frontend")
        try:
            subprocess.run(["npm", "run", "build"], cwd=frontend_dir, check=True, shell=True)
        except Exception as e:
            print(f"Error building frontend: {e}")
            print("Please run 'cd frontend && npm install && npm run build' manually.")
            sys.exit(1)

    port = 3000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    elif "--port" in sys.argv:
        idx = sys.argv.index("--port")
        if idx + 1 < len(sys.argv) and sys.argv[idx + 1].isdigit():
            port = int(sys.argv[idx + 1])

    print("=" * 70)
    print("   CPU SCHEDULING SIMULATOR — WEB PLATFORM")
    print("=" * 70)
    print(f"Starting FastAPI web server on http://127.0.0.1:{port} ...")
    print("Press Ctrl+C to terminate the server.\n")

    # Open the browser after a brief delay so the server has bound the port
    def open_browser():
        time.sleep(1.2)
        webbrowser.open(f"http://127.0.0.1:{port}")

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # Launch uvicorn
    try:
        import uvicorn
        uvicorn.run("backend.main:app", host="0.0.0.0", port=port, log_level="info")
    except ImportError:
        print("uvicorn is not installed. Run: pip install uvicorn fastapi")
        sys.exit(1)

if __name__ == "__main__":
    main()

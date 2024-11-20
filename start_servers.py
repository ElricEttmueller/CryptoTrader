import subprocess
import sys
import os
import time
from threading import Thread
from pathlib import Path

def run_frontend():
    frontend_dir = Path('frontend').absolute()
    os.chdir(frontend_dir)
    # First, ensure all dependencies are installed
    subprocess.run(['npm', 'install'], check=True)
    # Then start the development server
    subprocess.run(['npm', 'start'], check=True)

def run_backend():
    backend_dir = Path('backend').absolute()
    os.chdir(backend_dir)
    # Install Python dependencies if requirements.txt exists
    if Path('requirements.txt').exists():
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
    subprocess.run([sys.executable, '-m', 'uvicorn', 'main:app', '--reload', '--host', '0.0.0.0', '--port', '8000'], check=True)

if __name__ == "__main__":
    # Store the original directory
    original_dir = os.getcwd()
    
    try:
        print("Starting backend server...")
        backend_thread = Thread(target=run_backend)
        backend_thread.start()
        
        # Give the backend a moment to start
        time.sleep(2)
        
        print("Starting frontend server...")
        frontend_thread = Thread(target=run_frontend)
        frontend_thread.start()

        # Keep the main thread alive
        frontend_thread.join()
        backend_thread.join()

    except KeyboardInterrupt:
        print("\nShutting down servers...")
        # Change back to the original directory before exiting
        os.chdir(original_dir)
        sys.exit(0)
    except Exception as e:
        print(f"Error: {str(e)}")
        # Change back to the original directory before exiting
        os.chdir(original_dir)
        sys.exit(1)
    finally:
        # Always ensure we return to the original directory
        os.chdir(original_dir)

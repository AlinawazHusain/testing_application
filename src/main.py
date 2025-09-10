import os
import subprocess
import sys
import platform


"""
    Hypercorn Server Runner Script

    This script is used to run a FastAPI app using Hypercorn, a performant ASGI server. 
    It supports production and development configurations and dynamically calculates 
    the number of worker processes based on CPU cores (currently hardcoded to 1 for simplicity).

    Functions:
        get_worker_count(): Returns the recommended number of worker processes.
        run_hypercorn(): Constructs and executes the Hypercorn command with desired configurations.

    Usage:
        python main.py             # Runs in production mode
        python main.py --dev      # Runs in development mode with auto-reload enabled

    Log Format:
        Logs HTTP request details in a structured format for better observability.

    Environment:
        - Requires Hypercorn to be installed in the environment.
        - Expects the FastAPI app to be available at `main:app`.

    Note:
        Adjust worker count in production by uncommenting the `get_worker_count()` line.
"""


def get_worker_count():
    """
    Calculates the optimal number of worker processes for Hypercorn.

    Returns:
        int: Twice the number of CPU cores plus one, based on Gunicorn's recommendation.
    """
    
    return (os.cpu_count() * 2) + 1

def run_hypercorn():
    """
    Builds and executes the Hypercorn server command to run a FastAPI application.

    Supports optional development mode with `--dev` argument, which enables auto-reloading.

    The server binds to `0.0.0.0:80` and logs access requests in a detailed format.
    All server behavior is configured via command-line arguments passed to Hypercorn.
    """
    
    # workers = get_worker_count()
    workers = 1

    log_format = (
    "ip=%(h)s user=%(u)s time=%(t)s request=\"%(r)s\" "
    "status=%(s)s size=%(b)s duration=%(D)sµs"
    )

    command = [
         sys.executable,
        "-m", "hypercorn",
        "app:app",
        "--workers", str(workers),
        "--bind", "0.0.0.0:80",  
        "--access-logfile", "-", 
        "--access-logformat", log_format,
        "--graceful-timeout", "120",
        "--keep-alive", "7", 
        "--max-requests", "5000", 
        "--log-level", "info", 
        "--insecure-bind", "0.0.0.0:80",  
    ]

    is_dev = "--dev" in sys.argv
    if platform.system() != "Windows":
        command += ["--worker-class", "uvloop"]
    if is_dev:
        command.append("--reload")


    subprocess.run(command)

if __name__ == "__main__":
    run_hypercorn()

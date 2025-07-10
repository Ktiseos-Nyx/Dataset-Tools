
import subprocess
import time
import psutil
import sys
from datetime import datetime

# --- Configuration ---
# Command to launch your application.
# This uses sys.executable to ensure it uses the same Python interpreter.
APP_COMMAND = [sys.executable, "-m", "dataset_tools.main"]
# Interval in seconds to poll for resource usage.
POLL_INTERVAL = 1
# --- End Configuration ---

def monitor_application():
    """
    Launches and monitors the resource usage of a specified application.
    """
    print(f"Starting application: '''{' '.join(APP_COMMAND)}'''")
    
    try:
        # Launch the application as a separate process
        app_process = subprocess.Popen(APP_COMMAND)
        
        # Get the process object for monitoring
        p = psutil.Process(app_process.pid)
        print(f"Monitoring process {p.name()} with PID: {app_process.pid}")
        
    except (psutil.NoSuchProcess, FileNotFoundError) as e:
        print(f"Error starting or finding the application process: {e}")
        print("Please ensure the APP_COMMAND in the script is correct.")
        return

    resource_data = []
    print("Monitoring started. Close the application window to generate the report.")

    try:
        # Poll the process until it exits
        while app_process.poll() is None:
            try:
                # Get resource usage
                with p.oneshot():
                    cpu_percent = p.cpu_percent(interval=None)
                    memory_info = p.memory_info()
                    memory_rss_mb = memory_info.rss / (1024 * 1024) # Resident Set Size in MB
                    num_threads = p.num_threads()

                timestamp = datetime.now().isoformat()
                
                resource_data.append({
                    "timestamp": timestamp,
                    "cpu_percent": cpu_percent,
                    "memory_mb": memory_rss_mb,
                    "threads": num_threads,
                })

                # Wait for the next poll interval
                time.sleep(POLL_INTERVAL)

            except psutil.NoSuchProcess:
                # Process was terminated
                break
            except Exception as e:
                print(f"An error occurred during monitoring: {e}")
                break

    finally:
        # Ensure the process is terminated if the script exits unexpectedly
        if app_process.poll() is None:
            print("Terminating application process...")
            p.terminate()
            try:
                p.wait(timeout=3)
            except psutil.TimeoutExpired:
                p.kill()

    print("Application has exited. Generating report...")
    generate_report(resource_data)

def generate_report(data):
    """
    Analyzes the collected data and writes a summary report to a file.
    """
    if not data:
        print("No data was collected. Cannot generate a report.")
        return

    # Calculate statistics
    cpu_values = [d["cpu_percent"] for d in data]
    mem_values = [d["memory_mb"] for d in data]
    
    avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0
    max_cpu = max(cpu_values) if cpu_values else 0
    avg_mem = sum(mem_values) / len(mem_values) if mem_values else 0
    max_mem = max(mem_values) if mem_values else 0
    peak_threads = max(d["threads"] for d in data) if data else 0
    monitoring_duration = (datetime.fromisoformat(data[-1]["timestamp"]) - datetime.fromisoformat(data[0]["timestamp"])).total_seconds()

    # Create report content
    report = f"""
# Resource Usage Report
- **Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Monitoring Duration**: {monitoring_duration:.2f} seconds
- **Polling Interval**: {POLL_INTERVAL} second(s)

## Summary
- **Average CPU Usage**: {avg_cpu:.2f}%
- **Maximum CPU Usage**: {max_cpu:.2f}%
- **Average Memory Usage**: {avg_mem:.2f} MB
- **Maximum Memory Usage**: {max_mem:.2f} MB
- **Peak Thread Count**: {peak_threads}

## Raw Data
Timestamp, CPU (%), Memory (MB), Threads
"""
    for entry in data:
        report += f"{entry['timestamp']}, {entry['cpu_percent']:.2f}, {entry['memory_mb']:.2f}, {entry['threads']}\n"

    # Write report to a timestamped file
    filename = f"resource_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        with open(filename, "w") as f:
            f.write(report)
        print(f"Successfully saved report to: {filename}")
    except IOError as e:
        print(f"Error writing report file: {e}")

if __name__ == "__main__":
    monitor_application()

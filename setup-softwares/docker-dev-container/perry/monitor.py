import os, subprocess
import time
import signal
import sys

username = sys.argv[1]
questionID = sys.argv[2]
lang = sys.argv[3]

def run_test_script():
    """
    Execute the test script
    """
    try:
        os.system(f"python3 /dspcoder/perry/perry.py {username} {questionID} {lang} d")
    except subprocess.CalledProcessError as e:
        # print ("failed for perry")
        pass

def monitor_process():
    """
    Monitor the target process and run test script when found
    """
    test_script_running = False
    
    while True:
        try:
            # Check if the process is running
            output = subprocess.check_output(['ps', 'aux']).decode()
            
            if "extensions/kylinideteam.cppdebug" in output or "OpenDebugAD7" in output:
                # If test script is not already running, start it
                if not test_script_running:
                    run_test_script()
                    test_script_running = True
            else:
                # Reset the flag if process is not running
                test_script_running = False
            
            # Wait before next check
            time.sleep(2)
            # print(f"{test_script_running}, ps-> ", "extensions/kylinideteam.cppdebug" in output or "OpenDebugAD7" in output)
        except Exception as e:
            # print(f"Monitoring error: {e}")
            time.sleep(1)

def signal_handler(signum, frame):
    """
    Handle interruption signals
    """
    print("\nUser space debug monitoring stopped.")
    sys.exit(0)

def main():
    # Register signal handlers for clean exit
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start monitoring
    monitor_process()

if __name__ == "__main__":
    main()
import os
import subprocess
import sys
import signal
from datetime import datetime

class ErrorCounter:
    def __init__(self):
        self.count = 0
        self.process = None
        
    def increment(self):
        self.count += 1
        print(f"\n🚨 Error count: {self.count}")
            

error_counter = ErrorCounter()

def check_for_specific_error(line, error_log_path, context):
    """Check for the target error across multiple lines."""
    # Look for the FAILURES section
    if "================================== FAILURES ===================================" in line:
        context['collecting_failure'] = True
        context['buffer'] = [line]
        return False

    # If we're collecting the failure details
    if context.get('collecting_failure'):
        context['buffer'].append(line)
        
        # Check if we have the complete failure info
        full_context = "".join(context['buffer'])
        if (
            "test___ao_current_task___get_bool_property___returns_default_value" in full_context 
            and "AssertionError" in full_context
            and "assert False" in full_context
            and "where False = OutStream" in full_context
        ):
            error_counter.increment()
            print("\n🚨 DETECTED TARGET ERROR! Stopping execution...\n")
            error_text = f"Error detected in test output:\n{full_context}"
            
            with open(error_log_path, 'a') as f:
                f.write(f"\n=== Error detected at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                f.write(error_text)
                f.write("\n=====================================\n")
            
            return True
        
        # Reset if we've collected too many lines without finding the error
        if len(context['buffer']) > 20:
            context['collecting_failure'] = False
            context['buffer'] = []

    return False

def run_command(command, check=True):
    """Run command and monitor output for target error."""
    print(f"Running: {command}")
    error_log_path = os.path.join(os.getcwd(), 'error_log.txt')
    context = {'test_seen': False, 'buffer': []}
    
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            shell=True,
            preexec_fn=os.setsid if os.name != 'nt' else None,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        )
        error_counter.process = process
        
        for line in process.stdout:
            print(line, end='')
            if check_for_specific_error(line, error_log_path, context):
                return True
            
        process.wait()
        if check and process.returncode != 0 and error_counter.count == 0:
            sys.exit(process.returncode)
            
    except Exception as e:
        print(f"Error running command: {e}")
        sys.exit(1)
    finally:
        error_counter.process = None
    
    return False

def main():
    error_log_path = os.path.join(os.getcwd(), 'error_log.txt')
    if os.path.exists(error_log_path):
        os.remove(error_log_path)
    
    config_path = r"C:\nidaqmxconfig\targets\win64U\x64\msvc-14.0\release\nidaqmxconfig.exe"
    ini_path = os.path.join(os.getcwd(), "tests", "max_config", "nidaqmxMaxConfig.ini")
    
    if not os.path.exists(config_path):
        print(f"Error: Could not find nidaqmxconfig.exe at {config_path}")
        sys.exit(1)

    if not os.path.exists(ini_path):
        print(f"Error: Could not find config file at {ini_path}")
        sys.exit(1)

    config_command = f'"{config_path}" --eraseconfig --import "{ini_path}"'
    iterations = 0
    
    try:
        while True:
            iterations += 1
            print(f"\n--- Iteration {iterations} ---\n")
            
            run_command(config_command)
            if run_command("poetry run tox"):
                break  # Error found, stop iterations
            
    except KeyboardInterrupt:
        print("\nScript interrupted by user")
    finally:
        # Log final statistics
        with open(error_log_path, 'a') as f:
            f.write(f"\n=== Script stopped at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            f.write(f"Total iterations: {iterations}\n")
            f.write(f"Total error count: {error_counter.count}\n")
            f.write("=====================================\n")
        print(f"\nFinal Statistics:")
        print(f"Total iterations: {iterations}")
        print(f"Total error count: {error_counter.count}")
        print(f"See {error_log_path} for detailed error log")

if __name__ == "__main__":
    main()
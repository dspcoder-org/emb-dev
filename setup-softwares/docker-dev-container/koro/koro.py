from typing import Union, Tuple, Any, Optional
import importlib.util
import inspect, sys, re, os
from time import time
from threading import Timer
from ValgrindAnalyzer import *
import filecmp, glob
import subprocess, threading
import signal

# add dir path for json handler lib
sys.path.append('/dspcoder/')
from JSONHandler import *


class TimeoutException(Exception):
    """Custom exception for handling timeouts."""
    pass


def alarm_handler(signum, frame):
    """Signal handler for the timeout alarm."""
    raise TimeoutException("Timeout reached")

# Set the global signal handler for the timeout
signal.signal(signal.SIGALRM, alarm_handler)


class Koro:
    def __init__(self, username = sys.argv[1], questionID = sys.argv[2], lang = sys.argv[3], test_type = sys.argv[4]):
        i = questionID.find('_')+1
        self.foldername = self.capitalize_after_underscore(questionID[i].upper() + questionID[i+1:] + "_" + lang)
        self.jworker = testJsonHandler("/tmp/", self.foldername) # creating Run json for extension at /tmp
        self.submit_res = {"metadata": {}, "test_cases": {}}
        try:
            self.profiling = True if sys.argv[5] == 'p' else False
        except:
            self.profiling = False
        self.username = username
        self.test_type = test_type
        self.test_script_path = f"/dspcoder/codeFromServer/{self.foldername}/._tests/test.py"
        if self.test_type == 'r' or self.test_type == 's':
            self.test_executable = self.set_test_executable()
        else:
            self.test_executable = None # for case 'b' and 'br' it will get updated later after the build
        self.internal_executable = f"/dspcoder/codeFromServer/{self.foldername}/._dev/a.out"
        self.test_cases = None
        self.test_function_metadata = {}  # Store metadata for each test function
        if self.test_type != 'b':
            self.load_test_cases()
        else:
            self.build()
    
    def capitalize_after_underscore(self, snake_str):
        """Capitalize letters after underscores and retain underscores."""
        result = []
        capitalize_next = False

        for char in snake_str:
            if char == '_':
                result.append(char)
                capitalize_next = True
            elif capitalize_next:
                result.append(char.upper())
                capitalize_next = False
            else:
                result.append(char)

        return ''.join(result)

    def build(self):
        usr_make_path = f"/home/{self.username}/{self.foldername}/Makefile"
        flag = True
        if os.path.exists(usr_make_path):
            msg = ""
            identical = filecmp.cmp(usr_make_path, f"/dspcoder/codeFromServer/{self.foldername}/Makefile")
            if not identical:
                msg += "WARNING: Makefile seems changed, compilation might get failed.\n"

            # Command to run in subprocess
            command = f'su {self.username} -c "cd /home/{self.username}/{self.foldername} && make clean || true && make"'
            
            # Execute the command
            process = subprocess.Popen([command], 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE,
                                    text=True,
                                    shell=True)
            stdout, stderr = process.communicate()
            
            error_patterns = [
                r'error:', 
                r'Error', 
                r'ERROR',
                r'make(\[\d+\])?: \*\*\*',  # Matches make error format like "make[1]: ***"
                r'undefined reference to',
                r'command not found',
                r'fatal error:',
                r'compilation failed',
            ]
            
            # Check for errors in both stdout and stderr
            output = stdout + stderr
            for line in output.split('\n'):
                if any(re.search(pattern, line, re.IGNORECASE) for pattern in error_patterns):
                    self.jworker.update_metadata(compiled="FAIL")
                    flag = False
            if flag:
                self.jworker.update_metadata(compiled="PASS")
            msg += output
            self.jworker.update_metadata(compilation_output=msg)
            
            # updating json with the name of newly created bin name
            files = glob.glob(f"/home/{self.username}/{self.foldername}/*")
            most_recent_file = max(files, key=os.path.getmtime)
            if os.access(most_recent_file, os.X_OK):
                self.jworker.update_metadata(exe= "./"+os.path.basename(most_recent_file))

            self.test_executable = self.set_test_executable()

        else:
            self.jworker.update_metadata(compiled="FAIL", compilation_output="Makefile can't be found at the root directory of the question's workspace.")
        
        if not flag:
            raise Exception("Compilation Failed: Further execution is not required. \n**koro Terminated**\n")

    def set_test_executable(self):
        """
        Set the test executable path, first trying the full path with /home/{username}/{foldername},
        then trying a truncated path if the full path does not exist.
        """
        exe_name = self.jworker.get_metadata()['exe']
        # Initial full path
        test_executable = f"/home/{self.username}/{self.foldername}/{exe_name}"
        
        # Sanitize path to remove redundant slashes and dots
        test_executable = re.sub(r'/+', '/', test_executable)  # Replace multiple slashes with a single slash
        test_executable = re.sub(r'(/\./)|(\./)', '/', test_executable)  # Remove './' or '/.' patterns

        if os.path.exists(test_executable) and os.access(test_executable, os.X_OK) and test_executable[-1]!="/":
            return test_executable
        else:
            # Try the truncated path by removing `/home/{username}/{self.foldername}`
            test_executable = f"/{exe_name}"
            
            if os.path.exists(test_executable) and os.access(test_executable, os.X_OK) and test_executable[-1]!="/":
                return test_executable
            else:
                self.jworker.update_metadata(exe="",
                                            compilation_output= "Test executable not found at given path. Make sure to compile first or \n provide correct path for exe in dspcoder panel.")
                # Terminating Koro, Since no further execution required
                raise Exception("Test executable not found at either full or truncated paths.")

    def load_test_cases(self):
        """
        Load the testCases class from the test script file located at `self.test_script_path`
        and store the class instance in self.test_cases.
        """
        # Load the module from the specified file path
        spec = importlib.util.spec_from_file_location("test_module", self.test_script_path)
        test_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_module)
        
        # Access the testCases class from the module
        setattr(test_module, "execute_bin", self.run_exe_with_input)
        self.test_cases = getattr(test_module, 'testCases')(self.test_executable)
        
        # Ensure RUN, exe, and default_timeout_window attributes exist in testCases
        if not all(hasattr(self.test_cases, attr) for attr in ['RUN', 'exe', 'default_timeout_window', 'usage']):
            return "koro: The testCases class must have RUN, exe, default_timeout_window attributes, and usage."
            # raise AttributeError("The testCases class must have RUN, exe, default_timeout_window attributes, and usage.")
        
        if self.test_cases.usage != 'prod':
            return "koro: Usage of testCases class must be 'prod', set usage to 'prod' in init."
            #raise Exception("koro: Usage of testCases class must be 'prod', set usage to 'prod' in init.")
        

    def get_test_case_methods(self):
        """
        Get all methods in testCases class that start with 'test_case' and extract metadata.
        """
        test_case_methods = []
        
        for name, func in inspect.getmembers(self.test_cases, predicate=inspect.ismethod):
            if name.startswith('test_case'):
                # Extract default parameter values for timeout_window and override if available
                sig = inspect.signature(func)
                timeout_window = sig.parameters.get('timeout_window').default if 'timeout_window' in sig.parameters else None
                override = sig.parameters.get('override').default if 'override' in sig.parameters else None

                # Store metadata for future use
                self.test_function_metadata[name] = {
                                                        'timeout_window': timeout_window,
                                                        'override': override
                                                    }

                test_case_methods.append(func)

        return test_case_methods

    def run_exe_with_input(self, input_data: Any, exe: str, timeout: Optional[float] = None) -> Tuple[str, str, float]:
        """
        Run a compiled executable with provided input data using both signal-based and subprocess timeout mechanisms.

        Args:
            input_data: Input data of any type to be passed to the executable
            exe: Path to the executable
            timeout: Maximum execution time in milliseconds (default: None, uses 5000ms)

        Returns:
            Tuple[str, str, float]: (output, error, execution_time)
                - output: Program output or error message
                - error: Error message if any, None otherwise
                - execution_time: Execution time in milliseconds
        """
        # Input validation
        if not exe or not isinstance(exe, str):
            return "", "Invalid executable path", 0
        
        if not os.path.exists(exe):
            return "", f"Executable not found: {exe}", 0
        
        if not os.access(exe, os.X_OK):
            return "", f"Permission denied: {exe}", 0

        # Convert input data to string format with proper error handling
        try:
            if isinstance(input_data, (list, tuple)):
                input_str = '\n'.join(map(str, input_data)) + '\n'
            else:
                input_str = f"{str(input_data)}\n"
        except Exception as e:
            return "", f"Input data conversion error: {str(e)}", 0

        # Initialize variables
        process = None
        output = ""
        err = None
        execution_time = 0
        timeout_secs = (timeout or 50000) / 1000  # Convert ms to seconds, default 5s
        timeout_occurred = False

        def timeout_handler(signum, frame):
            """Signal handler for the timeout alarm."""
            nonlocal timeout_occurred
            timeout_occurred = True
            if process:
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                except:
                    pass
            raise TimeoutException("Timeout reached")

        # Set up signal handler
        original_handler = signal.signal(signal.SIGALRM, timeout_handler)

        try:
            # Start process with stricter parameters
            process = subprocess.Popen(
                [exe],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True,
                preexec_fn=os.setsid,  # Create new process group
                env=os.environ.copy()   # Use clean environment
            )

            # Set up both timeouts
            signal.setitimer(signal.ITIMER_REAL, timeout_secs)
            start_time = time() * 1000

            try:
                # Use communicate with timeout as a backup
                stdout, stderr = process.communicate(input=input_str, timeout=timeout_secs)
                execution_time = (time() * 1000) - start_time
                output = stdout.strip()
                err = stderr.strip() if stderr else None

            except (subprocess.TimeoutExpired, TimeoutException):
                timeout_occurred = True
                # Handle timeout by terminating the process group
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    # Give it 1 second to terminate gracefully
                    process.wait(timeout=1)
                except:
                    try:
                        # Force kill if still running
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    except:
                        pass
                
                output = "Timed out"
                execution_time = timeout or 5000  # Return the full timeout duration

        except FileNotFoundError:
            output = ""
            err = f"Executable '{exe}' not found"
        
        except PermissionError:
            output = ""
            err = f"Permission denied to execute '{exe}'"
        
        except Exception as e:
            output = ""
            err = f"Execution error: {str(e)}"

        finally:
            # Reset signal handler and timer
            signal.signal(signal.SIGALRM, original_handler)
            signal.setitimer(signal.ITIMER_REAL, 0)

            # Ensure process cleanup
            if process:
                try:
                    if process.poll() is None:
                        # If process is still running, force kill it
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    
                    # Close file descriptors
                    if process.stdout:
                        process.stdout.close()
                    if process.stderr:
                        process.stderr.close()
                    if process.stdin:
                        process.stdin.close()
                    
                    process.kill()
                    process.wait(timeout=1)
                except:
                    pass

            # If timeout occurred but we somehow got here without proper cleanup
            if timeout_occurred and not output:
                output = "Timed out"
                execution_time = timeout or 5000

        return output, err, execution_time

    def run_tests(self):
        """
        Run the test cases based on the test type. If test type is 'r', run only up to `RUN` methods.
        Otherwise, run all methods starting with 'test_case'.
        """
        val_arg = None
        if self.test_type == "r" or self.test_type == "br":
            if self.test_type == "br":
                self.build()

            cases = self.jworker.get_all_test_cases()
            for case_id, case_data in cases.items():
                if val_arg == None:
                    val_arg = case_data['input']
                out1, _, time1 = self.run_exe_with_input(input_data=case_data['input'], exe=self.internal_executable)
                out2, err2, time2 = self.run_exe_with_input(input_data=case_data['input'], exe=self.test_executable, timeout=time1+self.test_cases.default_timeout_window)
                if err2 or "._bad_input" in out2 :
                    self.jworker.update_test_case(case_id, status="FAIL", expected="", output=err2)
                else:
                    if out1 == out2:
                        self.jworker.update_test_case(case_id, status="PASS", expected=out1, output=out2)
                    else:
                        self.jworker.update_test_case(case_id, status="FAIL", expected=out1, output=out2)
        
        # Run all methods
        elif self.test_type == "s":
            failFlag = False
            TT = 0
            for test_method in self.get_test_case_methods():
                # override = 0
                # reserved for test.py developer

                # override = 1
                if self.test_function_metadata[test_method.__name__]["override"] == 1:
                    timeout = self.test_function_metadata[test_method.__name__]["timeout_window"] or self.test_cases.default_timeout_window
                    execution_time = 0

                    # Create an Event for thread synchronization
                    completed = threading.Event()
                    result = [None]
                    error_occurred = [False]

                    def run_test(self):
                        try:
                            result[0] = test_method()
                            completed.set()
                        except Exception as e:
                            error_occurred[0] = True
                            result[0] = str(e)
                            completed.set()

                    thread = threading.Thread(target=run_test, args=(self,))
                    thread.daemon = True  # Mark as daemon so it won't prevent program exit
                    
                    start_time = time() * 1000

                    thread.start()
                    # Wait for either completion or timeout
                    completed.wait(timeout=timeout/1000)  # Convert ms to seconds

                    execution_time = time() * 1000 - start_time

                    if completed.is_set():
                        if error_occurred[0] or "._bad_input" in result[0]:
                            self.submit_res["test_cases"][test_method.__name__] = {"status": "FAIL"}
                            failFlag = True
                        else:
                            test_passed = result[0]
                            self.submit_res["test_cases"][test_method.__name__] = {"status": "PASS" if test_passed else "FAIL"}
                            if not test_passed:
                                failFlag = True
                    else:
                        # Timeout occurred
                        self.submit_res["test_cases"][test_method.__name__] = {"status": "FAIL"}
                        failFlag = True
                        execution_time = timeout

                    TT+=execution_time

                # Default case
                else:
                    try:
                        ip, _ = test_method()
                    except:
                        ip = test_method()

                    if val_arg == None:
                        val_arg = ip
                    out1, _, time1 = self.run_exe_with_input(input_data=ip, exe=self.internal_executable)
                    out2, err2, time2 = self.run_exe_with_input(input_data=ip, exe=self.test_executable, timeout=time1+self.test_cases.default_timeout_window)
                    if err2 or "._bad_input" in out2:
                        self.submit_res["test_cases"][test_method.__name__]={"status": "FAIL"}
                    else:
                        if out2 == out1:
                            self.submit_res["test_cases"][test_method.__name__]={"status": "PASS"}
                        else:
                            self.submit_res["test_cases"][test_method.__name__]={"status": "FAIL"}
                            failFlag = True
                    TT+=time2
            self.submit_res["metadata"]["Total_Time"] = TT
            self.submit_res["metadata"]["overall_status"] = "FAIL" if failFlag else "PASS"

        else:
            return "koro : Invalid Run Type: Third Koro argument must be one of the identifier from 'r', 'br', 'b', or s"
            # raise Exception("Invalid Run Type: Third Koro argument must be one of the identifier from 'r', 'br', 'b', or s")
        
        # final valgrind check 
        memStat = {}
        if self.profiling:
            if isinstance(val_arg, (list, tuple)):
                val_arg = '\n'.join(map(str, val_arg)) + '\n'
            else:
                val_arg = f"{str(val_arg)}\n"
            analyzer = ValgrindAnalyzer(self.test_executable, input=val_arg)
            memStat = {"footprint": analyzer.get_memory_footprint(), "memory_leak":analyzer.check_memory_leaks(), "cache_profile":analyzer.get_cache_profile()}
        self.jworker.update_metadata(mem_stat=memStat)
        self.submit_res["metadata"]["mem_stat"] = memStat

        # saving Submit results in /dspcoder/results
        if self.test_type == 's':
            with open(f'/dspcoder/results/{self.foldername}.json', 'w') as file:
                json.dump(self.submit_res, file, indent=4)


#######################
#   Koro driver code  #
#######################
tester = Koro()

if sys.argv[4] == 'b':
    tester.build()
else:    
    tester.run_tests()
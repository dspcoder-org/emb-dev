from renode import renodeAutomation
import sys, os, importlib.util, inspect
import signal, threading, subprocess
import time
import inspect, sys, re, os
from typing import Union, Tuple, Any, Optional
import inspect, sys, re, os
from threading import Timer
import filecmp, glob
import subprocess, threading
import signal

renode_path = "/dspcoder/renode/renode"
qemu_path = ""


# add dir path for json handler lib
sys.path.append('/dspcoder/')
from JSONHandler import *

def timeout_handler(signum, frame):
    os.system("pkill -f dotnet")
    raise TimeoutError("Test Execution Timed Out")

def debug_timeout_handler(signum, frame):
    os.system("pkill -f dotnet")
    raise TimeoutError("Debugger Terminated")


class perry:
    def __init__(self, username = sys.argv[1], questionID = sys.argv[2], lang = sys.argv[3], test_type = sys.argv[4]):
        self.renode = renodeAutomation(renode_path)
        self.qemu = None
        self.username = username
        i = questionID.find('_')+1
        self.foldername = self.capitalize_after_underscore(questionID[i].upper() + questionID[i+1:] + "_" + lang)
        self.jworker = testJsonHandler("/tmp/", self.foldername) # creating Run json for extension at /tmp
        self.submit_res = {"metadata": {}, "test_cases": {}}
        self.run = 0
        self.test_type = test_type
        self.test_script_path = f"/dspcoder/codeFromServer/{self.foldername}/._tests/test.py"
        self.debug_script_path = f"/dspcoder/codeFromServer/{self.foldername}/._tests/debug.py"
        if self.test_type == 'r' or self.test_type == 's' or self.test_type == 'd':
            self.test_executable = self.set_test_executable()
        else:
            self.test_executable = None # for case 'b' and 'br' it will get updated later after the build

        self.test_cases = None
        self.test_function_metadata = {}  # Store metadata for each test function
        if self.test_type != 'b':
            self.load_test_cases()



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


    def execute_cmd(self, cmd, stopPrompt):
        """
        Executes a command based on the simulator being used.
        """
        if self.sim == "renode":
            if cmd == "loadElf":
                return self.renode.executeCmd(f"sysbus LoadELF @{self.test_executable}", stopPrompt=stopPrompt)
            else:      
                return self.renode.executeCmd(cmd, stopPrompt=stopPrompt)
        elif self.sim == "qemu":
            return self.qemu.executeCmd(cmd)
        else:
            raise Exception(f"SIM TYPE Error: {self.sim} is Invalid")


    def set_test_executable(self):
        """
        Set the test executable path, first trying the full path with /home/{username}/{foldername},
        then trying a truncated path if the full path does not exist.
        """
        exe_name = self.jworker.get_metadata()['exe']
        launch_json_file_path = f"/home/{self.username}/{self.foldername}/.vscode/launch.json"
        # Initial full path
        test_executable = f"/home/{self.username}/{self.foldername}/{exe_name}"
        
        # Sanitize path to remove redundant slashes and dots
        test_executable = re.sub(r'/+', '/', test_executable)  # Replace multiple slashes with a single slash
        test_executable = re.sub(r'(/\./)|(\./)', '/', test_executable)  # Remove './' or '/.' patterns

        if os.path.exists(test_executable) and os.access(test_executable, os.X_OK) and test_executable[-1]!="/":
            # updating the launch.json with test_executable
            with open(launch_json_file_path, "r") as file:
                content = file.read()
                content = re.sub(r'//.*', '', content)  # Remove comments
                data = json.loads(content)

            # Update the "program" field
            data["configurations"][0]["program"] = f"${{workspaceFolder}}/{os.path.basename(test_executable)}"

            # Write the updated JSON back
            with open(launch_json_file_path, "w") as file:
                json.dump(data, file, indent=2)
            return test_executable
        else:
            # Try the truncated path by removing `/home/{username}/{self.foldername}`
            test_executable = f"/{exe_name}"
            
            if os.path.exists(test_executable) and os.access(test_executable, os.X_OK) and test_executable[-1]!="/":
                # updating the launch.json with test_executable
                with open(launch_json_file_path, "r") as file:
                    content = file.read()
                    content = re.sub(r'//.*', '', content)  # Remove comments
                    data = json.loads(content)

                # Update the "program" field
                data["configurations"][0]["program"] = f"${{workspaceFolder}}/{os.path.basename(test_executable)}"

                # Write the updated JSON back
                with open(launch_json_file_path, "w") as file:
                    json.dump(data, file, indent=2)
                return test_executable
            else:
                self.jworker.update_metadata(exe="",
                                            compilation_output= "Test executable not found at given path. Make sure to compile first or \n provide correct path for exe in dspcoder panel.")
                # Terminating Koro, Since no further execution required
                raise Exception("Test executable not found at either full or truncated paths.")


    def get_test_case_methods(self):
        """
        Get all methods in testCases class that start with 'test_case' and extract metadata.
        """
        test_case_methods = []
        
        if self.test_type == 'd':
            for name, func in inspect.getmembers(self.test_cases, predicate=inspect.ismethod):
                if name.startswith('test_debug'):
                    test_case_methods.append(func)
            return test_case_methods

        for name, func in inspect.getmembers(self.test_cases, predicate=inspect.ismethod):
            if name.startswith('test_case'):
                # Extract default parameter values for timeout_window and override if available
                sig = inspect.signature(func)
                timeout_window = sig.parameters.get('timeout').default if 'timeout' in sig.parameters else None

                # Store metadata for future use
                self.test_function_metadata[name] = {
                                                        'timeout': timeout_window,
                                                    }

                test_case_methods.append(func)

        return test_case_methods

    def load_test_cases(self):
        """
        Load the testCases class from the test script file located at `self.test_script_path`
        and store the class instance in self.test_cases.
        """
        if self.test_type == 'd':
            # Load the module from the specified file path
            spec = importlib.util.spec_from_file_location("debug_module", self.debug_script_path)
            debug_module = importlib.util.module_from_spec(spec)
            # Inject the cmd() function from the perry class into the test module
            setattr(debug_module, "cmd", self.execute_cmd)
            spec.loader.exec_module(debug_module)
            if self.test_executable == None:
                    self.build()
            self.test_cases = getattr(debug_module, 'debugCases')()

            
            # Ensure RUN, exe attributes exist in debugCases
            if not all(hasattr(self.test_cases, attr) for attr in ["usage", "sim"]):
                return "perry : The debugCases class must have sim (simulator), and usage."
                # raise AttributeError("The debugCases class must have sim (simulator), and usage.")
            
            if self.test_cases.usage != 'prod':
                return "perry : Usage of debugCases class must be 'prod', set usage to 'prod' in init."
                # raise Exception("Perry: Usage of debugCases class must be 'prod', set usage to 'prod' in init.")
            
            self.sim = self.test_cases.sim
            return 0

        # Load the module from the specified file path
        spec = importlib.util.spec_from_file_location("test_module", self.test_script_path)
        test_module = importlib.util.module_from_spec(spec)
        # Inject the cmd() function from the perry class into the test module
        setattr(test_module, "cmd", self.execute_cmd)
        spec.loader.exec_module(test_module)
        if self.test_executable == None:
                self.build()
        self.test_cases = getattr(test_module, 'testCases')(self.test_executable)
        
        # Ensure RUN, exe, and default_timeout_window attributes exist in testCases
        if not all(hasattr(self.test_cases, attr) for attr in ['RUN', 'exe', 'default_timeout', 'usage', 'sim']):
            return "perry : The testCases class must have RUN, exe, default_timeout attributes, sim, and usage."
            # raise AttributeError("The testCases class must have RUN, exe, default_timeout attributes, sim, and usage.")
        
        if self.test_cases.usage != 'prod':
            return "perry : Usage of testCases class must be 'prod', set usage to 'prod' in init."
            # raise Exception("Perry: Usage of testCases class must be 'prod', set usage to 'prod' in init.")
        
        self.run = self.test_cases.RUN
        self.sim = self.test_cases.sim

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
            raise Exception("Compilation Failed: Furhter execution is not required. \n**Perry Terminated**\n")

    def run_with_timeout(self, func, timeout_value):
        """
        Run the provided function with a timeout.
        Returns (result, timed_out)
        """
        def monitor_process():
            time.sleep(10)
            while 1:
                output = subprocess.check_output(['ps', 'aux']).decode()
                if "extensions/kylinideteam.cppdebug" in output:
                    signal.alarm(0)
                else:
                    signal.alarm(1)
                    break

        if self.test_type == "d":
            # Set the signal handler and the alarm for the timeout
            signal.signal(signal.SIGALRM, debug_timeout_handler)
            signal.alarm(30)  # Set alarm for timeout

            monitor_thread = threading.Thread(target=monitor_process, daemon=True)
            monitor_thread.start()

            func() # start debug.py function
            
        else:
            # Set the signal handler and the alarm for the timeout
            timeout_value = timeout_value/1000
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.setitimer(signal.ITIMER_REAL, timeout_value)  # Set alarm for timeout

            try:
                result = func()
                signal.setitimer(signal.ITIMER_REAL, 0)  # Disable alarm if the function completes within time
                return result, False
            except TimeoutError:
                return None, True
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)   # Ensure alarm is disabled

    def run_tests(self):
        for i, testFun in enumerate(self.get_test_case_methods()[:self.run]):
            out, timeout = self.run_with_timeout(testFun, timeout_value = self.test_function_metadata[testFun.__name__]["timeout"] or self.test_cases.default_timeout)
            ip, expected = out[0], out[1]
            if timeout:
                self.jworker.update_test_case(f"Case {i+1}", status="FAIL", expected=ip, output="Timed out")
            elif "PASS" == self.test_cases.msg:
                self.jworker.update_test_case(f"Case {i+1}", status="PASS", expected=ip, output=expected)
            else:
                self.jworker.update_test_case(f"Case {i+1}", status="FAIL", expected=ip, output=self.test_cases.msg)

    def debug(self):
        self.run_with_timeout(self.get_test_case_methods()[0], timeout_value = None)

    def submit(self):
        failFlag = False
        start_time = time.time() * 1000
        for i, testFun in enumerate(self.get_test_case_methods()):
            out, timeout = self.run_with_timeout(testFun, timeout_value = self.test_function_metadata[testFun.__name__]["timeout"] or self.test_cases.default_timeout)
            ip, expected = out[0], out[1]
            if timeout:
                self.submit_res["test_cases"][testFun.__name__]={"status": "FAIL"}
                failFlag = True
            elif "PASS" == self.test_cases.msg:
                self.submit_res["test_cases"][testFun.__name__]={"status": "PASS"}
            else:
                self.submit_res["test_cases"][testFun.__name__]={"status": "FAIL"}
                failFlag = True
        TT = time.time() * 1000 - start_time
        self.submit_res["metadata"]["Total_Time"] = TT
        self.submit_res["metadata"]["overall_status"] = "FAIL" if failFlag else "PASS"

        # saving Submit results in /dspcoder/results
        if self.test_type == 's':
            with open(f'/dspcoder/results/{self.foldername}.json', 'w') as file:
                json.dump(self.submit_res, file, indent=4)



#######################
#  Perry driver code  #
#######################
tester = perry()

if sys.argv[4] == 'b':
    tester.build()
elif sys.argv[4] == 'd':
    tester.debug()
elif sys.argv[4] == 's':
    tester.submit()
else:    
    tester.run_tests()


# cleanup
os.system("pkill -f dotnet")
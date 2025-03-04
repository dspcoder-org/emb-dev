import concurrent.futures
import importlib.util
import inspect
import subprocess
import os, re
import sys

# Add directory path for JSON handler library
sys.path.append('/dspcoder/')
from JSONHandler import testJsonHandler

# ------------------------------- #
#           Constants             #
# ------------------------------- #
DATA_FILE_PATH = "/dspcoder/.data"
CODE_BASE_SCRIPT = "/dspcoder/scripts/setupCodeBase.sh"
CODE_SERVER_CMD = "code-server --install-extension"
TESTS_PATH = "/dspcoder/codeFromServer/{foldername}/._tests/test.py"

# ------------------------------- #
#       Argument Handling         #
# ------------------------------- #
# Read command-line arguments
username = sys.argv[1]
questionID = sys.argv[2]
lang = sys.argv[3]
question_type = questionID[0]
original = bool(sys.argv[4]) if len(sys.argv) > 4 else False
# Format folder name
i = questionID.find('_')+1
foldername = questionID[i].upper() + questionID[i+1:] + "_" + lang


# ------------------------------- #
#        Helper Functions         #
# ------------------------------- #
def capitalize_after_underscore(snake_str):
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

def dummyHandler(*args):
    '''
    Dummy function for test file support
    '''
    return ""

foldername = capitalize_after_underscore(foldername)

# ------------------------------- #
#       Setup Commands            #
# ------------------------------- #
commands = [
    f'su "{username}" -c "{CODE_SERVER_CMD} /bin/dspcoder-panel-0.0.1.vsix"',
    f'su "{username}" -c "{CODE_SERVER_CMD} llvm-vs-code-extensions.vscode-clangd"',
    f'su "{username}" -c "{CODE_SERVER_CMD} kylinideteam.cppdebug"',
    f'sh {CODE_BASE_SCRIPT} -c "{username}" "{foldername}"'
]


# ------------------------------- #
#      JSON Handling Setup        #
# ------------------------------- #
def touchJSON():
    """Load question folder from the azure storage"""
    os.system(f"mkdir /dspcoder/codeFromServer/{foldername}")
    os.system(f"python3 /dspcoder/azure_setup/download.py {questionID} {lang} {original} {username} {foldername}")

    """Prepare and initialize the test JSON using the given test file."""
    file_path = TESTS_PATH.format(foldername=foldername)

    # Load the test module dynamically
    spec = importlib.util.spec_from_file_location("module_name", file_path)
    module = importlib.util.module_from_spec(spec)
    if question_type == "2": # for EMB
        setattr(module, "cmd", dummyHandler)
    spec.loader.exec_module(module)

    # Extract the testCases class
    test_class = getattr(module, "testCases", None)
    if not test_class:
        print("No testCases class found in the file.")
        return

    test_instance = test_class(None)
    run_count = getattr(test_instance, "RUN", None)
    if not run_count:
        print("No RUN attribute found in the testCases class.")
        return

    # Extract and sort test methods based on the numeric suffix in the name
    test_methods = sorted(
        [
            method
            for name, method in inspect.getmembers(test_instance, predicate=inspect.ismethod)
            if name.startswith("test_case")
        ][:run_count],
        key=lambda method: int(re.search(r"\d+$", method.__name__).group())
    )

    # Initialize JSON handler
    json_handler = testJsonHandler(file_path="/tmp/", file_name=foldername, touch=True)
    if question_type == "1":
        json_handler.update_metadata(type="DSA", exe="./a.out")
    elif question_type == "2":
        json_handler.update_metadata(type="EMB", exe="./out.elf")
        os.system(f"python3 /dspcoder/perry/monitor.py {username} {questionID} {lang} &") # starting monitor for debugger
    else:
        raise ValueError("Error: Wrong question type, Check the question ID")

    # Append test cases to JSON
    for test_method in test_methods:
        try:
            result, _ = test_method()
        except:
            result = test_method()
        json_handler.append_test_case(
            status="", input_data=result, expected="", output=""
        )


# ------------------------------- #
#       Command Execution         #
# ------------------------------- #
def run_command(command):
    """Execute a shell command."""
    process = subprocess.Popen(command, shell=True)
    process.communicate()


# ------------------------------- #
#        Main Execution           #
# ------------------------------- #
def main():
    # Check if data file exists to determine which commands to run
    if os.path.exists(DATA_FILE_PATH):
        commands_to_run = commands[3:]  # Skip extension installations
    else:
        with open(DATA_FILE_PATH, 'w') as file:
            file.write("Necessary extensions are installed.")
        commands_to_run = commands

    # Execute commands in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(run_command, cmd) for cmd in commands_to_run]
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Command failed with exception: {e}")


if __name__ == "__main__":
    # dwonload from blob & initialize JSON
    touchJSON()
    
    # Build the internal executable based on the question type
    if question_type == "1": # for DSA
        build_cmd = f'cd /dspcoder/codeFromServer/{foldername}/._dev && sh build.sh'
        process = subprocess.Popen([build_cmd], 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE,
                                text=True,
                                shell=True)
        stdout, stderr = process.communicate()
    main()


import sys
import os
import subprocess


container_name = "/tmp"
questionID = sys.argv[1]
lang = sys.argv[2]
original = True if sys.argv[3]=="True" else False
username = sys.argv[4]
foldername = sys.argv[5]

# questionID = "00001_reverse_linked_list"
# lang = "c"
# original = dont care

source_path = f"/tmp/{questionID}/{lang}"
dest_path = f"/dspcoder/codeFromServer/{foldername}"

try:
    # Copy language-specific files
    subprocess.run(["cp", "-r", f"{source_path}/.", dest_path], check=True)
    
    # Copy test files
    test_path = f"/tmp/{questionID}/._tests"
    subprocess.run(["cp", "-r", test_path, dest_path], check=True)

    print("Files copied successfully.")

except subprocess.CalledProcessError as e:
    print(f"Error while copying files: {e}")


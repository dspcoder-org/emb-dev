import json
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64

class testJsonHandler:
    def __init__(self, file_path, file_name, key="FeynMan", touch=False, iv=None, mode=AES.MODE_CBC):
        # Generate a 32-byte AES key by repeating or padding the provided key
        self.key = (key * (32 // len(key)) + key[:32 % len(key)]).encode()
        self.iv = iv if iv else b"1034067890120450"  # Default IV if not provided
        self.mode = mode
        self.file_path = file_path + self._encrypt_filename(file_name)
        self.count = 0

        # Initial JSON structure with empty metadata and placeholder test cases
        initial_data = {
            "metadata": {
                "type": "",
                "exe": "",
                "compile": "",
                "compilation_output": "",
                "mem_stat": {}
            },
            "test_cases": {}
        }

        # Create the JSON file with initial data only if touch=True
        if touch:
            self.write(initial_data)
            os.chmod(self.file_path, 0o777)  # Set permissions to allow access by all users
        else:
            data = self.read()
            if data and "test_cases" in data:
                for c_N in data["test_cases"]:
                    self.count = int(c_N.split()[-1])

    def _encrypt_filename(self, file_name):
        """Encrypt the file name with the fixed IV for consistency."""
        cipher = AES.new(self.key, AES.MODE_CBC, iv=self.iv)
        ct_bytes = cipher.encrypt(pad(file_name.encode(), AES.block_size))
        ct = base64.b64encode(ct_bytes).decode('utf-8')
        ct = ct.replace("/", "-")
        return f"{ct}.json"

    def encrypt(self, data):
        """Encrypt data with AES using the instance mode and IV."""
        cipher = AES.new(self.key, self.mode, iv=self.iv)
        ct_bytes = cipher.encrypt(pad(data.encode(), AES.block_size))
        return json.dumps({'iv': base64.b64encode(self.iv).decode('utf-8'), 'ciphertext': base64.b64encode(ct_bytes).decode('utf-8')})

    def decrypt(self, encrypted_data):
        """Decrypt AES-encrypted data with the instance mode and IV."""
        try:
            b64 = json.loads(encrypted_data)
            ct = base64.b64decode(b64['ciphertext'])
            cipher = AES.new(self.key, self.mode, iv=self.iv)
            pt = unpad(cipher.decrypt(ct), AES.block_size)
            return pt.decode('utf-8')
        except (ValueError, KeyError) as e:
            print("Decryption error:", e)
            return None

    def write(self, data):
        """Encrypt and write JSON data to the file."""
        json_data = json.dumps(data)
        encrypted_data = self.encrypt(json_data)
        with open(self.file_path, 'w') as file:
            file.write(encrypted_data)

    def read(self):
        """Read and decrypt JSON data from the file."""
        if not os.path.exists(self.file_path):
            return None
        with open(self.file_path, 'r') as file:
            encrypted_data = file.read()
        decrypted_data = self.decrypt(encrypted_data)
        return json.loads(decrypted_data) if decrypted_data else None

    def update_metadata(self, type=None, exe=None, compiled=None, compilation_output=None, mem_stat=None):
        """Update specific metadata fields, only updating fields that are provided."""
        data = self.read()
        if data is not None and "metadata" in data:
            if type is not None:
                data["metadata"]["type"] = type
            if exe is not None:
                data["metadata"]["exe"] = exe
            if compiled is not None:
                data["metadata"]["compile"] = compiled
            if compilation_output is not None:
                data["metadata"]["compilation_output"] = compilation_output
            if mem_stat is not None:
                data["metadata"]["mem_stat"] = mem_stat
            self.write(data)

    def append_test_case(self, case_name=None, status="", input_data="", expected="", output=""):
        """Append a new test case result to the JSON structure."""
        data = self.read()
        if data is None:
            data = {"metadata": {}, "test_cases": {}}  # Initialize data if empty
        
        if case_name is None:
            self.count += 1
            case_name = "Case " + str(self.count)

        new_test_case = {
            "status": status,
            "input": input_data,
            "expected": expected,
            "output": output
        }
        data["test_cases"][case_name] = new_test_case
        self.write(data)

    def update_test_case(self, case_name, status=None, input_data=None, expected=None, output=None):
        """Update an existing test case's fields."""
        data = self.read()
        if data is not None and "test_cases" in data:
            if case_name in data["test_cases"]:
                test_case = data["test_cases"][case_name]
                if status is not None:
                    test_case["status"] = status
                if input_data is not None:
                    test_case["input"] = input_data
                if expected is not None:
                    test_case["expected"] = expected
                if output is not None:
                    test_case["output"] = output
                self.write(data)
            else:
                print(f"Test case '{case_name}' does not exist.")
        else:
            print("No data found or invalid format.")

    def get_all_test_cases(self):
        """Return all test cases from the JSON data."""
        data = self.read()
        return data["test_cases"] if data and "test_cases" in data else {}
    
    def get_metadata(self):
        """Return all test cases from the JSON data."""
        data = self.read()
        return data["metadata"] if data and "metadata" in data else {}

    def print_json(self):
        """Print JSON data in a neat, formatted way."""
        data = self.read()
        if data is not None:
            print(json.dumps(data, indent=4))
        else:
            print("No data available or file is empty.")

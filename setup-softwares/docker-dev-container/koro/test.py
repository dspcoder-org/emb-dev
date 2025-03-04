import time


class testCases:
    def __init__(self, koro_exe) -> None:
        self.RUN = 2  # do not use override for test case number upto the RUN value
        self.exe = koro_exe
        self.default_timeout_window = 10 #ms :this will be ignored for test case number upto the RUN value
        self.usage = 'dev'/'prod' # dev for development, prod for production


    def test_case_1(self):
        inputToexe = "Test input 1"
        return inputToexe
    

    def test_case_2(self):
        inputToexe = "Test input 2"
        return inputToexe
    

    '''
    For large test cases, where running both internal and user's executables can take up extra cpu resource 
    and koro's performance can suffer, use override level-0, where test developer is providing the 
    expected value too, so test framework only runs the user executable.
    '''
    def test_case_3(self, timeout_window = 1, override = 0):
        '''
            override level 0:
            return dict ->
            {"input": input values, "expected": expected output}
            timeout_window will be considered as total timeout for user's executable.
        '''
        return "Test Input Value", "Expected Output Value"


    '''
    For the test cases, where we want to analyze something specific, things which we cann't extract by comparing
    against or internal executable, use override level-1, In this case test developer have the responsibility 
    to run completer test and return the result in bool.
    '''
    def test_case_4(self, timeout_window = 1, override = 1):
        '''
            override level 1:
            write complete test using self.elf and return dict True for PASS, False for Fail
            timeout_window will be considered as total timeout for user's executable, and if not given default_timeout_window will be considered similarly.
        '''
        # start test body
        ip = "Test Input Value"
        # use 'execute_bin' method placeholder to run the executable
        out, err, Time = execute_bin(ip, self.exe)
        time.sleep(0.1)
        # finish test body
        return True/False
        


    def helper_function(self):
        print("Helper function -- ignored by koro")




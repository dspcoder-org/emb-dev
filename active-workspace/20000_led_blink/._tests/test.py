
class testCases:
    def __init__(self, koro_elf) -> None:
        self.RUN = 1
        self.exe = koro_elf
        self.default_timeout = 10
        self.usage = 'prod'
        self.sim = "renode"
        self.msg = ""

    def test_case_1(self, timeout=60000): # 1 minute
        # self.msg = "machine-0 init failed"
        # Create machine
        ret = cmd("mach create", "(machine-0)")
        # print("p1   :   ", ret)
        
        # Load platform
        ret = cmd("machine LoadPlatformDescription @platforms/boards/stm32f4_discovery.repl", "(machine-0)")
        # print("p2   :   ", ret)
        
        ret = cmd("loadElf", "(machine-0)")
        if "(machine-0)" in ret:
            self.msg = "PASS"        
        else:
            self.msg = "Bad Executable: ELF loading failed or incompatible elf."
        return "STM power and ELF Loading", "Elf Loaded Successfully" 
    #   return "Current Task description", "on pass: msg detail for user"




    # def test_case_2(self, timeout=300):
    #     self.failmsg = "machine-1 init failed"
    #     # Create machine
    #     ret = cmd("mach create", "(machine-1)")
    #     # print("p1   :   ", ret)
        
    #     # Load platform
    #     ret = cmd("machine LoadPlatformDescription @platforms/boards/stm32f4_discovery.repl", "(machine-1)")
    #     # print("p2   :   ", ret)
        
    #     ret = cmd("loadElf", "(machine-1)")
    #     # print("p2   :   ", ret)

    #     # Additional commands can be added here
    #     # ret = cmd("Command", "stop prompt")
    #     # print("p2   :   ", ret)

    #     return True
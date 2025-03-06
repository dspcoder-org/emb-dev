class debugCases:
    def __init__(self) -> None:
        self.sim = "renode"
        self.usage = "prod"
        
    def test_debug(self, timeout=None):
        # Create machine
        ret = cmd("mach create", "(machine-0)")
        
        # Load platform and elf
        ret = cmd("machine LoadPlatformDescription @platforms/boards/stm32f4_discovery.repl", "(machine-0)")
        
        ret = cmd("loadElf", "(machine-0)")

        # Additional commands can be added here
        ret = cmd("machine StartGdbServer 4857", "(machine-0)")

        while 1:
            pass
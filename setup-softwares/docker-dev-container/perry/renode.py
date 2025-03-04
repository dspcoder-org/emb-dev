import subprocess
import signal
import os
import time
import socket
import telnetlib3
import asyncio

class renodeAutomation:
    def __init__(self, _renode_path__):
        self._renode_path__ = _renode_path__
        self.process = None
        self.__reader = None
        self.__writer = None
        
        # Create event loop
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        self.killProcess("dotnet")
        time.sleep(0.2)
        self.process = subprocess.Popen(
            [self._renode_path__, "--disable-xwt", "--port", "9532"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Connect to Renode
        while not self.is_port_open(9532):
            time.sleep(0.3)
            
        # Initialize connection
        self.loop.run_until_complete(self._connect())
        
        # Read initial output
        initial_output = self.loop.run_until_complete(self._read_until_prompt("(monitor)"))
        # print(initial_output)

    async def _connect(self):
        """Establish async telnet connection"""
        self.__reader, self.__writer = await telnetlib3.open_connection(
            'localhost', 9532, connect_minwait=0.1
        )

    async def _read_until_prompt(self, stopPrompt, timeout=10):
        """
        Reads the telnet output until a known prompt or the end of a line is encountered.
        """
        async def read_loop():
            buffer = []
            while True:
                chunk = await self.__reader.read(1024)
                if not chunk:
                    break
                buffer.append(chunk)
                if stopPrompt in ''.join(buffer):
                    break
            return ''.join(buffer)

        try:
            buffer = await asyncio.wait_for(read_loop(), timeout=timeout)
            
            # Clean up the message
            message = buffer.strip()
            message = message.lstrip('\xff\xfd\x03\xff\xfb\x01\r\n')
            return message

        except asyncio.TimeoutError:
            raise TimeoutError(f"Timeout waiting for prompt: {stopPrompt}")
        except Exception as e:
            raise Exception(f"Error reading from telnet: {e}")

    def executeCmd(self, command, stopPrompt):
        """Execute a command and wait for the prompt"""
        async def _execute():
            self.__writer.write(f" {command}\n")
            await self.__writer.drain()
            await asyncio.sleep(0.1)
            return await self._read_until_prompt(stopPrompt)

        return self.loop.run_until_complete(_execute())

    def killProcess(self, process):
        if isinstance(process, str):
            # Try to find the process by name using 'pgrep'
            result = subprocess.run(['pgrep', '-f', process], capture_output=True, text=True)
            pids = result.stdout.strip().split()

            if pids:
                for pid in pids:
                    os.kill(int(pid), signal.SIGKILL)  # Kill each process by PID
                return 0
            else:
                return -1
        else:
            # If process is an integer (PID)
            os.kill(process, signal.SIGKILL)
            return 0

    def is_port_open(self, port):
        ret = False
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            try:
                s.connect(('localhost', port))
                time.sleep(0.2)
                ret = True
            except socket.error:
                ret = False
            except socket.timeout:
                ret = True  # application might be running after this timeout
            s.close()
            return ret

    def __del__(self):
        async def _cleanup():
            if self.process:
                self.killProcess("dotnet")
                self.__writer.close()
                await self.__writer.wait_closed()
                self.loop.close()
        try:
            if self.loop and not self.loop.is_closed():
                self.loop.run_until_complete(_cleanup())
        except:
            pass


# r = RenodeAutomation("/dspcoder/renode/renode")
# o = r.executeCmd("mach create", "(machine")
# print(o)

# o = r.executeCmd("mach create", "(machine")
# print(o)





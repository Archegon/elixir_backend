import threading
import time
import os
from dotenv import load_dotenv

import snap7
from snap7 import Area
from snap7.util import (
    get_bool,
    get_dword,
    get_int,
    get_real,
    set_bool,
    set_dword,
    set_int,
    set_real,
)

from core.logger import setup_logger, log_performance, ContextLogger


class OutputType:
    BOOL = 1
    INT = 2
    REAL = 3
    DWORD = 4


load_dotenv()

class S7_200:
    def __init__(self, ip=None, localtsap=None, remotetsap=None):
        # Set up logger for this class
        self.logger = setup_logger(f"{__name__}.S7_200", format_style="detailed")
        
        # Log initialization
        self.logger.info("Initializing S7-200 PLC connection")
        
        ip = ip or os.getenv("PLC_IP")
        localtsap = localtsap or int(os.getenv("PLC_LOCALTSAP"), 16)
        remotetsap = remotetsap or int(os.getenv("PLC_REMOTETSAP"), 16)
        
        self.logger.debug(f"Connection parameters: IP={ip}, LocalTSAP=0x{localtsap:04X}, RemoteTSAP=0x{remotetsap:04X}")
        
        self.plc = snap7.client.Client()
        self.plc.set_connection_type(3)
        self.plc.set_connection_params(ip, localtsap, remotetsap)
        self.lock = threading.Lock()

        try:
            self.logger.info(f"Attempting to connect to PLC at {ip}")
            self.plc.connect(ip, 0, 0)
            if self.plc.get_connected():
                self.logger.info("Successfully connected to S7-200 Smart PLC")
                print("Connected to S7-200 Smart")
            else:
                self.logger.warning("Connection established but PLC reports not connected")
        except Exception as e:
            self.logger.error(f"Failed to connect to PLC at {ip}: {e}")
            print(f"Connection failed: {e}")

    def _translate_alias(self, mem):
        """Translate memory aliases to standard format."""
        original_mem = mem
        mem = mem.upper()
        
        if mem.startswith("M") and "." in mem:
            byte, bit = mem[1:].split(".")
            translated = f"VX{byte}.{bit}"
            self.logger.debug(f"Translated memory alias: {original_mem} -> {translated}")
            return translated
        if mem.startswith("VD"):
            translated = f"DB1.DBD{mem[2:]}"
            self.logger.debug(f"Translated memory alias: {original_mem} -> {translated}")
            return translated
        if mem.startswith("VW"):
            translated = f"DB1.DBW{mem[2:]}"
            self.logger.debug(f"Translated memory alias: {original_mem} -> {translated}")
            return translated
        
        self.logger.debug(f"No translation needed for memory address: {original_mem}")
        return mem

    def _resolve_area(self, mem):
        """Resolve memory area from address string."""
        mem_lower = mem.lower()
        
        if mem_lower.startswith("db"):
            area = Area.DB
        elif mem_lower.startswith("ai") or mem_lower.startswith("iw"):
            area = Area.PE
        elif mem_lower.startswith("aq") or mem_lower.startswith("qw"):
            area = Area.PA
        elif mem_lower.startswith("q"):
            area = Area.PA
        elif mem_lower.startswith("i"):
            area = Area.PE
        elif mem_lower.startswith("v") or mem_lower.startswith("m"):
            area = Area.MK
        else:
            self.logger.error(f"Unknown memory area for address: {mem}")
            raise ValueError(f"Unknown memory area for '{mem}'")
        
        self.logger.debug(f"Resolved memory area for {mem}: {area}")
        return area

    @log_performance(setup_logger(f"{__name__}.S7_200"), "memory_read")
    def getMem(self, mem, returnByte=False):
        """Read memory from PLC with comprehensive logging."""
        original_mem = mem
        self.logger.debug(f"Reading memory from address: {original_mem}")
        
        with ContextLogger(self.logger, operation="MEMORY_READ", address=original_mem):
            try:
                mem = self._translate_alias(mem).lower()
                length = 1
                out_type = None
                bit = 0
                start = 0
                db_number = 0

                if mem.startswith("db"):
                    db_number = int(mem.split(".")[0][2:])
                    sub = mem.split(".")[1]

                    if sub.startswith("dbx"):
                        out_type = OutputType.BOOL
                        start = int(sub[3:].split(".")[0])
                        bit = int(sub.split(".")[1])
                        length = 1
                    elif sub.startswith("dbb"):
                        out_type = OutputType.INT
                        start = int(sub[3:])
                        length = 1
                    elif sub.startswith("dbw"):
                        out_type = OutputType.INT
                        start = int(sub[3:])
                        length = 2
                    elif sub.startswith("dbd"):
                        out_type = OutputType.REAL
                        start = int(sub[3:])
                        length = 4
                    area = Area.DB
                else:
                    area = self._resolve_area(mem)

                    if mem[1] == "x":
                        out_type = OutputType.BOOL
                        start = int(mem[2:].split(".")[0])
                        bit = int(mem.split(".")[1])
                        length = 1
                    elif mem[1] == "b":
                        out_type = OutputType.INT
                        start = int(mem[2:])
                        length = 1
                    elif mem[1] == "w":
                        out_type = OutputType.INT
                        start = int(mem[2:])
                        length = 2
                    elif mem[1] == "d":
                        start = int(mem[2:])
                        length = 4
                        if mem.startswith("vd"):
                            out_type = OutputType.REAL
                        else:
                            out_type = OutputType.DWORD
                    elif mem.startswith(("aiw", "aqw", "iw", "qw", "vw")):
                        start = int(mem[3:])
                        length = 2
                        out_type = OutputType.INT
                    elif mem.startswith("vd"):
                        start = int(mem[2:])
                        length = 4
                        out_type = OutputType.REAL

                self.logger.debug(f"Memory read parameters: area={area}, db={db_number}, start={start}, length={length}, type={out_type}")

                with self.lock:
                    data = self.plc.read_area(area, db_number, start, length)
                    self.logger.debug(f"Successfully read {length} bytes from PLC")

                if returnByte:
                    self.logger.debug(f"Returning raw bytes: {data}")
                    return data
                    
                # Process the data based on type
                if out_type == OutputType.BOOL:
                    result = get_bool(data, 0, bit)
                    self.logger.debug(f"Read BOOL value: {result}")
                    return result
                elif out_type == OutputType.INT:
                    result = get_int(data, 0)
                    self.logger.debug(f"Read INT value: {result}")
                    return result
                elif out_type == OutputType.REAL:
                    result = get_real(data, 0)
                    self.logger.debug(f"Read REAL value: {result}")
                    return result
                elif out_type == OutputType.DWORD:
                    result = get_dword(data, 0)
                    self.logger.debug(f"Read DWORD value: {result}")
                    return result
                    
            except Exception as e:
                self.logger.error(f"Failed to read memory from {original_mem}: {e}")
                raise

    @log_performance(setup_logger(f"{__name__}.S7_200"), "memory_write")
    def writeMem(self, mem, value):
        """Write memory to PLC with comprehensive logging."""
        original_mem = mem
        self.logger.debug(f"Writing value {value} to memory address: {original_mem}")
        
        with ContextLogger(self.logger, operation="MEMORY_WRITE", address=original_mem, value=value):
            try:
                mem = self._translate_alias(mem).lower()
                data = self.getMem(mem, returnByte=True)

                bit = 0
                start = 0
                db_number = 0

                if mem.startswith("db"):
                    db_number = int(mem.split(".")[0][2:])
                    sub = mem.split(".")[1]

                    if sub.startswith("dbx"):
                        start = int(sub[3:].split(".")[0])
                        bit = int(sub.split(".")[1])
                        set_bool(data, 0, bit, int(value))
                        self.logger.debug(f"Set BOOL bit {bit} to {value}")
                    elif sub.startswith("dbb"):
                        start = int(sub[3:])
                        set_int(data, 0, value)
                        self.logger.debug(f"Set BYTE to {value}")
                    elif sub.startswith("dbw"):
                        start = int(sub[3:])
                        set_int(data, 0, value)
                        self.logger.debug(f"Set WORD to {value}")
                    elif sub.startswith("dbd"):
                        start = int(sub[3:])
                        set_real(data, 0, value)
                        self.logger.debug(f"Set REAL to {value}")
                    area = Area.DB
                else:
                    area = self._resolve_area(mem)

                    if mem[1] == "x":
                        start = int(mem[2:].split(".")[0])
                        bit = int(mem.split(".")[1])
                        set_bool(data, 0, bit, int(value))
                        self.logger.debug(f"Set BOOL bit {bit} to {value}")
                    elif mem[1] == "b":
                        start = int(mem[2:])
                        set_int(data, 0, value)
                        self.logger.debug(f"Set BYTE to {value}")
                    elif mem[1] == "w":
                        start = int(mem[2:])
                        set_int(data, 0, value)
                        self.logger.debug(f"Set WORD to {value}")
                    elif mem[1] == "d":
                        start = int(mem[2:])
                        if mem.startswith("vd"):
                            set_real(data, 0, value)
                            self.logger.debug(f"Set REAL to {value}")
                        else:
                            set_dword(data, 0, value)
                            self.logger.debug(f"Set DWORD to {value}")
                    elif mem.startswith(("aqw", "qw", "vw")):
                        start = int(mem[3:])
                        set_int(data, 0, value)
                        self.logger.debug(f"Set WORD to {value}")
                    elif mem.startswith("vd"):
                        start = int(mem[2:])
                        set_real(data, 0, value)
                        self.logger.debug(f"Set REAL to {value}")

                self.logger.debug(f"Writing to PLC: area={area}, db={db_number}, start={start}")

                with self.lock:
                    result = self.plc.write_area(area, db_number, start, data)
                    time.sleep(0.05)  # Standard delay after write
                    
                self.logger.debug(f"Successfully wrote to PLC, result: {result}")
                return result
                
            except Exception as e:
                self.logger.error(f"Failed to write value {value} to {original_mem}: {e}")
                raise

    def disconnect(self):
        """Disconnect from PLC with logging."""
        self.logger.info("Disconnecting from PLC")
        try:
            self.plc.disconnect()
            self.logger.info("Successfully disconnected from PLC")
        except Exception as e:
            self.logger.error(f"Error during PLC disconnection: {e}")
            raise


if __name__ == "__main__":
    plc = S7_200()

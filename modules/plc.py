import threading
import time

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


class OutputType:
    BOOL = 1
    INT = 2
    REAL = 3
    DWORD = 4


class S7_200:
    def __init__(self, ip, localtsap, remotetsap):
        self.plc = snap7.client.Client()
        self.plc.set_connection_type(3)
        self.plc.set_connection_params(ip, localtsap, remotetsap)
        self.lock = threading.Lock()

        try:
            self.plc.connect(ip, 0, 0)
            if self.plc.get_connected():
                print("Connected to S7-200 Smart")
        except Exception as e:
            print(f"Connection failed: {e}")

    def _translate_alias(self, mem):
        mem = mem.upper()
        if mem.startswith("M") and "." in mem:
            byte, bit = mem[1:].split(".")
            return f"VX{byte}.{bit}"
        if mem.startswith("VD"):
            return f"DB1.DBD{mem[2:]}"
        if mem.startswith("VW"):
            return f"DB1.DBW{mem[2:]}"
        return mem

    def _resolve_area(self, mem):
        mem = mem.lower()
        if mem.startswith("db"):
            return Area.DB
        elif mem.startswith("ai") or mem.startswith("iw"):
            return Area.PE
        elif mem.startswith("aq") or mem.startswith("qw"):
            return Area.PA
        elif mem.startswith("q"):
            return Area.PA
        elif mem.startswith("i"):
            return Area.PE
        elif mem.startswith("v") or mem.startswith("m"):
            return Area.MK
        else:
            raise ValueError(f"Unknown memory area for '{mem}'")

    def getMem(self, mem, returnByte=False):
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

        with self.lock:
            data = self.plc.read_area(area, db_number, start, length)

        if returnByte:
            return data
        if out_type == OutputType.BOOL:
            return get_bool(data, 0, bit)
        elif out_type == OutputType.INT:
            return get_int(data, 0)
        elif out_type == OutputType.REAL:
            return get_real(data, 0)
        elif out_type == OutputType.DWORD:
            return get_dword(data, 0)

    def writeMem(self, mem, value):
        mem = self._translate_alias(mem).lower()
        data = self.getMem(mem, returnByte=True)

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
                set_bool(data, 0, bit, int(value))
            elif sub.startswith("dbb"):
                out_type = OutputType.INT
                start = int(sub[3:])
                set_int(data, 0, value)
            elif sub.startswith("dbw"):
                out_type = OutputType.INT
                start = int(sub[3:])
                set_int(data, 0, value)
            elif sub.startswith("dbd"):
                out_type = OutputType.REAL
                start = int(sub[3:])
                set_real(data, 0, value)
            area = Area.DB
        else:
            area = self._resolve_area(mem)

            if mem[1] == "x":
                out_type = OutputType.BOOL
                start = int(mem[2:].split(".")[0])
                bit = int(mem.split(".")[1])
                set_bool(data, 0, bit, int(value))
            elif mem[1] == "b":
                out_type = OutputType.INT
                start = int(mem[2:])
                set_int(data, 0, value)
            elif mem[1] == "w":
                out_type = OutputType.INT
                start = int(mem[2:])
                set_int(data, 0, value)
            elif mem[1] == "d":
                start = int(mem[2:])
                if mem.startswith("vd"):
                    out_type = OutputType.REAL
                    set_real(data, 0, value)
                else:
                    out_type = OutputType.DWORD
                    set_dword(data, 0, value)
            elif mem.startswith(("aqw", "qw", "vw")):
                out_type = OutputType.INT
                start = int(mem[3:])
                set_int(data, 0, value)
            elif mem.startswith("vd"):
                out_type = OutputType.REAL
                start = int(mem[2:])
                set_real(data, 0, value)

        with self.lock:
            result = self.plc.write_area(area, db_number, start, data)
            time.sleep(0.05)
        return result

    def disconnect(self):
        self.plc.disconnect()


if __name__ == "__main__":
    plc = S7_200("192.168.2.1", 0x0100, 0x0200)

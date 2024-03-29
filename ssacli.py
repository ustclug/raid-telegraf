#!/usr/bin/env python3
# Reference: https://gist.github.com/mrpeardotnet/a9ce41da99936c0175600f484fa20d03

import subprocess as sp
import os
from typing import Dict

SSACLI_EXEC = "/usr/sbin/ssacli"
if not os.path.exists(SSACLI_EXEC):
    SSACLI_EXEC = "ssacli"


class SsaCliBase:
    def __init__(self) -> None:
        output = self.run(["ctrl", "all", "show"])
        if b"Smart Array" not in output:
            raise RuntimeError("Self-check failed. Did you run this script with root?")

    def run(self, args: list) -> bytes:
        ret = sp.run([SSACLI_EXEC, *args], stdout=sp.PIPE)
        if ret.returncode != 0:
            raise RuntimeError("ssacli returns a non-zero value.")
        return ret.stdout

    def get_physical_disk_info(self) -> bytes:
        return self.run(["ctrl", "slot=0", "pd", "all", "show", "status"])


ssacli = SsaCliBase()


def get_disk_errors() -> dict:
    pdinfo = ssacli.get_physical_disk_info().strip().split(b"\n")
    info: Dict[int, Dict[str, Dict]] = {0: {}}
    for i in pdinfo:
        disk, status = i.rsplit(b":", 1)
        disk = disk.strip().decode("utf-8")
        # OK or Failed
        status = status.strip().decode("utf-8")
        if status not in ["OK", "Failed"]:
            status = f"Failed ({status})"
        info[0][disk] = {
            "media_error": 0,
            "other_error": 0,
            "predictive_failure": 0,
            "firmware": status,
            "smart_alert": "N/A",
        }
    return info


if __name__ == "__main__":
    print(get_disk_errors())

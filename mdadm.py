# Uses /proc/mdstat and smartctl to get disk errors
import subprocess as sp
import re
from typing import Dict, Tuple

MD_REGEX = re.compile(r"^(md.+?) : (in)?active( \([a-z-]+\))? (\w+)")
DEVICE_REGEX = re.compile(r" (\w+?)\[(\d+)\]((\([WJFSR]\))*)")
SYNC_REGEX = re.compile(r".+\[([U_]+)\]$")


class MdadmBase:
    def __init__(self) -> None:
        # check smartctl: an exception will be raised if smartctl is not installed
        assert self.smartctl_code(["-h"]) == 0, "smartctl gives unexpected return code."

    # https://linux.die.net/man/8/smartctl, "Return values"
    def smartctl_code(self, args: list) -> int:
        ret = sp.run(["smartctl", *args], stdout=sp.DEVNULL, stderr=sp.DEVNULL)
        return ret.returncode

    # https://raid.wiki.kernel.org/index.php/Mdstat is a bit misleading...
    # https://gist.github.com/taoky/f739fad4e7ef2d445b946b379cf2fa6b
    def mdstat_parse(self, mdstat: str) -> dict:
        ret = {}

        md_device = None
        for l in mdstat.split("\n"):
            l = l.strip()
            if MD_REGEX.match(l):
                md_device = MD_REGEX.findall(l)[0][0]
                devices = DEVICE_REGEX.findall(l)
                md_results = {}
                for device in devices:
                    output = "OK"
                    device_name = device[0]
                    status = device[2]
                    if "(F)" in status:
                        output = "Failed"
                    if "(W)" in status:
                        output += " (Writemostly)"
                    if "(J)" in status:
                        output += " (Journal)"
                    if "(S)" in status:
                        output += " (Spare)"
                    if "(R)" in status:
                        output += " (Replacement)"
                    md_results[device_name] = output
                ret[md_device] = md_results
            syncs = SYNC_REGEX.match(l)
            if syncs:
                assert md_device is not None
                sync_status = len(syncs[1])
                current_len = len(ret[md_device])
                for i in range(sync_status - current_len):
                    ret[md_device][f"unknown{i}"] = "Failed"
                md_device = None
        return ret

    # Tuple[result from mdstat, result from smartctl]
    def get_physical_disk_info(self) -> Tuple[dict, dict]:
        with open("/proc/mdstat", "r") as f:
            mdstat = f.read()
        mdstat_parsed = self.mdstat_parse(mdstat)
        smartctl_results = {}
        for md in mdstat_parsed:
            for sd in mdstat_parsed[md]:
                if not sd.startswith("unknown"):
                    smartctl_results[sd] = self.smartctl_code(["-H", f"/dev/{sd}"])
        return mdstat_parsed, smartctl_results


mdadm = MdadmBase()


def get_disk_errors() -> dict:
    pdinfo, smart = mdadm.get_physical_disk_info()
    # print(pdinfo)
    for md in pdinfo:
        for sd in pdinfo[md]:
            smart_failed = smart.get(sd, 0) != 0
            pdinfo[md][sd] = {
                "media_error": 0,
                "other_error": 0,
                "predictive_failure": 1 if smart_failed else 0,
                "firmware": pdinfo[md][sd],
                "smart_alert": "Yes" if smart_failed else "No",
            }
    return pdinfo


if __name__ == "__main__":
    print(get_disk_errors())

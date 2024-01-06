# Uses /proc/mdstat and smartctl to get disk errors
import subprocess as sp
import re
from typing import Dict, Tuple

MD_REGEX = re.compile(r"^(md.+?) :")
DEVICE_REGEX = re.compile(r"(\w+?)\[(\d+)\](\(F\))?")


class MdadmBase:
    def __init__(self) -> None:
        # check smartctl: an exception will be raised if smartctl is not installed
        assert self.smartctl_code(["-h"]) == 0, "smartctl gives unexpected return code."

    # https://linux.die.net/man/8/smartctl, "Return values"
    def smartctl_code(self, args: list) -> int:
        ret = sp.run(["smartctl", *args], stdout=sp.DEVNULL, stderr=sp.DEVNULL)
        return ret.returncode

    # https://raid.wiki.kernel.org/index.php/Mdstat
    def mdstat_parse(self, mdstat: str) -> dict:
        ret = {}

        md_device = None
        sd_mapping: Dict[int, Tuple[str, bool]] = {}
        sd_results: Dict[str, str] = {}
        check_status = False
        for l in mdstat.split("\n"):
            l = l.strip()
            if l.startswith("Personalities"):
                continue
            if MD_REGEX.match(l):
                md_device = MD_REGEX.findall(l)[0]
                device_str = l.split(" : ", 1)[1]
                devices = device_str.split(" ")[2:]
                for device in devices:
                    res = DEVICE_REGEX.findall(device)
                    assert res
                    failed = False
                    if res[0][2] == "(F)":
                        failed = True
                    sd_mapping[int(res[0][1])] = (res[0][0], failed)
                check_status = True
                continue
            if check_status:
                status = l.split(" ")[-1]
                # strip [ and ]
                status = status[1:-1]
                sdkeys = list(sd_mapping.keys())
                for i, s in enumerate(status):
                    if s == "U":
                        s = "OK"
                    elif s == "_":
                        s = "Failed"
                    else:
                        s = "Unknown"
                    if i not in sdkeys:
                        sd_results[f"unknown{i}"] = s
                    else:
                        sdkeys.remove(i)
                        sd_results[sd_mapping[i][0]] = s
                for i in sdkeys:
                    if sd_mapping[i][1]:
                        sd_results[sd_mapping[i][0]] = "Failed (Spare)"
                    else:
                        sd_results[sd_mapping[i][0]] = "Spare"
                ret[md_device] = sd_results
                check_status = False
                sd_mapping = {}
                sd_results = {}
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

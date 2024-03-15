# Uses /proc/mdstat and smartctl to get disk errors
import re
import subprocess as sp
from typing import Dict, Tuple

MD_REGEX = re.compile(r"^(md.+?) :")
DEVICE_REGEX = re.compile(r"(\w+?)\[(\d+)\](\(F\))?")
RAID_REGEX = r"raid\d\s(.*)$"


class MdadmBase:
    def __init__(self) -> None:
        # check smartctl: an exception will be raised if smartctl is not installed
        assert self.smartctl_code(["-h"]) == 0, "smartctl gives unexpected return code."

    def get_mdadm_raid_detail(self):
        command_output = sp.check_output(["sudo", "mdadm", "-D", "/dev/md0"]).decode(
            "utf-8"
        )
        raid_info = {}
        raid_info["Devices"] = []

        overall_device_state = ""
        in_devices_section = False

        for line in command_output.split("\n"):
            if line.startswith("/dev/md"):
                continue
            elif ":" in line:
                key, value = [part.strip() for part in line.split(":", 1)]
                if "Size" in key:
                    value = value.split(" ")[0]
                raid_info[key] = value
            elif "Number" in line:
                in_devices_section = True
                # on the next line we will start parsing the devices
            elif in_devices_section:
                splat = re.split(r"\s{2,}", line)
                if len(splat) < 2:
                    continue
                number = splat[1]
                major = splat[2]
                minor = splat[3]
                device = splat[4]
                state = splat[5]
                raid_info["Devices"].append(
                    {
                        "Number": number,
                        "Major": major,
                        "Minor": minor,
                        "RaidDevice": device,
                        "State": state,
                    }
                )
                if state not in overall_device_state:
                    overall_device_state += state + ";"
                raid_info["OverallDeviceState"] = overall_device_state
        return raid_info

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
                match = re.search(RAID_REGEX, l)
                if not match:
                    # TEMP fix to prevent crash on inactive array
                    if "inactive " in l:
                        device_str = l.split("inactive ")[1]
                        # TODO handle inactive state better.
                    else:
                        raise AssertionError("cannot parse /proc/mdstat")
                else:
                    device_str = match.group(1)

                devices = device_str.split(" ")
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


def raid_array_exists() -> bool:
    result = sp.run(["mdadm", "--detail", "--scan"], capture_output=True, text=True)
    if result.returncode == 0 and "/dev/md" in result.stdout:
        return True
    return False


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


def influxdb_print_mdadm_detail() -> None:
    result = mdadm.get_mdadm_raid_detail()
    print(
        'raid_detail,device={device} raid_level="{raid_level}",array_size={array_size},used_dev_size={used_dev_size},raid_devices={raid_devices},total_devices={total_devices},active_devices={active_devices},working_devices={working_devices},failed_devices={failed_devices},spare_devices={spare_devices},state="{state}",agg_device_state="{device_state}"'.format(
            device="md0",
            raid_level=result.get("Raid Level", "unknown"),
            array_size=result.get("Array Size", 0),
            used_dev_size=result.get("Used Dev Size", 0),
            raid_devices=result.get("Raid Devices", 0),
            total_devices=result.get("Total Devices", 0),
            active_devices=result.get("Active Devices", 0),
            working_devices=result.get("Working Devices", 0),
            failed_devices=result.get("Failed Devices", 0),
            spare_devices=result.get("Spare Devices", 0),
            state=result.get("State", "unknown"),
            device_state=result.get("OverallDeviceState", "unknown"),
        )
    )


if __name__ == "__main__":
    print(get_disk_errors())

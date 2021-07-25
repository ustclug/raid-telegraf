#!/usr/bin/env python3
# Reference: https://gist.github.com/demofly/53b26d7a3f12b3008716

import subprocess as sp
import re
import os
from collections import defaultdict

MEGACLI_EXEC = "/opt/MegaRAID/MegaCli/MegaCli64"
if not os.path.exists(MEGACLI_EXEC):
    MEGACLI_EXEC = "megacli"

ENDSTR_NUM_RE = re.compile(rb'(\d+)$')
STATE_RE = re.compile(rb': (.+)$')
ADAPTER_RE = re.compile(rb'#(\d+)$')

class MegaCliBase():
    def __init__(self):
        # self check
        output = self.run(["-AdpAllInfo", "-aAll", "-NoLog"])
        if b"Adapter #0" not in output:
            raise RuntimeError("Self-check failed. Did you run this script with root?")

    def run(self, args: list):
        ret = sp.run([MEGACLI_EXEC, *args], stdout=sp.PIPE)
        if ret.returncode != 0:
            raise RuntimeError("MegaCli returns a non-zero value.")
        return ret.stdout

    def get_physical_disk_info(self):
        return self.run(['-PDlist', '-aALL', '-NoLog'])

megacli = MegaCliBase()

def get_disk_errors():
    pdinfo = megacli.get_physical_disk_info().split(b'\n')
    adapter = 0
    info = defaultdict(dict)
    slot = {}
    for i in pdinfo:
        if b'Adapter #' in i:
            adapter_id = int(ADAPTER_RE.findall(i)[0])
            adapter = adapter_id
        if b'Slot Number' in i:
            slot_number = int(ENDSTR_NUM_RE.findall(i)[0])
        if b'Enclosure Device ID' in i:
            enclosure_id = int(ENDSTR_NUM_RE.findall(i)[0])
        if b'Media Error' in i:
            media_error_cnt = int(ENDSTR_NUM_RE.findall(i)[0])
            slot['media_error'] = media_error_cnt
        if b'Other Error' in i:
            other_error_cnt = int(ENDSTR_NUM_RE.findall(i)[0])
            slot['other_error'] = other_error_cnt
        if b'Predictive Failure Count' in i:
            predictive_failure_cnt = int(ENDSTR_NUM_RE.findall(i)[0])
            slot['predictive_failure'] = predictive_failure_cnt
        if b'Firmware state' in i:
            firmware_state = STATE_RE.findall(i)[0]
            slot['firmware'] = firmware_state.decode('utf-8')
        if b'S.M.A.R.T alert' in i:
            # SMART is the last message of one physical disk
            smart = STATE_RE.findall(i)[0]
            slot['smart_alert'] = smart.decode('utf-8')
            disk = 'Drive /c{adapter}/e{enclosure_id}/s{slot_number}'.format(
                adapter=adapter, enclosure_id=enclosure_id, slot_number=slot_number
            )
            info[adapter][disk] = slot
            slot = {}
    return dict(info)

if __name__ == '__main__':
    print(get_disk_errors())
    # Return example:
    # {0: {'Drive /c0/e32/s0': {'media_error': 0, 'other_error': 0, 'predictive_failure': 31, 'firmware': 'Online, Spun Up', 'smart_alert': 'Yes'}, 'Drive /c0/e32/s1': {'media_error': 0, 'other_error': 0, 'predictive_failure': 0, 'firmware': 'Online, Spun Up', 'smart_alert': 'No'}, 'Drive /c0/e32/s2': {'media_error': 0, 'other_error': 19, 'predictive_failure': 0, 'firmware': 'Online, Spun Up', 'smart_alert': 'No'}, 'Drive /c0/e32/s3': {'media_error': 25, 'other_error': 19, 'predictive_failure': 0, 'firmware': 'Online, Spun Up', 'smart_alert': 'No'}, 'Drive /c0/e32/s4': {'media_error': 0, 'other_error': 19, 'predictive_failure': 0, 'firmware': 'Online, Spun Up', 'smart_alert': 'No'}, 'Drive /c0/e32/s6': {'media_error': 0, 'other_error': 19, 'predictive_failure': 0, 'firmware': 'Unconfigured(good), Spun Up', 'smart_alert': 'No'}, 'Drive /c0/e32/s7': {'media_error': 0, 'other_error': 19, 'predictive_failure': 0, 'firmware': 'Online, Spun Up', 'smart_alert': 'No'}}}

#!/usr/bin/env python3

import subprocess as sp
import os
import json

STORCLI_EXEC = "/opt/MegaRAID/storcli/storcli64"
if not os.path.exists(STORCLI_EXEC):
    STORCLI_EXEC = "storcli"

class StorCliBase():
    def __init__(self):
        # self check
        output = self.run(["/c0", "show", "nolog"])
        status = output['Controllers'][0]['Command Status']['Status']
        if status != 'Success':
            raise RuntimeError("Self-check failed. Did you run this script with root? (Controller status gets {} rather than 'Success')".format(status))

    def run(self, args: list):
        # Get JSON output
        ret = sp.run([STORCLI_EXEC, *args, "J"], stdout=sp.PIPE)
        if ret.returncode != 0:
            raise RuntimeError("storcli returns a non-zero value.")
        return json.loads(ret.stdout)

    def get_physical_disk_info(self):
        return self.run(['/call', '/eall', '/sall', 'show', 'all', 'nolog'])

storcli = StorCliBase()

def update_dict(dict, key, value_dict):
    if key not in dict:
        dict[key] = value_dict
    else:
        dict[key].update(value_dict)

def get_disk_errors():
    pdinfo = storcli.get_physical_disk_info()['Controllers']
    info = {}
    for adapter in pdinfo:
        adapter_id = adapter['Command Status']['Controller']
        adapter_info = {}
        adapter_response = adapter['Response Data']
        for key in adapter_response:
            if 'Detailed Information' in key:
                disk = key.split("-")[0].strip()
                state = adapter_response[key][disk + " State"]
                media_error = int(state['Media Error Count'])
                other_error = int(state['Other Error Count'])
                predictive_failure = int(state['Predictive Failure Count'])
                smart = state["S.M.A.R.T alert flagged by drive"]
                update_dict(adapter_info, disk, {
                    'media_error': media_error,
                    'other_error': other_error,
                    'predictive_failure': predictive_failure,
                    'smart_alert': smart,
                })
            else:
                drive_info = adapter_response[key][0]  # WHY THIS IS A LIST???
                state = drive_info['State']
                spin = drive_info['Sp']
                firmware_state = "{state}, Spin {spin}".format(state=state, spin='Up' if spin == 'U' else 'Down')
                update_dict(adapter_info, key, {
                    'firmware': firmware_state,
                })
        info[adapter_id] = adapter_info

    return info

if __name__ == '__main__':
    print(get_disk_errors())
    # Return example:
    # {0: {'Drive /c0/e252/s0': {'firmware': 'Onln, Spin Up', 'media_error': 0, 'other_error': 0, 'predictive_failure': 0, 'smart_alert': 'No'}, 'Drive /c0/e252/s1': {'firmware': 'Onln, Spin Up', 'media_error': 0, 'other_error': 0, 'predictive_failure': 0, 'smart_alert': 'No'}, 'Drive /c0/e252/s4': {'firmware': 'Onln, Spin Up', 'media_error': 0, 'other_error': 0, 'predictive_failure': 0, 'smart_alert': 'No'}, 'Drive /c0/e252/s5': {'firmware': 'Onln, Spin Up', 'media_error': 0, 'other_error': 0, 'predictive_failure': 0, 'smart_alert': 'No'}, 'Drive /c0/e252/s6': {'firmware': 'Onln, Spin Up', 'media_error': 0, 'other_error': 0, 'predictive_failure': 0, 'smart_alert': 'No'}, 'Drive /c0/e252/s7': {'firmware': 'Onln, Spin Up', 'media_error': 0, 'other_error': 0, 'predictive_failure': 0, 'smart_alert': 'No'}}, 1: {'Drive /c1/e252/s0': {'firmware': 'Onln, Spin Up', 'media_error': 0, 'other_error': 0, 'predictive_failure': 0, 'smart_alert': 'No'}, 'Drive /c1/e252/s1': {'firmware': 'Onln, Spin Up', 'media_error': 0, 'other_error': 0, 'predictive_failure': 0, 'smart_alert': 'No'}, 'Drive /c1/e252/s2': {'firmware': 'Onln, Spin Up', 'media_error': 0, 'other_error': 0, 'predictive_failure': 0, 'smart_alert': 'No'}, 'Drive /c1/e252/s3': {'firmware': 'Onln, Spin Up', 'media_error': 0, 'other_error': 0, 'predictive_failure': 0, 'smart_alert': 'No'}, 'Drive /c1/e252/s4': {'firmware': 'Onln, Spin Up', 'media_error': 0, 'other_error': 0, 'predictive_failure': 0, 'smart_alert': 'No'}, 'Drive /c1/e252/s5': {'firmware': 'Onln, Spin Up', 'media_error': 0, 'other_error': 0, 'predictive_failure': 0, 'smart_alert': 'No'}, 'Drive /c1/e252/s6': {'firmware': 'Onln, Spin Up', 'media_error': 0, 'other_error': 0, 'predictive_failure': 0, 'smart_alert': 'No'}}}
#!/usr/bin/env python3

import subprocess as sp
import re
import os
from collections import defaultdict

ZPOOL_EXEC = "/sbin/zpool"
if not os.path.exists(ZPOOL_EXEC):
    ZPOOL_EXEC = "zpool"

ENDSTR_NUM_RE = re.compile(rb'(\d+)$')
STATE_RE = re.compile(rb': (.+)$')
ADAPTER_RE = re.compile(rb'#(\d+)$')

class ZFSPoolBase():
    def __init__(self):
        # self check
        try:
            self.get_physical_disk_info()
        except RuntimeError:
            raise RuntimeError("Self-check failed. Did you configure ZFS stack correctly?")

    def run(self, args: list):
        ret = sp.run([ZPOOL_EXEC, *args], stdout=sp.PIPE)
        if ret.returncode != 0:
            raise RuntimeError("zpool returns a non-zero value.")
        return ret.stdout

    def get_physical_disk_info(self):
        return self.run(['status'])


zpool = ZFSPoolBase()

def get_disk_errors():
    status = zpool.get_physical_disk_info().split(b'\n')
    info = defaultdict(dict)
    state = 0

    pool_info = {}
    for i in status:
        if b"pool:" in i:
            pool = STATE_RE.findall(i)[0].strip().decode('utf-8')
        elif b"NAME" in i:
            state = 1
        elif b"errors:" in i:
            state = 0
            info[pool] = pool_info
            pool_info = {}
        elif state == 1:
            disk_info = [_.strip() for _ in i.split(b" ") if _.strip() != b'']
            if len(disk_info) != 5:
                continue
            entity_name = disk_info[0].decode('utf-8')
            health = disk_info[1].decode('utf-8')
            read_error = int(disk_info[2])
            write_error = int(disk_info[3])
            checksum_error = int(disk_info[4])
            pool_info[entity_name] = {
                'health': health,
                'read_error': read_error,
                'write_error': write_error,
                'checksum_error': checksum_error,
            }
        
    return dict(info)

if __name__ == '__main__':
    print(get_disk_errors())
    # Return example:
    # {'pool0': {'pool0': {'health': 'ONLINE', 'read_error': 0, 'write_error': 0, 'checksum_error': 0}, 'raidz3-0': {'health': 'ONLINE', 'read_error': 0, 'write_error': 0, 'checksum_error': 0}, 'ata-HGST_HUSXXXXXXXXXXX_XXXXXXXX': {'health': 'ONLINE', 'read_error': 31, 'write_error': 22, 'checksum_error': 0}}, 'pool1': {'pool1': {'health': 'ONLINE', 'read_error': 0, 'write_error': 0, 'checksum_error': 0}, 'mirror-0': {'health': 'ONLINE', 'read_error': 0, 'write_error': 0, 'checksum_error': 0}, 'ata-INTEL_SSDSC2BB240G6_PHWA6441041N240AGN-part2': {'health': 'ONLINE', 'read_error': 0, 'write_error': 0, 'checksum_error': 0}, 'ata-INTEL_SSDSC2BB240G6_PHWA64410400240AGN-part2': {'health': 'ONLINE', 'read_error': 0, 'write_error': 0, 'checksum_error': 0}}}

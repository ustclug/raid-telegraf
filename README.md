# raid-telegraf

Compatible with Python 3.7+ (Latest Python version in Debian 10). No third-party dependencies.

/etc/telegraf/telegraf.d/raid.conf:

```
[[inputs.exec]]
 commands = ["sudo /opt/raid-telegraf/main.py --use megacli"]
 # or sudo /opt/raid-telegraf/main.py --use storcli
 timeout = "30s"
 data_format = "influx"
 interval = "5m"
```

/etc/sudoer:

```
telegraf ALL=(root) NOPASSWD: /opt/raid-telegraf/main.py
```

(Or modify `/etc/sudoers.d/telegraf`)

## Supported RAID controller software

- megacli
- storcli
- ssacli (HPE, currently supports single controller only, only physical disk status string)
- mdadm (with smartctl)

## Output

It outputs in influxdb format like this:

```influxdb
raid_telegraf,device=Drive\ /c0/e32/s0 media_error=0,other_error=0,predictive_failure=0,firmware="Online, Spun up",smart_alert="No"
```

For ssacli, only "device" and "firmware" are valid, other values will be 0 or "N/A".

## Limitation

- Heavily relies on parsing the output of the RAID controller software.
    - More testcase is needed.
- Influxdb format serialization is naive.

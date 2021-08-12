# raid-telegraf

Compatible with Python 3.5+ (Latest Python version in Debian 9)

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

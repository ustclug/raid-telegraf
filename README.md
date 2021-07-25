# raid-telegraf

/etc/telegraf/telegraf.d/raid.conf:

```
[[inputs.exec]]
 commands = ["sudo /opt/raid-telegraf/main.py --use megacli"]
 # or sudo /opt/raid-telegraf/main.py --use storcli
 timeout = "5s"
 data_format = "influx"
```

/etc/sudoer:

```
telegraf ALL=(root) NOPASSWD: /opt/raid-telegraf/main.py
```

(Or modify `/etc/sudoers.d/telegraf`)

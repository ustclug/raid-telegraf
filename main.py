#!/usr/bin/env python3
import argparse


def influxdb_gen(result):
    for adapter in result:
        for drive in result[adapter]:
            stat = result[adapter][drive]
            drive = drive.replace(" ", "\ ")  # escape space
            drive = drive.replace(",", "\,")  # escape comma
            print(
                'raid_telegraf,device={drive} media_error={media_error},other_error={other_error},predictive_failure={predictive_failure},firmware="{firmware}",smart_alert="{smart_alert}"'.format(
                    drive=drive,
                    media_error=stat["media_error"],
                    other_error=stat["other_error"],
                    predictive_failure=stat["predictive_failure"],
                    firmware=stat["firmware"],
                    smart_alert=stat["smart_alert"],
                )
            )


def main(args):
    if args.use == "megacli":
        from megacli import get_disk_errors
    elif args.use == "storcli":
        from storcli import get_disk_errors
    elif args.use == "ssacli":
        from ssacli import get_disk_errors
    else:
        raise ValueError("Unexpected use value: {}".format(args.use))

    result = get_disk_errors()
    # influxdb format (line protocol without timestamp):
    # raid_telegraf,device=Drive\ /c0/e32/s0 media_error=0,other_error=0,predictive_failure=0,firmware="Online, Spun up",smart_alert="No"

    influxdb_gen(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("raid-telegraf")
    parser.add_argument(
        "--use", choices=["megacli", "storcli", "ssacli"], required=True
    )

    args = parser.parse_args()

    main(args)

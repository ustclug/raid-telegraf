import argparse

def main(args):
    if args.use == 'megacli':
        from megacli import get_disk_errors
    elif args.use == 'storcli':
        from storcli import get_disk_errors
    else:
        raise ValueError(f'Unexpected use value: {args.use}')

    result = get_disk_errors()
    # influxdb format (line protocol without timestamp):
    # raid_telegraf,device="Drive /c0/e32/s0" media_error=0,other_error=0,predictive_failure=0,firmware="Online, Spun up",smart_alert="No"

    for adapter in result:
        for drive in result[adapter]:
            stat = result[adapter][drive]
            print(f"raid_telegraf,device=\"{drive}\" media_error={stat['media_error']},other_error={stat['other_error']},predictive_failure={stat['predictive_failure']},firmware=\"{stat['firmware']}\",smart_alert=\"{stat['smart_alert']}\"")

if __name__ == "__main__":
    parser = argparse.ArgumentParser("raid-telegraf")
    parser.add_argument("--use", choices=["megacli", "storcli"], required=True)

    args = parser.parse_args()

    main(args)

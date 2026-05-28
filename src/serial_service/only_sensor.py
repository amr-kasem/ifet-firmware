import argparse
import time
from serial_com import ModbusTcpCom, SerialCom
from sensors_handler.sensor import Sensor
from sensors_handler.new_sensor import NewSensor

CONFIG_FILE = "debug-sensor.json"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Poll a single pressure sensor and report the achieved read rate."
    )
    parser.add_argument(
        "-i", "--interval", type=float, default=0.0,
        help="Delay in seconds between reads (default: 0.0 = poll as fast as the bus allows).",
    )
    parser.add_argument(
        "-a", "--address", default="1",
        help="Modbus slave address of the sensor (default: 1).",
    )
    parser.add_argument(
        "-c", "--config", default=CONFIG_FILE,
        help=f"Serial config file (default: {CONFIG_FILE}).",
    )
    parser.add_argument(
        "-n", "--count", type=int, default=0,
        help="Number of reads before exiting (default: 0 = run until Ctrl-C).",
    )
    parser.add_argument(
        "-r", "--report-every", type=float, default=2.0,
        help="How often (seconds) to print the rolling read rate (default: 2.0).",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    config = {
        "name": args.address,
        "address": args.address,
        "debug": True,
        "value": "",
        "active": True,
        "type": "pressure2",
    }

    com_port = SerialCom(args.config)
    sensor = NewSensor(config, com_port=com_port)

    total = 0           # all reads issued (for --count)
    reads = 0           # reads in the current reporting window
    window_start = time.perf_counter()

    try:
        while True:
            t0 = time.perf_counter()
            value = sensor.read()
            dt = time.perf_counter() - t0
            total += 1
            reads += 1
            print(f"{value}  (transaction {dt * 1000:.1f} ms)")

            now = time.perf_counter()
            elapsed = now - window_start
            if elapsed >= args.report_every:
                print(
                    f"--- rate: {reads / elapsed:.1f} Hz over {reads} reads "
                    f"({elapsed:.1f}s) ---"
                )
                reads = 0
                window_start = now

            if args.count and total >= args.count:
                break
            if args.interval > 0:
                time.sleep(args.interval)
    except KeyboardInterrupt:
        print("Stopped by user.")


if __name__ == "__main__":
    main()

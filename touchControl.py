import subprocess
import threading
import signal
import sys
import logging
import argparse
import re


# Setup logging
def setup_logging(log_level):
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(levelname)s - %(message)s"
    )


def run_command(command):
    try:
        return subprocess.check_output(command, text=True).strip()
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        return None


def toggle_tap_to_click(touchpad_id):
    try:
        result = subprocess.run(
            ["./toggleTapToClick.sh", str(touchpad_id)],
            check=True,
            text=True,
            capture_output=True,
        )
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")


def listen_for_keypress(event, keyboard_id):
    """Listens for keypresses on the specified keyboard device."""
    try:
        with subprocess.Popen(
            ["xinput", "test", keyboard_id],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ) as p:
            for line in iter(p.stdout.readline, b""):
                event.set()
    except subprocess.SubprocessError as e:
        logging.error(f"Error in listen_for_keypress: {e}")


def set_touchpad_state(event, touchpad_ids, wait_time):
    """Controls the touchpad state based on keyboard activity."""
    try:
        while True:
            event.wait()
            for touchPadId in touchpad_ids:
                toggle_tap_to_click(touchPadId)
                event.clear()
                # Wait for a period of inactivity before re-enabling the touchpad
                event.wait(wait_time)
                toggle_tap_to_click(touchPadId)
    except KeyboardInterrupt:
        logging.info("Terminating script")


def signal_handler(touchpad_ids):
    def handle_signum(signum, frame):
        logging.info("Signal received, terminating script and enabling touchpad")
        for touchPadId in touchpad_ids:
            toggle_tap_to_click(touchPadId)
            sys.exit(0)

    return handle_signum


def find_device_ids(keyword):
    """Finds the device IDs for a given keyword (e.g., 'touchpad', 'keyboard')."""
    device_ids = []
    try:
        output = subprocess.check_output(["xinput", "--list"], text=True)
        for line in output.splitlines():
            if keyword.lower() in line.lower():
                match = re.search(r"id=(\d+)", line)
                if match:
                    device_ids.append(match.group(1))
    except subprocess.CalledProcessError as e:
        logging.error(f"Error finding {keyword} device IDs: {e}")

    print("Ids are: ", device_ids)
    return device_ids


def main():
    parser = argparse.ArgumentParser(
        description="Control touchpad based on keyboard activity."
    )
    parser.add_argument("wait_time", type=float, help="Waiting time in seconds")
    parser.add_argument("--log_level", type=str, default="INFO", help="Log level")
    args = parser.parse_args()

    setup_logging(getattr(logging, args.log_level.upper(), logging.INFO))

    touchpad_ids = find_device_ids("touchpad")
    keyboard_ids = find_device_ids("keyboard")

    if not touchpad_ids or not keyboard_ids:
        logging.error("Could not find touchpad or keyboard IDs")
        sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler(touchpad_ids))
    signal.signal(signal.SIGTERM, signal_handler(touchpad_ids))

    event = threading.Event()

    # Create and start a thread for each keyboard ID
    for keyboard_id in keyboard_ids:
        keypress_thread = threading.Thread(
            target=listen_for_keypress, args=(event, keyboard_id), daemon=True
        )
        keypress_thread.start()

    try:
        set_touchpad_state(event, touchpad_ids, args.wait_time)
    finally:
        # Wait for all keypress threads to finish (optional)
        for thread in threading.enumerate():
            if thread is not threading.current_thread():
                thread.join()


if __name__ == "__main__":
    main()

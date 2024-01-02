import subprocess
import threading
import signal
import time
import sys
import logging
import argparse

# Global variable
touchpad_id_global = None


# Setup logging
def setup_logging(log_level):
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(levelname)s - %(message)s"
    )


def disable_tap_to_click(touchpad_id):
    """Disables tap-to-click feature of the touchpad."""
    logging.info("Disabling tap-to-click")
    run_command(["xinput", "set-prop", touchpad_id, "337", "0"])


def enable_tap_to_click(touchpad_id):
    """Enables tap-to-click feature of the touchpad."""
    logging.info("Enabling tap-to-click")
    run_command(["xinput", "set-prop", touchpad_id, "337", "1"])


def run_command(command):
    """Executes a command and handles exceptions."""
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error executing command: {e}")
        sys.exit(1)


def toggle_touchpad(touchpad_id, enable):
    """Toggles the touchpad state."""
    if enable:
        enable_tap_to_click(touchpad_id)
    else:
        disable_tap_to_click(touchpad_id)


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
        sys.exit(1)


def set_touchpad_state(event, touchpad_id, wait_time):
    """Controls the touchpad state based on keyboard activity."""
    disabled = False
    try:
        while True:
            event.wait(wait_time)
            if event.is_set() and not disabled:
                toggle_touchpad(touchpad_id, False)
                disabled = True
            elif not event.is_set() and disabled:
                toggle_touchpad(touchpad_id, True)
                disabled = False
            event.clear()
    except KeyboardInterrupt:
        logging.info("Terminating script")


def signal_handler(signum, frame):
    global touchpad_id_global
    logging.info("Signal received, terminating script and enabling touchpad")
    toggle_touchpad(touchpad_id_global, True)
    sys.exit(0)


def main():
    global touchpad_id_global
    parser = argparse.ArgumentParser(
        description="Control touchpad based on keyboard activity."
    )
    parser.add_argument("touchpad_id", type=str, help="Touchpad device ID")
    parser.add_argument("keyboard_id", type=str, help="Keyboard device ID")
    parser.add_argument("wait_time", type=float, help="Waiting time in seconds")
    parser.add_argument("--log_level", type=str, default="INFO", help="Log level")
    args = parser.parse_args()

    setup_logging(getattr(logging, args.log_level.upper(), logging.INFO))

    touchpad_id_global = args.touchpad_id
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    event = threading.Event()
    keypress_thread = threading.Thread(
        target=listen_for_keypress, args=(event, args.keyboard_id), daemon=True
    )
    keypress_thread.start()

    try:
        set_touchpad_state(event, args.touchpad_id, args.wait_time)
    finally:
        keypress_thread.join()


if __name__ == "__main__":
    main()

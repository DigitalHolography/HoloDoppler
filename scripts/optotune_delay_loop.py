import socket
import time
import signal
from opto import Opto

A_CURRENT_mA = 98
B_CURRENT_mA = 109.5

TIME_DELAY_period_A = 2  # s
TIME_DELAY_period_B = 4  # s

def set_lens_current_mA(lens, value):
    """Set lens current using an already connected Opto object"""
    try:
        lens.current(value)
        print(f"Lens current set to {value} mA.")
        return True
    except Exception as e:
        print(f"Error setting current to {value} mA: {e}")
        return False

def loop_function(lens):
    t = 0
    try:
        while True:  # break manually (Ctrl+C)
            if not set_lens_current_mA(lens, A_CURRENT_mA):
                break
            time.sleep(TIME_DELAY_period_A)

            if not set_lens_current_mA(lens, B_CURRENT_mA):
                break
            time.sleep(TIME_DELAY_period_B)

            t += (TIME_DELAY_period_A + TIME_DELAY_period_B)
            print(f"Total time elapsed: {t:.1f} seconds")

    except KeyboardInterrupt:
        print("\nLoop interrupted by user")
    except Exception as e:
        print(f"Unexpected error in loop: {e}")
    finally:
        # Reset to a safe state before exiting
        print("Resetting lens to initial state...")
        set_lens_current_mA(lens, A_CURRENT_mA)

def main():
    try:
        # Open connection once
        with Opto(port='COM4') as lens:
            print(f"Connected to Optotune on COM4")

            # Initialize to A state
            set_lens_current_mA(lens, A_CURRENT_mA)
            time.sleep(0.5)  # Give time for initialization

            # Run the main loop
            loop_function(lens)

    except Exception as e:
        print(f"Failed to connect to Optotune: {e}")
        print("Please check:")
        print("  - Is the device powered on?")
        print("  - Is it connected to COM4?")
        print("  - Is the port already in use by another program?")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())

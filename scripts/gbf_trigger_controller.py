# import pyvisa
# import time

# # Connect using pyvisa-py backend
# rm = pyvisa.ResourceManager('@py')

# # List resources to confirm you have the right one
# resources = rm.list_resources()
# print("Available resources:", resources)

# # Find the USB resource
# usb_resources = [res for res in resources if res.startswith('USB')]
# if not usb_resources:
#     print("No USB device found!")
#     exit()

# # Use the first USB resource (should be your AFG)
# resource_string = usb_resources[0]
# print(f"Using: {resource_string}")

# # Open the connection
# afg = rm.open_resource(resource_string)
# afg.read_termination = '\n'
# afg.write_termination = '\n'

# # Verify connection
# try:
#     idn = afg.query('*IDN?')
#     print(f"Connected to: {idn}")
# except Exception as e:
#     print(f"Error: {e}")
#     exit()

# # Recall preset 1 and turn on channel 1
# preset_number = 1
# afg.write(f'*RCL {preset_number}')
# print(f"Recalled preset {preset_number}")
# time.sleep(0.1)

# afg.write('OUTPut1:STATe ON')
# print("Channel 1 output turned ON")

# # Close connection
# afg.close()

# install with pip install tm_devices

import socket
import time
import signal
import pyvisa

# --- Tektronix AFG3252C Configuration ---
TIME_DELAY = 5.0  # seconds to wait before turning on after trigger
TIME_OFF = 20.0  # seconds to keep output on before turning off


# --- Initialize Tektronix Connection ---
def init_tektronix():
    """Initialize and return the AFG connection, default output OFF"""
    rm = pyvisa.ResourceManager("@py")
    resources = rm.list_resources()

    # Find the USB resource
    usb_resources = [res for res in resources if res.startswith("USB")]
    if not usb_resources:
        raise Exception("No USB device found!")

    resource_string = usb_resources[0]
    print(f"📡 Using Tektronix at: {resource_string}")

    # Open the connection
    afg = rm.open_resource(resource_string)
    afg.read_termination = "\n"
    afg.write_termination = "\n"

    # Verify connection
    idn = afg.query("*IDN?")
    print(f"✅ Connected to: {idn}")

    # Set default state: recall preset and turn OFF
    afg.write("*RCL 1")
    print("📋 Recalled preset 1")
    time.sleep(0.1)

    afg.write("OUTPut1:STATe OFF")
    print("🔴 Channel 1 output OFF (default)")

    return afg


def tektronix_on(afg):
    """Turn on the Tektronix output"""
    afg.write("OUTPut1:STATe ON")
    print("🟢 Channel 1 output ON")


def tektronix_off(afg):
    """Turn off the Tektronix output"""
    afg.write("OUTPut1:STATe OFF")
    print("🔴 Channel 1 output OFF")


def trigger_function(afg):
    """Trigger sequence: wait, turn on, wait, turn off"""
    print(f"⏳ Waiting {TIME_DELAY}s before turning on...")
    time.sleep(TIME_DELAY)

    tektronix_on(afg)

    print(f"⏳ Keeping output ON for {TIME_OFF}s...")
    time.sleep(TIME_OFF)

    tektronix_off(afg)


# --- TCP Configuration ---
TCP_IP = "127.0.0.1"
TCP_PORT = 50000

# --- Global flag for graceful shutdown ---
running = True


def signal_handler(sig, frame):
    """Handle Ctrl+C to exit gracefully."""
    global running
    print("\n🛑 Ctrl+C detected. Shutting down...")
    running = False


def main():
    global running
    signal.signal(signal.SIGINT, signal_handler)

    # Initialize Tektronix (output starts OFF)
    try:
        afg = init_tektronix()
    except Exception as e:
        print(f"❌ Failed to initialize Tektronix: {e}")
        return

    print(f"🔌 Connecting to TCP server at {TCP_IP}:{TCP_PORT}...")

    client_socket = None

    try:
        # Create socket and connect
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(1.0)  # Timeout to allow checking running flag
        client_socket.connect((TCP_IP, TCP_PORT))

        print(f"✅ Connected to server at {TCP_IP}:{TCP_PORT}")
        print("📡 Listening for messages... (Press Ctrl+C to exit)\n")

        # Main loop: receive and process messages
        while running:
            try:
                # Receive data
                data = client_socket.recv(1024)
                if not data:
                    print("⚠️ Server disconnected.")
                    break

                message = data.decode("utf-8").strip()
                print(f"📩 Received: '{message}'")

                # Check for RECORD_START
                if message == "RECORD_START":
                    print("🎯 RECORD_START detected! Triggering Tektronix sequence...")
                    trigger_function(afg)

            except socket.timeout:
                # Timeout occurred, loop will check running flag
                continue
            except ConnectionResetError:
                print("⚠️ Connection reset by server.")
                break
            except Exception as e:
                print(f"❌ Error receiving data: {e}")
                break

    except ConnectionRefusedError:
        print(f"❌ Could not connect to {TCP_IP}:{TCP_PORT}")
        print("Make sure the MATLAB TCP server is running.")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Cleanup: Turn off output and close connection
        print("\n🧹 Cleaning up...")
        try:
            tektronix_off(afg)
            afg.close()
            print("✅ Tektronix connection closed")
        except Exception as e:
            pass

        if client_socket:
            client_socket.close()
        print("✅ Client stopped.")


if __name__ == "__main__":
    main()

# import socket
# import time
# import signal
# import sys
# from opto import Opto  # Python interface for Optotune lenses

# # --- Configuration ---
# TCP_IP = '127.0.0.1'
# TCP_PORT = 50000
# LENS_PORT = 'COM4'  # ✅ Updated to your correct port
# START_DIOPT = 1.0
# END_DIOPT = 5.0
# DELAY_SECONDS = 1.0

# # --- Calibration: Current to Diopter mapping ---
# # ⚠️ CRITICAL: You need to calibrate these values for your specific lens
# # This is a placeholder. The actual mapping depends on your lens and driver.
# def diopter_to_current(diopter):
#     """
#     Convert diopter to current (mA).
#     This is a linear approximation. REPLACE with actual calibration data.
#     """
#     # Example: 1 diopter = 100 mA, 5 diopters = 500 mA
#     # YOU MUST CALIBRATE THIS FOR YOUR SPECIFIC LENS
#     return diopter * 100.0  # Placeholder - REPLACE WITH REAL CALIBRATION

# # --- Global flag for graceful shutdown ---
# running = True

# def signal_handler(sig, frame):
#     """Handle Ctrl+C to exit gracefully."""
#     global running
#     print("\nCtrl+C detected. Shutting down...")
#     running = False

# def main():
#     global running
#     signal.signal(signal.SIGINT, signal_handler)

#     # --- 1. Initialize the Optotune lens ---
#     print(f"Connecting to Optotune lens on {LENS_PORT}...")
#     try:
#         # The 'opto' library uses a context manager for safe connection handling
#         with Opto(port=LENS_PORT) as lens:
#             print(f"✅ Lens connected successfully on {LENS_PORT}")

#             # --- 2. Setup TCP Server ---
#             server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#             server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#             server_socket.bind((TCP_IP, TCP_PORT))
#             server_socket.listen(1)
#             print(f"✅ TCP Server listening on {TCP_IP}:{TCP_PORT}")
#             print("Waiting for a client to connect...")

#             # --- 3. Wait for a connection ---
#             client_socket, client_address = server_socket.accept()
#             print(f"✅ Connection established with {client_address}")
#             print("\n--- Ready and waiting for commands ---")
#             print("Send 'RECORD_START' to trigger lens change")
#             print("Press Ctrl+C to exit\n")

#             # --- 4. Main loop: receive messages and process commands ---
#             while running:
#                 try:
#                     # Receive data (up to 1024 bytes)
#                     data = client_socket.recv(1024)
#                     if not data:
#                         # Client disconnected
#                         print("⚠️ Client disconnected.")
#                         break

#                     message = data.decode('utf-8').strip()
#                     print(f"📩 Received message: '{message}'")

#                     # Check for the trigger command
#                     if message == "RECORD_START":
#                         print(f"🎯 Trigger received! Waiting {DELAY_SECONDS}s...")
#                         time.sleep(DELAY_SECONDS)

#                         # Calculate current for target diopter
#                         target_current = diopter_to_current(END_DIOPT)
#                         print(f"🔧 Setting lens to {END_DIOPT} diopters ({target_current:.1f} mA)")

#                         # Set the lens current
#                         lens.current(target_current)

#                         print(f"✅ Lens set to {END_DIOPT} diopters")

#                         # Optional: Send confirmation back to client
#                         client_socket.send(f"Lens set to {END_DIOPT} diopters\n".encode('utf-8'))

#                         # Optional: Reset to start diopter after 3 seconds (uncomment if needed)
#                         # print(f"⏱️ Resetting to {START_DIOPT} diopters in 3s...")
#                         # time.sleep(3)
#                         # start_current = diopter_to_current(START_DIOPT)
#                         # lens.current(start_current)
#                         # print(f"✅ Lens reset to {START_DIOPT} diopters")

#                     else:
#                         print(f"ℹ️ Ignoring unrecognized message: '{message}'")

#                 except ConnectionResetError:
#                     print("⚠️ Connection reset by client.")
#                     break
#                 except Exception as e:
#                     print(f"❌ An error occurred: {e}")
#                     break

#             # --- 5. Clean up ---
#             print("\n🧹 Cleaning up...")
#             client_socket.close()
#             server_socket.close()
#             print("✅ Program finished.")

#     except Exception as e:
#         print(f"❌ Failed to initialize lens: {e}")
#         print("Please check:")
#         print("  1. Is the lens driver powered on?")
#         print(f"  2. Is it connected to {LENS_PORT}?")
#         print("  3. Do you have the correct drivers installed?")
#         sys.exit(1)

# if __name__ == "__main__":
#     main()

import socket
import time
import signal

# import sys
from opto import Opto

A_CURRENT_mA=105
B_CURRENT_mA=110
TIME_DELAY_before_A = 1 #s
TIME_DELAY_period_A = 1 #s
TIME_DELAY_period_B = 1 #s
TIME_DELAY_end = 10 #s


def set_lens_current_mA(value):
    # Set lens current to value mA
    with Opto(port="COM4") as lens:
        lens.current(value)
        print(f"Lens current set to {value} mA.")

set_lens_current_mA(B_CURRENT_mA) #init

def trigger_function():
    t=0
    set_lens_current_mA(B_CURRENT_mA) #reset but should already be
    time.sleep(TIME_DELAY_before_A)
    while t <= TIME_DELAY_end:
        set_lens_current_mA(B_CURRENT_mA)
        time.sleep(TIME_DELAY_period_B)
        set_lens_current_mA(A_CURRENT_mA)
        time.sleep(TIME_DELAY_period_A)
        t+=(TIME_DELAY_period_A+TIME_DELAY_period_B)
    set_lens_current_mA(B_CURRENT_mA) #reset but should already be


# --- Configuration ---
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
                    print("🎯 RECORD_START detected!")

                    trigger_function()
                    # Here you can add your action
                    # For example: call your lens control function
                    # from opto import Opto
                    # with Opto(port='COM4') as lens:
                    #     lens.current(500.0)  # Set to 5 diopters

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
        print("\n🧹 Cleaning up...")
        if client_socket:
            client_socket.close()
        print("✅ Client stopped.")


if __name__ == "__main__":
    trigger_function()
    main()

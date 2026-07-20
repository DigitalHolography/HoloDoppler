import socket
import time
import signal
import threading
from opto import Opto

# Configuration des courants
A_CURRENT_mA = 98
B_CURRENT_mA = 109.5
TIME_DELAY = 2.0  # Temps entre chaque commutation (en secondes)

# État global
current_state = 'B'  # État initial
running = True
trigger_pending = False
trigger_time = 0
next_switch_time = 0
lock = threading.Lock()

def set_lens_current_mA(value):
    """Définit le courant de la lentille en mA"""
    with Opto(port='COM4') as lens:
        lens.current(value)
        print(f"[{time.time():.3f}] Lens current set to {value} mA.")

def toggle_current():
    """Bascule entre le courant A et B"""
    global current_state
    
    if current_state == 'B':
        set_lens_current_mA(A_CURRENT_mA)
        current_state = 'A'
    else:
        set_lens_current_mA(B_CURRENT_mA)
        current_state = 'B'

def trigger_function():
    """Fonction appelée lors du trigger - impose un switch dans TIME_DELAY secondes"""
    global trigger_pending, trigger_time, next_switch_time
    
    with lock:
        current_time = time.time()
        trigger_pending = True
        trigger_time = current_time + TIME_DELAY
        
        # Annule le prochain switch programmé
        next_switch_time = trigger_time
        print(f"⏰ [{current_time:.3f}] Trigger enregistré - Switch forcé à {trigger_time:.3f}s (dans {TIME_DELAY*1000:.0f}ms)")
        print(f"   ↳ Prochain switch programmé annulé et remplacé par le switch forcé")

def perform_forced_switch():
    """Effectue un switch forcé"""
    global trigger_pending, next_switch_time
    
    current_time = time.time()
    print(f"🔀 [{current_time:.3f}] Switch FORCÉ déclenché par le trigger")
    toggle_current()
    
    # Après le switch forcé, reprogramme le prochain switch
    next_switch_time = current_time + TIME_DELAY
    print(f"   ↳ Prochain switch programmé à {next_switch_time:.3f}s")

def main_loop():
    """Boucle principale qui commute en permanence entre A et B"""
    global running, trigger_pending, trigger_time, next_switch_time
    
    # Initialisation
    set_lens_current_mA(B_CURRENT_mA)
    next_switch_time = time.time() + TIME_DELAY
    
    print(f"🔄 Commutation entre {A_CURRENT_mA}mA et {B_CURRENT_mA}mA toutes les {TIME_DELAY*1000:.0f}ms")
    print(f"   ↳ Prochain switch programmé à {next_switch_time:.3f}s")
    print("📡 En attente de triggers... (Appuyez sur Ctrl+C pour arrêter)\n")
    
    while running:
        current_time = time.time()
        
        # Vérifie si un trigger est en attente
        with lock:
            if trigger_pending and current_time >= trigger_time:
                # Effectue le switch forcé
                perform_forced_switch()
                trigger_pending = False
                continue
        
        # Vérifie si c'est l'heure de la commutation programmée
        if current_time >= next_switch_time:
            print(f"🔄 [{current_time:.3f}] Switch programmé")
            toggle_current()
            next_switch_time = current_time + TIME_DELAY
            print(f"   ↳ Prochain switch programmé à {next_switch_time:.3f}s")
        
        # Petite pause pour ne pas surcharger le CPU (1ms pour haute précision)
        time.sleep(0.001)

# --- Configuration TCP ---
TCP_IP = '127.0.0.1'
TCP_PORT = 50000

def signal_handler(sig, frame):
    """Gère Ctrl+C pour arrêter proprement"""
    global running
    print("\n🛑 Ctrl+C détecté. Arrêt en cours...")
    running = False

def main():
    global running
    signal.signal(signal.SIGINT, signal_handler)
    
    print(f"🔌 Connexion au serveur TCP {TCP_IP}:{TCP_PORT}...")
    
    client_socket = None
    
    try:
        # Crée le socket et se connecte
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(0.01)  # Timeout court pour meilleure réactivité
        client_socket.connect((TCP_IP, TCP_PORT))
        
        print(f"✅ Connecté au serveur {TCP_IP}:{TCP_PORT}")
        print("📡 Écoute des messages... (Ctrl+C pour quitter)\n")
        
        # Démarre la boucle de commutation dans un thread séparé
        switch_thread = threading.Thread(target=main_loop, daemon=True)
        switch_thread.start()
        
        # Boucle principale pour recevoir les messages TCP
        while running:
            try:
                data = client_socket.recv(1024)
                if not data:
                    print("⚠️ Serveur déconnecté.")
                    break
                
                message = data.decode('utf-8').strip()
                print(f"📩 [{time.time():.3f}] Reçu : '{message}'")
                
                # Vérifie si c'est RECORD_START
                if message == "RECORD_START":
                    trigger_function()
                    
            except socket.timeout:
                continue
            except ConnectionResetError:
                print("⚠️ Connexion réinitialisée par le serveur.")
                break
            except Exception as e:
                print(f"❌ Erreur de réception : {e}")
                break
                
    except ConnectionRefusedError:
        print(f"❌ Impossible de se connecter à {TCP_IP}:{TCP_PORT}")
        print("Vérifiez que le serveur TCP MATLAB est en cours d'exécution.")
    except Exception as e:
        print(f"❌ Erreur : {e}")
    finally:
        print("\n🧹 Nettoyage...")
        running = False
        if client_socket:
            client_socket.close()
        print("✅ Client arrêté.")

if __name__ == "__main__":
    main()
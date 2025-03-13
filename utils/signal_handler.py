import signal
import sys
import time

def signal_handler(sig, frame):
    print("\n👋 Script terminato. Browser ancora attivo!")
    sys.exit(0)

def keep_running():
    print("\n✨ Script completato. Browser attivo. Premi Ctrl+C per terminare.")
    while True:
        time.sleep(1)

def setup_signal_handling():
    signal.signal(signal.SIGINT, signal_handler)
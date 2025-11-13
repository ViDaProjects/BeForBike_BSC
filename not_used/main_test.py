import sys
import time
from PySide6.QtCore import QCoreApplication, Slot


from blinker_module import BlinkerSystem

@Slot(str)
def on_blinker_active(direction):
    print(f"Blinker active to direction: {direction}")

@Slot(str)
def on_blinker_inactive(direction):
    print(f"{direction} blinker is inactive")

if __name__ == "__main__":
    app = QCoreApplication(sys.argv)
    
    print("--- Main Test Application Started ---")
    
    blinker_system = BlinkerSystem(app)
    
    blinker_system.blinkerActivated.connect(on_blinker_active)
    blinker_system.worker.blinkerDeactivated.connect(on_blinker_inactive)
    
    try:
        
        sys.exit(app.exec())
        
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt caught. Cleaning up...")
        
    finally:
        
        blinker_system.cleanup()
        print("--- Main Test Application Finished ---")

from PySide6.QtCore import QObject, QMutex, Slot, Signal

class RideState(QObject):
    """
    Esta classe é a "Fonte Única da Verdade" para o estado da corrida.
    Ela é thread-safe.
    """
    
    # Sinal opcional para a UI, se necessário
    state_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_riding = False
        self._mutex = QMutex()

    @Slot()
    def start_ride(self):
        """Inicia a corrida."""
        self._mutex.lock()
        self._is_riding = True
        self._mutex.unlock()
        self.state_changed.emit(True)
        # logging.info("[RideState]: Corrida INICIADA")

    @Slot()
    def stop_ride(self):
        """Para a corrida."""
        self._mutex.lock()
        self._is_riding = False
        self._mutex.unlock()
        self.state_changed.emit(False)
        # logging.info("[RideState]: Corrida PARADA")

    def is_riding(self) -> bool:
        """Verifica o estado da corrida de forma thread-safe."""
        self._mutex.lock()
        status = self._is_riding
        self._mutex.unlock()
        return status
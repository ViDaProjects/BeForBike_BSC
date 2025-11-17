from PySide6.QtCore import QObject, QMutex, Slot, Signal
import logging # Importar logging é uma boa prática para debug

class RideState(QObject):
    """
    Esta classe é a "Fonte Única da Verdade" para o estado da corrida.
    Ela é thread-safe.
    """
    
    # Sinal que emite o novo estado (True/False)
    state_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_riding = False
        self._mutex = QMutex()

    @Slot(bool) # O Slot agora espera um booleano
    def set_ride_status(self, is_riding: bool):
        """
        Define o estado da corrida (True para INICIAR, False para PARAR).
        """
        self._mutex.lock()
        # Verifica se o estado realmente mudou para evitar emissões desnecessárias
        if self._is_riding != is_riding:
            self._is_riding = is_riding
            status = "INICIADA" if is_riding else "PARADA"
            # logging.info(f"[RideState]: Corrida {status}")
            self.state_changed.emit(is_riding)
        self._mutex.unlock()

    # Métodos de conveniência (opcional, mas bom para clareza)
    @Slot()
    def start_ride(self):
        self.set_ride_status(True)

    @Slot()
    def stop_ride(self):
        self.set_ride_status(False)

    def is_riding(self) -> bool:
        """Verifica o estado da corrida de forma thread-safe."""
        self._mutex.lock()
        status = self._is_riding
        self._mutex.unlock()
        return status
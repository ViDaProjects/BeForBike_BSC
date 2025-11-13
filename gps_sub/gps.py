import sys
import serial
import json
import time
import signal
from PySide6.QtCore import QThread, QCoreApplication, QTimer, Signal as pyqtSignal

DURACAO_COLETA_SEGUNDOS = 1 * 60 

class GpsGatherSignal(QThread):
    collectionFinished = pyqtSignal() 

    def __init__(self, parent=None):
        super().__init__(parent) 
        
        self.port = "/dev/serial0"
        self.baudrate = 9600
        self.is_running = True
        
        self.collected_data = [] 
        self.collected_data2 = []

    def run(self):
        """
        Este método é executado na nova thread.
        """
        print(f"GpsGatherThread: Iniciando coleta na thread ID:")        
        try:
            ser = serial.Serial(self.port, self.baudrate, timeout=0.5)
            print("GpsGatherThread: Aguardando dados do GPS...")
            
            # Variáveis para controlar o lote
            self.collected_data = []  # O lote atual, do segundo atual
            self.collected_data2 = [] # Onde guardamos os lotes fechados
            last_timestamp = None     # O timestamp do último segundo que vimos
            
            while self.is_running:
                try:
                    # 1. Ler a linha, decodificar e limpar (remover \n, \r, etc.)
                    newdata = ser.readline().decode('ascii', errors='replace').strip()
                    
                    # 2. Se a linha estiver vazia (por causa do timeout), pule para a próxima
                    if not newdata:
                        continue
                        
                    # 3. Procure pela sua "sentença âncora"
                    #    Usaremos GNRMC, mas GPRMC, GNGGA, etc., também funcionam.
                    #    O importante é que ela contenha o timestamp no campo 1.
                    if newdata.startswith(('$GNRMC', '$GPRMC', '$GNGGA')):
                        fields = newdata.split(',')
                        
                        # Verificação de segurança: a linha tem campos suficientes?
                        if len(fields) > 1:
                            current_timestamp = fields[1] # Ex: "001118.00"
                            
                            # 4. Esta é a lógica principal!
                            # Se o timestamp mudou E não é a primeira vez que rodamos...
                            if current_timestamp != last_timestamp and last_timestamp is not None:
                                
                                # 5. O lote anterior está completo. Salve-o.
                                if self.collected_data:
                                    self.collected_data2.append(self.collected_data)
                                    # O print abaixo é útil para debug, mas pode poluir
                                    print(f"Lote salvo para {last_timestamp}: {len(self.collected_data)} mensagens.")
                                
                                # 6. Comece um novo lote
                                self.collected_data = []
                            
                            # 7. Atualize o "último timestamp" visto
                            last_timestamp = current_timestamp

                    # 8. Adicione a linha atual ao lote
                    #    Isso garante que a GNRMC e todas as GSA, GSV, etc.,
                    #    sejam adicionadas ao lote do segundo a que pertencem.
                    #    Só começamos a adicionar DEPOIS de ver o primeiro timestamp.
                    if last_timestamp is not None:
                        self.collected_data.append(newdata)
                
                except Exception as e:
                    print(f"GpsGatherThread: Erro no loop: {e}. Linha: '{newdata}'")

        except serial.SerialException as e:
            print(f"GpsGatherThread: Falha ao abrir porta serial {self.port}. {e}")
        
        finally:
            print("GpsGatherThread: Coleta encerrada.")
            if 'ser' in locals() and ser.is_open:
                self.save_data()

                ser.close()
                self.collectionFinished.emit()



    def save_data(self):
        if not self.collected_data:
            print("GpsGatherThread: Nenhum dado foi coletado. Nenhum arquivo salvo.")
            return

        print(f"GpsGatherThread: Salvando {len(self.collected_data)} linhas de dados...")
        
        try:
            with open("gps_data_semtrip.txt", "w") as f_txt:
                for line in self.collected_data2:
                    f_txt.write(str(line) )
                    f_txt.write("\n")
            print("GpsGatherThread: Dados salvos em gps_data.txt")
        except IOError as e:
            print(f"GpsGatherThread: Erro ao salvar TXT: {e}")
        
        try:
            with open("gps_data.json", "w") as f_json:
                json.dump(self.collected_data2, f_json, indent=4)
                f_json.write("\n")

            print("GpsGatherThread: Dados salvos em gps_data.json")
        except IOError as e:
            print(f"GpsGatherThread: Erro ao salvar JSON: {e}")

    def stop(self):
        """
        Este método é chamado (pelo QTimer ou Ctrl+C) a partir do thread principal
        para sinalizar que a thread 'run()' deve parar.
        """
        if self.is_running:
            print("GpsGatherThread: Recebido sinal de parada (do thread principal).")
            self.is_running = False

if __name__ == "__main__":
    
    app = QCoreApplication(sys.argv)
    
# gps.py (linha 94)
    print(f"Main: Script iniciado na thread ID")
    print(f"Main: A coleta rodará por {DURACAO_COLETA_SEGUNDOS / 60:.0f} minutos.")

    gps_thread = GpsGatherSignal()
    
    gps_thread.collectionFinished.connect(app.quit)

    stop_timer = QTimer()
    stop_timer.setSingleShot(True) 
    

    stop_timer.timeout.connect(gps_thread.stop)
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    try:
        gps_thread.start()
        
        stop_timer.start(DURACAO_COLETA_SEGUNDOS * 1000)
        
        print("Main: Loop de eventos do Qt iniciado. Pressione Ctrl+C para parar antes.")
        status = app.exec()
        print(f"Main: Loop de eventos terminado com status {status}.")

    except KeyboardInterrupt:
        print("\nMain: Ctrl+C recebido. Parando a thread e salvando...")
        stop_timer.stop() 
        gps_thread.stop()  
        
        if gps_thread.isRunning():
            print("Main: Aguardando a thread finalizar o salvamento...")
            gps_thread.wait()
            
        print("Main: Script finalizado manualmente.")
        sys.exit(0)

    print("Main: Script finalizado (via QApp).")
    sys.exit(status)
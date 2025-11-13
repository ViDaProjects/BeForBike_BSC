# al.py
import json
import random

from datetime import datetime
import time
import sys
from comm_protocol import FileManagerMsg, FileMngMsgId, PacketInfo, GpsData, CrankData, TelemetryMsg
from file_mannager import FileMannagerThread
from queue import Queue
# Importe QObject e Slot para lidar com os sinais
from PySide6.QtCore import QCoreApplication, QObject, Slot

# --- Configurações ---
NUM_LINES = 30
# Coordenadas base (Curitiba)
BASE_LAT = -25.4296
BASE_LON = -49.2675

class Generator(QObject):
    """
    Esta classe vai gerenciar a lógica assíncrona para nós.
    Ela vai pedir o ID e esperar o sinal de resposta.
    """
    def __init__(self, app, file_thread, file_queue, parent=None):
        super().__init__(parent)
        self.app = app
        self.thread = file_thread
        self.queue = file_queue
        self.ride_id = -1 # Valor padrão
    
    def start_process(self):
        """ Inicia todo o processo. """
        
        # 1. Conectar o sinal:
        # O sinal 'id' em file_mannager.py emite um 'int'.
        # Portanto, nosso slot 'on_id_received' deve aceitar um 'int'.
        print("Conectando sinal 'id'...")
        self.thread.id.connect(self.on_id_received)
        
        # 2. Iniciar a thread
        print("Iniciando FileMannagerThread...")
        self.thread.start()
        
        # 3. Pedir o ID
        print("Solicitando novo Ride ID da thread...")
        msg = FileManagerMsg(msg_id=FileMngMsgId.GET_RIDE_ID)
        self.queue.put(msg)
        # O script agora vai esperar (no app.exec()) até o sinal ser recebido.

    @Slot(int) # Este decorador diz ao Qt que esta função é um slot que recebe um 'int'
    def on_id_received(self, received_id):
        """
        Esta função é CHAMADA AUTOMATICAMENTE quando a thread
        emite o sinal 'id'.
        """
        print(f"Ride ID recebido da thread: {received_id}")
        self.ride_id = received_id
        
        # 4. Agora que temos o ID, podemos gerar os dados e pedir para salvar
        self.generate_and_save_data()
        time.sleep(2)
        msg = FileManagerMsg(msg_id=FileMngMsgId.SEARCH_FILES)
        self.queue.put(msg)
        time.sleep(2)
        #msg = FileManagerMsg(msg_id=FileMngMsgId.DELETE_FILE, file_name=f"Ride{self.ride_id}.json")
        #self.queue.put(msg)
        time.sleep(2)


        # 5. Terminar o processo de forma limpa
        print("Solicitando parada da thread...")
        self.thread.stop()
        self.thread.wait() # Espera a thread realmente parar
        print("Encerrando aplicação.")
        self.app.quit() # Pede para o loop de eventos sair




# --- A função corrigida ---
# (Assumindo que esta função é um método de uma classe 
#  que tem 'self.ride_id' e 'self.queue')

    def generate_and_save_data(self):
        """ 
        Gera os dados e envia a mensagem CREATE_FILE,
        com a ESTRUTURA CORRETA (TelemetryMsg). 
        """

        file_name = f"Ride{self.ride_id}.json"
        print(f"Gerando {NUM_LINES} linhas de dados para o arquivo '{file_name}'...")

        lista = []
        try:
            for i in range(NUM_LINES):
                # 1. Obter informações de data/hora
                now = datetime.now()
                current_date = now.strftime("%Y-%m-%d")
                current_time = now.strftime("%H:%M:%S")
                current_timestamp = now.isoformat()

                # 2. Criar o objeto PacketInfo
                info_data = PacketInfo(
                    ride_id=self.ride_id,
                    date=current_date,
                    time=current_time
                )

                # 3. Gerar dados e criar o objeto GpsData
                latitude = round(BASE_LAT + random.uniform(-0.01, 0.01), 6)
                longitude = round(BASE_LON + random.uniform(-0.01, 0.01), 6)
                # O 'velocity' do seu código original, mapeado para 'speed'
                velocity_kmh = round(random.uniform(0.0, 50.0), 1) 

                altitude_val = None
                if random.random() < 0.8: # 80% de chance de ter altitude
                    altitude_val = round(random.uniform(850.0, 950.0), 1)

                gps_data = GpsData(
                    timestamp=current_timestamp,
                    latitude=latitude,
                    longitude=longitude,
                    altitude=altitude_val,
                    speed=velocity_kmh, # Usando a 'velocity' do seu código original
                    direction=round(random.uniform(0.0, 359.9), 1), # Fictício
                    fix_satellites=random.randint(4, 12),           # Fictício
                    fix_quality=random.choice([1, 2])               # Fictício
                )

                # 4. Gerar dados e criar o objeto CrankData (opcional)
                crank_data = None
                if random.random() < 0.9: # 90% de chance de ter dados do crank
                    power = round(random.uniform(50.0, 400.0), 1)
                    crank_data = CrankData(
                        power=power,
                        cadence=round(random.uniform(60.0, 110.0), 1), # Fictício
                        joules=round(random.uniform(1000.0, 50000.0), 0), # Fictício
                        calories=round(random.uniform(100.0, 1000.0), 0), # Fictício
                        speed_ms=velocity_kmh / 3.6,                  # Fictício
                        speed=velocity_kmh,                           # Fictício
                        distance=round(random.uniform(1.0, 50.0), 2)  # Fictício
                    )

                # 5. Montar a mensagem TelemetryMsg
                telemetry_msg = TelemetryMsg(
                    info=info_data,
                    gps=gps_data,
                    crank=crank_data
                )

                # 6. Converter para dicionário e depois para string JSON
                # O método .to_dict() cria a estrutura {"info":..., "gps":..., "crank":...}
                json_data = json.dumps(telemetry_msg.to_dict())
                lista.append(json_data)

            # 7. Enviar a mensagem para criar o arquivo (seu código original está correto)
            data_msg = FileManagerMsg(FileMngMsgId.CREATE_FILE, file_name=file_name, telemetry_list=lista)
            self.queue.put(data_msg)
            print(f"Mensagem 'CREATE_FILE' para '{file_name}' enviada para a fila.")

        except Exception as e:
            print(f"\nErro ao gerar dados: {e}")


# --- Ponto de Entrada Principal ---
if __name__ == "__main__":
    # Precisa passar sys.argv para QCoreApplication
    app = QCoreApplication(sys.argv)
    
    FileManagerQueue = Queue()
    SendDataQueue = Queue() # Necessário pela assinatura do __init__
    
    # Cria a thread
    ble_controler = FileMannagerThread(app, FileManagerQueue, SendDataQueue)
    
    # Cria nosso gerenciador de lógica
    generator = Generator(app, ble_controler, FileManagerQueue)
    
    # Inicia o processo
    generator.start_process()
    
    # 7. Inicia o loop de eventos do Qt
    # O script ficará "preso" aqui, processando eventos (como
    # a resposta do sinal da thread) até app.quit() ser chamado.
    print("Iniciando loop de eventos do Qt. Aguardando sinal...")
    sys.exit(app.exec())
import asyncio
from asyncio import Lock
import logging
import json
# QObject foi removido, QThread foi adicionado
from PySide6.QtCore import Slot, QThread, QSocketNotifier, QTimer, Signal

from bleak import BleakClient, BleakScanner
from queue import Queue, Empty
from collections import deque
from comm_protocol import FileManagerMsg, FileMngMsgId, RideDataMsg, CrankReading
import gzip


FIXED_PERIPHERAL_MAC = "01:23:45:67:90:E7"
COMPANY_ID = 0xF0F0
SECRET_KEY = b"Oficinas3"

# --- Constantes de UUIDs Usadas por esta Biblioteca ---
# CHARACTERISTIC_UUID_TX = "0000ffe1-0000-1000-8000-00805f9b34fb"
CHARACTERISTIC_UUID_TX = "12345678-1234-5678-1234-56789abcdef0"
UART_SERVICE_UUID_RX = "0000ffe1-0000-1000-8000-00805f9b34fb"

# 1. A classe agora herda de QThread
class BleManager(QThread):
    
    #device_connected_nano = Signal(str)
    #device_connected_tel = Signal(str)
    #device_desconnected_nano = Signal(str)
    #device_desconnected_tel = Signal(str)
    
    device_connection_failed = Signal(str)

    crank_connection_status = Signal(bool)
    app_connection_status = Signal(bool)


    def __init__(self, sendRideDataQueue: Queue, ProcessCrankDataQueue: Queue, FileManagerQueue: Queue, parent=None):
        # 2. Construtor do QThread é chamado
        super().__init__(parent)
        
        self.ble_buffers = {}

        self.fixed_mac = FIXED_PERIPHERAL_MAC
        self.company_id = COMPANY_ID
        self.secret_key = SECRET_KEY
        # dicionario para mapear endereços MAC para clientes BleakClient
        self.clients = {}
        # Set para rastrear dispositivos gerenciados(são removidos apenas quando falharem em reconectar)
        self.managed_devices = set()
        self.connection_tasks = {}
        self.main_loop = None
        self.ride_name= None 

        
        # 3. is_running começa como False
        self.is_running = False
        self.ble_lock = Lock()
        self.mobile_client_address = None
        self.latest_received_data = {}
        self.is_sending = False
        self.asked = False

        # ------------------------queues------------------------
        self.sendRideDataQueue = sendRideDataQueue
        self.ProcessCrankDataQueue = ProcessCrankDataQueue
        self.FileManagerQueue = FileManagerQueue
        self.priority_queue = deque()  # Fila de prioridade para dados perdidos

        self.setObjectName("BluetoothThread")

    # 4. Método start() adicionado (padrão FileMannagerThread)
    def start(self):
        """
        Inicia a thread. Define a flag de execução
        e chama o start() da classe base (QThread).
        """
        if self.is_running:
            logging.warning("Thread BleManager já está em execução.")
            return

        self.is_running = True
        # Chama o QThread.start(), que por sua vez chama o self.run()
        super().start()
        logging.info("Thread BleManager (asyncio) iniciada.")

    # 5. Lógica de parada do asyncio (o 'stop' original)
    def _stop_async_loop(self):
        """Cancela as tarefas asyncio pendentes."""
        self.is_running = False # Garante que loops async parem
        if self.main_loop and self.main_loop.is_running():
            logging.debug("Cancelando tarefas asyncio...")
            for task in asyncio.all_tasks(loop=self.main_loop):
                task.cancel()
        else:
            logging.debug("Loop asyncio não estava rodando ou não existe.")

    # 6. Método stop() adicionado (padrão FileMannagerThread)
    @Slot()
    def stop(self):
        """
        Para a thread de forma limpa (QThread e asyncio).
        """
        if not self.is_running:
            return

        logging.warning("Parando a thread BleManager...")
        
        # Primeiro, sinaliza para o loop asyncio parar
        self._stop_async_loop()

        # Pede para a thread Qt sair do seu loop de eventos (run())
        self.quit()

        # Espera a thread terminar
        if not self.wait(5000):
            logging.error("Thread BleManager não respondeu. Forçando finalização.")
            self.terminate()
        else:
            logging.info("Thread BleManager finalizada com sucesso.")

    # 7. O método run() é o que a thread executa.
    #    (Este era o seu 'run' original, mas não é mais um Slot)
    def run(self):
        """
        Este é o coração da thread. Inicia o loop de eventos asyncio.
        """
        self.main_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.main_loop)
        try:
            self.main_loop.run_until_complete(self._main_async_task())
        except asyncio.CancelledError:
            logging.info("Loop asyncio (BleManager) foi cancelado.")
        finally:
            logging.info("Loop asyncio (BleManager) finalizado.")
            self.main_loop.close()
            

    def _notification_handler(self, sender, data, address):
        logging.debug(f"Recebeu chunk de {address}: {data}")

        if address != self.fixed_mac:
            logging.warning(f"Recebeu notificação de dispositivo inesperado: {address}")
            return
        
        # (self.nano_buffer não foi definido no init, adicionando)
        if not hasattr(self, 'nano_buffer'):
            self.nano_buffer = b""
        
        self.nano_buffer += data
        while b"\n" in self.nano_buffer:
            try:
                message_bytes, self.nano_buffer = self.nano_buffer.split(b"\n", 1)
            except ValueError:
                break 
            try:
                message_str = message_bytes.decode('utf-8').strip()
            except UnicodeDecodeError as e:
                logging.error(f"Erro de decodificação (UTF-8) de {address}: {e}. Dados (hex): {message_bytes.hex()}")
                continue 
            if not message_str:
                continue
            try:
                data_dict = json.loads(message_str)
            except json.JSONDecodeError as e:
                logging.error(f"Erro ao decodificar JSON de {address}: {e}. String: '{message_str}'")
                continue
            #logging.info(f">>> [THREAD PRINCIPAL] Recebeu JSON de {address}: {data_dict}")
            """         debug
            self.latest_received_data[address] = data_dict

            try:
                with open(self.log_filepath, "a") as f: 
                    json.dump(data_dict, f)
                    f.write("\n") 
            except Exception as e:
                logging.error(f"Erro ao salvar dado no arquivo de log: {e}")

            """
            reading = CrankReading(data_dict['w'], data_dict['a'])
            #logging.info(reading)
            #print(f"Recebeu chunk de {reading})")

            self.ProcessCrankDataQueue.put(reading)

    def _disconnect_callback(self, client):
        address = client.address
        logging.warning(f"Dispositivo {address} desconectado.")
        if address in self.clients:
            del self.clients[address]
        if address == self.mobile_client_address:
            self.mobile_client_address = None
        
    async def _stabilize_connection(self, client, address):
        stabilization_time = 5
        start_time = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - start_time) < stabilization_time:
            if not client.is_connected:
                return False
            await asyncio.sleep(0.5)
        return client.is_connected

    async def _connect_and_manage(self, address):
        try:
            async with self.ble_lock:
                client = BleakClient(address, pair=False, disconnected_callback=self._disconnect_callback)
                await client.connect(timeout=15.0)
            if (client.is_connected 
           # and await self._stabilize_connection(client, address)
            ):
                self.clients[address] = client
                self.managed_devices.add(address)
                if address == self.fixed_mac:
                    #self.device_connected_nano.emit(address)
                    self.crank_connection_status.emit(True)

                    await client.start_notify(
                        UART_SERVICE_UUID_RX,
                        lambda s, d: self._notification_handler(s, d, address)
                    )
                else:
                    logging.info(f"Dispositivo móvel {address} conectado.")
                    #self.device_connected_tel.emit(address)
                    self.app_connection_status.emit(True)

                    self.mobile_client_address = address
                    self.send_data() 
                while client.is_connected and self.is_running:
                    await asyncio.sleep(1)
                return True
            elif 'client' in locals() and client.is_connected:
                await client.disconnect()
        except Exception as e:
            logging.error(f"Falha na conexão com {address}: {e}")
        return False

    async def _persistent_connection_task(self, address):
        MAX_RETRIES = 1 #TODO: 3
        RETRY_DELAY_SECONDS = 5
        retry_count = 0
        while self.is_running and retry_count < MAX_RETRIES:
            if await self._connect_and_manage(address):
                retry_count = 0
            else:
                retry_count += 1
                logging.warning(f"Falha na conexão com {address}. Tentativa {retry_count}/{MAX_RETRIES}")
                if self.is_running and retry_count < MAX_RETRIES:
                    await asyncio.sleep(RETRY_DELAY_SECONDS)
        if address in self.managed_devices:
            self.managed_devices.remove(address)
        if retry_count >= MAX_RETRIES:
            if address == self.fixed_mac:
                self.crank_connection_status.emit(False)
                #self.device_desconnected_nano.emit(address) 
            else:
                self.app_connection_status.emit(False)
                self.is_sending = False
                #self.device_desconnected_tel.emit(address)


    async def _periodic_scanner_task(self):
        """Scanner periódico que procura por novos dispositivos."""
        while self.is_running:
            try:
                if len(self.managed_devices) >= 2:
                    await asyncio.sleep(10)
                    continue

                async with self.ble_lock:
                    logging.info(f"Scanner ativo. Dispositivos gerenciados: {len(self.managed_devices)}")

                    discovered = await BleakScanner.discover(timeout=5.0)

                for dev in discovered:
                    if not self.is_running: break
                    if dev.address in self.managed_devices: continue

                    props = dev.details.get('props', {})
                    manufacturer_data = props.get('ManufacturerData', {})
                    #print(props)
                    if self.company_id in manufacturer_data :
                        if manufacturer_data[self.company_id] == self.secret_key:
                            if any(addr != self.fixed_mac for addr in self.managed_devices):
                                logging.info(f"Celular {dev.address} encontrado, mas já existe um celular sendo gerenciado.")
                                continue # Pula este dispositivo
                            logging.info(f"Celular encontrado: {dev.address}. Iniciando gerenciamento.")
                            self.managed_devices.add(dev.address)
                            task = asyncio.create_task(self._persistent_connection_task(dev.address))
                            self.connection_tasks[dev.address] = task

                    elif dev.address == self.fixed_mac:
                        logging.info(f"Dispositivo fixo encontrado: {dev.address}. Iniciando gerenciamento.")
                        self.managed_devices.add(dev.address)
                        task = asyncio.create_task(self._persistent_connection_task(dev.address))
                        self.connection_tasks[dev.address] = task

            except Exception as e:
                logging.error(f"Erro no scanner: {e}")

            if self.is_running:
                await asyncio.sleep(10)

    async def _main_async_task(self):
        asyncio.create_task(self._periodic_scanner_task())
        while self.is_running:
            await asyncio.sleep(1)

    def send_data(self):
        """Slot público que inicia a tarefa de envio, se não estiver rodando."""
        if self.is_sending:
            logging.info("Tarefa de envio já em execução, nova chamada ignorada.")
            return
        
        if self.main_loop and self.main_loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self._async_send_data(),
                self.main_loop
            )
        else:
            logging.error("Não foi possível agendar envio: Loop principal (asyncio) não está rodando.")


    async def _async_send_data(self):
        """
        Corrotina que drena as filas de envio e manda os dados para o celular.
        """
        
        if self.is_sending:
            logging.warning("_async_send_data chamada, mas já estava em execução. Saindo.")
            return
        
        self.is_sending = True
        logging.info("Tarefa de envio iniciada.")
        
        try:
            while(self.is_running):
                
                if not self.mobile_client_address:
                    logging.debug("Tarefa de envio pausada (sem celular conectado).")
                    await asyncio.sleep(1) 
                    continue 

                client_address = self.mobile_client_address
                client = self.clients.get(client_address)

                if not client or not client.is_connected:
                    logging.warning(f"Cliente {client_address} não encontrado ou desconectado. Pausando.")
                    await asyncio.sleep(1) # Espera o cliente se reconectar
                    continue
                
                data_list = None
                source_queue_name = None
                
                try:
                    data_list = self.priority_queue.popleft() 
                    source_queue_name = "prioridade (queue2)"
                except IndexError:
                    try:
                        #data_list = self.sendRideDataQueue.get()
                        data = self.sendRideDataQueue.get(timeout=1)
                        self.ride_name= data.file_name
                        data_list = data.telemetry_log
                        #self.ride_name= (f"ride_{data_list[0]["file_name"]}.json")
                        #data_list = data_list[1:]
                        source_queue_name = "principal (queue1)"
                    except Empty:
                        if not(self.asked):
                            self.asked = True
                            request = FileManagerMsg(msg_id=FileMngMsgId.SEARCH_FILES)
                            
                            self.FileManagerQueue.put(request)

                        await asyncio.sleep(0.1) 
                        continue
                
                logging.info(f"Processando bloco da fila {source_queue_name}...")

               
                if not isinstance(data_list, (list, deque)):
                    logging.warning(f"Item inesperado na fila (tipo {type(data_list)}): {data_list}. Ignorando.")
                    continue

                logging.info(f"Iniciando envio de {len(data_list)} pacotes ('chunks') para {client_address}...")
                BATCH_SIZE = 3
                for i in range(0, len(data_list), BATCH_SIZE):                    
                    if not self.is_running or self.mobile_client_address != client_address or not client.is_connected:
                        logging.warning(f"Envio interrompido no pacote {i+1}. O cliente desconectou ou mudou.")
                        remaining_data = data_list[i:]
                        self.priority_queue.appendleft(remaining_data) # Devolve para queue2
                        logging.info(f"{len(remaining_data)} itens devolvidos à fila de prioridade (queue2).")
                        break 
                    
                    try:
                        item = data_list[i:i+BATCH_SIZE]
                        if len(item) != 1:
                            payload_str = json.dumps(item)
                        payload = payload_str.encode('utf-8')
    
                        payload = gzip.compress(payload)
                        if len(payload) > 512:
                            logging.error(f"Pacote {i+1} é muito grande ({len(payload)} bytes > 512). PULANDO.")
                            continue
                        logging.info(f"Pacote {i+1}({len(payload)} ). .")

                        
                        await asyncio.wait_for(
                            client.write_gatt_char(
                                CHARACTERISTIC_UUID_TX,
                                payload,
                                response=True
                            ),
                            timeout=10.0 
                        )


                    except asyncio.TimeoutError as e:
                        logging.error(f"Erro ao enviar pacote {i+BATCH_SIZE+1}: Timeout de escrita (10s). A conexão está 'zumbi'. Abortando.")
                        remaining_data = data_list[i:]
                        self.priority_queue.appendleft(remaining_data) # Devolve para queue2
                        logging.info(f"{len(remaining_data)} itens devolvidos à fila de prioridade (queue2).")
                        
                        logging.error("Timeout é considerado um erro fatal. Forçando desconexão.")
                        try:
                            self._disconnect_callback(client)
                            await client.disconnect()
                        except Exception as disconnect_e:
                            logging.error(f"Erro ao tentar forçar a desconexão: {disconnect_e}")
                        
                        break 

                    except Exception as e:
                        logging.error(f"Erro ao enviar pacote {i+BATCH_SIZE +1}: {e}. Abortando envio atual.")
                        remaining_data = data_list[i:]
                        self.priority_queue.appendleft(remaining_data) # Devolve para queue2
                        logging.info(f"{len(remaining_data)} itens devolvidos à fila de prioridade (queue2).")
                        
                        error_str = str(e) 
                        
                        if ("0x12" in error_str or "Database Out Of Sync" in error_str or
                            "0x01" in error_str or "Invalid Handle" in error_str or
                            "0x0e" in error_str or "Unlikely Error" in error_str or
                            "InvalidArguments" in error_str):
                            
                            logging.error(f"Erro fatal de conexão GATT/BlueZ detectado ({error_str}). Forçando desconexão.")
                            try:
                                self._disconnect_callback(client)
                                await client.disconnect()
                            except Exception as disconnect_e:
                                logging.error(f"Erro ao tentar forçar a desconexão: {disconnect_e}")
                        
                        break 
                
                else:
                    logging.info(f"Envio de {len(data_list)} pacotes concluído com sucesso.")
                    if self.ride_name: # Garante que só deleta se o nome do ride foi pego da fila principal
                        #TODO: descomentar
                        #self.FileManagerQueue.put(FileManagerMsg(file_name=self.ride_name, msg_id=FileMngMsgId.DELETE_FILE))
                        self.ride_name= None 

        
        except asyncio.CancelledError:
            logging.info("Tarefa de envio (_async_send_data) foi cancelada.")
        except Exception as e:
            # Captura exceções inesperadas do loop principal
            logging.error(f"Erro catastrófico na tarefa de envio: {e}.")
        finally:
            self.is_sending = False # Garante que o flag seja limpo
            logging.info("Tarefa de envio finalizada/pausada.")

import os
import logging
from datetime import datetime, timezone, timedelta
from PySide6.QtCore import QObject, Slot

try:
    from ds1302 import DS1302
except ImportError:
    logging.critical("Biblioteca 'ds1302' não encontrada. Esta classe requer um RPi e a biblioteca 'ds1302-rpi'.")
    class DS1302:
        def __init__(self, *args, **kwargs):
            raise ImportError("Dependência 'ds1302' não encontrada.")


# --- Configuração dos Pinos ---
CLK_PIN = 17  # RTC_CLK -> GPIO17 (Pin 11)
DAT_PIN = 27  # RTC_DAT -> GPIO27 (Pin 13)
RST_PIN = 22  # RTC_RST -> GPIO22 (Pin 15)
# ---------------------

class RTCManager(QObject):
    """
    Gerencia um relógio de tempo real (RTC) DS1302.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.log = logging.getLogger("RTCManager")
        self.rtc = None
        try:
            self.rtc = DS1302(CLK_PIN, DAT_PIN, RST_PIN)
            self.log.info("RTC DS1302 inicializado com sucesso.")
        except Exception as e:
            self.log.error(f"Falha ao inicializar o DS1302: {e}")
            self.log.error("Verifique as permissões de GPIO ou se o hardware está conectado.")

    def _converter_utc_para_local(self, horario_utc_str: str, data_utc_str: str, fuso_offset_horas: int = -3) -> datetime | None:
        """
        Método auxiliar privado para converter strings UTC para datetime local.
        """
        timestamp_completo_str = f"{data_utc_str} {horario_utc_str.split('.')[0]}"
        formato_utc = "%d%m%y %H%M%S"

        try:
            dt_naive = datetime.strptime(timestamp_completo_str, formato_utc)
            dt_utc = dt_naive.replace(tzinfo=timezone.utc)
            fuso_local_desejado = timezone(timedelta(hours=fuso_offset_horas))
            dt_local = dt_utc.astimezone(fuso_local_desejado)
            return dt_local

        except ValueError as e:
            self.log.error(f"Erro ao parsear data/hora: '{timestamp_completo_str}'. Erro: {e}")
            return None
        
    @Slot(str, str)
    def set_rtc_from_utc_strings(self, horario_utc_str: str, data_utc_str: str, fuso_offset_horas: int = -3):
        """
        Recebe strings de data e hora do GPS (UTC), converte para o fuso local
        e acerta o relógio do RTC.
        """
        if not self.rtc:
            self.log.warning("set_rtc: RTC não inicializado. Abortando.")
            return

        dt_local = self._converter_utc_para_local(horario_utc_str, data_utc_str, fuso_offset_horas) 

        if dt_local:
            day_of_week_to_set = dt_local.isoweekday() 

            date_list = [
                dt_local.second,
                dt_local.minute,
                dt_local.hour,
                dt_local.day,
                dt_local.month,
                day_of_week_to_set,
                dt_local.year - 2000
            ]
            
            try:
                self.rtc.setDateTime(date_list)
                self.log.info(f"RTC atualizado para (local): {dt_local.strftime('%Y-%m-%d %H:%M:%S')}")
            except Exception as e:
                self.log.error(f"Erro ao tentar escrever no RTC: {e}")
        else:
            self.log.warning(f"set_rtc: Falha ao converter o tempo. RTC não atualizado.")

    def read_rtc_datetime(self) -> datetime | None:
        """
        Lê a data/hora atual do RTC e a retorna como um objeto datetime.
        """
        if not self.rtc:
            self.log.warning("read_rtc: RTC não inicializado. Abortando.")
            return None
        
        try:
            t_str = self.rtc.getDateTime()
            
            try:
                data_hora_str = t_str.split(' ', 1)[1]
                formato = "%Y-%m-%d %H:%M:%S"
                dt_local = datetime.strptime(data_hora_str, formato)

                self.log.info(f"RTC lido com sucesso (string parseada): {dt_local}")
                return dt_local
                
            except (ValueError, IndexError, Exception) as e:
                self.log.error(f"Dados do RTC corrompidos ou em formato inesperado! Erro: {e}")
                self.log.error(f"Dados brutos recebidos: {t_str}")
                return None

        except Exception as e:
            self.log.error(f"Erro ao ler do RTC: {e}")
            return None

    def cleanup(self):
        """Limpa os pinos GPIO."""
        if self.rtc:
            self.log.info("Limpando pinos GPIO...")
            self.rtc.cleanupGPIO()

# --- Bloco de Execução Principal ---
if __name__ == "__main__":
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    log_main = logging.getLogger("Main")
    log_main.info("Iniciando script set_rtc.py...")

    meu_rtc = RTCManager()
    
    horario_gps_utc = "004620.00"
    data_gps_utc = "101125"
    
    log_main.info(f"--- Testando Escrita no RTC ---")
    log_main.info(f"Definindo RTC com data: {data_gps_utc}, hora: {horario_gps_utc} (UTC)")
    meu_rtc.set_rtc_from_utc_strings(horario_gps_utc, data_gps_utc)
    log_main.info("Escrita solicitada.")

    log_main.info(f"--- Testando Leitura do RTC (após escrita) ---")
    horario_lido = meu_rtc.read_rtc_datetime()
    
    if horario_lido:
        log_main.info(f"Horário lido do RTC: {horario_lido} (Deve ser ~2025-11-09 21:46:20)")
    else:
        log_main.warning("Não foi possível ler o horário do RTC.")
    
    meu_rtc.cleanup()
    log_main.info("Script finalizado.")
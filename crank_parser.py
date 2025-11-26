import time

from PySide6.QtCore import QThread
from queue import Queue
import signal
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import logging

from comm_protocol import CrankData, PowerData

DURACAO_COLETA_SEGUNDOS = 1 * 60 

class CrankParser(QThread):
    
    ''' Data from the crank: cadence, power '''

    ''' Calculated data: calories, speed, distance'''
    def __init__(self, in_queue: Queue, out_queue: Queue):

        super().__init__()
        self.running = True

        self.in_queue = in_queue
        self.out_queue = out_queue

        self.start_time = time.time()
        self.count = 0
        self.accel = []
        self.weight = 0
    
    def calculate_freq(self, readings, time):

        fft_data = np.fft.fft(readings)
        fft_magnitude = np.abs(fft_data)

        # Compute the frequency axis
        sample_rate = len(readings) / time  # Hz

        n = len(readings)
        freqs = np.fft.fftfreq(n, 1/sample_rate)

        # Keep only the positive frequencies
        half_n = n // 2
        freqs = freqs[:half_n]
        fft_magnitude = fft_magnitude[:half_n]

        # --- Extract dominant frequencies ---
        # Find peaks in the FFT magnitude
        peaks, _ = find_peaks(fft_magnitude, height=np.max(fft_magnitude)*0.2)  # adjust threshold if needed

        # Sort peaks by magnitude (descending)
        top_indices = peaks[np.argsort(fft_magnitude[peaks])][::-1]

        # Pick the top N frequencies
        N = 5
        top_freqs = freqs[top_indices[:N]]
        top_mags = fft_magnitude[top_indices[:N]]

        weighted_avg = 0

        for i in range(len(top_freqs)):
            if top_freqs[i] < 1:
                weighted_avg += top_freqs[i] * top_mags[i]
        if top_mags.sum() == 0:
            logging.info("Person is stopped")
            return 0
        weighted_avg /= top_mags.sum()
        #print(weighted_avg)
        return weighted_avg

    # Refazer pra pegar da queue de verdade (as variáveis fake não são necessárias, apenas setar power e cadence)
    # Retornar True se tiver dados novos, False caso contrário
    def get_from_queue(self) -> bool: 

        # Trocar pelas leituras do bluetooth
        try:

            ble_data =self.in_queue.get(block=True,timeout=0.2)
            #print(ble_data)

            #logging.info("[CankParser] %s", ble_data)
            # Colocar booleano se teve leitura (ou bloquear)
            try:
                if(ble_data):
                    self.accel.append(ble_data.a)
                    self.weight += ble_data.w
                    self.count += 1 
            except Exception as e:
                logging.error(f"[CrankParser] Erro em colocar dados na fila{e}")

        except Exception as e:
            pass#logging.error(f"Erro em extrair dados da fila {e}")

        return ((time.time() - self.start_time) >= 10)

    def calculate_data(self):
        t = time.time()
        if t - self.start_time >= 10:
            
            if len(self.accel) != 0:
                freq = self.calculate_freq(self.accel, t - self.start_time)
                
            else:
                freq = 0

            if freq < 0.2:
                self.power = 0
                self.cadence = 0
            
            else:
                if self.count == 0:
                    avg_weight = 0
                else:
                    avg_weight = self.weight / self.count

                n_rotations = freq * (t - self.start_time)

                pedal_distance = 0.175 * 2 * np.pi * n_rotations

                pedal_speed = pedal_distance / (t - self.start_time)

                # This is because the load cell is going to cause issues due to the direction of the force being applied, my initial guess is 1 / sqrt(2) since the power will be mostly done throughout the front stroke
                magic_number = 2/np.sqrt(2)

                self.power = 2 * pedal_speed * avg_weight * magic_number
                self.cadence = freq * 60 # We want rpm

                # Reset values
            self.start_time = t
            self.count = 0
            self.weight = 0
            self.accel = []
            
            data = PowerData(cadence = self.cadence,power = self.power)
            logging.info(data)
            self.out_queue.put(data)
        
            # Jogar power e cadence na tabela

    def run(self):
        self.running = True
        while(self.running):
            
            if self.get_from_queue():
                self.calculate_data()
            #            time.sleep(0.4) # Precisaria andar a uns 70++kmh para passar disso 

    def stop(self):
        self.running = False

if __name__ == "__main__":
    
    in_queue = Queue()
    out_queue = Queue()

    obj = CrankProcess(in_queue, out_queue)

    signal.signal(signal.SIGINT, signal.SIG_DFL) 

    obj.start()


    time.sleep(5)

    obj.stop()

    obj.wait()
    '''
    # Test
    for i in range(2700):
        obj.get_from_queue()
        obj.calculate_data()
    '''

import csv
import time
import math

from PySide6.QtCore import QThread
from queue import Queue

from comm_protocol import CrankData,TelemetryOrigin,ProcessedDataMsg

class CrankProcessor(QThread):
    
    ''' Data from the crank: cadence, power '''

    ''' Calculated data: calories, speed, distance'''
    def __init__(self, in_queue: Queue, out_queue: Queue):

        super().__init__()
        self.running = True

        self.in_queue = in_queue
        self.out_queue = out_queue

        self.cadence = 0
        self.power = 0

        self.joules = 0
        self.calories = 0
        self.speed_ms = 0
        self.speed = 0
        self.distance = 0

        self.last_power = 0
    
    # Refazer pra pegar da queue de verdade (as variáveis fake não são necessárias, apenas setar power e cadence)
    # Retornar True se tiver dados novos, False caso contrário
    def get_from_queue(self) -> bool: 

        try:

            data = self.in_queue.get(block=True,timeout=0.2)

            self.power = data.power
            self.cadence = data.cadence

            return True
        
        except:
            return False

    def calculate_data(self):

        # Delta energy
        d_energy = (self.power + self.last_power) / 2
        #if not self.cadence:
        #    return
        time = 10

        # Total energy
        self.joules += d_energy * time

        # In kcal
        self.calories = self.joules * 0.23900574 / 1000

        wheel_radius = 0.35 + 0.028 # 700 millimiter + tire radius
        wheel_circunference = wheel_radius * 3.1415 * 2 # Full rotation
        gear_ratio = 44 / 14

        pedal_rotations = self.cadence / 10

        distance = pedal_rotations * gear_ratio * wheel_circunference

        # In meters
        self.distance += distance

        self.speed_ms = distance / 10
        # In km/h
        self.speed = self.speed_ms * 3.6

        self.last_power = self.power

        data = CrankData(self.power, self.cadence, self.joules, self.calories, self.speed_ms ,self.speed, self.distance)
        Telemetry = ProcessedDataMsg(TelemetryOrigin.CRANK, data)
        self.out_queue.put(Telemetry)
        #print(Telemetry)
        #print(self.calories)
        #print(average)

    def run(self):
        while(self.running):
            if self.get_from_queue():
                self.calculate_data()
            #            time.sleep(0.4) # Precisaria andar a uns 70++kmh para passar disso 

    def stop(self):
        self.running = False

if __name__ == "__main__":
    
    in_queue = Queue()
    out_queue = Queue()

    obj = DataCalculator(in_queue, out_queue)

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
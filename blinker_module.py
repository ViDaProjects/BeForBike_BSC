import sys
import time
from PySide6.QtCore import QObject, QThread, Signal, Slot, QTimer
import RPi.GPIO as GPIO
from rpi_ws281x import *
from gpiozero import Button

SERVO_PIN = 12
LEFT_BUTTON_PIN = 5
RIGHT_BUTTON_PIN = 6

LED_COUNT = 6
LED_PIN = 18
LED_BRIGHTNESS = 100
LEDS_TO_LIGHT = 6

LEFT_ANGLE = 2.5
NEUTRAL_ANGLE = 7.5
RIGHT_ANGLE = 12.5

BLINKER_DURATION_MS = 5000
BLINK_INTERVAL_MS = 500

class BlinkerSystemWorker(QObject):
    finished = Signal()
    _buttonPressed = Signal(str)
    blinkerDeactivated = Signal(str)

    def __init__(self):
        super().__init__()
        self.is_busy = False
        self.servo = None
        self.leds = None
        self.blinker_direction = ""

    @Slot()
    def setup_hardware(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(SERVO_PIN, GPIO.OUT)
        
        self.servo = GPIO.PWM(SERVO_PIN, 50)
        self.servo.start(NEUTRAL_ANGLE)
        
        self.leds = Adafruit_NeoPixel(LED_COUNT, LED_PIN, brightness=LED_BRIGHTNESS)
        self.leds.begin()
        self._turn_leds_off()
        
        self.blink_timer = QTimer()
        self.duration_timer = QTimer()
        
        self.blink_timer.setInterval(int(BLINK_INTERVAL_MS / 2))
        self.blink_timer.timeout.connect(self._on_blink_timeout)
        
        self.duration_timer.setSingleShot(True)
        self.duration_timer.setInterval(BLINKER_DURATION_MS)
        self.duration_timer.timeout.connect(self._on_duration_timeout)

    def _turn_leds_on(self):
        for i in range(LEDS_TO_LIGHT):
            self.leds.setPixelColor(i, Color(255, 100, 0))
        self.leds.show()

    def _turn_leds_off(self):
        for i in range(self.leds.numPixels()):
            self.leds.setPixelColor(i, Color(0,0,0))
        self.leds.show()

    @Slot()
    def _on_blink_timeout(self):
        if not hasattr(self, '_led_state'):
            self._led_state = False
            
        if self._led_state:
            self._turn_leds_off()
            self._led_state = False
        else:
            self._turn_leds_on()
            self._led_state = True

    @Slot()
    def _on_duration_timeout(self):
        self.blink_timer.stop()
        self.servo.ChangeDutyCycle(NEUTRAL_ANGLE)
        self._turn_leds_off()
        self.is_busy = False

        #Send signal to UI to disable arrow icon
        self.blinkerDeactivated.emit(self.blinker_direction)

    @Slot(str)
    def do_trigger_blink(self, direction):
        if self.is_busy:
            return

        self.is_busy = True
        self._buttonPressed.emit(direction)
        self.blinker_direction = direction
        angle = LEFT_ANGLE if direction == "left" else RIGHT_ANGLE
        self.servo.ChangeDutyCycle(angle)
        
        self._led_state = False
        self.blink_timer.start()
        self.duration_timer.start()

    @Slot()
    def stop(self):
        if hasattr(self, 'blink_timer'):
            self.blink_timer.stop()
        if hasattr(self, 'duration_timer'):
            self.duration_timer.stop()
        
        self.servo.ChangeDutyCycle(NEUTRAL_ANGLE)
        self._turn_leds_off()
        GPIO.cleanup()
        self.finished.emit()

class BlinkerSystem(QObject):
    _stop_worker_requested = Signal()
    blinkerActivated = Signal(str)
    _trigger_requested = Signal(str)

    def __init__(self, app_instance):
        super().__init__()
        self.thread = QThread()
        self.worker = BlinkerSystemWorker()
        self.worker.moveToThread(self.thread)
        
        self._stop_worker_requested.connect(self.worker.stop)
        self.worker.finished.connect(self.thread.quit)
        self.thread.started.connect(self.worker.setup_hardware)
        self.worker._buttonPressed.connect(self.blinkerActivated)
        self._trigger_requested.connect(self.worker.do_trigger_blink)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(app_instance.quit)
        
        self.left_button = Button(LEFT_BUTTON_PIN, pull_up=False)
        self.right_button = Button(RIGHT_BUTTON_PIN, pull_up=False)

        self.left_button.when_pressed = self.handle_left_press
        self.right_button.when_pressed = self.handle_right_press
        
        self.thread.start()

    def handle_left_press(self):
        self._trigger_requested.emit("left")
        
    def handle_right_press(self):
        self._trigger_requested.emit("right")

    def cleanup(self):
        if self.thread.isRunning():
            self._stop_worker_requested.emit()
            self.thread.wait()

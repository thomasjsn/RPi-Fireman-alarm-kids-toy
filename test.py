import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)   # set board mode to Broadcom
GPIO.setwarnings(False)  # don't show warnings

greenButton = 20
redButton = 16
bottomButton = 21

greenLamp = 5
yellowLamp = 6
redLamp = 13
blueStrobe = 19
buzzer = 26

GPIO.setup(greenButton, GPIO.IN)
GPIO.setup(redButton, GPIO.IN)
GPIO.setup(bottomButton, GPIO.IN)

GPIO.setup(greenLamp, GPIO.OUT)
GPIO.setup(yellowLamp, GPIO.OUT)
GPIO.setup(redLamp, GPIO.OUT)
GPIO.setup(blueStrobe, GPIO.OUT)
GPIO.setup(buzzer, GPIO.OUT)


def get_input(pin):
    return not GPIO.input(pin)


def set_output(pin, state):
    return GPIO.output(pin, state)


def shutdown():
    command = "/usr/bin/sudo /sbin/shutdown -H now"
    import subprocess
    subprocess.Popen(command.split(), stdout=subprocess.PIPE)


def boot_sequence():
    set_output(redLamp, True)
    time.sleep(2)
    set_output(redLamp, False)
    set_output(greenLamp, True)
    time.sleep(0.5)
    set_output(greenLamp, False)

    for i in range(2):
        set_output(buzzer, True)
        time.sleep(0.05)
        set_output(buzzer, False)
        time.sleep(0.05)
    return


def shutdown_sequence():
    start_time = time.time()
    while get_input(bottomButton) is False:
        set_output(redLamp, True)
        time.sleep(0.1)
        set_output(redLamp, False)
        time.sleep(0.1)
        if (time.time() - start_time) > 10:
            set_output(greenLamp, True)
            set_output(yellowLamp, True)
            set_output(redLamp, True)
            shutdown()

    set_output(greenLamp, True)
    time.sleep(0.1)
    set_output(greenLamp, False)
    time.sleep(0.1)
    return

boot_sequence()
start_time = time.time()

while True:
    if get_input(greenButton) is True and get_input(redButton) is False:
        set_output(greenLamp, True)
        time.sleep(0.5)
        set_output(greenLamp, False)
        set_output(blueStrobe, True)

    if get_input(redButton) is True and get_input(greenButton) is False:
        set_output(redLamp, True)
        time.sleep(0.5)
        set_output(redLamp, False)
        set_output(blueStrobe, False)

    if get_input(greenButton) is True and get_input(redButton) is True:
        set_output(yellowLamp, True)
        time.sleep(0.5)
        set_output(yellowLamp, False)

        for i in range(3):
            set_output(buzzer, True)
            time.sleep(0.1)
            set_output(buzzer, False)
            time.sleep(0.1)

    if get_input(bottomButton) is False and get_input(redButton) is True:
        shutdown_sequence()

    time.sleep(0.1)

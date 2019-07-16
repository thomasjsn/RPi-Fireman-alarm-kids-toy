import RPi.GPIO as GPIO
import time
import paho.mqtt.client as mqtt

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

buzzerEnable = False
greenEnable = False
yellowEnable = False
redEnable = False

upperBunk = None


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("node/gzl/+/+")
    client.subscribe("state/kids/top_bunk")

    if rc==0:
        client.connected_flag=True
        client.publish("$CONNECTED/gzl", 1, retain=True)
    else:
        client.bad_connection_flag=True


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic + " " + str(msg.payload))
    if msg.topic == 'node/gzl/strobe/set':
        value = set_output(blueStrobe, bool(int(msg.payload.decode('utf-8'))))
        client.publish('node/gzl/strobe', value)

    if msg.topic == 'node/gzl/buzzer/set':
        global buzzerEnable
        buzzerEnable = bool(int(msg.payload.decode('utf-8')))
        client.publish('node/gzl/buzzer', int(buzzerEnable))
        print(buzzerEnable)

    if msg.topic == 'node/gzl/green/set':
        global greenEnable
        greenEnable = bool(int(msg.payload.decode('utf-8')))
        client.publish('node/gzl/green', int(greenEnable))

    if msg.topic == 'node/gzl/yellow/set':
        global yellowEnable
        yellowEnable = bool(int(msg.payload.decode('utf-8')))
        client.publish('node/gzl/yellow', int(yellowEnable))

    if msg.topic == 'node/gzl/red/set':
        global redEnable
        redEnable = bool(int(msg.payload.decode('utf-8')))
        client.publish('node/gzl/red', int(redEnable))

    if msg.topic == 'state/kids/top_bunk':
        global upperBunk
        upperBunk = msg.payload.decode('utf-8')
        print(upperBunk)


def get_input(pin):
    return not GPIO.input(pin)


def set_output(pin, state):
    GPIO.output(pin, state)
    return GPIO.input(pin)


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

    #for i in range(2):
    #    set_output(buzzer, True)
    #    time.sleep(0.05)
    #    set_output(buzzer, False)
    #    time.sleep(0.05)


def shutdown_sequence():
    start_time = time.time()

    while get_input(bottomButton) is False:
        remain = time.time() - start_time
        if remain > 3:
            set_output(greenLamp, True)
        if remain > 6:
            set_output(yellowLamp, True)
        if remain > 9:
            set_output(redLamp, True)
        time.sleep(0.1)
        set_output(greenLamp, False)
        set_output(yellowLamp, False)
        set_output(redLamp, False)
        time.sleep(0.1)
        if remain > 12:
            set_output(greenLamp, False)
            set_output(yellowLamp, True)
            set_output(redLamp, False)
            shutdown()

    set_output(greenLamp, True)
    time.sleep(1)
    set_output(greenLamp, False)
    time.sleep(1)

print('boot')
boot_sequence()
start_time = time.time()

client = mqtt.Client('gzl')
client.on_connect = on_connect
client.on_message = on_message
client.will_set("$CONNECTED/gzl", 0, qos=0, retain=True)
client.connect("mqtt.lan.uctrl.net")
client.loop_start()

while True:
    set_output(buzzer, False)

    if get_input(greenButton) is True and get_input(redButton) is False:
        print('green pressed')
        set_output(greenLamp, True)
        time.sleep(0.5)
        set_output(greenLamp, False)
        set_output(blueStrobe, True)
        client.publish('node/gzl/strobe', 1)

    if get_input(redButton) is True and get_input(greenButton) is False:
        print('red pressed')
        set_output(redLamp, True)
        time.sleep(0.5)
        set_output(redLamp, False)
        set_output(blueStrobe, False)
        client.publish('node/gzl/strobe', 0)

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

    if get_input(bottomButton) is False and bool(GPIO.input(blueStrobe)) is False:
        for i in range(5):
            set_output(yellowLamp, True)
            time.sleep(0.5)
            set_output(yellowLamp, False)
            time.sleep(0.5)

        if upperBunk == 'Alexander':
            set_output(redLamp, True)
        if upperBunk == 'Niklas':
            set_output(greenLamp, True)

        time.sleep(10)
        #set_output(buzzer, True)
        #time.sleep(0.1)
        #set_output(buzzer, False)

        set_output(redLamp, False)
        set_output(greenLamp, False)

    if bool(GPIO.input(blueStrobe)) is True and buzzerEnable is True and (time.time() - start_time) > 3:
        set_output(buzzer, True)
        start_time = time.time()

    if greenEnable:
        set_output(greenLamp, not GPIO.input(greenLamp))
    else:
        set_output(greenLamp, False)

    if yellowEnable:
        set_output(yellowLamp, not GPIO.input(yellowLamp))
    else:
        set_output(yellowLamp, False)

    if redEnable:
        set_output(redLamp, not GPIO.input(redLamp))
    else:
        set_output(redLamp, False)

    time.sleep(0.1)

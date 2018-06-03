import RPi.GPIO as GPIO
import time
import signal
import atexit

def init():
    atexit.register(GPIO.cleanup)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(6,GPIO.OUT,initial=GPIO.HIGH)
    # GPIO.setup(21,GPIO.OUT,initial=GPIO.HIGH)
    # GPIO.setup(13,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
    # GPIO.setup(20,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)


p1_now=4
p2_now=7

def beep(flag):
    if flag:
        GPIO.output(6,GPIO.LOW)
    else:
        GPIO.output(6,GPIO.HIGH)
    # time.sleep(seconds)

def beepBatch(seconds,timespan,counts):
    for i in range(counts):
        beep(seconds)
        time.sleep(timespan)

def distance():
    return GPIO.input(13)

def smoke():
    return GPIO.input(20)

def tem():
    i=tem1()
    i1=tem1()
    if i==0:
        return i1
    else:
        return i

def tem1():
    time.sleep(2)
    GPIO.setup(12, GPIO.OUT)
    GPIO.output(12, GPIO.LOW)
    time.sleep(0.02)
    GPIO.output(12, GPIO.HIGH)
    GPIO.setup(12, GPIO.IN)
    data = [0 for i in range(40)]
    j = 0
    while GPIO.input(12) == GPIO.LOW:
        continue
    while GPIO.input(12) == GPIO.HIGH:
        continue
    while j < 40:
        k = 0
        while GPIO.input(12) == GPIO.LOW:
            continue
        while GPIO.input(12) == GPIO.HIGH:
            k += 1
            if k > 100:
                break
        if k < 8:
            data[j]=0
        else:
            data[j]=1

        j += 1

    humidity_bit = data[0:8]
    humidity_point_bit = data[8:16]
    temperature_bit = data[16:24]
    temperature_point_bit = data[24:32]
    check_bit = data[32:40]

    humidity = 0
    humidity_point = 0
    temperature = 0
    temperature_point = 0
    check = 0
    for i in range(8):
        humidity += humidity_bit[i] * 2 ** (7-i)
        humidity_point += humidity_point_bit[i] * 2 ** (7-i)
        temperature += temperature_bit[i] * 2 ** (7-i)
        temperature_point += temperature_point_bit[i] * 2 ** (7-i)
        check += check_bit[i] * 2 ** (7-i)

    tmp = humidity + humidity_point + temperature + temperature_point

    if check == tmp:
        return temperature,humidity
    else:
        return 0,0

def turn1(direction):
    global p1_now
    global p2_now
    p1 = get_pin(19)
    p2 = get_pin(26)
    print(direction)
    if direction == "up":
        p1_now+=0.2
        p1.ChangeDutyCycle(p1_now)
        # print(p1_now)
        time.sleep(0.2)
    elif direction == "down" :
        p1_now-=0.2
        p1.ChangeDutyCycle(p1_now)
        time.sleep(0.2)
    elif direction == "left" :
        p2_now+=0.2
        p2.ChangeDutyCycle(p2_now)
        time.sleep(0.2)
    elif direction == "right":
        p2_now-=0.2
        p2.ChangeDutyCycle(p2_now)
        time.sleep(0.2)
    else:
        pass

def turn(direction):
    turn1(direction)
    # time.sleep(0.1)

def get_pin(servopin):
    GPIO.setup(servopin, GPIO.OUT, initial=False)
    p = GPIO.PWM(servopin, 50)
    p.start(0)
    print('initial the pin %d' %servopin)
    return p


def reset():
    #p1 3~6 4=mid
    #p2 5~9 7=mid

    p1 = get_pin(19)
    p2 = get_pin(26)
    p1.ChangeDutyCycle(4)
    p1_now=4
    time.sleep(1)
    p2.ChangeDutyCycle(7)
    p2_now=7
    time.sleep(1)


import time
import RPi.GPIO as GPIO  
import signal
import atexit

# initialize status
# if the owner is in house
owner_flag = False
# the current people number in house
owner_number = 0
# if a stranger comes in
stranger_flag = False
# frame counting
frame_num = 0
# cemera switch
p1_now = 4
p2_now = 7.5 

# hardware part
def beep(flag):  
	if flag==1:
		GPIO.output(21,GPIO.LOW) 
	else:
		GPIO.output(21,GPIO.HIGH)   
	
def turn1(direction):
	global p1_now
	global p2_now
	p1 = get_pin(19)
	p2 = get_pin(26)
	if direction == "up":
		p1_now+=0.2
		p1.ChangeDutyCycle(p1_now)
		# print(p1_now)
	elif direction == "down" :
		p1_now-=0.2
		p1.ChangeDutyCycle(p1_now)
	elif direction == "left" :
		p2_now+=0.2
		p2.ChangeDutyCycle(p2_now)
	elif direction == "right":
		p2_now-=0.2
		p2.ChangeDutyCycle(p2_now)

def get_pin(servopin):
	GPIO.setup(servopin, GPIO.OUT, initial=False)
	p = GPIO.PWM(servopin, 50)
	p.start(0)
	return p
	
def reset():
	#p1 3~6 4=mid
	#p2 5~9 7.5=mid
	global p1_now, p2_now
	p1 = get_pin(19)
	p2 = get_pin(26)
	p1.ChangeDutyCycle(4)
	p1_now=4
	time.sleep(1)
	p2.ChangeDutyCycle(7.5)
	p2_now=7.5
	time.sleep(1)

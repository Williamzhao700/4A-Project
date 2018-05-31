import time
import subprocess

print('[i] Starting 3 processes...')

p1 = subprocess.Popen(('python3', 'server.py'))
p2 = subprocess.Popen(('python3', 'server_streaming.py'))
p3 = subprocess.Popen(('python3', 'person_recognition.py'))

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print('[!] Killing all servers and tasks...')
    p1.kill()
    p2.kill()
    p3.kill()

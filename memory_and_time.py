import subprocess
import psutil
import os
import time
import matplotlib.pyplot as plt


memory = []
i = 0
x = []

shell_cmd = 'testrun.bat'
p = subprocess.Popen(["python", "main.py", "evaluation/astrea_test/time/mapping.ttl"], shell=True)
start = time.time()
while p.poll() is None:
    try:
        time.sleep(0.1)
        i += 1
        x += [i]
        memory.append((psutil.Process(p.pid).memory_info().rss / 1024 ** 2))
        print((psutil.Process(p.pid).memory_info().rss / 1024 ** 2))
    except:
        break

memory.append((psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2))
end = time.time()
ptime = end - start
plt.plot(x, memory)
print(ptime)
plt.show()
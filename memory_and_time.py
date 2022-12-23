import subprocess
import psutil
import os
import time
import matplotlib.pyplot as plt
import numpy as np

memory = []
cpu = []
p = subprocess.Popen(["python", "main.py", "evaluation/astrea_test/time/mapping.ttl"], shell=True)
# p = subprocess.Popen(["evaluation.bat"], shell=True)
current_process = psutil.Process(p.pid)
children = psutil.Process(p.pid).children(recursive=True)
start = time.time()
while p.poll() is None:
    try:
        currentmem = current_process.memory_info()[0]
        currentcpu = current_process.cpu_percent()
        for child in current_process.children(recursive=True):
            currentmem += child.memory_info()[0]
            currentcpu += child.cpu_percent()
        currentmem = (currentmem / 1024 ** 2)
        memory.append(currentmem)
        cpu.append(currentcpu)

    except:
        pass

ptime = round(time.time() - start, 1)
x = np.linspace(0, ptime, len(memory))

# Memory usage
plt.figure(1)
plt.plot(x, memory)
plt.title('Memory usage in MiB')
# axs[0].set_ylabel('Memory [MiB]')
plt.xlabel('time [s]')

# CPU usage
plt.figure(2)
plt.plot(x, cpu)
plt.title('CPU usage in %')
# axs[1].set_ylabel('CPU usage [%]')
plt.xlabel('time [s]')

# time
print('----------------------------------')
print(f"Total execution time in seconds: {ptime}s")
plt.show()

# timelist = []
# timemax = 0
# timemin = 9999999
# for i in range(50):
#
#     p = subprocess.Popen(["evaluation1.bat"], shell=True)
#     current_process = psutil.Process(os.getpid())
#     children = psutil.Process(p.pid).children(recursive=True)
#     start = time.time()
#     while p.poll() is None:
#         try:
#             time.sleep(0.1)
#         except:
#             pass
#     ptime = round(time.time() - start, 1)
#     timelist.append(ptime)
#     if ptime < timemin:
#         timemin = (ptime*1)
#     if ptime > timemax:
#         timemax = (ptime*1)
# timeavg = sum(timelist) / len(timelist)
# print('min:',timemin)
# print('max:',timemax)
# print('avg:',timeavg)
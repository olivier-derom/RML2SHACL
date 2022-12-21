import subprocess
import psutil
import os
import time
import matplotlib.pyplot as plt
import numpy as np
import tracemalloc

memory = []
cpu = []

shell_cmd = 'testrun.bat'
p = subprocess.Popen(["python", "main.py", "evaluation/astrea_test/time/mapping.ttl"], shell=True)
# p = subprocess.Popen(["evaluation.bat"], shell=True)
current_process = psutil.Process(os.getpid())
children = psutil.Process(p.pid).children(recursive=True)
start = time.time()
while p.poll() is None:
    try:
        time.sleep(0.1)
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

end = time.time()
ptime = round(end - start, 1)
x = np.linspace(0, ptime, len(memory))
fig, axs = plt.subplots(2, 2)
axs[0, 0].plot(x, memory)
axs[0, 0].set_title('Memory usage in MiB')
# axs[0, 0].set_ylabel('Memory [MiB]')
axs[0, 0].set_xlabel('time [s]')
axs[0, 1].plot(x, cpu)
axs[0, 0].set_title('CPU usage in %')
# axs[0, 1].set_ylabel('CPU usage [%]')
axs[0, 1].set_xlabel('time [s]')
print(ptime)
plt.show()
